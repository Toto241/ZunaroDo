"""
Demo - fuehrt alle Module und Schnittstellen End-to-End vor.

Gezeigt werden:
  - Schnittstelle 1: Assistent/GUI <-> Modul   (registry.dispatch)
  - Schnittstelle 2: Modul <-> Modul           (ModuleContext.call)
  - Schnittstelle 3: Dashboard                 (registry.collect_events)
  - Ausgabedienst:   Kuendigungsschreiben als PDF + Mail-Entwurf
  - Vorschlags-Ablage: Mail-Analyse -> Vorschlag -> Uebernahme

So startest du:  python main.py
Optional mit echtem LLM:  ANTHROPIC_API_KEY=... python main.py
"""
from __future__ import annotations

from datetime import date, timedelta

from assistant import Assistant
from core.interface import ModuleRegistry
from database import (ContractRepository, Database, ExpenseRepository,
                      FamilyRepository, ProposalRepository)
from modules.contracts import ContractModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from services.output import OutputService

SAMPLE_MAIL = """Betreff: Wichtige Information zu Ihrem Netflix-Abo

Sehr geehrter Kunde,

wir moechten Sie darueber informieren, dass wir zum naechsten
Abrechnungszeitraum eine Preisanpassung vornehmen. Ihr neuer
monatlicher Preis betraegt 15,99 EUR pro Monat.

Mit freundlichen Gruessen
Ihr Netflix-Team
"""


def trenner(titel: str) -> None:
    print(f"\n{'=' * 64}\n  {titel}\n{'=' * 64}")


def main() -> None:
    # --- 1. Datenschicht + Ausgabedienst -----------------------------
    db = Database("alltagshelfer_demo.db")
    output = OutputService("ausgaben")

    # --- 2. Registry + alle Module einstecken ------------------------
    registry = ModuleRegistry()
    registry.register(ContractModule(ContractRepository(db), output))   # A
    registry.register(FinanceModule(ExpenseRepository(db)))             # B
    registry.register(FamilyModule(FamilyRepository(db)))               # D
    registry.register(InboxModule(ProposalRepository(db)))              # Posteingang

    assistant = Assistant(registry)

    trenner("System gestartet")
    print(f"Assistent-Modus: {assistant.mode}")
    for cap in registry.all_capabilities():
        print(f"  - {cap.name:30s} <- Modul '{cap.module_id}'")

    # --- 3. Beispieldaten anlegen ------------------------------------
    trenner("Beispieldaten anlegen (via registry.dispatch)")
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
    print("  Modul A: 2 Vertraege angelegt")

    for name, role in [("Anna", "erwachsen"), ("Bernd", "erwachsen"),
                        ("Mia", "kind")]:
        registry.dispatch("family.add_member", {"name": name, "role": role})
    registry.dispatch("family.add_task", {
        "title": "Muell rausbringen", "interval_days": 7,
        "assignees": ["Anna", "Bernd"],
        "first_due": (date.today() + timedelta(days=2)).isoformat()})
    print("  Modul D: 3 Mitglieder, 1 wiederkehrende Aufgabe angelegt")

    # einmaliger Auftrag, gezielt zugewiesen
    res = registry.dispatch("family.add_order", {
        "title": "Auto zur Inspektion bringen", "assignee": "Bernd",
        "due_date": (date.today() + timedelta(days=5)).isoformat(),
        "description": "Termin bei der Werkstatt ist vereinbart."})
    print(f"  Modul D: Auftrag '{res['order']['title']}' "
          f"-> {res['order']['assignee']}")

    # --- 4. Kuendigungsschreiben (Modul A + Ausgabedienst) -----------
    trenner("Kuendigungsschreiben erstellen (PDF + Mail-Entwurf)")
    res = registry.dispatch("contracts.generate_cancellation", {
        "contract_id": 2,                       # Streaming-Abo
        "sender_name": "Anna Beispiel",
        "sender_address": "Musterstrasse 1, 44135 Dortmund",
        "sender_city": "Dortmund",
        "recipient_email": "kuendigung@netflix.example",
        "channel": "both"})
    print(f"  Vertrag:           {res['contract']}")
    print(f"  Kuendigung zum:    {res['cancellation_date']}")
    print(f"  PDF zum Drucken:   {res.get('pdf_path')}")
    print(f"  Mail-Entwurf:      {res.get('email_draft_path')}")

    # --- 5. Mail-Analyse -> Vorschlag -> Uebernahme ------------------
    trenner("Mail-Analyse und zentrale Vorschlags-Ablage")
    analyse = registry.dispatch("inbox.analyze_mail", {"mail_text": SAMPLE_MAIL})
    print(f"  Mail analysiert -> {analyse['found']} Vorschlag/Vorschlaege")

    offen = registry.dispatch("inbox.proposals", {})
    for p in offen["proposals"]:
        print(f"  Vorschlag #{p['id']}: {p['summary']}")
        print(f"     Ziel-Capability: {p['target_capability']}")

    if offen["proposals"]:
        pid = offen["proposals"][0]["id"]
        alt = registry.dispatch("contracts.list", {})["contracts"][1]["monthly_cost"]
        print(f"\n  Preis vor Uebernahme:  {alt:.2f} EUR")
        uebern = registry.dispatch("inbox.accept_proposal", {"proposal_id": pid})
        neu = registry.dispatch("contracts.list", {})["contracts"][1]["monthly_cost"]
        print(f"  Vorschlag uebernommen -> Ziel '{uebern['target']}' aufgerufen")
        print(f"  Preis nach Uebernahme: {neu:.2f} EUR")

    # --- 6. Dashboard ------------------------------------------------
    trenner("Dashboard - registry.collect_events() ueber alle Module")
    for ev in registry.collect_events(horizon_days=120):
        mark = {"hoch": "[!!!]", "mittel": "[ ! ]", "normal": "[   ]"}[ev.urgency]
        d = ev.days_remaining
        when = (f"in {d} Tagen" if d > 0 else "heute faellig" if d == 0
                else f"{-d} Tag(e) ueberfaellig")
        print(f"  {mark} {ev.due_date}  {ev.title}  ({when})")

    # --- 7. Kontext-Ueberblick ---------------------------------------
    trenner("Kontext-Ueberblick aller Module")
    print(registry.context_overview())

    # --- 8. Nutzerfragen an den Assistenten --------------------------
    for frage in ["Was steht als naechstes an?",
                   "Welche Auftraege gibt es?",
                   "Gibt es offene Vorschlaege im Posteingang?"]:
        trenner(f"Nutzer: {frage}")
        print(assistant.ask(frage))

    db.close()
    print("\nFertig. (Demo-DB: alltagshelfer_demo.db, Ausgaben in ./ausgaben/)")


if __name__ == "__main__":
    main()
