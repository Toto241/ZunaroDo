"""
GUI - CustomTkinter-Oberflaeche fuer ZunaroDo.

Die GUI ist nur ein Front-End. Sie greift NIE direkt auf Datenbank oder
Module zu, sondern ausschliesslich ueber die Schnittstellen:
  - registry.collect_events()    -> Dashboard
  - registry.context_overview()  -> Modulstatus
  - registry.dispatch(...)       -> Aktionen
  - assistant.ask(...)           -> Chat

Tabs:
  Dashboard - Vertraege - Familie - Finanzen - Kalender - Sozial
  - Posteingang - Assistent

Start:  python gui.py
"""
from __future__ import annotations

import os
import queue
import re
import threading
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from app_core.presenters import (DashboardPresenter, OrdersPresenter,
                                 SearchPresenter)
from app_core.profiles import ProfilesManager
from assistant import Assistant
from core.interface import ModuleRegistry
from database import (AssistantLogRepository, AuditLogRepository, Database,
                      ModuleStateRepository, SettingsRepository)
from main import (apply_persisted_module_states, build_registry,
                    make_auto_backup_worker, make_smtp_config)
from services.sync_runtime import resolve_sync_provider
from services.config import (DEFAULTS, ENV_MAP, SECRET_KEYS, AppConfig,
                              load_config, save_value)
from services.gemini import GeminiClient
from services.i18n import I18n
from services.output import OutputService
from services.profile import db_path, resolve_profile, state_dir
from services.scheduler import ProactiveScheduler
from services.sync import PeriodicSyncWorker, install_sync_hook

SAMPLE_MAIL = (
    "Betreff: Information zu Ihrem Netflix-Abo\n\n"
    "Sehr geehrter Kunde, wir nehmen eine Preisanpassung vor. Ihr neuer "
    "monatlicher Preis betraegt 15,99 EUR.\n\nIhr Netflix-Team")

URGENCY_COLOR = {"hoch": "#d9534f", "mittel": "#e8a33d", "normal": "#5b9bd5"}
URGENCY_LABEL = {"hoch": "DRINGEND", "mittel": "BALD", "normal": "GEPLANT"}
# Einheitliche Karten-/Trennlinien-Farbe (Light, Dark) - Windows-11-Fluent.
# Zentral, damit alle Tabs denselben Rahmen verwenden.
CARD_BORDER = ("#E5E5E5", "#3A3A3A")
APP_DISPLAY_NAME = "ZunaroDo"
_WIN11_APPEARANCE_MODE = "light"
_CRITICAL_CONFIRMATION_CAPABILITIES = {
    "inbox.bulk_delete_archived",
    "notes.delete",
    "templates.delete",
}
_CRITICAL_CONFIRMATION_PREFIXES = (
    "calendar.purge",
    "contracts.purge",
    "family.purge",
    "finance.purge",
    "social.purge",
)

# ---------------------------------------------------------------------------
# Windows-11-Look (Fluent / Mica) fuer die Desktop-Oberflaeche
# ---------------------------------------------------------------------------
_FONT_CANDIDATES = (
    "Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI",
    "Segoe UI Emoji", "Helvetica", "Arial",
)


def _win11_font(size: int = 13, weight: str = "normal") -> ctk.CTkFont:
    """Liefert einen CTkFont im Windows-11-Stil mit Fallback."""
    try:
        import tkinter.font as tkfont
        available = set(tkfont.families())
    except Exception:                                  # noqa: BLE001
        available = set()
    for family in _FONT_CANDIDATES:
        if not available or family in available:
            return ctk.CTkFont(family=family, size=size, weight=weight)
    return ctk.CTkFont(size=size, weight=weight)


def _apply_win11_theme() -> None:
    """
    Patched die globalen customtkinter-Theme-Werte fuer einen
    Windows-11-Look (abgerundete Ecken, Segoe UI, sanfte Farben).
    Muss VOR Erzeugung der Widgets aufgerufen werden.
    """
    ctk.set_appearance_mode(_WIN11_APPEARANCE_MODE)
    ctk.set_default_color_theme("blue")

    theme = ctk.ThemeManager.theme
    # Buttons: moderate Abrundung wie Win11
    theme["CTkButton"]["corner_radius"] = 6
    theme["CTkButton"]["border_spacing"] = 6
    # Frames / Cards
    theme["CTkFrame"]["corner_radius"] = 8
    # Eingabefelder
    theme["CTkEntry"]["corner_radius"] = 6
    theme["CTkOptionMenu"]["corner_radius"] = 6
    theme["CTkComboBox"]["corner_radius"] = 6
    # Tabs (aeltere customtkinter-Versionen haben kein CTkTabview-Theme)
    tabview = theme.get("CTkTabview")
    if isinstance(tabview, dict):
        tabview["corner_radius"] = 8
        seg = tabview.get("segmented_button")
        if isinstance(seg, dict):
            seg["corner_radius"] = 6
    # Texte
    theme["CTkTextbox"]["corner_radius"] = 6
    theme["CTkScrollableFrame"]["corner_radius"] = 8
    # Schriftfamilie global bevorzugen
    for widget_key in theme:
        if isinstance(theme[widget_key], dict) and "font" in theme[widget_key]:
            font_spec = theme[widget_key]["font"]
            if isinstance(font_spec, tuple) and len(font_spec) >= 2:
                theme[widget_key]["font"] = (_FONT_CANDIDATES[2],) + font_spec[1:]


def _critical_confirmation_required(capability_name: str) -> bool:
    """True fuer irreversible oder gebuendelte Aktionen."""
    return (capability_name in _CRITICAL_CONFIRMATION_CAPABILITIES
            or any(capability_name.startswith(prefix)
                   for prefix in _CRITICAL_CONFIRMATION_PREFIXES))


# Tk-Geometry-String: 'WIDTHxHEIGHT' oder 'WIDTHxHEIGHT+X+Y' (X/Y koennen
# auch negativ sein). Mit Sanity-Bounds: kein Fenster ausserhalb realer
# Bildschirme.
_GEOMETRY_RE = re.compile(r"^(\d+)x(\d+)(?:([+-]\d+)([+-]\d+))?$")


def _is_valid_geometry(value: str) -> bool:
    if not value:
        return False
    m = _GEOMETRY_RE.match(value)
    if not m:
        return False
    w, h = int(m.group(1)), int(m.group(2))
    if not (300 <= w <= 8000 and 200 <= h <= 5000):
        return False
    if m.group(3) and m.group(4):
        x, y = int(m.group(3)), int(m.group(4))
        if not (-2000 <= x <= 8000 and -2000 <= y <= 5000):
            return False
    return True


# ---------------------------------------------------------------------
#  Beispieldaten beim ersten Start
# ---------------------------------------------------------------------
def _has_any_data(registry: ModuleRegistry) -> bool:
    """True, wenn schon irgendwelche Nutzdaten vorhanden sind."""
    if registry.dispatch("contracts.list", {}).get("count", 0) > 0:
        return True
    if registry.dispatch("family.members", {}).get("count", 0) > 0:
        return True
    return False


def _seed_demo_data(registry: ModuleRegistry) -> None:
    """Legt das bekannte Demo-Datenset an. NICHT automatisch."""
    registry.dispatch("family.add_member",
                        {"name": "Anna", "role": "erwachsen",
                         "birthday": "1989-07-12"})
    registry.dispatch("family.add_member",
                        {"name": "Bernd", "role": "erwachsen",
                         "birthday": "1986-03-04"})
    registry.dispatch("family.add_member",
                        {"name": "Mia", "role": "kind",
                         "birthday": "2018-11-22"})
    # Anna explizit namentlich suchen statt blind ueber Index [0] zu
    # greifen - so bricht der Seed-Pfad nicht, falls jemand die
    # Reihenfolge oben veraendert oder die DB nicht ganz leer war.
    members = registry.dispatch("family.members", {}).get("members", [])
    anna_id = next(
        (m["id"] for m in members if m["name"].lower() == "anna"),
        members[0]["id"] if members else None,
    )
    if anna_id is None:
        return
    for v in [
        dict(name="Handyvertrag", category="mobilfunk", provider="Telekom",
             customer_number="DE-4471180", start_date="2024-06-01",
             minimum_term_months=24, notice_period_months=3,
             auto_renew_months=12, monthly_cost=39.99, owner_id=anna_id),
        dict(name="Streaming-Abo", category="streaming", provider="Netflix",
             customer_number="NF-99213", start_date="2025-11-01",
             minimum_term_months=1, notice_period_months=1,
             auto_renew_months=1, monthly_cost=13.99, owner_id=anna_id),
    ]:
        registry.dispatch("contracts.add", v)
    registry.dispatch("family.add_task", {
        "title": "Muell rausbringen", "interval_days": 7,
        "assignees": ["Anna", "Bernd"],
        "first_due": (date.today() + timedelta(days=2)).isoformat()})
    registry.dispatch("family.add_order", {
        "title": "Auto zur Inspektion bringen", "assignee": "Bernd",
        "due_date": (date.today() + timedelta(days=5)).isoformat(),
        "description": "Werkstatt-Termin ist vereinbart."})
    registry.dispatch("calendar.add_event", {
        "title": "TUEV Familienauto",
        "due_date": (date.today() + timedelta(days=45)).isoformat(),
        "category": "tuev"})
    registry.dispatch("social.add_contact",
                        {"name": "Oma", "relation": "Familie",
                         "cadence_days": 14})


def bootstrap() -> tuple[Database, ModuleRegistry, Assistant, AppConfig,
                          SettingsRepository, ModuleStateRepository, object,
                          str]:
    # Aktives Profil: Env (ALLTAGSHELFER_PROFILE) hat Vorrang, sonst die
    # per UI/Assistent gesetzte Pointer-Datei (ProfilesManager) - so wirkt
    # ein Profilwechsel ueber Neustarts hinweg.
    profile = ProfilesManager().active()
    # Vereinheitlichter Basis-Dateiname: 'alltagshelfer.db', plus optional
    # ein '-<profil>'-Suffix. Frueher gab es zwei verschiedene Default-
    # Namen (alltagshelfer_demo / alltagshelfer_gui), das ist jetzt
    # konsistent (F4).
    db = Database(db_path(profile, "alltagshelfer.db"))
    settings = SettingsRepository(db)
    config = load_config(settings)

    output = OutputService("ausgaben", smtp=make_smtp_config(config))
    # Lizenz vor Gemini-Init pruefen - Free/abgelaufen = kein LLM-Start
    from services.licensing import load_license
    from services.license_gate import install_gate
    license_at_boot = load_license(settings)
    if license_at_boot.allows_ai():
        llm = GeminiClient(model=config.gemini_model,
                           api_key=config.gemini_api_key or None)
        active_llm = llm if llm.is_available else None
    else:
        active_llm = None
    registry = build_registry(db, output, llm=active_llm)
    install_gate(registry, lambda: load_license(settings))
    # Grandfathering: einmalig markieren, wenn beim ersten Pricing-
    # Launch bereits Daten vorliegen. Laeuft NACH install_gate, damit
    # die Lese-Calls (_has_any_data) durch den Gate gehen - die
    # ALWAYS_OPEN-Liste haelt sie offen.
    from services.licensing import apply_grandfathering_if_needed
    apply_grandfathering_if_needed(settings, lambda: _has_any_data(registry))

    module_states = ModuleStateRepository(db)
    apply_persisted_module_states(registry, module_states)

    # Audit-Hook fuer destruktive Aktionen
    _audit_repo = AuditLogRepository(db)

    def _audit(capability: str, args: dict, result: dict) -> None:
        import json as _json
        entity_type = capability.split(".", 1)[0]
        eid = (args.get("contract_id") or args.get("event_id")
                or args.get("contact_id") or args.get("member_id")
                or args.get("expense_id") or args.get("note_id")
                or args.get("proposal_id") or args.get("task_id")
                or args.get("order_id"))
        try:
            details = _json.dumps(args, ensure_ascii=False)[:500]
        except Exception:
            details = str(args)[:500]
        _audit_repo.append(capability, entity_type=entity_type,
                              entity_id=eid, details=details,
                              actor=profile or "local")

    registry.set_audit_hook(_audit)

    # Onboarding wird im GUI-Hauptloop entschieden (nicht automatisch).
    assistant = Assistant(
        registry, log=AssistantLogRepository(db), llm=active_llm,
        max_iterations=config.gemini_max_iterations,
        max_output_tokens=config.gemini_max_tokens,
    )

    provider = resolve_sync_provider(config, settings, state_dir(profile))
    synced = None
    if provider is not None:
        synced = install_sync_hook(registry, provider)
        try:
            provider.compact_if_needed()
        except Exception:
            pass
        synced.apply_remote()
    auto_backup = make_auto_backup_worker(db, config)
    return (db, registry, assistant, config, settings, module_states,
            synced, profile, auto_backup)


# ---------------------------------------------------------------------
#  Wiederverwendbare Hilfen
# ---------------------------------------------------------------------
def _labeled_entry(parent, label: str, placeholder: str = "",
                   width: int = 200) -> ctk.CTkEntry:
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=3)
    ctk.CTkLabel(row, text=label, width=130, anchor="w").pack(side="left")
    entry = ctk.CTkEntry(row, placeholder_text=placeholder, width=width)
    entry.pack(side="left", fill="x", expand=True)
    return entry


def _labeled_option_menu(parent, label: str, values: list[str],
                         default: str = "") -> ctk.CTkOptionMenu:
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=3)
    ctk.CTkLabel(row, text=label, width=130, anchor="w").pack(side="left")
    menu = ctk.CTkOptionMenu(row, values=values)
    menu.set(default or (values[0] if values else ""))
    menu.pack(side="left", fill="x", expand=True)
    return menu


def _parse_float(raw: str, default: float = 0.0) -> float:
    # Akzeptiert deutsche Komma-Dezimalzahlen ("10,50"); leer -> default.
    raw = (raw or "").strip().replace(",", ".")
    return float(raw) if raw else default


def _parse_int(raw: str, default: int = 0) -> int:
    raw = (raw or "").strip()
    return int(raw) if raw else default


def _clear(frame) -> None:
    for w in frame.winfo_children():
        w.destroy()


def _empty_state(parent, text: str) -> None:
    """Einheitlicher, zentrierter Leer-Zustand fuer Listen/Tabs.

    Wird ueber alle Tabs hinweg verwendet, damit ein leerer Bereich immer
    gleich aussieht (statt ad-hoc grauer Labels mit wechselndem Padding).
    """
    box = ctk.CTkFrame(parent, fg_color="transparent")
    box.pack(fill="x", pady=(46, 0))
    ctk.CTkLabel(box, text="—", text_color="gray",
                 font=_win11_font(size=22, weight="bold")).pack()
    ctk.CTkLabel(box, text=text, text_color="gray",
                 font=_win11_font(size=13)).pack(pady=(2, 0))


def _card_row(parent):
    """Einheitliche Listenzeile als dezente Karte (gleiches Aussehen wie die
    Vertraege-/Posteingang-Karten). Gibt den inneren Body-Frame zurueck, in
    den der Aufrufer Label/Buttons packt."""
    card = ctk.CTkFrame(parent)
    card.pack(fill="x", pady=4, padx=2)
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.pack(fill="x", padx=12, pady=8)
    return body


# ---------------------------------------------------------------------
#  Hauptfenster
# ---------------------------------------------------------------------
class AlltagshelferGUI(ctk.CTk):

    def __init__(self, registry: ModuleRegistry, assistant: Assistant,
                 config: AppConfig,
                 settings_repo: SettingsRepository,
                 module_states: ModuleStateRepository,
                 synced=None,
                 profile: str = "",
                 auto_backup=None):
        super().__init__()
        self.registry = registry
        # Geteilte, headless getestete Verhaltens-Schicht (app_core).
        self._present_search = SearchPresenter(registry.dispatch)
        self._present_orders = OrdersPresenter(registry.dispatch)
        self._present_dashboard = DashboardPresenter(registry.dispatch)
        self.assistant = assistant
        self.config = config
        self.settings_repo = settings_repo
        self.module_states = module_states
        self.synced = synced
        self.profile = profile
        self.auto_backup = auto_backup
        self.i18n = I18n(language=config.i18n_language)
        # Sammlung aller scheduled-After-Callbacks fuer sauberes Canceln
        # beim Fenster-Close - frueher lazy, jetzt explizit (F2).
        self._after_ids: set[str] = set()
        self._streaming_active: bool = False
        # Tk/Tcl ist NICHT thread-sicher: Hintergrund-Worker duerfen .after()
        # nicht direkt aufrufen. Stattdessen legen sie Callables in diese
        # Queue, die ein Main-Thread-Loop (_drain_ui_queue) abarbeitet.
        self._ui_queue: "queue.Queue" = queue.Queue()
        self._drain_ui_queue()
        from services.license_events import license_event_source
        from services.licensing import load_license as _load_license_for_sched
        self.scheduler = ProactiveScheduler(
            registry, warn_within_days=config.notify_warn_within_days,
            extra_event_sources=[
                license_event_source(
                    lambda: _load_license_for_sched(self.settings_repo)),
            ],
            state_path=(state_dir(self.profile)
                        / ProactiveScheduler.STATE_FILE_NAME))
        self.sync_worker = PeriodicSyncWorker(
            synced, interval_seconds=config.sync_interval_seconds) \
            if synced is not None else None

        self.title(self.i18n.t("app.title"))
        # Persistierte Geometrie: Fenster merkt sich Groesse und Position
        # ueber Sessions hinweg. Default nur, wenn nichts oder etwas
        # offensichtlich Kaputtes gespeichert wurde (M6).
        saved_geometry = self.settings_repo.get("gui.geometry")
        if saved_geometry and _is_valid_geometry(saved_geometry):
            self.geometry(saved_geometry)
        else:
            self.geometry("1080x720")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Lizenz vor Sidebar laden, damit der Tier-Indikator gleich
        # mit dem aktuellen Stand gefuellt werden kann.
        from services.licensing import load_license as _load_license
        self._current_license = _load_license(self.settings_repo)

        self._build_sidebar()

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=1, sticky="nsew",
                       padx=(0, 10), pady=10)
        # Tab-Labels durch i18n - Reihenfolge bleibt fest (Werte sind die
        # Builder-Funktionen, Schluessel die uebersetzten Labels).
        # self._current_license wurde bereits in __init__ geladen.
        t = self.i18n.t
        # Tab-Label -> (Builder, gated_module_id). gated_module_id ist None
        # fuer immer offene Tabs, sonst die Modul-ID, gegen die License
        # geprueft wird.
        self.tab_gating: dict[str, Optional[str]] = {
            t("tab.dashboard"): None,
            t("tab.contracts"): "contracts",
            t("tab.family"): "family",
            t("tab.finance"): "finance",
            t("tab.calendar"): "calendar",
            t("tab.social"): "social",
            t("tab.inbox"): "inbox",
            t("tab.statistics"): None,
            t("tab.data"): None,
            t("tab.assistant"): "assistant_ai",
            t("tab.search"): None,
            t("tab.history"): None,
            t("tab.modules"): None,
            t("tab.settings"): None,
        }
        self.tab_builders: dict[str, Callable] = {
            t("tab.dashboard"): self._build_dashboard,
            t("tab.contracts"): self._build_contracts,
            t("tab.family"): self._build_family,
            t("tab.finance"): self._build_finance,
            t("tab.calendar"): self._build_calendar,
            t("tab.social"): self._build_social,
            t("tab.inbox"): self._build_inbox,
            t("tab.statistics"): self._build_statistics,
            t("tab.data"): self._build_data,
            t("tab.assistant"): self._build_chat,
            t("tab.search"): self._build_search,
            t("tab.history"): self._build_history,
            t("tab.modules"): self._build_module_admin,
            t("tab.settings"): self._build_settings,
        }
        # Nutzer kann ueber `gui.tab_order` eine eigene Reihenfolge der
        # Tabs vorgeben (kommaseparierte Tab-Keys wie 'dashboard,finance').
        # Unbekannte oder fehlende Tabs landen am Ende in Standard-Reihenfolge.
        ordered = self._resolve_tab_order(self.tab_builders, t)
        for name, builder in ordered:
            display = self._tab_display_label(name)
            tab_widget = self.tabs.add(display)
            # Wenn der Tab durch Lizenz gesperrt ist, kommt statt der
            # normalen UI ein Upgrade-Panel mit Pricing + CTA.
            if self._is_tab_locked(name):
                self._build_upgrade_panel(tab_widget, plain_label=name)
            else:
                builder(tab_widget)

        # Assistant bei destruktiven Aufrufen den Nutzer fragen lassen
        self.assistant.set_confirm_callback(self._confirm_destructive)

        # Tastatur-Shortcuts
        self._bind_shortcuts()

        self._refresh_all()
        self._append_chat(self.i18n.t("common.assistant"),
                           self.i18n.t("chat.greeting"))
        # Onboarding-Dialog erst nach mainloop-Start zeigen, damit alle
        # Widgets sichtbar sind. ueber _safe_after, damit der Callback beim
        # Schliessen gecancelt wird (kein Feuern ins zerstoerte Fenster).
        self._safe_after(200, self._maybe_run_onboarding)

    def _tab_display_label(self, plain_label: str) -> str:
        """Schloss-Marker vor Tab-Labels von Modulen, die die Lizenz sperrt."""
        return (f"[Pro] {plain_label}" if self._is_tab_locked(plain_label)
                else plain_label)

    def _is_tab_locked(self, plain_label: str) -> bool:
        """True wenn der Tab durch den aktuellen Tier gesperrt ist."""
        gated_id = self.tab_gating.get(plain_label)
        if gated_id is None:
            return False
        lic = self._current_license
        if gated_id == "assistant_ai":
            return not lic.allows_ai()
        return not lic.allows_module(gated_id)

    def _build_upgrade_panel(self, parent, *, plain_label: str) -> None:
        """Stand-In fuer gesperrte Tabs: erklaert, was Pro freischaltet."""
        from services.license_ui import (build_pricing_rows, make_tier_status)
        from services.licensing import recommended_tier

        parent.grid_columnconfigure(0, weight=1)
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(
            wrap,
            text=f"{plain_label} ist eine Pro-Funktion",
            font=_win11_font(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 6))

        st = make_tier_status(self._current_license)
        ctk.CTkLabel(
            wrap, justify="left", wraplength=720, anchor="w",
            text=(f"Aktueller Tier: {st.headline}\n"
                  f"{st.detail}\n\n"
                  "Pro-Funktionen umfassen alle acht Module, "
                  "den KI-Assistenten, Mehrgeraete-Sync, OCR und "
                  "SQLCipher-Verschluesselung. "
                  "Die Aktivierung erfolgt im Tab 'Einstellungen' - "
                  "entweder per Trial oder per Pro-Lizenz-Token."),
        ).pack(anchor="w", pady=(0, 12))

        persons = max(1, self._current_license.persons)
        rec = recommended_tier(persons)
        ctk.CTkLabel(wrap, text="Preise (Brutto):",
                      font=ctk.CTkFont(weight="bold")
                      ).pack(anchor="w", pady=(4, 4))
        for row in build_pricing_rows(persons, recommended=rec):
            marker = "  > " if row.is_recommended else "    "
            ctk.CTkLabel(wrap,
                          text=f"{marker}{row.label:24} {row.price_text}",
                          justify="left", anchor="w",
                          font=ctk.CTkFont(family="Courier")
                          ).pack(anchor="w")

        cta = ctk.CTkFrame(wrap, fg_color="transparent")
        cta.pack(anchor="w", pady=(16, 0))
        if st.can_start_trial:
            ctk.CTkButton(cta, text="14 Tage kostenlos testen",
                          command=self._on_start_trial_from_upgrade
                          ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            cta, text="Zu den Einstellungen",
            fg_color="transparent", border_width=1,
            command=self._switch_to_settings_tab
        ).pack(side="left")

    def _on_start_trial_from_upgrade(self) -> None:
        """Trial-Start vom Upgrade-Panel aus."""
        from services.license_ui import action_start_trial
        result = action_start_trial(self.settings_repo)
        self._current_license_msg = result.message
        self._refresh_license_state()
        # Hinweis fuer den Nutzer - mit einer Toplevel-Message, weil
        # die Pricing-Panels keine eigene Status-Zeile haben.
        self._show_dialog("Trial", result.message)

    def _switch_to_settings_tab(self) -> None:
        try:
            self.tabs.set(self.i18n.t("tab.settings"))
        except Exception:
            pass

    def _resolve_tab_order(self, builders: dict, t) -> list[tuple[str, Callable]]:
        """Wendet eine vom Nutzer hinterlegte Tab-Reihenfolge an.

        Schluessel sind die kurzen Tab-Keys ('dashboard', 'finance', ...) -
        sie werden ueber i18n auf die tatsaechlichen Tab-Labels gemappt.
        Unbekannte Eintraege werden ignoriert, fehlende landen unten in
        Standardreihenfolge.
        """
        raw = (self.config.gui_tab_order or "").strip()
        if not raw:
            return list(builders.items())
        wanted_keys = [k.strip() for k in raw.split(",") if k.strip()]
        # short_key -> translated label (alles, was der Builder anbietet)
        short_to_label = {}
        for short in ("dashboard", "contracts", "family", "finance",
                       "calendar", "social", "inbox", "statistics",
                       "data", "assistant", "search", "history",
                       "modules", "settings"):
            label = t(f"tab.{short}")
            if label in builders:
                short_to_label[short] = label
        ordered: list[tuple[str, Callable]] = []
        used: set[str] = set()
        for k in wanted_keys:
            label = short_to_label.get(k)
            if label and label not in used:
                ordered.append((label, builders[label]))
                used.add(label)
        for label, builder in builders.items():
            if label not in used:
                ordered.append((label, builder))
        return ordered

    def _maybe_run_onboarding(self) -> None:
        """Bei leerer DB einmaligen Dialog zeigen - Demo-Daten oder leer?

        Vorgeschaltet: einmaliger Pricing-Reveal (Free / Trial / Pro),
        sobald die DB noch leer UND der Pricing-Reveal noch nicht
        gezeigt wurde. Beide Dialoge laufen sequenziell.
        """
        if _has_any_data(self.registry):
            return
        # Pricing-Reveal nur einmal pro DB
        from services.licensing import KEY_PRICING_ONBOARDED
        if not self.settings_repo.get(KEY_PRICING_ONBOARDED):
            self._show_pricing_reveal(
                on_done=self._show_demo_data_onboarding)
            return
        self._show_demo_data_onboarding()

    def _show_pricing_reveal(self, *, on_done) -> None:
        """Einmaliger Erst-Start-Dialog: Free / Trial / Pro-Token."""
        from services.licensing import KEY_PRICING_ONBOARDED
        from services.license_ui import (action_apply_token,
                                           action_start_trial)
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Willkommen bei {APP_DISPLAY_NAME}")
        dlg.geometry("560x460")
        dlg.transient(self)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=f"Willkommen bei {APP_DISPLAY_NAME}",
                      font=_win11_font(size=18, weight="bold")
                      ).pack(padx=20, pady=(20, 4), anchor="w")
        ctk.CTkLabel(
            dlg, wraplength=500, justify="left", anchor="w",
            text=("Wie willst du starten? Du kannst spaeter im Tab "
                  "'Einstellungen' jederzeit wechseln."),
        ).pack(padx=20, pady=(0, 12), anchor="w")

        def _finish(message: str = "") -> None:
            self.settings_repo.set(KEY_PRICING_ONBOARDED, "true")
            dlg.destroy()
            if message:
                self._show_dialog("Lizenz", message)
            self._refresh_license_state()
            on_done()

        def _choose_free():
            _finish()

        def _choose_trial():
            result = action_start_trial(self.settings_repo)
            _finish(result.message)

        def _choose_token():
            dlg.destroy()
            self._show_token_paste_dialog(on_done=lambda r: (
                self.settings_repo.set(KEY_PRICING_ONBOARDED, "true"),
                self._refresh_license_state(),
                on_done(),
            ))

        for label, sub, cmd in (
            ("Free starten",
             "1 Person, 2 Module - jederzeit upgradebar.",
             _choose_free),
            ("14 Tage Trial",
             "Voller Pro-Zugriff, einmalig pro Geraet. "
             "Danach automatisch Free.",
             _choose_trial),
            ("Pro-Token einfuegen",
             "Du hast bereits gekauft und einen Aktivierungs-Token "
             "per Mail erhalten.",
             _choose_token),
        ):
            row = ctk.CTkFrame(dlg, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkButton(row, text=label, width=200,
                          command=cmd).pack(side="left", padx=(0, 12))
            ctk.CTkLabel(row, text=sub, text_color="gray",
                          wraplength=320, justify="left", anchor="w",
                          ).pack(side="left", fill="x", expand=True)

    def _show_token_paste_dialog(self, *, on_done) -> None:
        """Schlanker Dialog nur fuer Token-Eingabe (Onboarding-Variante)."""
        from services.license_ui import action_apply_token
        dlg = ctk.CTkToplevel(self)
        dlg.title("Pro-Token aktivieren")
        dlg.geometry("560x220")
        dlg.transient(self)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="Pro-Token aktivieren",
                      font=ctk.CTkFont(size=14, weight="bold")
                      ).pack(padx=20, pady=(20, 4), anchor="w")
        ctk.CTkLabel(
            dlg, wraplength=500, justify="left", anchor="w",
            text=("Fuege den Token aus deiner Kauf-Mail ein. "
                  "Du kannst dies auch spaeter im Settings-Tab tun."),
        ).pack(padx=20, pady=(0, 12), anchor="w")
        entry = ctk.CTkEntry(dlg, placeholder_text="<payload>.<signature>")
        entry.pack(fill="x", padx=20)
        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=14)

        def _apply():
            result = action_apply_token(self.settings_repo, entry.get())
            dlg.destroy()
            self._show_dialog("Aktivierung", result.message)
            on_done(result)

        def _skip():
            dlg.destroy()
            on_done(None)

        ctk.CTkButton(btns, text="Aktivieren", command=_apply
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="Spaeter",
                      fg_color="transparent", border_width=1,
                      command=_skip).pack(side="left")

    def _show_demo_data_onboarding(self) -> None:
        """Bisheriger Demo/Empty-Dialog - getrennt extrahiert."""
        t = self.i18n.t
        dlg = ctk.CTkToplevel(self)
        dlg.title(t("onboarding.title"))
        dlg.geometry("520x260")
        dlg.transient(self)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=t("onboarding.title"),
                     font=ctk.CTkFont(size=15, weight="bold")
                     ).pack(padx=20, pady=(20, 6))
        ctk.CTkLabel(dlg, text=t("onboarding.intro"),
                     wraplength=460, justify="left"
                     ).pack(padx=20, pady=(0, 12))
        ctk.CTkLabel(dlg, text="• " + t("onboarding.option_demo"),
                     text_color="gray", wraplength=460, justify="left",
                     anchor="w").pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(dlg, text="• " + t("onboarding.option_empty"),
                     text_color="gray", wraplength=460, justify="left",
                     anchor="w").pack(fill="x", padx=20, pady=2)
        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=14)

        def _choose_demo():
            dlg.destroy()
            _seed_demo_data(self.registry)
            self._refresh_all()

        def _choose_empty():
            dlg.destroy()

        ctk.CTkButton(btn_row, text=t("onboarding.choose_demo"),
                      command=_choose_demo).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text=t("onboarding.choose_empty"),
                      fg_color="transparent", border_width=1,
                      command=_choose_empty).pack(side="left")

    # ================================================================
    #  Sidebar
    # ================================================================
    def _build_sidebar(self) -> None:
        # Sidebar im Win11-Look: sanfter Hintergrund, keine harte Kante
        bar = ctk.CTkFrame(self, width=260, corner_radius=0)
        bar.grid(row=0, column=0, sticky="nsew")

        t = self.i18n.t
        # App-Titel mit etwas Abstand und Segoe-UI-Gewichtung
        ctk.CTkLabel(
            bar, text=t("app.title"),
            font=_win11_font(size=20, weight="bold"),
        ).pack(padx=24, pady=(24, 2))

        ctk.CTkLabel(
            bar,
            text=f"{t('sidebar.assistant_mode')}: {self.assistant.mode}",
            font=_win11_font(size=11),
            text_color="gray",
        ).pack(padx=24, pady=(0, 2))

        ctk.CTkLabel(
            bar,
            text=f"{t('sidebar.profile')}: "
                 f"{self.profile or t('sidebar.profile.default')}",
            font=_win11_font(size=11),
            text_color="gray",
        ).pack(padx=24, pady=(0, 4))

        # Tier-Indikator (Free / Trial XYd / Pro XYd / Karenz)
        from services.license_ui import sidebar_indicator
        self.tier_indicator = ctk.CTkLabel(
            bar,
            text=sidebar_indicator(self._current_license),
            font=_win11_font(size=11),
            text_color="gray",
        )
        self.tier_indicator.pack(padx=24, pady=(0, 16))

        # Modulstatus als "Card" im Sidebar-Look
        ctk.CTkLabel(
            bar, text=t("sidebar.module_status"),
            font=_win11_font(size=12, weight="bold"),
        ).pack(padx=24, anchor="w")

        self.status_box = ctk.CTkTextbox(
            bar, width=220, height=320, wrap="word",
            font=_win11_font(size=11),
        )
        self.status_box.pack(padx=16, pady=8, fill="both", expand=True)

        # Aktionsbuttons unten mit etwas Abstand
        btn_pad = {"padx": 16, "pady": 3, "fill": "x"}
        ctk.CTkButton(
            bar, text=t("sidebar.refresh_all"),
            font=_win11_font(weight="bold"),
            command=self._refresh_all,
        ).pack(**btn_pad)
        ctk.CTkButton(
            bar, text=t("sidebar.check_now"),
            font=_win11_font(weight="bold"),
            command=self._check_notifications,
        ).pack(**btn_pad)

    # ================================================================
    #  Dashboard
    # ================================================================
    def _build_dashboard(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        t = self.i18n.t
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(6, 8))
        ctk.CTkLabel(header, text=t("dashboard.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).pack(side="left")
        # Kompakte Kennzahl neben dem Titel (Anzahl / ueberfaellig).
        self.dash_count = ctk.CTkLabel(
            header, text="", text_color="gray", font=_win11_font(size=12))
        self.dash_count.pack(side="left", padx=(10, 0))
        self.horizon = ctk.CTkSegmentedButton(
            header,
            values=[t("dashboard.horizon.30"),
                     t("dashboard.horizon.90"),
                     t("dashboard.horizon.all")],
            command=lambda _v: self._refresh_dashboard())
        self.horizon.set(t("dashboard.horizon.90"))
        self.horizon.pack(side="right")
        # Ansicht-Umschalter: chronologische Liste vs. Tages-Agenda (Woche).
        self.dash_view = ctk.CTkSegmentedButton(
            header, values=["Liste", "Woche"],
            command=lambda _v: self._refresh_dashboard())
        self.dash_view.set("Liste")
        self.dash_view.pack(side="right", padx=(0, 8))

        self.dash_list = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.dash_list.grid(row=1, column=0, sticky="nsew")

    def _refresh_dashboard(self) -> None:
        if not hasattr(self, "dash_list"):
            return
        _clear(self.dash_list)
        t = self.i18n.t
        if hasattr(self, "dash_view") and self.dash_view.get() == "Woche":
            self._render_agenda()
            return
        horizon = {
            t("dashboard.horizon.30"): 30,
            t("dashboard.horizon.90"): 90,
            t("dashboard.horizon.all"): 3650,
        }[self.horizon.get()]
        events = self.registry.collect_events(horizon)
        if not events:
            self.dash_count.configure(text="")
            _empty_state(self.dash_list, t("dashboard.none"))
            return
        overdue = sum(1 for e in events if getattr(e, "days_remaining", 0) < 0)
        self.dash_count.configure(
            text=(f"{len(events)} Ereignisse"
                  + (f"  ·  {overdue} ueberfaellig" if overdue else "")))
        for event in events:
            self._event_card(event)

    def _render_agenda(self) -> None:
        """Tages-/Wochenuebersicht (system.agenda): nach Kalendertag
        gruppiert, Ueberfaellige zuerst."""
        if not hasattr(self, "dash_list"):
            return
        result = self._present_dashboard.week(horizon_days=7)
        if hasattr(self, "dash_count"):
            oc = result.get("overdue_count", 0)
            self.dash_count.configure(
                text=(f"{result.get('total', 0)} diese Woche"
                      + (f"  ·  {oc} ueberfaellig" if oc else "")))
        if result.get("overdue_count"):
            ctk.CTkLabel(
                self.dash_list,
                text=f"{self.i18n.t('dashboard.overdue')} "
                     f"({result['overdue_count']})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=URGENCY_COLOR["hoch"]).pack(anchor="w", pady=(4, 2))
            for ev in result.get("overdue", []):
                self._agenda_card(ev)
        for day in result.get("days", []):
            ctk.CTkLabel(self.dash_list,
                         text=f"{day['weekday']}, {day['date']}",
                         font=ctk.CTkFont(size=13, weight="bold")
                         ).pack(anchor="w", pady=(8, 2))
            if not day["count"]:
                ctk.CTkLabel(self.dash_list, text="  -", text_color="gray"
                             ).pack(anchor="w", padx=12)
            for ev in day["events"]:
                self._agenda_card(ev)

    def _agenda_card(self, ev: dict) -> None:
        row = ctk.CTkFrame(self.dash_list, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=1)
        ctk.CTkLabel(row, text=f"- {ev.get('title', '')}", anchor="w"
                     ).pack(side="left", fill="x", expand=True)
        detail = ev.get("module_name") or ev.get("detail") or ""
        if detail:
            ctk.CTkLabel(row, text=detail, text_color="gray",
                         font=ctk.CTkFont(size=10)).pack(side="right")

    def _event_card(self, event) -> None:
        color = URGENCY_COLOR[event.urgency]
        card = ctk.CTkFrame(
            self.dash_list, height=88,
            border_width=1, border_color=CARD_BORDER,
        )
        card.pack(fill="x", pady=4, padx=4)
        card.pack_propagate(False)
        # Farbiger Akzentstreifen links mit Abrundung oben/unen
        accent = ctk.CTkFrame(card, width=5, fg_color=color, corner_radius=3)
        accent.pack(side="left", fill="y", padx=(4, 0), pady=4)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        days = event.days_remaining
        when = (f"in {days} Tagen" if days > 0
                else "heute faellig" if days == 0
                else f"{-days} Tage ueberfaellig")
        ctk.CTkLabel(
            top,
            text=f"{event.due_date.strftime('%d.%m.%Y')}  -  {when}",
            height=16, font=_win11_font(size=11), text_color="gray",
        ).pack(side="left")
        ctk.CTkLabel(
            top, text=URGENCY_LABEL[event.urgency], height=16,
            font=_win11_font(size=10, weight="bold"),
            text_color=color,
        ).pack(side="right")
        ctk.CTkLabel(
            body, text=event.title, height=22,
            font=_win11_font(size=14, weight="bold"),
        ).pack(anchor="w")
        if event.detail:
            ctk.CTkLabel(
                body, text=event.detail, height=16,
                font=_win11_font(size=11),
                text_color="gray", wraplength=560, justify="left",
            ).pack(anchor="w")

    # ================================================================
    #  Vertraege
    # ================================================================
    def _build_contracts(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        t = self.i18n.t

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(6, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=t("tab.contracts"),
                     font=_win11_font(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        self.contract_filter = ctk.CTkOptionMenu(
            header, width=170,
            values=["Alle", "mobilfunk", "streaming", "strom",
                    "versicherung", "sonstiges"],
            command=lambda _v: self._refresh_contracts())
        self.contract_filter.set("Alle")
        self.contract_filter.grid(row=0, column=1, sticky="e")

        form = ctk.CTkFrame(
            parent, border_width=1, border_color=CARD_BORDER,
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.contract_inputs = {
            "name": _labeled_entry(form, t("form.name"), "z.B. Stromvertrag"),
            "provider": _labeled_entry(form, t("form.provider"),
                                          "z.B. Stadtwerke"),
            "category": _labeled_entry(form, t("form.category"),
                                          "mobilfunk / streaming / strom / "
                                          "versicherung / sonstiges"),
            "monthly_cost": _labeled_entry(form, t("form.monthly_cost"),
                                              "0.00"),
            "start_date": _labeled_entry(form, t("form.start_date"),
                                             date.today().isoformat()),
            "minimum_term_months": _labeled_entry(form, t("form.min_term"),
                                                     "12"),
            "notice_period_months": _labeled_entry(form,
                                                      t("form.notice_period"),
                                                      "3"),
            "auto_renew_months": _labeled_entry(form, t("form.auto_renew"),
                                                  "12"),
            "owner_name": _labeled_entry(form, t("form.person"),
                                            t("form.empty_no_person")),
        }
        ctk.CTkButton(form, text=t("action.create_contract"),
                      command=self._on_contract_add).pack(pady=8)

        self.contract_list = ctk.CTkScrollableFrame(parent,
                                                      fg_color="transparent")
        self.contract_list.grid(row=2, column=0, sticky="nsew")

    def _on_contract_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.contract_inputs.items()}
        if not v["name"] or not v["category"]:
            return
        try:
            payload = {
                "name": v["name"],
                "provider": v["provider"],
                "category": v["category"] or "sonstiges",
                "start_date": v["start_date"] or None,
                "monthly_cost": _parse_float(v["monthly_cost"], 0.0),
                "minimum_term_months": _parse_int(v["minimum_term_months"], 12),
                "notice_period_months": _parse_int(v["notice_period_months"], 3),
                "auto_renew_months": _parse_int(v["auto_renew_months"], 12),
            }
        except ValueError:
            self._show_dialog("Eingabe ungueltig",
                              "Bitte in den Zahlenfeldern (Kosten, Laufzeit, "
                              "Kuendigungsfrist) gueltige Zahlen eingeben.")
            return
        if v["owner_name"]:
            members = self.registry.dispatch("family.members",
                                               {}).get("members", [])
            for m in members:
                if m["name"].lower() == v["owner_name"].lower():
                    payload["owner_id"] = m["id"]
                    break
        self.registry.dispatch("contracts.add", payload)
        for e in self.contract_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_contracts(self) -> None:
        if not hasattr(self, "contract_list"):
            return
        _clear(self.contract_list)
        args: dict = {}
        if hasattr(self, "contract_filter"):
            chosen = self.contract_filter.get()
            if chosen and chosen != "Alle":
                args["category"] = chosen
        contracts = self.registry.dispatch("contracts.list",
                                             args).get("contracts", [])
        if not contracts:
            _empty_state(self.contract_list, "Noch keine Vertraege.")
            return
        for c in contracts:
            self._contract_row(c)

    def _contract_row(self, c: dict) -> None:
        body = _card_row(self.contract_list)

        owner = f" - {c['owner']}" if c.get("owner") else ""
        ctk.CTkLabel(body,
                     text=f"{c['name']} ({c.get('provider', '') or '-'}){owner}",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(anchor="w")
        ctk.CTkLabel(body,
                     text=(f"{c['monthly_cost']:.2f} EUR/Monat - "
                            f"Kuendigung {c['notice_period_months']} Mon., "
                            f"Verlaengerung {c['auto_renew_months']} Mon."),
                     text_color="gray", font=ctk.CTkFont(size=11)
                     ).pack(anchor="w")

        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(anchor="w", pady=(6, 0))
        ctk.CTkButton(btns, text=self.i18n.t("action.cancellation_letter"),
                      width=170,
                      command=lambda i=c["id"], n=c["name"]:
                      self._on_generate_cancellation(i, n)
                      ).pack(side="left", padx=(0, 6))

    def _on_generate_cancellation(self, contract_id: int,
                                   contract_name: str) -> None:
        result = self.registry.dispatch("contracts.generate_cancellation", {
            "contract_id": contract_id,
            "sender_name": "(Ihr Name)",
            "sender_address": "(Ihre Anschrift)",
            "sender_city": "(Ort)",
            "channel": "both",
        })
        pdf = result.get("pdf_path")
        msg = (f"Kuendigung fuer '{contract_name}' erstellt.\n"
               f"PDF: {pdf}\nMail-Entwurf: {result.get('email_draft_path')}\n\n"
               f"Frist zum: {result.get('cancellation_date')}")
        self._show_dialog("Kuendigungsschreiben", msg, pdf_path=pdf)

    # ================================================================
    #  Familie (Mitglieder + Aufgaben + Auftraege + Einkaufsliste)
    # ================================================================
    def _build_family(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        t = self.i18n.t

        sub = ctk.CTkTabview(parent)
        sub.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self._build_family_members(sub.add(t("family.sub.members")))
        self._build_family_tasks(sub.add(t("family.sub.tasks")))
        self._build_family_orders(sub.add(t("family.sub.orders")))
        self._build_family_shopping(sub.add(t("family.sub.shopping")))

    def _build_family_members(self, parent) -> None:
        t = self.i18n.t
        form = ctk.CTkFrame(parent, border_width=1, border_color=CARD_BORDER)
        form.pack(fill="x", pady=(6, 8))
        self.member_inputs = {
            "name": _labeled_entry(form, t("form.name")),
            "role": _labeled_entry(form, t("form.role"),
                                    "erwachsen / kind / sonstiges"),
            "birthday": _labeled_entry(form, t("form.birthday")),
        }
        ctk.CTkButton(form, text=t("common.add"),
                      command=self._on_member_add).pack(pady=6)
        self.member_list = ctk.CTkScrollableFrame(parent,
                                                    fg_color="transparent")
        self.member_list.pack(fill="both", expand=True)

    def _on_member_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.member_inputs.items()}
        if not v["name"]:
            return
        payload = {"name": v["name"], "role": v["role"] or "erwachsen"}
        if v["birthday"]:
            payload["birthday"] = v["birthday"]
        self.registry.dispatch("family.add_member", payload)
        for e in self.member_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_members(self) -> None:
        if not hasattr(self, "member_list"):
            return
        _clear(self.member_list)
        members = self.registry.dispatch("family.members",
                                          {}).get("members", [])
        if not members:
            _empty_state(self.member_list, "Noch keine Familienmitglieder.")
            return
        for m in members:
            bday = f"  - Geburtstag {m['birthday']}" if m.get("birthday") else ""
            row = _card_row(self.member_list)
            ctk.CTkLabel(row,
                         text=f"#{m['id']}  {m['name']} ({m['role']}){bday}",
                         anchor="w").pack(side="left", fill="x", expand=True)

    def _build_family_tasks(self, parent) -> None:
        t = self.i18n.t
        form = ctk.CTkFrame(parent, border_width=1, border_color=CARD_BORDER)
        form.pack(fill="x", pady=(6, 8))
        self.task_inputs = {
            "title": _labeled_entry(form, t("form.title")),
            "interval_days": _labeled_entry(form, t("form.interval_days"),
                                                "7"),
            "assignees": _labeled_entry(form, t("form.rotation"),
                                          "Anna, Bernd"),
            "first_due": _labeled_entry(form, t("form.first_due"),
                                           date.today().isoformat()),
        }
        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", pady=6)
        ctk.CTkButton(btn_row, text=t("action.add_task"),
                      command=self._on_task_add).pack(side="left",
                                                        padx=(0, 8))
        ctk.CTkButton(btn_row, text=t("action.bulk_complete_overdue"),
                      fg_color="transparent", border_width=1,
                      command=self._bulk_complete_overdue
                      ).pack(side="left")
        self.task_list = ctk.CTkScrollableFrame(parent,
                                                  fg_color="transparent")
        self.task_list.pack(fill="both", expand=True)

    def _bulk_complete_overdue(self) -> None:
        self.registry.dispatch("family.bulk_complete_overdue", {})
        self._refresh_all()

    def _on_task_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.task_inputs.items()}
        if not v["title"]:
            return
        assignees = [a.strip() for a in v["assignees"].split(",") if a.strip()]
        try:
            interval_days = _parse_int(v["interval_days"], 7)
        except ValueError:
            self._show_dialog("Eingabe ungueltig",
                              "Das Intervall (Tage) muss eine Zahl sein.")
            return
        self.registry.dispatch("family.add_task", {
            "title": v["title"],
            "interval_days": interval_days,
            "assignees": assignees,
            "first_due": v["first_due"] or None,
        })
        for e in self.task_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_tasks(self) -> None:
        if not hasattr(self, "task_list"):
            return
        _clear(self.task_list)
        tasks = self.registry.dispatch("family.tasks", {}).get("tasks", [])
        if not tasks:
            _empty_state(self.task_list, "Keine Aufgaben angelegt.")
            return
        for t in tasks:
            row = _card_row(self.task_list)
            ctk.CTkLabel(row,
                         text=(f"{t['title']}  -  faellig {t['next_due']}, "
                                f"zustaendig {t['current_assignee']} "
                                f"(alle {t['interval_days']} Tage)"),
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text="Abhaken", width=80,
                          command=lambda i=t["id"]:
                          self._dispatch_and_refresh(
                              "family.complete_task", {"task_id": i})
                          ).pack(side="right")

    def _build_family_orders(self, parent) -> None:
        t = self.i18n.t
        form = ctk.CTkFrame(parent, border_width=1, border_color=CARD_BORDER)
        form.pack(fill="x", pady=(6, 8))
        self.order_inputs = {
            "title": _labeled_entry(form, t("form.title")),
            "assignee": _labeled_entry(form, t("form.who"), t("form.name")),
            "due_date": _labeled_entry(form, t("form.due_date")),
            "description": _labeled_entry(form, t("form.note")),
            "category": _labeled_entry(form, t("form.category"),
                                       t("form.optional")),
        }
        self.order_priority = _labeled_option_menu(
            form, t("form.priority"), ["normal", "mittel", "hoch"], "normal")
        ctk.CTkButton(form, text=t("action.add_order"),
                      command=self._on_order_add).pack(pady=6)
        self.order_list = ctk.CTkScrollableFrame(parent,
                                                   fg_color="transparent")
        self.order_list.pack(fill="both", expand=True)

    def _on_order_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.order_inputs.items()}
        result = self._present_orders.add(
            v["title"], assignee=v["assignee"], due_date=v["due_date"],
            description=v["description"], priority=self.order_priority.get(),
            category=v.get("category", ""))
        if "error" in result:
            return
        for e in self.order_inputs.values():
            e.delete(0, "end")
        self.order_priority.set("normal")
        self._refresh_all()

    def _refresh_orders(self) -> None:
        if not hasattr(self, "order_list"):
            return
        _clear(self.order_list)
        orders = self._present_orders.list()["items"]
        if not orders:
            _empty_state(self.order_list, "Noch keine Auftraege.")
            return
        for o in orders:
            row = _card_row(self.order_list)
            status_mark = "[ok]" if o["status"] == "erledigt" else "[offen]"
            faellig = f", bis {o['due_date']}" if o.get("due_date") else ""
            prio = o.get("priority", "normal")
            prio_mark = {"hoch": "[!] ", "mittel": "[~] "}.get(prio, "")
            kat = f" #{o['category']}" if o.get("category") else ""
            ctk.CTkLabel(row,
                         text=(f"{prio_mark}{status_mark} {o['title']} -> "
                                f"{o.get('assignee') or 'niemand'}"
                                f"{faellig}{kat}"),
                         anchor="w").pack(side="left", fill="x", expand=True)
            if o["status"] != "erledigt":
                ctk.CTkButton(row, text="Erledigt", width=80,
                              command=lambda i=o["id"]:
                              self._dispatch_and_refresh(
                                  "family.complete_order", {"order_id": i})
                              ).pack(side="right")

    def _build_family_shopping(self, parent) -> None:
        t = self.i18n.t
        form = ctk.CTkFrame(parent, border_width=1, border_color=CARD_BORDER)
        form.pack(fill="x", pady=(6, 8))
        self.shopping_inputs = {
            "name": _labeled_entry(form, t("form.what")),
            "quantity": _labeled_entry(form, t("form.quantity"),
                                          "z.B. 1 kg"),
            "added_by": _labeled_entry(form, t("form.from"), t("form.name")),
        }
        ctk.CTkButton(form, text=t("action.shopping_add"),
                      command=self._on_shopping_add).pack(pady=6)
        self.shopping_list = ctk.CTkScrollableFrame(parent,
                                                       fg_color="transparent")
        self.shopping_list.pack(fill="both", expand=True)

    def _on_shopping_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.shopping_inputs.items()}
        if not v["name"]:
            return
        self.registry.dispatch("family.shopping_add", v)
        for e in self.shopping_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_shopping(self) -> None:
        if not hasattr(self, "shopping_list"):
            return
        _clear(self.shopping_list)
        items = self.registry.dispatch(
            "family.shopping_list",
            {"include_bought": True}).get("items", [])
        if not items:
            _empty_state(self.shopping_list, "Einkaufsliste ist leer.")
            return
        for item in items:
            row = _card_row(self.shopping_list)
            qty = f" ({item['quantity']})" if item.get("quantity") else ""
            by = f" - von {item['added_by']}" if item.get("added_by") else ""
            mark = "[x]" if item.get("bought") else "[ ]"
            ctk.CTkLabel(row, text=f"{mark} {item['name']}{qty}{by}",
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="Abhaken" if not item["bought"] else "Zuruecksetzen",
                width=110,
                command=lambda i=item["id"], b=not item["bought"]:
                self._dispatch_and_refresh(
                    "family.shopping_mark",
                    {"item_id": i, "bought": b})
            ).pack(side="right")

    # ================================================================
    #  Finanzen
    # ================================================================
    def _build_finance(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        t = self.i18n.t

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(6, 4))
        ctk.CTkLabel(header, text=t("tab.finance"),
                     font=_win11_font(size=18, weight="bold")
                     ).pack(side="left")
        self.finance_summary = ctk.CTkLabel(header, text="", text_color="gray")
        self.finance_summary.pack(side="right")

        form = ctk.CTkFrame(parent, border_width=1, border_color=CARD_BORDER)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.expense_inputs = {
            "description": _labeled_entry(form, t("form.description"),
                                              "z.B. Wocheneinkauf"),
            "amount": _labeled_entry(form, t("form.amount"), "0.00"),
            "category": _labeled_entry(form, t("form.category"),
                                          "lebensmittel / freizeit / sonstiges"),
            "spent_on": _labeled_entry(form, t("form.date"),
                                          date.today().isoformat()),
            "owner_name": _labeled_entry(form, t("form.person"),
                                            t("form.empty_no_person")),
        }
        ctk.CTkButton(form, text=t("action.add_expense"),
                      command=self._on_expense_add).pack(pady=8)

        self.expense_list = ctk.CTkScrollableFrame(parent,
                                                       fg_color="transparent")
        self.expense_list.grid(row=2, column=0, sticky="nsew")

    def _on_expense_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.expense_inputs.items()}
        if not v["description"] or not v["amount"]:
            return
        try:
            amount = _parse_float(v["amount"], 0.0)
        except ValueError:
            self._show_dialog("Eingabe ungueltig",
                              "Bitte einen gueltigen Betrag eingeben "
                              "(z.B. 10.50).")
            return
        payload = {
            "description": v["description"],
            "amount": amount,
            "category": v["category"] or "sonstiges",
            "spent_on": v["spent_on"] or None,
        }
        if v["owner_name"]:
            for m in self.registry.dispatch(
                    "family.members", {}).get("members", []):
                if m["name"].lower() == v["owner_name"].lower():
                    payload["owner_id"] = m["id"]
                    break
        self.registry.dispatch("finance.add_expense", payload)
        for e in self.expense_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_finance(self) -> None:
        if not hasattr(self, "expense_list"):
            return
        _clear(self.expense_list)
        over = self.registry.dispatch("finance.monthly_overview", {})
        if "error" in over:
            # Modul deaktiviert o.ae. - nicht mit KeyError den ganzen
            # _refresh_all abbrechen.
            return
        self.finance_summary.configure(
            text=(f"{over['month']}: Vertraege {over['recurring_contracts']:.2f} "
                   f"+ einmalig {over['one_time_this_month']:.2f} = "
                   f"{over['total_monthly']:.2f} EUR"))
        for e in self.registry.dispatch("finance.list_expenses",
                                            {}).get("expenses", []):
            row = _card_row(self.expense_list)
            owner = f"  -  {e['owner']}" if e.get("owner") else ""
            ctk.CTkLabel(row,
                         text=(f"{e.get('spent_on', '?')}  {e['description']}: "
                                f"{e['amount']:.2f} EUR  [{e['category']}]{owner}"),
                         anchor="w").pack(side="left", fill="x", expand=True)

    # ================================================================
    #  Kalender
    # ================================================================
    def _build_calendar(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        t = self.i18n.t

        ctk.CTkLabel(parent, text=t("calendar.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 4))

        form = ctk.CTkFrame(parent, border_width=1, border_color=CARD_BORDER)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.calendar_inputs = {
            "title": _labeled_entry(form, t("form.title")),
            "due_date": _labeled_entry(form, t("form.calendar_date"),
                                          date.today().isoformat()),
            "category": _labeled_entry(form, t("form.category"),
                                          "termin / garantie / tuev / "
                                          "steuer / geburtstag / sonstiges"),
            "description": _labeled_entry(form, t("form.note")),
            "recurrence_days": _labeled_entry(form,
                                                  t("form.recurrence_days"),
                                                  "(leer = einmalig)"),
        }
        ctk.CTkButton(form, text=t("action.add_event"),
                      command=self._on_calendar_add).pack(pady=6)

        self.calendar_list = ctk.CTkScrollableFrame(parent,
                                                        fg_color="transparent")
        self.calendar_list.grid(row=2, column=0, sticky="nsew")

    def _on_calendar_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.calendar_inputs.items()}
        if not v["title"] or not v["due_date"]:
            return
        payload = {
            "title": v["title"],
            "due_date": v["due_date"],
            "category": v["category"] or "termin",
            "description": v["description"],
        }
        if v["recurrence_days"]:
            try:
                payload["recurrence_days"] = int(v["recurrence_days"])
            except ValueError:
                pass
        self.registry.dispatch("calendar.add_event", payload)
        for e in self.calendar_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_calendar(self) -> None:
        if not hasattr(self, "calendar_list"):
            return
        _clear(self.calendar_list)
        t = self.i18n.t
        events = self.registry.dispatch("calendar.list_events",
                                            {}).get("events", [])
        if not events:
            _empty_state(self.calendar_list, t("calendar.no_events"))
            return
        for e in events:
            row = _card_row(self.calendar_list)
            extra = f" - {e['person']}" if e.get("person") else ""
            recur = (t("calendar.recurring_suffix").format(
                         days=e['recurrence_days'])
                     if e.get("recurrence_days") else "")
            ctk.CTkLabel(row,
                         text=(f"{e['due_date']}  [{e['category']}]  "
                                f"{e['title']}{extra}{recur}"),
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text=t("common.delete"), width=90,
                          fg_color="transparent", border_width=1,
                          command=lambda i=e["id"]:
                          self._dispatch_and_refresh(
                              "calendar.delete_event", {"event_id": i})
                          ).pack(side="right")

    # ================================================================
    #  Sozial
    # ================================================================
    def _build_social(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        t = self.i18n.t

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(6, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=t("social.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        self.social_filter = ctk.CTkOptionMenu(
            header, width=170, values=["Alle"],
            command=lambda _v: self._refresh_social())
        self.social_filter.set("Alle")
        self.social_filter.grid(row=0, column=1, sticky="e")

        form = ctk.CTkFrame(parent, border_width=1, border_color=CARD_BORDER)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.social_inputs = {
            "name": _labeled_entry(form, t("form.name")),
            "relation": _labeled_entry(form, t("form.relation"),
                                          "Familie / Freund / Kollege ..."),
            "cadence_days": _labeled_entry(form, t("form.cadence_days"),
                                              "30"),
            "notes": _labeled_entry(form, t("form.note")),
        }
        ctk.CTkButton(form, text=t("action.add_contact"),
                      command=self._on_social_add).pack(pady=6)

        self.social_list = ctk.CTkScrollableFrame(parent,
                                                      fg_color="transparent")
        self.social_list.grid(row=2, column=0, sticky="nsew")

    def _on_social_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.social_inputs.items()}
        if not v["name"]:
            return
        payload = {"name": v["name"], "relation": v["relation"],
                    "notes": v["notes"]}
        if v["cadence_days"]:
            try:
                payload["cadence_days"] = _parse_int(v["cadence_days"], 0)
            except ValueError:
                self._show_dialog("Eingabe ungueltig",
                                  "Der Rhythmus (Tage) muss eine Zahl sein.")
                return
        self.registry.dispatch("social.add_contact", payload)
        for e in self.social_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_social(self) -> None:
        if not hasattr(self, "social_list"):
            return
        _clear(self.social_list)
        t = self.i18n.t
        # Dropdown mit den vorhandenen Beziehungen befuellen.
        all_contacts = self.registry.dispatch(
            "social.contacts", {}).get("contacts", [])
        args: dict = {}
        if hasattr(self, "social_filter"):
            rels = sorted({c.get("relation") for c in all_contacts
                           if c.get("relation")})
            self.social_filter.configure(values=["Alle"] + rels)
            chosen = self.social_filter.get()
            if chosen and chosen != "Alle":
                args["relation"] = chosen
        contacts = (self.registry.dispatch("social.contacts", args)
                    .get("contacts", []) if args else all_contacts)
        if not contacts:
            _empty_state(self.social_list, t("social.no_contacts"))
            return
        for c in contacts:
            row = _card_row(self.social_list)
            days = c.get("days_until_due", 0)
            when = (t("social.due_in").format(days=days) if days > 0
                    else t("social.due_today") if days == 0
                    else t("social.due_overdue").format(days=-days))
            relation = f" ({c['relation']})" if c.get("relation") else ""
            label = (f"{c['name']}{relation}  -  "
                     + t("social.next_due").format(when=when))
            ctk.CTkLabel(row, text=label, anchor="w"
                         ).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text=t("action.contacted"), width=110,
                          command=lambda i=c["id"]:
                          self._dispatch_and_refresh(
                              "social.mark_contacted", {"contact_id": i})
                          ).pack(side="right", padx=(0, 4))
            ctk.CTkButton(row, text=t("action.draft"), width=80,
                          command=lambda i=c["id"], n=c["name"]:
                          self._show_message_draft(i, n)
                          ).pack(side="right", padx=(0, 4))

    def _show_message_draft(self, contact_id: int, name: str) -> None:
        result = self.registry.dispatch("social.draft_message",
                                          {"contact_id": contact_id,
                                           "template": "kurz"})
        self._show_dialog(f"Entwurf fuer {name}",
                            result.get("message", str(result)))

    # ================================================================
    #  Posteingang
    # ================================================================
    def _build_inbox(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)
        t = self.i18n.t

        ctk.CTkLabel(parent, text=t("inbox.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 4))

        entry = ctk.CTkFrame(parent, fg_color="transparent")
        entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        entry.grid_columnconfigure(0, weight=1)
        self.mail_box = ctk.CTkTextbox(entry, height=120, wrap="word")
        self.mail_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.mail_box.insert("1.0", SAMPLE_MAIL)
        actions = ctk.CTkFrame(entry, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="n")
        ctk.CTkButton(actions, text=t("inbox.analyze"), width=130,
                      command=self._analyze_mail).pack(pady=2)
        ctk.CTkButton(actions, text=t("inbox.fetch_imap"), width=130,
                      command=self._fetch_imap).pack(pady=2)

        info_row = ctk.CTkFrame(parent, fg_color="transparent")
        info_row.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        self.inbox_info = ctk.CTkLabel(
            info_row, text=t("inbox.proposals_count").format(count=0),
            font=ctk.CTkFont(size=14, weight="bold"))
        self.inbox_info.pack(side="left")
        ctk.CTkButton(info_row, text=t("inbox.bulk_reject"), width=130,
                      fg_color="transparent", border_width=1,
                      command=self._bulk_reject_open
                      ).pack(side="right", padx=(0, 4))
        ctk.CTkButton(info_row, text=t("inbox.bulk_purge"), width=140,
                      fg_color="transparent", border_width=1,
                      command=self._bulk_delete_archived
                      ).pack(side="right", padx=(0, 4))

        self.proposal_list = ctk.CTkScrollableFrame(parent,
                                                       fg_color="transparent")
        self.proposal_list.grid(row=3, column=0, sticky="nsew")

    def _analyze_mail(self) -> None:
        text = self.mail_box.get("1.0", "end-1c").strip()
        if not text:
            return
        result = self.registry.dispatch("inbox.analyze_mail",
                                          {"mail_text": text})
        found = result.get("found", 0)
        self.inbox_info.configure(
            text=(f"Analyse: {found} neue Vorschlaege" if found
                  else "Analyse: kein bekanntes Muster"))
        self.mail_box.delete("1.0", "end")
        self._refresh_inbox(keep_info=True)
        self._refresh_status()

    def _fetch_imap(self) -> None:
        # IMAP-Verbindung kann mehrere Sekunden brauchen - im Thread.
        self.inbox_info.configure(text="IMAP wird abgefragt ...")

        def worker():
            result = self.registry.dispatch("inbox.fetch_imap", {})
            self._post(lambda: self._on_imap_done(result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_imap_done(self, result: dict) -> None:
        if result.get("status") == "uebersprungen":
            self.inbox_info.configure(text="IMAP nicht konfiguriert")
            self._show_dialog("IMAP nicht konfiguriert",
                                result.get("hinweis", ""))
            return
        if result.get("status") == "fehler":
            self.inbox_info.configure(
                text=f"IMAP-Fehler: {result.get('error', '?')}")
            return
        self.inbox_info.configure(
            text=f"IMAP: {result.get('checked', 0)} Mails geprueft, "
                  f"{result.get('found', 0)} neue Vorschlaege")
        self._refresh_all()

    def _refresh_inbox(self, keep_info: bool = False) -> None:
        if not hasattr(self, "proposal_list"):
            return
        _clear(self.proposal_list)
        t = self.i18n.t
        data = self.registry.dispatch("inbox.proposals", {})
        count = data.get("count", 0)
        if not keep_info:
            self.inbox_info.configure(
                text=t("inbox.proposals_count").format(count=count))
        if count == 0:
            _empty_state(self.proposal_list, t("inbox.no_proposals"))
            return
        for proposal in data["proposals"]:
            self._proposal_card(proposal)

    def _proposal_card(self, p: dict) -> None:
        # Randlose Listen-Karte wie alle anderen Listeneintraege.
        body = _card_row(self.proposal_list)
        ctk.CTkLabel(body, text=p["summary"], anchor="w", justify="left",
                     wraplength=560,
                     font=_win11_font(size=13, weight="bold")
                     ).pack(anchor="w")
        ctk.CTkLabel(body,
                     text=f"Quelle: {p['source']}  -  Ziel: {p['target_capability']}",
                     anchor="w", text_color="gray",
                     font=_win11_font(size=10)).pack(anchor="w", pady=(2, 6))
        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.pack(anchor="w")
        t = self.i18n.t
        ctk.CTkButton(buttons, text=t("inbox.accept"), width=120,
                      command=lambda i=p["id"]:
                      self._decide_proposal(i, True)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text=t("inbox.edit"), width=110,
                      fg_color="transparent", border_width=1,
                      command=lambda pp=p:
                      self._open_proposal_editor(pp)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text=t("inbox.reject"), width=100,
                      fg_color="transparent", border_width=1,
                      command=lambda i=p["id"]:
                      self._decide_proposal(i, False)
                      ).pack(side="left")

    def _open_proposal_editor(self, proposal: dict) -> None:
        """
        Oeffnet einen Dialog mit Formularfeldern, die aus dem Schema der
        Ziel-Capability erzeugt werden. So kann der Nutzer Halluzinationen
        oder fehlende Felder korrigieren, bevor der Vorschlag uebernommen
        wird.
        """
        target = proposal["target_capability"]
        cap = self.registry.get_capability(target)
        if cap is None:
            self._show_dialog(
                "Bearbeiten nicht moeglich",
                f"Die Ziel-Capability '{target}' ist nicht verfuegbar. "
                "Pruefe, ob das zustaendige Modul aktiviert ist.")
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Vorschlag #{proposal['id']} bearbeiten")
        dlg.geometry("620x520")
        dlg.grab_set()

        ctk.CTkLabel(dlg, text=f"Bearbeiten: {target}",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(padx=20, pady=(20, 6), anchor="w")
        ctk.CTkLabel(dlg, text=cap.localized_description(self.i18n),
                     text_color="gray", wraplength=560, justify="left"
                     ).pack(padx=20, pady=(0, 10), anchor="w")

        # Kurzbeschreibung
        summary_row = ctk.CTkFrame(dlg, fg_color="transparent")
        summary_row.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(summary_row, text="Kurzbeschreibung",
                     width=180, anchor="w").pack(side="left")
        summary_entry = ctk.CTkEntry(summary_row)
        summary_entry.insert(0, proposal.get("summary", ""))
        summary_entry.pack(side="left", fill="x", expand=True)

        # Formularfelder pro Parameter
        scroll = ctk.CTkScrollableFrame(dlg, fg_color="transparent",
                                          height=240)
        scroll.pack(fill="both", expand=True, padx=20, pady=(8, 8))
        param_inputs: dict[str, ctk.CTkEntry] = {}
        payload = proposal.get("payload", {})
        for name, spec in cap.parameters.items():
            if not isinstance(spec, dict):
                continue
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)
            required = " *" if spec.get("_required") else ""
            label_text = (f"{name}{required}  ({spec.get('type', 'string')})")
            ctk.CTkLabel(row, text=label_text,
                          width=200, anchor="w"
                          ).pack(side="left")
            entry = ctk.CTkEntry(row)
            entry.insert(0, "" if payload.get(name) is None
                                else str(payload.get(name)))
            entry.pack(side="left", fill="x", expand=True)
            description = spec.get("description", "")
            if description:
                ctk.CTkLabel(scroll, text=f"   {description}",
                              text_color="gray",
                              font=ctk.CTkFont(size=10),
                              anchor="w", justify="left",
                              wraplength=520
                              ).pack(fill="x", padx=(8, 0))
            param_inputs[name] = entry

        status = ctk.CTkLabel(dlg, text="", text_color="gray")
        status.pack(fill="x", padx=20)

        # Aktions-Buttons
        actions = ctk.CTkFrame(dlg, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(8, 16))

        def _collect_payload() -> tuple[dict, list[str]]:
            new_payload: dict = {}
            problems: list[str] = []
            for name, spec in cap.parameters.items():
                if not isinstance(spec, dict):
                    continue
                raw = param_inputs[name].get().strip()
                if not raw:
                    if spec.get("_required"):
                        problems.append(f"'{name}' ist Pflichtfeld")
                    continue
                ptype = spec.get("type", "string")
                try:
                    if ptype == "integer":
                        new_payload[name] = int(raw)
                    elif ptype == "number":
                        new_payload[name] = float(raw)
                    elif ptype == "boolean":
                        new_payload[name] = raw.lower() in ("1", "true",
                                                              "yes", "ja")
                    else:
                        new_payload[name] = raw
                except ValueError:
                    problems.append(
                        f"'{name}' erwartet {ptype}, '{raw}' ungueltig")
            return new_payload, problems

        def _do_save(then_accept: bool) -> None:
            new_payload, problems = _collect_payload()
            if problems:
                status.configure(text="; ".join(problems),
                                  text_color="#d9534f")
                return
            result = self.registry.dispatch("inbox.update_proposal", {
                "proposal_id": proposal["id"],
                "summary": summary_entry.get().strip()
                            or proposal.get("summary", ""),
                "payload": new_payload,
            })
            if "error" in result:
                status.configure(text=result["error"], text_color="#d9534f")
                return
            if then_accept:
                accept = self.registry.dispatch(
                    "inbox.accept_proposal",
                    {"proposal_id": proposal["id"]})
                if "error" in accept:
                    status.configure(text=accept["error"],
                                      text_color="#d9534f")
                    return
            dlg.destroy()
            self._refresh_all()

        ctk.CTkButton(actions, text="Speichern",
                      command=lambda: _do_save(False)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Speichern + Uebernehmen",
                      command=lambda: _do_save(True)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Abbrechen",
                      fg_color="transparent", border_width=1,
                      command=dlg.destroy).pack(side="right")

    def _decide_proposal(self, proposal_id: int, accept: bool) -> None:
        cap = "inbox.accept_proposal" if accept else "inbox.reject_proposal"
        self.registry.dispatch(cap, {"proposal_id": proposal_id})
        self._refresh_all()

    def _bulk_reject_open(self) -> None:
        self.registry.dispatch("inbox.bulk_reject_open", {})
        self._refresh_all()

    def _bulk_delete_archived(self) -> None:
        self.registry.dispatch("inbox.bulk_delete_archived", {})
        self._refresh_all()

    # ================================================================
    #  Chat
    # ================================================================
    def _build_chat(self, parent) -> None:
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        self.chat = ctk.CTkTextbox(parent, wrap="word",
                                    font=ctk.CTkFont(size=13))
        self.chat.grid(row=0, column=0, columnspan=2, sticky="nsew",
                       pady=(6, 8))
        self.chat.configure(state="disabled")
        self.entry = ctk.CTkEntry(
            parent,
            placeholder_text=self.i18n.t("common.placeholder.question"))
        self.entry.grid(row=1, column=0, sticky="ew", padx=(0, 6),
                         pady=(0, 6))
        self.entry.bind("<Return>", lambda _e: self._on_send())
        ctk.CTkButton(parent, text=self.i18n.t("common.send"), width=90,
                      command=self._on_send
                      ).grid(row=1, column=1, sticky="e", pady=(0, 6))

    def _on_send(self) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        # Streaming-Lock: zwei Sends gleichzeitig wuerden die Chat-Box
        # durcheinanderbringen. Ein zweiter Klick waehrend eines aktiven
        # Streams wird ignoriert (K4).
        if getattr(self, "_streaming_active", False):
            return
        self._streaming_active = True
        self.entry.delete(0, "end")
        self._append_chat(self.i18n.t("common.you"), text)
        self._begin_assistant_stream()
        threading.Thread(target=self._chat_worker,
                          args=(text,), daemon=True).start()

    def _chat_worker(self, prompt: str) -> None:
        """
        Ruft den Assistenten auf. Wenn der LLM streamt, schreibt jeder
        Chunk live in die Chat-Box; im Offline-Modus simulieren wir
        Streaming, indem wir die fertige Antwort Wort fuer Wort
        einblenden - das fuehlt sich fluessiger an als ein Schlag-
        artiges Auftauchen.
        """
        def stream_callback(chunk: str) -> None:
            self._post(lambda c=chunk: self._append_to_stream(c))

        try:
            if self.assistant.llm is not None:
                answer = self.assistant.ask(prompt,
                                              stream_callback=stream_callback)
                self._post(lambda a=answer: self._finalize_stream(a))
            else:
                answer = self.assistant.ask(prompt)
                # Wort-fuer-Wort-Simulation auf dem Main-Thread laufen lassen,
                # damit ihre after()-Timer nicht aus diesem Worker stammen.
                self._post(lambda a=answer: self._simulate_word_stream(a))
        finally:
            # Streaming-Lock immer freigeben, damit naechster Send geht.
            self._post(self._end_stream)
        self._post(self._refresh_all)

    def _begin_assistant_stream(self) -> None:
        """
        Setzt einen Tk-Mark an die Einfuegestelle. Tk-Marks bewegen sich
        bei Inserts automatisch - kein String-Akkumulieren mehr.
        """
        if not hasattr(self, "chat"):
            return
        self.chat.configure(state="normal")
        label = self.i18n.t("common.assistant")
        self.chat.insert("end", f"{label}:\n")
        # Mark mit Gravity 'left': Inserts AN dieser Position schieben
        # die Mark mit nach rechts, sodass der naechste Chunk an die
        # richtige Stelle kommt.
        self.chat.mark_set("stream_mark", "end-1c")
        self.chat.mark_gravity("stream_mark", "left")
        self.chat.insert("end", "\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")
        self._stream_received_anything = False

    def _append_to_stream(self, chunk: str) -> None:
        """Haengt einen Streaming-Chunk an der Tk-Mark an."""
        if not chunk:
            return
        if not hasattr(self, "chat"):
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.chat.configure(state="normal")
        self.chat.insert("stream_mark", chunk)
        self.chat.see("end")
        self.chat.configure(state="disabled")
        self._stream_received_anything = True

    def _finalize_stream(self, full_answer: str) -> None:
        """Wenn nichts gestreamt wurde, die ganze Antwort einmal einsetzen."""
        if self._stream_received_anything:
            return
        self._append_to_stream(full_answer)

    def _end_stream(self) -> None:
        """Stream-Lock freigeben."""
        self._streaming_active = False

    def _simulate_word_stream(self, text: str, delay_ms: int = 25) -> None:
        """Im Offline-Modus: Wort fuer Wort mit kurzem Delay anzeigen."""
        tokens = text.split(" ")
        for i, token in enumerate(tokens):
            chunk = token + (" " if i < len(tokens) - 1 else "")
            self._safe_after(i * delay_ms,
                              lambda c=chunk: self._append_to_stream(c))

    def _append_chat(self, who: str, text: str) -> None:
        if not hasattr(self, "chat"):
            return
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}:\n{text}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _replace_last_chat(self, answer: str) -> None:
        if not hasattr(self, "chat"):
            return
        self.chat.configure(state="normal")
        content = self.chat.get("1.0", "end-1c")
        assistant_label = self.i18n.t("common.assistant")
        marker = (f"{assistant_label}:\n"
                   f"{self.i18n.t('chat.thinking')}\n\n")
        if content.endswith(marker):
            self.chat.delete(f"end-{len(marker) + 1}c", "end")
        self.chat.insert("end", f"{assistant_label}:\n{answer}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    # ================================================================
    #  Aktualisierung
    # ================================================================
    def _refresh_status(self) -> None:
        if not hasattr(self, "status_box"):
            return
        self.status_box.configure(state="normal")
        self.status_box.delete("1.0", "end")
        self.status_box.insert("end", self.registry.context_overview())
        self.status_box.configure(state="disabled")

    def _refresh_all(self) -> None:
        self._refresh_status()
        self._refresh_dashboard()
        self._refresh_contracts()
        self._refresh_members()
        self._refresh_tasks()
        self._refresh_orders()
        self._refresh_shopping()
        self._refresh_finance()
        self._refresh_calendar()
        self._refresh_social()
        self._refresh_inbox()
        self._refresh_module_admin()
        self._refresh_statistics()
        # Verlauf nur auf Anforderung aktualisieren - das Lesen von
        # assistant_log ist zwar billig, soll aber nicht jeden
        # Refresh-Tick mitmachen. Der Daten-Tab ebenfalls statisch.

    def _dispatch_and_refresh(self, capability: str, args: dict) -> None:
        self.registry.dispatch(capability, args)
        self._refresh_all()

    # ================================================================
    #  Hilfsdialog
    # ================================================================
    def _show_dialog(self, title: str, message: str,
                     pdf_path: str | None = None) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.geometry("520x320")
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=title,
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(padx=20, pady=(20, 6), anchor="w")
        box = ctk.CTkTextbox(dlg, wrap="word")
        box.pack(fill="both", expand=True, padx=20, pady=10)
        box.insert("1.0", message)
        box.configure(state="disabled")
        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 12))
        if pdf_path:
            ctk.CTkButton(btns, text="Drucken",
                          command=lambda: self._print_file(pdf_path)
                          ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="Schliessen",
                      command=dlg.destroy).pack(side="right")

    def _print_file(self, path: str) -> None:
        result = OutputService.print_file(path)
        self._show_dialog("Drucken",
                            result.get("status") or result.get("error", ""))

    # ================================================================
    #  Statistiken (Tab "Statistiken")
    # ================================================================
    def _build_statistics(self, parent) -> None:
        import tkinter
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        t = self.i18n.t

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(6, 6))
        ctk.CTkLabel(header, text=t("stats.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).pack(side="left")
        ctk.CTkButton(header, text=t("common.refresh"), width=120,
                      command=self._refresh_statistics).pack(side="right")

        self.stats_box = ctk.CTkScrollableFrame(
            parent, fg_color="transparent")
        self.stats_box.grid(row=1, column=0, sticky="nsew")

    def _refresh_statistics(self) -> None:
        if not hasattr(self, "stats_box"):
            return
        import tkinter as tk
        _clear(self.stats_box)
        t = self.i18n.t

        # 1) Ausgaben pro Monat - Bar-Chart per Canvas
        per_month = self.registry.dispatch(
            "stats.expenses_per_month", {"months": 12}).get("buckets", [])
        max_value = max((b["total"] for b in per_month), default=0.0)
        if max_value <= 0 and not per_month:
            _empty_state(self.stats_box, t("stats.no_data"))
            return

        ctk.CTkLabel(self.stats_box, text=t("stats.expenses_per_month"),
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(fill="x", padx=12, pady=(8, 4))

        chart_w = 720
        chart_h = 180
        # Canvas-Hintergrund an Light/Dark-Mode anpassen
        color_index = 1 if ctk.get_appearance_mode() == "Dark" else 0
        bg_hex = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][color_index]
        label_theme = ctk.ThemeManager.theme["CTkLabel"]
        text_hex = label_theme["text_color"][color_index]
        muted_colors = label_theme.get("text_color_disabled",
                                       label_theme["text_color"])
        muted_hex = muted_colors[color_index]
        canvas = tk.Canvas(self.stats_box, width=chart_w, height=chart_h,
                           bg=bg_hex, highlightthickness=0)
        canvas.pack(padx=12, pady=4)
        n = max(1, len(per_month))
        bar_w = (chart_w - 40) / n
        for i, bucket in enumerate(per_month):
            value = bucket["total"]
            ratio = (value / max_value) if max_value > 0 else 0
            bar_h = int((chart_h - 40) * ratio)
            x0 = 20 + i * bar_w + 4
            x1 = 20 + (i + 1) * bar_w - 4
            y0 = chart_h - 20 - bar_h
            y1 = chart_h - 20
            canvas.create_rectangle(
                x0, y0, x1, y1, fill="#0078D4", outline="")
            canvas.create_text((x0 + x1) / 2, chart_h - 8,
                               text=bucket["month"][-2:],     # nur Monat
                               fill=muted_hex,
                               font=("Segoe UI", 9))
            if value > 0:
                canvas.create_text((x0 + x1) / 2, y0 - 8,
                                   text=f"{value:.0f}",
                                   fill=text_hex,
                                   font=("Segoe UI", 9))

        # 2) Vertraege-Ueberblick
        overview = self.registry.dispatch("stats.contracts_overview", {})
        ctk.CTkLabel(
            self.stats_box,
            text=t("stats.contracts_overview"),
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x", padx=12, pady=(16, 4))
        summary_text = (
            t("stats.contracts_count").format(count=overview['count'])
            + "  -  "
            + t("stats.monthly_total").format(amount=overview['monthly_total'])
            + "  -  "
            + t("stats.yearly_total").format(amount=overview['yearly_total']))
        ctk.CTkLabel(self.stats_box, text=summary_text,
                     text_color="gray", anchor="w"
                     ).pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(self.stats_box, text=t("stats.top_3"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray", anchor="w"
                     ).pack(fill="x", padx=12, pady=(4, 2))
        for entry in overview.get("top_3", []):
            ctk.CTkLabel(
                self.stats_box,
                text=(f"   {entry['name']} ({entry['provider'] or '-'}): "
                       f"{entry['monthly_cost']:.2f} EUR/Monat"),
                anchor="w"
            ).pack(fill="x", padx=12)

        # 3) Jahresueberblick
        yearly = self.registry.dispatch("stats.yearly_summary", {})
        ctk.CTkLabel(
            self.stats_box,
            text=f"{t('stats.yearly_summary')} ({yearly['year']})",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x", padx=12, pady=(16, 4))
        ctk.CTkLabel(
            self.stats_box,
            text=(f"{yearly['expense_count']} Ausgaben, "
                   f"{yearly['expense_total']:.2f} EUR. "
                   + t("stats.average_per_month")
                   + f": {yearly['average_per_month']:.2f} EUR."),
            text_color="gray", anchor="w"
        ).pack(fill="x", padx=12)

    # ================================================================
    #  Daten (Tab "Daten")
    # ================================================================
    def _build_data(self, parent) -> None:
        from services.backup import list_backups
        parent.grid_columnconfigure(0, weight=1)
        t = self.i18n.t

        ctk.CTkLabel(parent, text=t("data.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 6))

        # Profil-Info
        profile_row = ctk.CTkFrame(parent, fg_color="transparent")
        profile_row.grid(row=1, column=0, sticky="ew", pady=(4, 12))
        ctk.CTkLabel(profile_row, text=t("data.profile_label") + ":",
                     anchor="w", width=160).pack(side="left")
        ctk.CTkLabel(
            profile_row,
            text=(self.profile or t("data.profile_default")),
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w").pack(side="left")

        # Backup
        backup_card = ctk.CTkFrame(
            parent, border_width=1, border_color=CARD_BORDER,
        )
        backup_card.grid(row=2, column=0, sticky="ew", pady=4)
        backup_body = ctk.CTkFrame(backup_card, fg_color="transparent")
        backup_body.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(backup_body, text=t("data.backup_section"),
                     font=_win11_font(size=13, weight="bold")
                     ).pack(anchor="w")
        backup_btn_row = ctk.CTkFrame(backup_body, fg_color="transparent")
        backup_btn_row.pack(fill="x", pady=(4, 4))
        ctk.CTkButton(backup_btn_row, text=t("data.backup_create"),
                      command=self._do_backup
                      ).pack(side="left", padx=(0, 8))
        self.backup_info = ctk.CTkLabel(backup_btn_row, text="",
                                          text_color="gray")
        self.backup_info.pack(side="left")

        # Letztes Backup anzeigen
        backups = list_backups(Path("backups"))
        last_label = ctk.CTkLabel(
            backup_body,
            text=(t("data.last_backup") + ": "
                   + (backups[0].name if backups
                       else t("data.backup_list_empty"))),
            text_color="gray", anchor="w")
        last_label.pack(anchor="w")

        # Export
        export_card = ctk.CTkFrame(
            parent, border_width=1, border_color=CARD_BORDER,
        )
        export_card.grid(row=3, column=0, sticky="ew", pady=4)
        export_body = ctk.CTkFrame(export_card, fg_color="transparent")
        export_body.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(export_body, text=t("data.export_section"),
                     font=_win11_font(size=13, weight="bold")
                     ).pack(anchor="w")
        export_row = ctk.CTkFrame(export_body, fg_color="transparent")
        export_row.pack(fill="x", pady=(4, 4))
        ctk.CTkButton(export_row, text=t("data.export_run"),
                      command=self._do_export
                      ).pack(side="left", padx=(0, 8))
        self.export_info = ctk.CTkLabel(export_row, text="",
                                          text_color="gray")
        self.export_info.pack(side="left")

        # Import
        import_card = ctk.CTkFrame(
            parent, border_width=1, border_color=CARD_BORDER,
        )
        import_card.grid(row=4, column=0, sticky="ew", pady=4)
        import_body = ctk.CTkFrame(import_card, fg_color="transparent")
        import_body.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(import_body, text=t("data.import_section"),
                     font=_win11_font(size=13, weight="bold")
                     ).pack(anchor="w")
        ctk.CTkLabel(import_body, text=t("data.import_warning"),
                     text_color="gray",
                     font=ctk.CTkFont(size=11)).pack(anchor="w")
        import_row = ctk.CTkFrame(import_body, fg_color="transparent")
        import_row.pack(fill="x", pady=(4, 4))
        ctk.CTkButton(import_row, text=t("data.import_pick_dir"),
                      command=self._do_import
                      ).pack(side="left", padx=(0, 8))
        self.import_info = ctk.CTkLabel(import_row, text="",
                                          text_color="gray")
        self.import_info.pack(side="left")

    def _do_backup(self) -> None:
        from database import Database
        from services.backup import default_backup_name, make_backup
        from services.profile import db_path, resolve_profile
        try:
            db_file = db_path(resolve_profile(),
                                str(self.assistant.log.db.path
                                     if self.assistant.log else
                                     "alltagshelfer_gui.db"))
            db = Database(db_file)
            try:
                target = Path("backups") / default_backup_name()
                make_backup(db, target)
                self.backup_info.configure(text=str(target))
            finally:
                db.close()
        except Exception as exc:                              # noqa: BLE001
            self.backup_info.configure(text=f"Fehler: {exc}",
                                          text_color="#d9534f")

    def _do_export(self) -> None:
        from database import (CalendarRepository, ContractRepository,
                                ExpenseRepository, FamilyRepository,
                                SocialRepository)
        from services.export import export_all
        from datetime import datetime
        target = (Path("ausgaben")
                   / f"export-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        # Wir koennen direkt die laufende DB benutzen - sie ist sowieso
        # offen.
        db = self.registry.modules()[0].repo.db                  # type: ignore[attr-defined]
        counts = export_all(
            target,
            ContractRepository(db), ExpenseRepository(db),
            CalendarRepository(db), SocialRepository(db),
            FamilyRepository(db))
        total = sum(counts.values())
        self.export_info.configure(
            text=f"{target} ({total} Zeilen)")

    def _do_import(self) -> None:
        from tkinter import filedialog
        from database import (CalendarRepository, ContractRepository,
                                ExpenseRepository, FamilyRepository,
                                SocialRepository)
        from services.import_csv import import_all
        directory = filedialog.askdirectory(
            title=self.i18n.t("data.import_pick_dir"))
        if not directory:
            return
        db = self.registry.modules()[0].repo.db                  # type: ignore[attr-defined]
        counts = import_all(
            Path(directory),
            ContractRepository(db), ExpenseRepository(db),
            CalendarRepository(db), SocialRepository(db),
            FamilyRepository(db))
        total = sum(counts.values())
        self.import_info.configure(text=f"{total} Zeilen importiert")
        self._refresh_all()

    # ================================================================
    #  Modul-Verwaltung (Tab "Module")
    # ================================================================
    def _build_module_admin(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        t = self.i18n.t

        ctk.CTkLabel(parent, text=t("modules.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 8))
        ctk.CTkLabel(parent, text=t("modules.hint"),
                     text_color="gray", wraplength=720, justify="left"
                     ).grid(row=0, column=0, sticky="sw", pady=(0, 6))

        self.module_admin_list = ctk.CTkScrollableFrame(
            parent, fg_color="transparent")
        self.module_admin_list.grid(row=1, column=0, sticky="nsew")

    def _refresh_module_admin(self) -> None:
        if not hasattr(self, "module_admin_list"):
            return
        _clear(self.module_admin_list)
        t = self.i18n.t
        for state in self.registry.module_states():
            card = ctk.CTkFrame(self.module_admin_list)
            card.pack(fill="x", padx=2, pady=4)
            body = ctk.CTkFrame(card, fg_color="transparent")
            body.pack(fill="x", padx=12, pady=8)

            top = ctk.CTkFrame(body, fg_color="transparent")
            top.pack(fill="x")
            ctk.CTkLabel(
                top,
                text=f"{state['display_name']} ({state['module_id']})",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(side="left")
            switch_var = ctk.BooleanVar(value=state["enabled"])
            ctk.CTkSwitch(top, text=t("modules.active"),
                           variable=switch_var,
                           command=lambda mid=state["module_id"],
                           var=switch_var: self._toggle_module(mid, var)
                           ).pack(side="right")

            ctk.CTkLabel(
                body,
                text=t("modules.capabilities_label").format(
                    n=len(state['capabilities']))
                      + " " + ", ".join(state["capabilities"]),
                text_color="gray", font=ctk.CTkFont(size=11),
                wraplength=720, justify="left"
            ).pack(anchor="w", pady=(4, 0))

    def _toggle_module(self, module_id: str, var) -> None:
        enabled = bool(var.get())
        self.registry.set_module_enabled(module_id, enabled)
        self.module_states.set_enabled(module_id, enabled)
        self._refresh_all()

    # ================================================================
    #  Tastatur-Shortcuts
    # ================================================================
    SHORTCUT_MAP: list[tuple[str, str, str]] = [
        # (Tk-Sequence, Tab-Key, Aktion)
        ("<Control-n>", "tab.contracts", "focus_new_contract"),
        ("<Control-f>", "tab.search", "focus_search"),
        ("<Control-i>", "tab.inbox", ""),
        ("<F5>", "", "refresh_all"),
        ("<Control-s>", "", "backup_now"),
        ("<Control-q>", "", "close"),
    ]

    def _bind_shortcuts(self) -> None:
        # add='+' verhindert, dass wir bestehende globale Bindings
        # ueberschreiben (z.B. F5 von CustomTkinter) - N3.
        for sequence, tab_key, action in self.SHORTCUT_MAP:
            self.bind_all(
                sequence,
                lambda e, t=tab_key, a=action:
                self._run_shortcut(e, t, a),
                add="+")

    def _focus_is_text_entry(self, event) -> bool:
        """True, wenn der Fokus auf einem Text-Eingabe-Widget liegt -
        dann keine seiteneffekt-belasteten Shortcuts abfangen (M4)."""
        try:
            focused = event.widget if event is not None else None
        except Exception:
            focused = None
        if focused is None:
            try:
                focused = self.focus_get()
            except Exception:
                focused = None
        if focused is None:
            return False
        # Tk-Klassen-Namen: 'Entry', 'Text', plus CTk-Aequivalente
        try:
            cls = focused.winfo_class()
        except Exception:
            return False
        return cls in ("Entry", "Text", "TEntry", "CTkEntry", "CTkTextbox")

    def _run_shortcut(self, event, tab_key: str, action: str) -> str:
        """
        Wechselt auf den Tab und fuehrt die Folgeaktion aus. 'break'
        verhindert weiteres Event-Bubbling.

        Seiteneffekt-belastete Shortcuts (backup_now, close) werden
        unterdrueckt, wenn der Nutzer gerade in einem Text-Feld tippt
        (M4). Reine Navigations-Shortcuts (focus_*, refresh_all) sind
        immer erlaubt.
        """
        side_effect_actions = {"backup_now", "close"}
        if action in side_effect_actions and self._focus_is_text_entry(event):
            return None         # Default-Verhalten des Widgets erlauben
        if tab_key:
            try:
                self.tabs.set(self.i18n.t(tab_key))
            except Exception:
                pass
        if action == "focus_new_contract":
            entry = self.contract_inputs.get("name") \
                if hasattr(self, "contract_inputs") else None
            if entry is not None:
                entry.focus_set()
        elif action == "focus_search":
            if hasattr(self, "search_entry"):
                self.search_entry.focus_set()
        elif action == "refresh_all":
            self._refresh_all()
        elif action == "backup_now":
            try:
                self._do_backup()
            except Exception:
                pass
        elif action == "close":
            self._on_close()
        return "break"

    # ================================================================
    #  Fenster-Schluss: Geometrie persistieren + after-Callbacks canceln
    # ================================================================
    def _safe_after(self, ms: int, callback) -> str:
        """
        Wie self.after(...), nur dass die ID gesammelt wird, damit wir
        sie beim Fenster-Close alle abbrechen koennen (M5). Verhindert
        TclError, wenn ein verzoegerter Callback ein zerstoertes Widget
        anspricht.
        """
        try:
            after_id = self.after(ms, callback)
        except Exception:
            return ""
        self._after_ids.add(after_id)
        return after_id

    def _post(self, callback) -> None:
        """Thread-sicher: aus JEDEM Thread aufrufbar. Reiht einen Callback
        ein, den _drain_ui_queue auf dem Main-Thread ausfuehrt. So ruft kein
        Worker-Thread jemals direkt eine Tk/Tcl-Funktion auf."""
        self._ui_queue.put(callback)

    def _drain_ui_queue(self) -> None:
        """Main-Thread-Loop: arbeitet eingereihte Worker-Callbacks ab und
        plant sich selbst neu ein. Reschedule laeuft ueber _safe_after, wird
        also beim Fenster-Close mit abgebrochen."""
        try:
            while True:
                callback = self._ui_queue.get_nowait()
                try:
                    callback()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self._safe_after(20, self._drain_ui_queue)

    def _cancel_pending_after(self) -> None:
        for aid in list(self._after_ids):
            try:
                self.after_cancel(aid)
            except Exception:
                pass
        self._after_ids.clear()

    def _on_close(self) -> None:
        # Pending Callbacks zuerst stoppen - sonst feuern Simulate-Word-
        # Stream-Timer noch in zerstoerte Widgets.
        self._cancel_pending_after()
        # Geometry validieren bevor wir sie persistieren - eine kaputte
        # ('iconified', 'withdrawn') wuerde beim naechsten Start crashen.
        try:
            current = self.geometry()
            if _is_valid_geometry(current):
                self.settings_repo.set("gui.geometry", current)
        except Exception:
            pass
        self.destroy()

    # ================================================================
    #  Suche
    # ================================================================
    def _build_search(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(parent, text=self.i18n.t("search.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 6))

        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        bar.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(
            bar, placeholder_text=self.i18n.t("search.placeholder"))
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda _e: self._run_search())
        ctk.CTkButton(bar, text=self.i18n.t("search.button"), width=110,
                      command=self._run_search).grid(row=0, column=1)

        # Optionale Filter (Kategorie / Status / Zeitraum). Leer = ignoriert;
        # ein gesetzter Filter erlaubt auch eine Suche ohne Stichwort.
        filt = ctk.CTkFrame(parent, fg_color="transparent")
        filt.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(filt, text=self.i18n.t("search.filter_label"),
                     text_color="gray").pack(side="left", padx=(0, 6))
        self.search_category = ctk.CTkEntry(
            filt, placeholder_text=self.i18n.t("search.ph_category"),
            width=130)
        self.search_category.pack(side="left", padx=4)
        self.search_status = ctk.CTkEntry(
            filt, placeholder_text=self.i18n.t("search.ph_status"), width=110)
        self.search_status.pack(side="left", padx=4)
        self.search_date_from = ctk.CTkEntry(
            filt, placeholder_text=self.i18n.t("search.ph_date_from"),
            width=130)
        self.search_date_from.pack(side="left", padx=4)
        self.search_date_to = ctk.CTkEntry(
            filt, placeholder_text=self.i18n.t("search.ph_date_to"),
            width=130)
        self.search_date_to.pack(side="left", padx=4)
        for _e in (self.search_category, self.search_status,
                   self.search_date_from, self.search_date_to):
            _e.bind("<Return>", lambda _ev: self._run_search())

        self.search_results = ctk.CTkScrollableFrame(
            parent, fg_color="transparent")
        self.search_results.grid(row=3, column=0, sticky="nsew")

    def _run_search(self) -> None:
        _clear(self.search_results)
        result = self._present_search.search(
            self.search_entry.get(),
            category=self.search_category.get(),
            status=self.search_status.get(),
            date_from=self.search_date_from.get(),
            date_to=self.search_date_to.get())
        if result["status"] != "ok":
            if result["status"] == "empty":
                _empty_state(self.search_results,
                             self.i18n.t("search.no_hits"))
                return
            text = (self.i18n.t("search.too_short")
                    if result["status"] == "too_short"
                    else result["message"])
            ctk.CTkLabel(self.search_results, text=text,
                         text_color="gray").pack(pady=20)
            return
        ctk.CTkLabel(self.search_results,
                     text=self.i18n.t("search.results_count").format(
                         count=result['count']),
                     text_color="gray").pack(anchor="w", pady=(4, 8))
        for hit in result["hits"]:
            self._search_card(hit)

    def _search_card(self, hit: dict) -> None:
        body = _card_row(self.search_results)
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=f"[{hit['source']}]", height=18,
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="gray").pack(side="left")
        ctk.CTkLabel(top, text=f"#{hit['entity_id']}", height=18,
                     font=ctk.CTkFont(size=10), text_color="gray"
                     ).pack(side="right")
        ctk.CTkLabel(body, text=hit["title"],
                     font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w", justify="left", wraplength=620
                     ).pack(fill="x", pady=(2, 0))
        if hit.get("detail"):
            ctk.CTkLabel(body, text=hit["detail"],
                         font=ctk.CTkFont(size=11),
                         text_color="gray", anchor="w", justify="left",
                         wraplength=620).pack(fill="x")

    # ================================================================
    #  Verlauf (Chat-Historie aus assistant_log)
    # ================================================================
    def _build_history(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(6, 4))
        ctk.CTkLabel(header, text=self.i18n.t("history.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).pack(side="left")
        ctk.CTkButton(header, text=self.i18n.t("history.refresh"),
                      width=120,
                      command=self._refresh_history).pack(side="right")

        self.history_text = ctk.CTkTextbox(
            parent, wrap="word", font=ctk.CTkFont(size=12))
        self.history_text.grid(row=1, column=0, sticky="nsew")
        self.history_text.configure(state="disabled")

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_text"):
            return
        # Vorhandenes Log-Repository des Assistenten weiterverwenden -
        # neu zu konstruieren wuerde die DB-Referenz unnoetig duplizieren
        # (und mypy laesst keinen Optional-Database durchgehen).
        repo = self.assistant.log
        entries = []
        if repo is not None:
            try:
                entries = repo.tail(limit=200)
            except Exception:
                entries = []
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if not entries:
            self.history_text.insert("1.0", self.i18n.t("history.empty"))
        else:
            you_label = self.i18n.t("common.you")
            assistant_label = self.i18n.t("common.assistant")
            for entry in entries:
                who = (you_label if entry.role == "user"
                        else assistant_label if entry.role == "assistant"
                        else entry.role)
                self.history_text.insert("end", f"{who}:\n{entry.content}\n\n")
        self.history_text.configure(state="disabled")
        self.history_text.see("end")

    # ================================================================
    #  Einstellungen
    # ================================================================
    SETTING_FIELDS: list[tuple[str, str, str]] = [
        # (config-Key, Label, Hilfetext)
        ("gemini.model", "Gemini-Modell",
         "z.B. gemini-2.5-flash oder gemini-2.5-pro"),
        ("gemini.max_iterations", "Max. Tool-Iterationen", "Sicherheitslimit"),
        ("gemini.max_tokens", "Max. Antwort-Tokens", ""),
        ("imap.host", "IMAP-Host",
         "Leer = aus. Login ueber Env (ALLTAGSHELFER_IMAP_PASS)."),
        ("imap.user", "IMAP-Benutzer", ""),
        ("imap.folder", "IMAP-Ordner", "Standard: INBOX"),
        ("smtp.host", "SMTP-Host", "Leer = aus"),
        ("smtp.port", "SMTP-Port", ""),
        ("smtp.user", "SMTP-Benutzer", ""),
        ("smtp.sender", "SMTP-Absender", ""),
        ("smtp.starttls", "SMTP STARTTLS", "true / false"),
        ("sync.dir", "Sync-Ordner",
         "Pfad zum geteilten Ordner (z.B. OneDrive)"),
        ("sync.enabled", "Sync aktiv",
         "auto | true | false (greift erst beim Neustart)"),
        ("sync.interval_seconds", "Sync-Intervall (s)", ""),
        ("notify.warn_within_days", "Notifikationen ab Tagen", ""),
    ]

    def _build_settings(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        t = self.i18n.t

        ctk.CTkLabel(parent, text=t("settings.title"),
                     font=_win11_font(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 6))

        ctk.CTkLabel(parent, text=t("settings.intro"), text_color="gray",
                     wraplength=720, justify="left"
                     ).grid(row=0, column=0, sticky="sw", pady=(0, 6))

        body = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")

        self.setting_inputs: dict[str, ctk.CTkEntry] = {}
        for key, label, helptext in self.SETTING_FIELDS:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, width=200, anchor="w"
                          ).pack(side="left")
            current = self.settings_repo.get(key, DEFAULTS.get(key, ""))
            entry = ctk.CTkEntry(row, width=320)
            entry.insert(0, current or "")
            entry.pack(side="left", padx=(0, 8))
            self.setting_inputs[key] = entry
            if helptext:
                ctk.CTkLabel(row, text=helptext, text_color="gray",
                             font=ctk.CTkFont(size=10)
                             ).pack(side="left", fill="x", expand=True)

        # Sekundaere Geheim-Felder: Hinweis, aber kein Input
        secrets_info = ctk.CTkFrame(body, fg_color="transparent")
        secrets_info.pack(fill="x", pady=(20, 4))
        ctk.CTkLabel(
            secrets_info, text=t("settings.secrets_intro"),
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        for key in sorted(SECRET_KEYS):
            env = ENV_MAP.get(key, "(kein Env-Mapping)")
            set_text = (t("settings.secret_set") if os.environ.get(env)
                         else t("settings.secret_unset"))
            ctk.CTkLabel(
                secrets_info,
                text=f"  {key}  ->  {env}   [{set_text}]",
                text_color="gray", font=ctk.CTkFont(size=11)
            ).pack(anchor="w")

        # Lizenz-Sektion: Status + Pricing + Trial + Token-Paste
        self._build_license_section(body)

        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=8)
        ctk.CTkButton(actions, text=t("settings.save"),
                      command=self._save_settings
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text=t("settings.reset"),
                      fg_color="transparent", border_width=1,
                      command=self._reset_settings
                      ).pack(side="left")
        self.settings_status = ctk.CTkLabel(actions, text="", text_color="gray")
        self.settings_status.pack(side="right")

    # ----------------------------------------------------------------
    #  Lizenz-Sektion (Settings-Tab)
    # ----------------------------------------------------------------
    def _build_license_section(self, body) -> None:
        from services.license_ui import (build_pricing_rows, make_tier_status)
        from services.licensing import recommended_tier

        section = ctk.CTkFrame(
            body, border_width=1, border_color=CARD_BORDER,
        )
        section.pack(fill="x", pady=(24, 6), padx=4)
        ctk.CTkLabel(section, text="Lizenz",
                     font=_win11_font(size=14, weight="bold")
                     ).pack(anchor="w", padx=14, pady=(10, 0))

        st = make_tier_status(self._current_license)
        self._license_status_label = ctk.CTkLabel(
            section, text=f"Aktueller Tier: {st.headline}\n{st.detail}",
            justify="left", anchor="w", wraplength=720)
        self._license_status_label.pack(anchor="w", pady=(4, 12),
                                         fill="x", padx=14)

        # 'Mein Abo': sichtbar nur, wenn ein Pro-Abo aktiv ist
        self._build_subscription_block(section)

        # Pricing-Tabelle
        ctk.CTkLabel(section, text="Preise (Brutto, inkl. USt.)",
                     font=_win11_font(weight="bold")
                     ).pack(anchor="w", pady=(4, 4), padx=14)
        persons = max(1, self._current_license.persons)
        rec = recommended_tier(persons)
        for row in build_pricing_rows(persons, recommended=rec):
            marker = "  > " if row.is_recommended else "    "
            text = f"{marker}{row.label:24} {row.price_text}"
            ctk.CTkLabel(section, text=text, justify="left",
                          anchor="w", font=ctk.CTkFont(family="Courier")
                          ).pack(anchor="w", padx=14)
            ctk.CTkLabel(section, text=f"      {row.description}",
                          text_color="gray",
                          font=ctk.CTkFont(family="Courier", size=10),
                          ).pack(anchor="w", pady=(0, 2), padx=14)

        # Trial-Button + Checkout-Buttons (falls Checkout-URLs konfiguriert)
        actions_frame = ctk.CTkFrame(section, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(12, 4), padx=14)
        trial_btn = ctk.CTkButton(
            actions_frame,
            text=("14 Tage Trial starten"
                  if st.can_start_trial else "Trial nicht verfuegbar"),
            command=self._on_start_trial,
            state="normal" if st.can_start_trial else "disabled")
        trial_btn.pack(side="left", padx=(0, 8))
        for label, url in (
            ("Pro monatlich kaufen", self.config.checkout_url_monthly),
            ("Pro jaehrlich kaufen", self.config.checkout_url_annual),
            ("Pro Familie kaufen", self.config.checkout_url_family),
        ):
            if not url:
                continue
            ctk.CTkButton(
                actions_frame, text=label,
                command=lambda u=url: self._open_checkout(u),
            ).pack(side="left", padx=(0, 8))

        # Token-Paste
        token_frame = ctk.CTkFrame(section, fg_color="transparent")
        token_frame.pack(fill="x", pady=(12, 4), padx=14)
        ctk.CTkLabel(token_frame, text="Pro-Lizenz-Token einfuegen:"
                     ).pack(anchor="w")
        entry_row = ctk.CTkFrame(token_frame, fg_color="transparent")
        entry_row.pack(fill="x", pady=(2, 0))
        self._license_token_entry = ctk.CTkEntry(entry_row,
                                                    placeholder_text="<payload>.<signature>")
        self._license_token_entry.pack(side="left", fill="x", expand=True,
                                          padx=(0, 8))
        ctk.CTkButton(entry_row, text="Aktivieren",
                      command=self._on_apply_token
                      ).pack(side="left")
        self._license_action_status = ctk.CTkLabel(
            section, text="", text_color="gray", wraplength=720,
            justify="left", anchor="w")
        self._license_action_status.pack(anchor="w", pady=(8, 10),
                                         fill="x", padx=14)

    def _build_subscription_block(self, parent) -> None:
        """'Mein Abo': Vertragsdaten + Kuendigungs-Link beim Provider."""
        from services.license_ui import make_subscription_info
        info = make_subscription_info(
            self._current_license,
            manage_url=self.config.checkout_manage_url)
        if not info.has_subscription:
            return
        block = ctk.CTkFrame(
            parent, border_width=1, border_color=CARD_BORDER,
        )
        block.pack(fill="x", pady=(0, 12), padx=14)
        ctk.CTkLabel(block, text="Mein Abo",
                      font=_win11_font(weight="bold")
                      ).pack(anchor="w", padx=14, pady=(10, 4))
        lines = [
            f"Tier:           {info.tier_label}",
            f"Personen:       {info.persons}",
        ]
        if info.purchased_at_iso:
            lines.append(f"Gekauft am:     {info.purchased_at_iso}")
        if info.expires_at_iso:
            grace_hint = "  (in Karenzzeit)" if info.in_grace_period else ""
            lines.append(
                f"Aktiv bis:      {info.expires_at_iso}"
                f"  ({info.days_remaining} Tag(e)){grace_hint}")
        ctk.CTkLabel(block, text="\n".join(lines),
                      justify="left", anchor="w",
                      font=ctk.CTkFont(family="Courier"),
                      ).pack(anchor="w", padx=10, pady=(0, 8))
        if info.manage_url:
            ctk.CTkButton(
                block,
                text="Abo verwalten / kuendigen (oeffnet Browser)",
                fg_color="transparent", border_width=1,
                command=lambda u=info.manage_url: self._open_checkout(u),
            ).pack(anchor="w", padx=10, pady=(0, 8))
        else:
            ctk.CTkLabel(
                block,
                text=("Zum Kuendigen die Kunden-Mail des Bezahldienst-"
                      "leisters oeffnen - dort gibt es einen Self-Service-"
                      "Link zum Abo-Portal."),
                text_color="gray", wraplength=600, justify="left",
                anchor="w",
            ).pack(anchor="w", padx=10, pady=(0, 8))

    def _on_start_trial(self) -> None:
        from services.license_ui import action_start_trial
        result = action_start_trial(self.settings_repo)
        self._license_action_status.configure(text=result.message)
        if result.success:
            self._refresh_license_state()

    def _open_checkout(self, url: str) -> None:
        """Oeffnet die Checkout-URL des Bezahldienstleisters im Browser."""
        import webbrowser
        try:
            webbrowser.open(url, new=2)
            self._license_action_status.configure(
                text=("Checkout im Browser geoeffnet. "
                      "Nach erfolgreicher Zahlung erhaeltst du den Token "
                      "per Mail - dann hier unten einfuegen."))
        except Exception as exc:                        # noqa: BLE001
            self._license_action_status.configure(
                text=f"Konnte Browser nicht oeffnen: {exc}")

    def _on_apply_token(self) -> None:
        from services.license_ui import action_apply_token
        token_str = self._license_token_entry.get().strip()
        result = action_apply_token(self.settings_repo, token_str)
        self._license_action_status.configure(text=result.message)
        if result.success:
            self._license_token_entry.delete(0, "end")
            self._refresh_license_state()

    def _refresh_license_state(self) -> None:
        """Lizenz neu laden, Tier-Indikator + Tab-Decorations updaten."""
        from services.licensing import load_license as _load_license
        from services.license_ui import (make_tier_status,
                                           sidebar_indicator)
        self._current_license = _load_license(self.settings_repo)
        try:
            self.tier_indicator.configure(
                text=sidebar_indicator(self._current_license))
        except Exception:
            pass
        try:
            st = make_tier_status(self._current_license)
            self._license_status_label.configure(
                text=f"Aktueller Tier: {st.headline}\n{st.detail}")
        except Exception:
            pass
        # Hinweis: Tab-Labels neu zu setzen erfordert in CTkTabview einen
        # Rebuild - wir zeigen den Hinweis im Status statt zu spammen.
        # Wie die Bloecke oben abgesichert: das Widget existiert erst, wenn
        # die Lizenz-/Settings-Sektion gebaut wurde.
        try:
            if self._current_license.is_pro():
                self._license_action_status.configure(
                    text=(self._license_action_status.cget("text")
                          + "  Tipp: Neustart laedt gesperrte Tabs neu."))
        except Exception:
            pass

    def _save_settings(self) -> None:
        from services.licensing import load_license

        saved = 0
        sync_blocked = False
        for key, entry in self.setting_inputs.items():
            value = entry.get().strip()
            if key == "sync.enabled" and value.lower() in ("true", "1", "yes"):
                if not load_license(self.settings_repo).allows_sync():
                    value = "false"
                    entry.delete(0, "end")
                    entry.insert(0, "false")
                    sync_blocked = True
            save_value(self.settings_repo, key, value)
            saved += 1
        msg = self.i18n.t("settings.saved").format(count=saved)
        if sync_blocked:
            msg += " " + self.i18n.t(
                "settings.sync_pro_required",
                "Mehrgeraete-Sync erfordert eine Pro-Lizenz.")
        self.settings_status.configure(text=msg)

    def _reset_settings(self) -> None:
        for key, entry in self.setting_inputs.items():
            entry.delete(0, "end")
            entry.insert(0, DEFAULTS.get(key, ""))
            save_value(self.settings_repo, key, DEFAULTS.get(key, ""))
        self.settings_status.configure(
            text=self.i18n.t("settings.reset_done"))

    # ================================================================
    #  Destruktiv-Bestaetigung (vom Assistant aufgerufen)
    # ================================================================
    def _confirm_destructive(self, tool_call) -> bool:
        if not _critical_confirmation_required(tool_call.name):
            return True
        from tkinter import messagebox
        text = (f"Der Assistent moechte die kritische Aktion "
                f"'{tool_call.name}' ausfuehren.\n\n"
                f"Argumente: {tool_call.args}\n\nZulassen?")
        return messagebox.askyesno("Aktion bestaetigen", text)

    # ================================================================
    #  Scheduler
    # ================================================================
    def _check_notifications(self) -> None:
        triggered = self.scheduler.check_now()
        msg = (f"{len(triggered)} Notifikation(en) ausgeloest."
               if triggered else "Aktuell nichts Akutes.")
        self._show_dialog("Notifikationen", msg)


def main() -> None:
    _apply_win11_theme()
    (db, registry, assistant, config, settings, module_states,
     synced, profile, auto_backup) = bootstrap()
    app = AlltagshelferGUI(registry, assistant, config,
                             settings, module_states, synced, profile,
                             auto_backup=auto_backup)
    # Hintergrund-Dienste starten
    app.scheduler.start()
    if app.sync_worker is not None:
        app.sync_worker.start()
    if app.auto_backup is not None:
        app.auto_backup.start()
    try:
        app.mainloop()
    finally:
        app.scheduler.stop()
        if app.sync_worker is not None:
            app.sync_worker.stop()
        if app.auto_backup is not None:
            app.auto_backup.stop()
        db.close()


if __name__ == "__main__":
    main()
