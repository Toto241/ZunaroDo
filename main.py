"""
Konsolen-Demo - fuehrt alle Module und Schnittstellen End-to-End vor.

Gezeigt werden:
  - Schnittstelle 1: Assistent/GUI <-> Modul   (registry.dispatch)
  - Schnittstelle 2: Modul <-> Modul           (ModuleContext.call)
  - Schnittstelle 3: Dashboard                 (registry.collect_events)
  - Ausgabedienst:   Kuendigungsschreiben als PDF + Mail-Entwurf
  - Vorschlags-Ablage: Mail-Analyse -> Vorschlag -> Uebernahme
  - Modul C, D, E:    Termine, Familie, Soziales
  - Scheduler:        proaktive Notifikationen (einmaliger Check)

So startest du:  python main.py
Optional mit echtem LLM:  ANTHROPIC_API_KEY=... python main.py
"""
from __future__ import annotations

from datetime import date, timedelta

from pathlib import Path

from assistant import Assistant
from core.interface import ModuleRegistry
from database import (AssistantLogRepository, CalendarRepository,
                      ContractRepository, Database, ExpenseRepository,
                      FamilyRepository, PriceMemoryRepository,
                      ProposalRepository, ShoppingRepository, SocialRepository)
from modules.calendar import CalendarModule
from modules.contracts import ContractModule
from modules.daystructure import DayStructureModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from modules.social import SocialModule
from services.gemini import GeminiClient
from services.output import OutputService
from services.scheduler import ProactiveScheduler
from services.sync import FileSyncProvider, install_sync_hook

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


def build_registry(db: Database, output: OutputService,
                    llm=None) -> ModuleRegistry:
    """Steckt alle Module ein - dieselbe Funktion nutzt auch die GUI."""
    registry = ModuleRegistry()
    registry.register(ContractModule(ContractRepository(db), output))
    registry.register(FinanceModule(ExpenseRepository(db),
                                     PriceMemoryRepository(db)))
    registry.register(FamilyModule(FamilyRepository(db),
                                    ShoppingRepository(db)))
    registry.register(CalendarModule(CalendarRepository(db)))
    registry.register(SocialModule(SocialRepository(db), llm=llm))
    registry.register(DayStructureModule())
    registry.register(InboxModule(ProposalRepository(db), llm=llm))
    return registry


def main() -> None:
    db = Database("alltagshelfer_demo.db")
    output = OutputService("ausgaben")
    llm = GeminiClient()
    registry = build_registry(db, output, llm=llm if llm.is_available else None)
    assistant = Assistant(registry, llm=llm if llm.is_available else None,
                           log=AssistantLogRepository(db))

    # Mehrgeraete-Sync - aktiv, sobald ALLTAGSHELFER_SYNC_DIR gesetzt ist
    sync = FileSyncProvider.from_env(Path(".alltagshelfer-state"))
    synced = None
    if sync is not None:
        synced = install_sync_hook(registry, sync)
        applied = synced.apply_remote()
        if applied:
            print(f"Sync: {applied} Fremd-Event(s) angewendet.")

    trenner("System gestartet")
    print(f"Assistent-Modus: {assistant.mode}")
    print(f"DB-Modus:        {db.encryption_mode}")
    if sync is not None:
        print(f"Sync-Modus:      Datei-basiert ({sync.sync_dir})")
        print(f"Geraete-ID:      {sync.device_id}")
    print(f"Module: {len(registry.modules())}, "
          f"Capabilities: {len(registry.all_capabilities())}")

    # --- Beispieldaten ------------------------------------------------
    trenner("Beispieldaten anlegen (via registry.dispatch)")

    # Familie zuerst - die anderen Module beziehen sich darauf
    for name, role, bday in [
        ("Anna", "erwachsen", "1989-07-12"),
        ("Bernd", "erwachsen", "1986-03-04"),
        ("Mia", "kind", "2018-11-22"),
    ]:
        registry.dispatch("family.add_member",
                            {"name": name, "role": role, "birthday": bday})
    anna_id = registry.dispatch(
        "family.members", {})["members"][0]["id"]
    print("  Modul D: 3 Mitglieder mit Geburtstagen angelegt")

    # Vertraege - mit Person-Zuordnung
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
    print("  Modul A: 2 Vertraege, beide Anna zugeordnet")

    # Aufgaben + Auftrag
    registry.dispatch("family.add_task", {
        "title": "Muell rausbringen", "interval_days": 7,
        "assignees": ["Anna", "Bernd"],
        "first_due": (date.today() + timedelta(days=2)).isoformat()})
    registry.dispatch("family.add_order", {
        "title": "Auto zur Inspektion bringen", "assignee": "Bernd",
        "due_date": (date.today() + timedelta(days=5)).isoformat(),
        "description": "Termin bei der Werkstatt ist vereinbart."})
    print("  Modul D: 1 wiederkehrende Aufgabe, 1 Auftrag")

    # Einkaufsliste
    for item in [("Milch", "1 L", "Anna"), ("Apfel", "1 kg", "Bernd")]:
        registry.dispatch("family.shopping_add",
                            {"name": item[0], "quantity": item[1],
                             "added_by": item[2]})
    print("  Modul D: Einkaufsliste mit 2 Eintraegen")

    # Termine - Garantie + TUEV
    registry.dispatch("calendar.add_event", {
        "title": "TUEV Familienauto",
        "due_date": (date.today() + timedelta(days=45)).isoformat(),
        "category": "tuev", "person_id": anna_id})
    registry.dispatch("calendar.add_event", {
        "title": "Garantie Geschirrspueler",
        "due_date": (date.today() + timedelta(days=120)).isoformat(),
        "category": "garantie",
        "description": "Bei Defekt vorher pruefen lassen."})
    print("  Modul C: 2 Termine (TUEV + Garantie)")

    # Soziale Kontakte
    registry.dispatch("social.add_contact",
                        {"name": "Oma", "relation": "Familie",
                         "cadence_days": 14})
    registry.dispatch("social.add_contact",
                        {"name": "Tobias", "relation": "Freund",
                         "cadence_days": 30})
    print("  Modul E: 2 Kontakte")

    # Ausgaben (Modul B) - mit Person + Preis-Gedaechtnis
    registry.dispatch("finance.add_expense",
                        {"description": "Wocheneinkauf", "amount": 84.20,
                         "category": "lebensmittel", "owner_id": anna_id})
    registry.dispatch("finance.remember_price",
                        {"product": "Vollmilch 1L", "price": 1.39,
                         "category": "lebensmittel"})
    print("  Modul B: 1 Ausgabe (Anna), 1 Preisgedaechtnis-Eintrag")

    # --- Kuendigungsschreiben ----------------------------------------
    trenner("Kuendigungsschreiben erstellen (PDF + Mail-Entwurf)")
    res = registry.dispatch("contracts.generate_cancellation", {
        "contract_id": 2,
        "sender_name": "Anna Beispiel",
        "sender_address": "Musterstrasse 1, 44135 Dortmund",
        "sender_city": "Dortmund",
        "recipient_email": "kuendigung@netflix.example",
        "channel": "both"})
    print(f"  Vertrag:           {res['contract']}")
    print(f"  Kuendigung zum:    {res['cancellation_date']}")
    print(f"  PDF zum Drucken:   {res.get('pdf_path')}")
    print(f"  Mail-Entwurf:      {res.get('email_draft_path')}")

    # --- Mail-Analyse + Vorschlag -------------------------------------
    trenner("Mail-Analyse und zentrale Vorschlags-Ablage")
    analyse = registry.dispatch("inbox.analyze_mail",
                                  {"mail_text": SAMPLE_MAIL})
    print(f"  -> {analyse['found']} Vorschlag/Vorschlaege")
    offen = registry.dispatch("inbox.proposals", {})
    if offen["proposals"]:
        pid = offen["proposals"][0]["id"]
        registry.dispatch("inbox.accept_proposal", {"proposal_id": pid})
        preis = registry.dispatch("contracts.list", {})["contracts"][1]["monthly_cost"]
        print(f"  Streaming-Preis nach Uebernahme: {preis:.2f} EUR")

    # --- Dashboard ----------------------------------------------------
    trenner("Dashboard - registry.collect_events()")
    for ev in registry.collect_events(horizon_days=120):
        mark = {"hoch": "[!!!]", "mittel": "[ ! ]", "normal": "[   ]"}[ev.urgency]
        d = ev.days_remaining
        when = (f"in {d} Tagen" if d > 0 else "heute faellig" if d == 0
                else f"{-d} Tage ueberfaellig")
        print(f"  {mark} {ev.due_date}  {ev.title}  ({when})")

    # --- Proaktiver Scheduler (einmaliger Check) ----------------------
    trenner("Proaktiver Scheduler - einmaliger Check")
    scheduler = ProactiveScheduler(registry, warn_within_days=14)
    triggered = scheduler.check_now()
    print(f"  Notifikationen ausgeloest: {len(triggered)}")
    for title in triggered:
        print(f"    - {title}")

    # --- Kontext-Ueberblick ------------------------------------------
    trenner("Kontext-Ueberblick aller Module")
    print(registry.context_overview())

    # --- Beispielfragen an den Assistenten ---------------------------
    for frage in [
        "Was steht als naechstes an?",
        "Welche Termine kommen?",
        "Wer wartet auf einen Anruf?",
        "Was steht auf der Einkaufsliste?",
    ]:
        trenner(f"Nutzer: {frage}")
        print(assistant.ask(frage))

    db.close()
    print("\nFertig. (Demo-DB: alltagshelfer_demo.db, Ausgaben in ./ausgaben/)")


if __name__ == "__main__":
    main()
