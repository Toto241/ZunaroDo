"""
GUI - CustomTkinter-Oberflaeche fuer den Alltagshelfer.

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
import threading
from datetime import date, timedelta
from typing import Callable

import customtkinter as ctk

from pathlib import Path

from assistant import Assistant
from core.interface import ModuleRegistry
from database import (AssistantLogRepository, Database, ModuleStateRepository,
                      SettingsRepository)
from main import (apply_persisted_module_states, build_registry,
                    make_smtp_config, make_sync_provider)
from services.config import (DEFAULTS, ENV_MAP, SECRET_KEYS, AppConfig,
                              load_config, save_value)
from services.gemini import GeminiClient
from services.i18n import I18n
from services.output import OutputService
from services.scheduler import ProactiveScheduler
from services.sync import PeriodicSyncWorker, install_sync_hook

SAMPLE_MAIL = (
    "Betreff: Information zu Ihrem Netflix-Abo\n\n"
    "Sehr geehrter Kunde, wir nehmen eine Preisanpassung vor. Ihr neuer "
    "monatlicher Preis betraegt 15,99 EUR.\n\nIhr Netflix-Team")

URGENCY_COLOR = {"hoch": "#d9534f", "mittel": "#e8a33d", "normal": "#5b9bd5"}
URGENCY_LABEL = {"hoch": "DRINGEND", "mittel": "BALD", "normal": "GEPLANT"}


# ---------------------------------------------------------------------
#  Beispieldaten beim ersten Start
# ---------------------------------------------------------------------
def _seed_if_empty(registry: ModuleRegistry) -> None:
    if registry.dispatch("contracts.list", {}).get("count", 0) > 0:
        return
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
                          SettingsRepository, ModuleStateRepository, object]:
    db = Database("alltagshelfer_gui.db")
    settings = SettingsRepository(db)
    config = load_config(settings)

    output = OutputService("ausgaben", smtp=make_smtp_config(config))
    llm = GeminiClient(model=config.gemini_model,
                       api_key=config.gemini_api_key or None)
    active_llm = llm if llm.is_available else None
    registry = build_registry(db, output, llm=active_llm)

    module_states = ModuleStateRepository(db)
    apply_persisted_module_states(registry, module_states)

    _seed_if_empty(registry)
    assistant = Assistant(
        registry, log=AssistantLogRepository(db), llm=active_llm,
        max_iterations=config.gemini_max_iterations,
        max_output_tokens=config.gemini_max_tokens,
    )

    provider = make_sync_provider(Path(".alltagshelfer-state")) \
        if config.sync_enabled != "false" else None
    synced = None
    if provider is not None:
        synced = install_sync_hook(registry, provider)
        try:
            provider.compact_if_needed()
        except Exception:
            pass
        synced.apply_remote()
    return db, registry, assistant, config, settings, module_states, synced


# ---------------------------------------------------------------------
#  Wiederverwendbare Hilfen
# ---------------------------------------------------------------------
def _labeled_entry(parent, label: str, placeholder: str = "",
                   width: int = 200) -> ctk.CTkEntry:
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=2)
    ctk.CTkLabel(row, text=label, width=130, anchor="w").pack(side="left")
    entry = ctk.CTkEntry(row, placeholder_text=placeholder, width=width)
    entry.pack(side="left", fill="x", expand=True)
    return entry


def _clear(frame) -> None:
    for w in frame.winfo_children():
        w.destroy()


# ---------------------------------------------------------------------
#  Hauptfenster
# ---------------------------------------------------------------------
class AlltagshelferGUI(ctk.CTk):

    def __init__(self, registry: ModuleRegistry, assistant: Assistant,
                 config: AppConfig,
                 settings_repo: SettingsRepository,
                 module_states: ModuleStateRepository,
                 synced=None):
        super().__init__()
        self.registry = registry
        self.assistant = assistant
        self.config = config
        self.settings_repo = settings_repo
        self.module_states = module_states
        self.synced = synced
        self.i18n = I18n(language=config.i18n_language)
        self.scheduler = ProactiveScheduler(
            registry, warn_within_days=config.notify_warn_within_days)
        self.sync_worker = PeriodicSyncWorker(
            synced, interval_seconds=config.sync_interval_seconds) \
            if synced is not None else None

        self.title(self.i18n.t("app.title"))
        self.geometry("1080x720")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=1, sticky="nsew",
                       padx=(0, 10), pady=10)
        # Tab-Labels durch i18n - Reihenfolge bleibt fest (Werte sind die
        # Builder-Funktionen, Schluessel die uebersetzten Labels).
        t = self.i18n.t
        self.tab_builders: dict[str, Callable] = {
            t("tab.dashboard"): self._build_dashboard,
            t("tab.contracts"): self._build_contracts,
            t("tab.family"): self._build_family,
            t("tab.finance"): self._build_finance,
            t("tab.calendar"): self._build_calendar,
            t("tab.social"): self._build_social,
            t("tab.inbox"): self._build_inbox,
            t("tab.assistant"): self._build_chat,
            t("tab.search"): self._build_search,
            t("tab.history"): self._build_history,
            t("tab.modules"): self._build_module_admin,
            t("tab.settings"): self._build_settings,
        }
        for name, builder in self.tab_builders.items():
            builder(self.tabs.add(name))

        # Assistant bei destruktiven Aufrufen den Nutzer fragen lassen
        self.assistant.set_confirm_callback(self._confirm_destructive)

        self._refresh_all()
        self._append_chat("Assistent",
                           "Hallo! Im Dashboard siehst du deine naechsten "
                           "Ereignisse. Hier kannst du mich alles fragen.")

    # ================================================================
    #  Sidebar
    # ================================================================
    def _build_sidebar(self) -> None:
        bar = ctk.CTkFrame(self, width=260, corner_radius=0)
        bar.grid(row=0, column=0, sticky="nsew")

        t = self.i18n.t
        ctk.CTkLabel(bar, text=t("app.title"),
                     font=ctk.CTkFont(size=20, weight="bold")
                     ).pack(padx=20, pady=(20, 2))
        ctk.CTkLabel(
            bar,
            text=f"{t('sidebar.assistant_mode')}: {self.assistant.mode}",
            text_color="gray").pack(padx=20, pady=(0, 14))

        ctk.CTkLabel(bar, text=t("sidebar.module_status"),
                     font=ctk.CTkFont(weight="bold")
                     ).pack(padx=20, anchor="w")
        self.status_box = ctk.CTkTextbox(bar, width=240, height=320, wrap="word")
        self.status_box.pack(padx=10, pady=8)

        ctk.CTkButton(bar, text=t("sidebar.refresh_all"),
                      command=self._refresh_all).pack(padx=15, pady=4, fill="x")
        ctk.CTkButton(bar, text=t("sidebar.check_now"),
                      command=self._check_notifications
                      ).pack(padx=15, pady=4, fill="x")

    # ================================================================
    #  Dashboard
    # ================================================================
    def _build_dashboard(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(6, 8))
        ctk.CTkLabel(header, text="Naechste Ereignisse",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).pack(side="left")
        self.horizon = ctk.CTkSegmentedButton(
            header, values=["30 Tage", "90 Tage", "Alle"],
            command=lambda _v: self._refresh_dashboard())
        self.horizon.set("90 Tage")
        self.horizon.pack(side="right")

        self.dash_list = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.dash_list.grid(row=1, column=0, sticky="nsew")

    def _refresh_dashboard(self) -> None:
        _clear(self.dash_list)
        horizon = {"30 Tage": 30, "90 Tage": 90, "Alle": 3650}[self.horizon.get()]
        events = self.registry.collect_events(horizon)
        if not events:
            ctk.CTkLabel(self.dash_list, text="Keine anstehenden Ereignisse.",
                         text_color="gray").pack(pady=30)
            return
        for event in events:
            self._event_card(event)

    def _event_card(self, event) -> None:
        color = URGENCY_COLOR[event.urgency]
        card = ctk.CTkFrame(self.dash_list, height=84)
        card.pack(fill="x", pady=3, padx=2)
        card.pack_propagate(False)
        ctk.CTkFrame(card, width=6, fg_color=color, corner_radius=0
                     ).pack(side="left", fill="y")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=12, pady=8)
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        days = event.days_remaining
        when = (f"in {days} Tagen" if days > 0
                else "heute faellig" if days == 0
                else f"{-days} Tage ueberfaellig")
        ctk.CTkLabel(top, text=f"{event.due_date.strftime('%d.%m.%Y')}  -  {when}",
                     height=16, font=ctk.CTkFont(size=11), text_color="gray"
                     ).pack(side="left")
        ctk.CTkLabel(top, text=URGENCY_LABEL[event.urgency], height=16,
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=color).pack(side="right")
        ctk.CTkLabel(body, text=event.title, height=22,
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(anchor="w")
        if event.detail:
            ctk.CTkLabel(body, text=event.detail, height=16,
                         font=ctk.CTkFont(size=11),
                         text_color="gray", wraplength=560, justify="left"
                         ).pack(anchor="w")

    # ================================================================
    #  Vertraege
    # ================================================================
    def _build_contracts(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(parent, text="Vertraege",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 4))

        form = ctk.CTkFrame(parent)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.contract_inputs = {
            "name": _labeled_entry(form, "Name", "z.B. Stromvertrag"),
            "provider": _labeled_entry(form, "Anbieter", "z.B. Stadtwerke"),
            "category": _labeled_entry(form, "Kategorie",
                                         "mobilfunk / streaming / strom / "
                                         "versicherung / sonstiges"),
            "monthly_cost": _labeled_entry(form, "Monatspreis (EUR)", "0.00"),
            "start_date": _labeled_entry(form, "Start (YYYY-MM-DD)",
                                            date.today().isoformat()),
            "minimum_term_months": _labeled_entry(form, "Mindestlaufzeit (Mon.)",
                                                     "12"),
            "notice_period_months": _labeled_entry(form, "Kuendigungsfrist (Mon.)",
                                                     "3"),
            "auto_renew_months": _labeled_entry(form, "Verlaengerung (Mon.)",
                                                  "12"),
            "owner_name": _labeled_entry(form, "Person", "(leer = ohne)"),
        }
        ctk.CTkButton(form, text="Vertrag anlegen",
                      command=self._on_contract_add).pack(pady=8)

        self.contract_list = ctk.CTkScrollableFrame(parent,
                                                      fg_color="transparent")
        self.contract_list.grid(row=2, column=0, sticky="nsew")

    def _on_contract_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.contract_inputs.items()}
        if not v["name"] or not v["category"]:
            return
        payload = {
            "name": v["name"],
            "provider": v["provider"],
            "category": v["category"] or "sonstiges",
            "start_date": v["start_date"] or None,
            "monthly_cost": float(v["monthly_cost"] or 0),
            "minimum_term_months": int(v["minimum_term_months"] or 12),
            "notice_period_months": int(v["notice_period_months"] or 3),
            "auto_renew_months": int(v["auto_renew_months"] or 12),
        }
        if v["owner_name"]:
            members = self.registry.dispatch("family.members",
                                               {})["members"]
            for m in members:
                if m["name"].lower() == v["owner_name"].lower():
                    payload["owner_id"] = m["id"]
                    break
        self.registry.dispatch("contracts.add", payload)
        for e in self.contract_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_contracts(self) -> None:
        _clear(self.contract_list)
        contracts = self.registry.dispatch("contracts.list",
                                             {}).get("contracts", [])
        if not contracts:
            ctk.CTkLabel(self.contract_list,
                         text="Noch keine Vertraege.",
                         text_color="gray").pack(pady=20)
            return
        for c in contracts:
            self._contract_row(c)

    def _contract_row(self, c: dict) -> None:
        card = ctk.CTkFrame(self.contract_list)
        card.pack(fill="x", pady=4, padx=2)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=8)

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
        ctk.CTkButton(btns, text="Kuendigungsschreiben",
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

        sub = ctk.CTkTabview(parent)
        sub.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self._build_family_members(sub.add("Mitglieder"))
        self._build_family_tasks(sub.add("Aufgaben"))
        self._build_family_orders(sub.add("Auftraege"))
        self._build_family_shopping(sub.add("Einkaufsliste"))

    def _build_family_members(self, parent) -> None:
        form = ctk.CTkFrame(parent)
        form.pack(fill="x", pady=(6, 8))
        self.member_inputs = {
            "name": _labeled_entry(form, "Name"),
            "role": _labeled_entry(form, "Rolle",
                                    "erwachsen / kind / sonstiges"),
            "birthday": _labeled_entry(form, "Geburtstag (YYYY-MM-DD)"),
        }
        ctk.CTkButton(form, text="Hinzufuegen",
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
        _clear(self.member_list)
        for m in self.registry.dispatch("family.members",
                                          {}).get("members", []):
            bday = f"  - Geburtstag {m['birthday']}" if m.get("birthday") else ""
            ctk.CTkLabel(self.member_list,
                         text=f"#{m['id']}  {m['name']} ({m['role']}){bday}",
                         anchor="w").pack(fill="x", padx=12, pady=2)

    def _build_family_tasks(self, parent) -> None:
        form = ctk.CTkFrame(parent)
        form.pack(fill="x", pady=(6, 8))
        self.task_inputs = {
            "title": _labeled_entry(form, "Titel"),
            "interval_days": _labeled_entry(form, "Intervall (Tage)", "7"),
            "assignees": _labeled_entry(form, "Rotation (Komma)",
                                          "Anna, Bernd"),
            "first_due": _labeled_entry(form, "Erstmals (YYYY-MM-DD)",
                                           date.today().isoformat()),
        }
        ctk.CTkButton(form, text="Aufgabe anlegen",
                      command=self._on_task_add).pack(pady=6)
        self.task_list = ctk.CTkScrollableFrame(parent,
                                                  fg_color="transparent")
        self.task_list.pack(fill="both", expand=True)

    def _on_task_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.task_inputs.items()}
        if not v["title"]:
            return
        assignees = [a.strip() for a in v["assignees"].split(",") if a.strip()]
        self.registry.dispatch("family.add_task", {
            "title": v["title"],
            "interval_days": int(v["interval_days"] or 7),
            "assignees": assignees,
            "first_due": v["first_due"] or None,
        })
        for e in self.task_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_tasks(self) -> None:
        _clear(self.task_list)
        for t in self.registry.dispatch("family.tasks",
                                          {}).get("tasks", []):
            row = ctk.CTkFrame(self.task_list, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
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
        form = ctk.CTkFrame(parent)
        form.pack(fill="x", pady=(6, 8))
        self.order_inputs = {
            "title": _labeled_entry(form, "Titel"),
            "assignee": _labeled_entry(form, "Wer", "Name"),
            "due_date": _labeled_entry(form, "Bis wann (YYYY-MM-DD)"),
            "description": _labeled_entry(form, "Notiz"),
        }
        ctk.CTkButton(form, text="Auftrag anlegen",
                      command=self._on_order_add).pack(pady=6)
        self.order_list = ctk.CTkScrollableFrame(parent,
                                                   fg_color="transparent")
        self.order_list.pack(fill="both", expand=True)

    def _on_order_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.order_inputs.items()}
        if not v["title"]:
            return
        payload = {"title": v["title"], "assignee": v["assignee"],
                    "description": v["description"]}
        if v["due_date"]:
            payload["due_date"] = v["due_date"]
        self.registry.dispatch("family.add_order", payload)
        for e in self.order_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_orders(self) -> None:
        _clear(self.order_list)
        for o in self.registry.dispatch("family.orders",
                                           {}).get("orders", []):
            row = ctk.CTkFrame(self.order_list, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            status_mark = "[ok]" if o["status"] == "erledigt" else "[offen]"
            faellig = f", bis {o['due_date']}" if o.get("due_date") else ""
            ctk.CTkLabel(row,
                         text=(f"{status_mark} {o['title']} -> "
                                f"{o.get('assignee') or 'niemand'}{faellig}"),
                         anchor="w").pack(side="left", fill="x", expand=True)
            if o["status"] != "erledigt":
                ctk.CTkButton(row, text="Erledigt", width=80,
                              command=lambda i=o["id"]:
                              self._dispatch_and_refresh(
                                  "family.complete_order", {"order_id": i})
                              ).pack(side="right")

    def _build_family_shopping(self, parent) -> None:
        form = ctk.CTkFrame(parent)
        form.pack(fill="x", pady=(6, 8))
        self.shopping_inputs = {
            "name": _labeled_entry(form, "Was"),
            "quantity": _labeled_entry(form, "Menge", "z.B. 1 kg"),
            "added_by": _labeled_entry(form, "Von", "Name"),
        }
        ctk.CTkButton(form, text="Auf die Liste",
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
        _clear(self.shopping_list)
        items = self.registry.dispatch(
            "family.shopping_list",
            {"include_bought": True}).get("items", [])
        for item in items:
            row = ctk.CTkFrame(self.shopping_list, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
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

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(6, 4))
        ctk.CTkLabel(header, text="Finanzen",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).pack(side="left")
        self.finance_summary = ctk.CTkLabel(header, text="", text_color="gray")
        self.finance_summary.pack(side="right")

        form = ctk.CTkFrame(parent)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.expense_inputs = {
            "description": _labeled_entry(form, "Wofuer", "z.B. Wocheneinkauf"),
            "amount": _labeled_entry(form, "Betrag (EUR)", "0.00"),
            "category": _labeled_entry(form, "Kategorie",
                                         "lebensmittel / freizeit / sonstiges"),
            "spent_on": _labeled_entry(form, "Datum (YYYY-MM-DD)",
                                           date.today().isoformat()),
            "owner_name": _labeled_entry(form, "Person", "(leer = ohne)"),
        }
        ctk.CTkButton(form, text="Ausgabe erfassen",
                      command=self._on_expense_add).pack(pady=8)

        self.expense_list = ctk.CTkScrollableFrame(parent,
                                                       fg_color="transparent")
        self.expense_list.grid(row=2, column=0, sticky="nsew")

    def _on_expense_add(self) -> None:
        v = {k: e.get().strip() for k, e in self.expense_inputs.items()}
        if not v["description"] or not v["amount"]:
            return
        payload = {
            "description": v["description"],
            "amount": float(v["amount"]),
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
        _clear(self.expense_list)
        over = self.registry.dispatch("finance.monthly_overview", {})
        self.finance_summary.configure(
            text=(f"{over['month']}: Vertraege {over['recurring_contracts']:.2f} "
                   f"+ einmalig {over['one_time_this_month']:.2f} = "
                   f"{over['total_monthly']:.2f} EUR"))
        for e in self.registry.dispatch("finance.list_expenses",
                                            {}).get("expenses", []):
            row = ctk.CTkFrame(self.expense_list, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
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

        ctk.CTkLabel(parent, text="Termine & Kalender",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 4))

        form = ctk.CTkFrame(parent)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.calendar_inputs = {
            "title": _labeled_entry(form, "Titel"),
            "due_date": _labeled_entry(form, "Datum (YYYY-MM-DD)",
                                          date.today().isoformat()),
            "category": _labeled_entry(form, "Kategorie",
                                          "termin / garantie / tuev / "
                                          "steuer / geburtstag / sonstiges"),
            "description": _labeled_entry(form, "Notiz"),
            "recurrence_days": _labeled_entry(form, "Wiederh. (Tage)",
                                                  "(leer = einmalig)"),
        }
        ctk.CTkButton(form, text="Termin anlegen",
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
        _clear(self.calendar_list)
        # Eigene Termine + alle synthetischen Events fuer kompletten Blick
        events = self.registry.dispatch("calendar.list_events",
                                            {}).get("events", [])
        if not events:
            ctk.CTkLabel(self.calendar_list, text="Noch keine Termine.",
                         text_color="gray").pack(pady=20)
            return
        for e in events:
            row = ctk.CTkFrame(self.calendar_list, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            extra = f" - {e['person']}" if e.get("person") else ""
            recur = (f", wiederkehrend alle {e['recurrence_days']} Tage"
                     if e.get("recurrence_days") else "")
            ctk.CTkLabel(row,
                         text=(f"{e['due_date']}  [{e['category']}]  "
                                f"{e['title']}{extra}{recur}"),
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text="Loeschen", width=90,
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

        ctk.CTkLabel(parent, text="Soziale Pflege",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 4))

        form = ctk.CTkFrame(parent)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.social_inputs = {
            "name": _labeled_entry(form, "Name"),
            "relation": _labeled_entry(form, "Beziehung",
                                          "Familie / Freund / Kollege ..."),
            "cadence_days": _labeled_entry(form, "Rhythmus (Tage)", "30"),
            "notes": _labeled_entry(form, "Notiz"),
        }
        ctk.CTkButton(form, text="Kontakt hinzufuegen",
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
            payload["cadence_days"] = int(v["cadence_days"])
        self.registry.dispatch("social.add_contact", payload)
        for e in self.social_inputs.values():
            e.delete(0, "end")
        self._refresh_all()

    def _refresh_social(self) -> None:
        _clear(self.social_list)
        for c in self.registry.dispatch("social.contacts",
                                           {}).get("contacts", []):
            row = ctk.CTkFrame(self.social_list, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            days = c.get("days_until_due", 0)
            when = (f"in {days} Tagen" if days > 0
                    else "heute" if days == 0
                    else f"{-days} Tage ueberfaellig")
            relation = f" ({c['relation']})" if c.get("relation") else ""
            ctk.CTkLabel(row,
                         text=f"{c['name']}{relation}  -  naechstes Melden {when}",
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text="Kontaktiert", width=110,
                          command=lambda i=c["id"]:
                          self._dispatch_and_refresh(
                              "social.mark_contacted", {"contact_id": i})
                          ).pack(side="right", padx=(0, 4))
            ctk.CTkButton(row, text="Entwurf", width=80,
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

        ctk.CTkLabel(parent, text="Eingegangene Mail analysieren",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 4))

        entry = ctk.CTkFrame(parent, fg_color="transparent")
        entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        entry.grid_columnconfigure(0, weight=1)
        self.mail_box = ctk.CTkTextbox(entry, height=120, wrap="word")
        self.mail_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.mail_box.insert("1.0", SAMPLE_MAIL)
        actions = ctk.CTkFrame(entry, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="n")
        ctk.CTkButton(actions, text="Analysieren", width=130,
                      command=self._analyze_mail).pack(pady=2)
        ctk.CTkButton(actions, text="IMAP abrufen", width=130,
                      command=self._fetch_imap).pack(pady=2)

        self.inbox_info = ctk.CTkLabel(
            parent, text="Offene Vorschlaege",
            font=ctk.CTkFont(size=14, weight="bold"))
        self.inbox_info.grid(row=2, column=0, sticky="w", pady=(0, 4))

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
            self.after(0, lambda: self._on_imap_done(result))

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
        _clear(self.proposal_list)
        data = self.registry.dispatch("inbox.proposals", {})
        count = data.get("count", 0)
        if not keep_info:
            self.inbox_info.configure(text=f"Offene Vorschlaege ({count})")
        if count == 0:
            ctk.CTkLabel(self.proposal_list, text="Keine offenen Vorschlaege.",
                         text_color="gray").pack(pady=24)
            return
        for proposal in data["proposals"]:
            self._proposal_card(proposal)

    def _proposal_card(self, p: dict) -> None:
        card = ctk.CTkFrame(self.proposal_list, corner_radius=8)
        card.pack(fill="x", pady=4, padx=2)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(body, text=p["summary"], anchor="w", justify="left",
                     wraplength=560,
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(anchor="w")
        ctk.CTkLabel(body,
                     text=f"Quelle: {p['source']}  -  Ziel: {p['target_capability']}",
                     anchor="w", text_color="gray",
                     font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 6))
        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.pack(anchor="w")
        ctk.CTkButton(buttons, text="Uebernehmen", width=120,
                      command=lambda i=p["id"]:
                      self._decide_proposal(i, True)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="Bearbeiten", width=110,
                      fg_color="transparent", border_width=1,
                      command=lambda pp=p:
                      self._open_proposal_editor(pp)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="Ablehnen", width=100,
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
        ctk.CTkLabel(dlg, text=cap.description,
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
        self.entry = ctk.CTkEntry(parent, placeholder_text="Frage eingeben ...")
        self.entry.grid(row=1, column=0, sticky="ew", padx=(0, 6),
                         pady=(0, 6))
        self.entry.bind("<Return>", lambda _e: self._on_send())
        ctk.CTkButton(parent, text="Senden", width=90,
                      command=self._on_send
                      ).grid(row=1, column=1, sticky="e", pady=(0, 6))

    def _on_send(self) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._append_chat("Du", text)
        self._append_chat("Assistent", "denkt nach ...")
        threading.Thread(target=self._chat_worker,
                          args=(text,), daemon=True).start()

    def _chat_worker(self, prompt: str) -> None:
        answer = self.assistant.ask(prompt)
        self.after(0, lambda: self._replace_last_chat(answer))
        self.after(0, self._refresh_all)

    def _append_chat(self, who: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}:\n{text}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _replace_last_chat(self, answer: str) -> None:
        self.chat.configure(state="normal")
        content = self.chat.get("1.0", "end-1c")
        marker = "Assistent:\ndenkt nach ...\n\n"
        if content.endswith(marker):
            self.chat.delete(f"end-{len(marker) + 1}c", "end")
        self.chat.insert("end", f"Assistent:\n{answer}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    # ================================================================
    #  Aktualisierung
    # ================================================================
    def _refresh_status(self) -> None:
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
        # Verlauf nur auf Anforderung aktualisieren - das Lesen von
        # assistant_log ist zwar billig, soll aber nicht jeden
        # Refresh-Tick mitmachen.

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
    #  Modul-Verwaltung (Tab "Module")
    # ================================================================
    def _build_module_admin(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(parent, text="Module ein-/ausschalten",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 8))
        ctk.CTkLabel(parent,
                     text=("Deaktivierte Module liefern weder Capabilities "
                            "noch Dashboard-Eintraege. Die Daten bleiben "
                            "in der DB erhalten."),
                     text_color="gray", wraplength=720, justify="left"
                     ).grid(row=0, column=0, sticky="sw", pady=(0, 6))

        self.module_admin_list = ctk.CTkScrollableFrame(
            parent, fg_color="transparent")
        self.module_admin_list.grid(row=1, column=0, sticky="nsew")

    def _refresh_module_admin(self) -> None:
        if not hasattr(self, "module_admin_list"):
            return
        _clear(self.module_admin_list)
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
            ctk.CTkSwitch(top, text="aktiv", variable=switch_var,
                           command=lambda mid=state["module_id"],
                           var=switch_var: self._toggle_module(mid, var)
                           ).pack(side="right")

            ctk.CTkLabel(
                body,
                text=f"{len(state['capabilities'])} Capabilities: "
                      + ", ".join(state["capabilities"]),
                text_color="gray", font=ctk.CTkFont(size=11),
                wraplength=720, justify="left"
            ).pack(anchor="w", pady=(4, 0))

    def _toggle_module(self, module_id: str, var) -> None:
        enabled = bool(var.get())
        self.registry.set_module_enabled(module_id, enabled)
        self.module_states.set_enabled(module_id, enabled)
        self._refresh_all()

    # ================================================================
    #  Suche
    # ================================================================
    def _build_search(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(parent, text="Volltextsuche",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 6))

        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        bar.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(
            bar, placeholder_text="Mindestens 2 Zeichen ...")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda _e: self._run_search())
        ctk.CTkButton(bar, text="Suchen", width=110,
                      command=self._run_search).grid(row=0, column=1)

        self.search_results = ctk.CTkScrollableFrame(
            parent, fg_color="transparent")
        self.search_results.grid(row=2, column=0, sticky="nsew")

    def _run_search(self) -> None:
        query = self.search_entry.get().strip()
        _clear(self.search_results)
        if len(query) < 2:
            ctk.CTkLabel(self.search_results,
                         text="Bitte mindestens 2 Zeichen eingeben.",
                         text_color="gray").pack(pady=20)
            return
        result = self.registry.dispatch(
            "system.search", {"query": query, "limit": 100})
        if "error" in result:
            ctk.CTkLabel(self.search_results,
                         text=result["error"], text_color="gray"
                         ).pack(pady=20)
            return
        hits = result.get("hits", [])
        if not hits:
            ctk.CTkLabel(self.search_results,
                         text="Keine Treffer.", text_color="gray"
                         ).pack(pady=20)
            return
        ctk.CTkLabel(self.search_results,
                     text=f"{result['count']} Treffer:",
                     text_color="gray").pack(anchor="w", pady=(4, 8))
        for hit in hits:
            self._search_card(hit)

    def _search_card(self, hit: dict) -> None:
        card = ctk.CTkFrame(self.search_results)
        card.pack(fill="x", pady=3, padx=2)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=8)
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
        ctk.CTkLabel(header, text="Assistenten-Verlauf",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).pack(side="left")
        ctk.CTkButton(header, text="Aktualisieren", width=120,
                      command=self._refresh_history).pack(side="right")

        self.history_text = ctk.CTkTextbox(
            parent, wrap="word", font=ctk.CTkFont(size=12))
        self.history_text.grid(row=1, column=0, sticky="nsew")
        self.history_text.configure(state="disabled")

    def _refresh_history(self) -> None:
        from database import AssistantLogRepository
        repo = AssistantLogRepository(self.assistant.log.db
                                        if self.assistant.log
                                        else None)
        try:
            entries = repo.tail(limit=200)
        except Exception:
            entries = []
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if not entries:
            self.history_text.insert("1.0",
                "Noch keine Eintraege - frage den Assistenten etwas.")
        else:
            for entry in entries:
                who = ("Du" if entry.role == "user"
                        else "Assistent" if entry.role == "assistant"
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

        ctk.CTkLabel(parent, text="Einstellungen",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(6, 6))

        info = ("Werte werden in der DB persistiert. Geheime Felder "
                "(API-Schluessel, Passwoerter) liest die App ausschliesslich "
                "aus Umgebungsvariablen, sie werden NICHT in der DB "
                "gespeichert.")
        ctk.CTkLabel(parent, text=info, text_color="gray",
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
            secrets_info, text="Geheimnisse (nur per Umgebungsvariable):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        for key in sorted(SECRET_KEYS):
            env = ENV_MAP.get(key, "(kein Env-Mapping)")
            set_text = "gesetzt" if os.environ.get(env) else "nicht gesetzt"
            ctk.CTkLabel(
                secrets_info,
                text=f"  {key}  ->  {env}   [{set_text}]",
                text_color="gray", font=ctk.CTkFont(size=11)
            ).pack(anchor="w")

        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=8)
        ctk.CTkButton(actions, text="Speichern (Neustart noetig)",
                      command=self._save_settings
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Auf Default zuruecksetzen",
                      fg_color="transparent", border_width=1,
                      command=self._reset_settings
                      ).pack(side="left")
        self.settings_status = ctk.CTkLabel(actions, text="", text_color="gray")
        self.settings_status.pack(side="right")

    def _save_settings(self) -> None:
        saved = 0
        for key, entry in self.setting_inputs.items():
            value = entry.get().strip()
            save_value(self.settings_repo, key, value)
            saved += 1
        self.settings_status.configure(
            text=f"{saved} Werte gespeichert. Neustart fuer einige Felder.")

    def _reset_settings(self) -> None:
        for key, entry in self.setting_inputs.items():
            entry.delete(0, "end")
            entry.insert(0, DEFAULTS.get(key, ""))
            save_value(self.settings_repo, key, DEFAULTS.get(key, ""))
        self.settings_status.configure(text="Auf Defaults zurueckgesetzt.")

    # ================================================================
    #  Destruktiv-Bestaetigung (vom Assistant aufgerufen)
    # ================================================================
    def _confirm_destructive(self, tool_call) -> bool:
        # Tkinter ist nicht thread-safe; der Assistent laeuft im
        # Hintergrundthread - daher messagebox aus tkinter nutzen.
        from tkinter import messagebox
        text = (f"Der Assistent moechte '{tool_call.name}' ausfuehren.\n\n"
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
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    db, registry, assistant, config, settings, module_states, synced = bootstrap()
    app = AlltagshelferGUI(registry, assistant, config,
                             settings, module_states, synced)
    # Hintergrund-Dienste starten
    app.scheduler.start()
    if app.sync_worker is not None:
        app.sync_worker.start()
    try:
        app.mainloop()
    finally:
        app.scheduler.stop()
        if app.sync_worker is not None:
            app.sync_worker.stop()
        db.close()


if __name__ == "__main__":
    main()
