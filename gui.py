"""
GUI - CustomTkinter-Oberflaeche fuer den Alltagshelfer.

Die GUI ist nur ein Front-End. Sie greift NIEMALS direkt auf Datenbank
oder Module zu, sondern ausschliesslich ueber die Schnittstellen:
  - registry.collect_events()    -> Dashboard (naechste Ereignisse)
  - registry.context_overview()  -> Modulstatus in der Sidebar
  - registry.dispatch(...)       -> Aktionen
  - assistant.ask(...)           -> Chat

Aufbau:
  +----------+------------------------------+
  | Sidebar  |  [ Dashboard ] [ Assistent ] |
  | Status   |  Tab-Inhalt                  |
  +----------+------------------------------+

Start:  python gui.py
"""
from __future__ import annotations

import threading
from datetime import date, timedelta

import customtkinter as ctk

from assistant import Assistant
from core.interface import ModuleRegistry
from database import (ContractRepository, Database, ExpenseRepository,
                      FamilyRepository, ProposalRepository)
from modules.contracts import ContractModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from services.output import OutputService

# Beispielmail, mit der man den Posteingang sofort ausprobieren kann
SAMPLE_MAIL = (
    "Betreff: Information zu Ihrem Netflix-Abo\n\n"
    "Sehr geehrter Kunde, wir nehmen eine Preisanpassung vor. Ihr neuer "
    "monatlicher Preis betraegt 15,99 EUR.\n\nIhr Netflix-Team")

# Farben je Dringlichkeitsstufe (siehe models.classify_urgency)
URGENCY_COLOR = {"hoch": "#d9534f", "mittel": "#e8a33d", "normal": "#5b9bd5"}
URGENCY_LABEL = {"hoch": "DRINGEND", "mittel": "BALD", "normal": "GEPLANT"}


def _seed_if_empty(registry: ModuleRegistry) -> None:
    """Legt beim ersten Start Beispieldaten an, damit die GUI nicht leer ist."""
    if registry.dispatch("contracts.list", {}).get("count", 0) > 0:
        return
    for v in [
        dict(name="Handyvertrag", category="mobilfunk", provider="Telekom",
             customer_number="DE-4471180", start_date="2024-06-01",
             minimum_term_months=24, notice_period_months=3,
             auto_renew_months=12, monthly_cost=39.99),
        dict(name="Streaming-Abo", category="streaming", provider="Netflix",
             customer_number="NF-99213", start_date="2025-11-01",
             minimum_term_months=1, notice_period_months=1,
             auto_renew_months=1, monthly_cost=13.99),
    ]:
        registry.dispatch("contracts.add", v)
    for name, role in [("Anna", "erwachsen"), ("Bernd", "erwachsen"),
                       ("Mia", "kind")]:
        registry.dispatch("family.add_member", {"name": name, "role": role})
    registry.dispatch("family.add_task", {
        "title": "Muell rausbringen", "interval_days": 7,
        "assignees": ["Anna", "Bernd"],
        "first_due": (date.today() + timedelta(days=2)).isoformat()})
    registry.dispatch("family.add_order", {
        "title": "Auto zur Inspektion bringen", "assignee": "Bernd",
        "due_date": (date.today() + timedelta(days=5)).isoformat(),
        "description": "Werkstatt-Termin ist vereinbart."})


def bootstrap() -> tuple[Database, ModuleRegistry, Assistant]:
    """Baut das System auf - identisch zu main.py, nur fuer die GUI."""
    db = Database("alltagshelfer_gui.db")
    output = OutputService("ausgaben")
    registry = ModuleRegistry()
    registry.register(ContractModule(ContractRepository(db), output))  # Modul A
    registry.register(FinanceModule(ExpenseRepository(db)))            # Modul B
    registry.register(FamilyModule(FamilyRepository(db)))              # Modul D
    registry.register(InboxModule(ProposalRepository(db)))             # Posteingang
    _seed_if_empty(registry)
    return db, registry, Assistant(registry)


class AlltagshelferGUI(ctk.CTk):
    """Hauptfenster: Sidebar + Tabs fuer Dashboard und Assistent."""

    def __init__(self, registry: ModuleRegistry, assistant: Assistant):
        super().__init__()
        self.registry = registry
        self.assistant = assistant

        self.title("Alltagshelfer")
        self.geometry("900x600")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self._build_dashboard(self.tabs.add("Dashboard"))
        self._build_inbox(self.tabs.add("Posteingang"))
        self._build_chat(self.tabs.add("Assistent"))

        self._refresh_status()
        self._refresh_dashboard()
        self._refresh_inbox()
        self._append("Assistent",
                      "Hallo! Im Dashboard siehst du deine naechsten "
                      "Ereignisse. Hier kannst du mich alles fragen.")

    # ================================================================
    #  Sidebar - Modulstatus
    # ================================================================
    def _build_sidebar(self) -> None:
        bar = ctk.CTkFrame(self, width=240, corner_radius=0)
        bar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(bar, text="Alltagshelfer",
                     font=ctk.CTkFont(size=20, weight="bold")
                     ).pack(padx=20, pady=(20, 2))
        ctk.CTkLabel(bar, text=f"Assistent-Modus: {self.assistant.mode}",
                     text_color="gray").pack(padx=20, pady=(0, 14))

        ctk.CTkLabel(bar, text="Modulstatus",
                     font=ctk.CTkFont(weight="bold")).pack(padx=20, anchor="w")
        self.status_box = ctk.CTkTextbox(bar, width=210, height=200, wrap="word")
        self.status_box.pack(padx=15, pady=8)

        ctk.CTkButton(bar, text="Alles aktualisieren",
                      command=self._refresh_all).pack(padx=15, pady=4)

    # ================================================================
    #  Tab 1 - Dashboard (naechste Ereignisse)
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
        """Holt die Ereignisse ueber registry.collect_events() und rendert sie."""
        for widget in self.dash_list.winfo_children():
            widget.destroy()

        horizon = {"30 Tage": 30, "90 Tage": 90, "Alle": 3650}[self.horizon.get()]
        events = self.registry.collect_events(horizon)

        if not events:
            ctk.CTkLabel(self.dash_list, text="Keine anstehenden Ereignisse.",
                         text_color="gray").pack(pady=30)
            return

        for event in events:
            self._event_card(event)

    def _event_card(self, event) -> None:
        """Eine einzelne Ereignis-Karte, farbcodiert nach Dringlichkeit."""
        color = URGENCY_COLOR[event.urgency]
        card = ctk.CTkFrame(self.dash_list, height=84)
        card.pack(fill="x", pady=3, padx=2)
        card.pack_propagate(False)      # feste Hoehe, nicht an Inhalt anpassen

        # farbiger Akzentbalken links
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
                         text_color="gray", wraplength=480, justify="left"
                         ).pack(anchor="w")

    # ================================================================
    #  Tab 2 - Assistent (Chat)
    # ================================================================
    def _build_chat(self, parent) -> None:
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.chat = ctk.CTkTextbox(parent, wrap="word",
                                   font=ctk.CTkFont(size=13))
        self.chat.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(6, 8))
        self.chat.configure(state="disabled")

        self.entry = ctk.CTkEntry(parent, placeholder_text="Frage eingeben ...")
        self.entry.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        self.entry.bind("<Return>", lambda _e: self._on_send())

        ctk.CTkButton(parent, text="Senden", width=90, command=self._on_send
                      ).grid(row=1, column=1, sticky="e", pady=(0, 6))

    def _on_send(self) -> None:
        text = self.entry.get().strip()
        if text:
            self.entry.delete(0, "end")
            self._ask(text)

    def _ask(self, prompt: str) -> None:
        """Frage an den Assistenten - in einem Thread, damit die GUI
        nicht einfriert (wichtig im API-Modus)."""
        self._append("Du", prompt)
        self._append("Assistent", "denkt nach ...")
        threading.Thread(target=self._worker, args=(prompt,),
                         daemon=True).start()

    def _worker(self, prompt: str) -> None:
        answer = self.assistant.ask(prompt)
        # GUI-Updates muessen im Hauptthread laufen:
        self.after(0, lambda: self._replace_last(answer))
        self.after(0, self._refresh_all)

    def _append(self, who: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}:\n{text}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _replace_last(self, answer: str) -> None:
        """Ersetzt das 'denkt nach ...' durch die echte Antwort."""
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
        self._refresh_inbox()

    # ================================================================
    #  Tab - Posteingang (Mail-Analyse + zentrale Vorschlags-Ablage)
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
        self.mail_box.insert("1.0", SAMPLE_MAIL)            # Beispiel vorbefuellt
        ctk.CTkButton(entry, text="Analysieren", width=120,
                      command=self._analyze_mail).grid(row=0, column=1, sticky="n")

        self.inbox_info = ctk.CTkLabel(
            parent, text="Offene Vorschlaege",
            font=ctk.CTkFont(size=14, weight="bold"))
        self.inbox_info.grid(row=2, column=0, sticky="w", pady=(0, 4))

        self.proposal_list = ctk.CTkScrollableFrame(
            parent, fg_color="transparent")
        self.proposal_list.grid(row=3, column=0, sticky="nsew")
        self.proposal_list.grid_columnconfigure(0, weight=1)

    def _analyze_mail(self) -> None:
        text = self.mail_box.get("1.0", "end-1c").strip()
        if not text:
            return
        result = self.registry.dispatch("inbox.analyze_mail",
                                        {"mail_text": text})
        found = result.get("found", 0)
        if found:
            self.inbox_info.configure(
                text=f"Analyse: {found} neue(r) Vorschlag/Vorschlaege")
        else:
            self.inbox_info.configure(
                text="Analyse: kein bekanntes Muster erkannt")
        self.mail_box.delete("1.0", "end")
        self._refresh_inbox(keep_info=True)
        self._refresh_status()

    def _refresh_inbox(self, keep_info: bool = False) -> None:
        for child in self.proposal_list.winfo_children():
            child.destroy()
        data = self.registry.dispatch("inbox.proposals", {})
        count = data.get("count", 0)
        if not keep_info:
            self.inbox_info.configure(
                text=f"Offene Vorschlaege ({count})")
        if count == 0:
            ctk.CTkLabel(self.proposal_list,
                         text="Keine offenen Vorschlaege.",
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
                     wraplength=460,
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(anchor="w")
        ctk.CTkLabel(body,
                     text=f"Quelle: {p['source']}  |  "
                          f"Ziel: {p['target_capability']}",
                     anchor="w", text_color="gray",
                     font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 6))

        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.pack(anchor="w")
        ctk.CTkButton(buttons, text="Uebernehmen", width=120,
                      command=lambda i=p["id"]: self._decide_proposal(i, True)
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="Ablehnen", width=100,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=lambda i=p["id"]: self._decide_proposal(i, False)
                      ).pack(side="left")

    def _decide_proposal(self, proposal_id: int, accept: bool) -> None:
        capability = ("inbox.accept_proposal" if accept
                      else "inbox.reject_proposal")
        result = self.registry.dispatch(capability,
                                        {"proposal_id": proposal_id})
        message = result.get("status") or result.get("error", "")
        self.inbox_info.configure(text=message)
        # Uebernahme kann Vertraege/Auftraege geaendert haben -> alles neu laden
        self._refresh_inbox(keep_info=True)
        self._refresh_status()
        self._refresh_dashboard()


def main() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    db, registry, assistant = bootstrap()
    app = AlltagshelferGUI(registry, assistant)
    try:
        app.mainloop()
    finally:
        db.close()


if __name__ == "__main__":
    main()
