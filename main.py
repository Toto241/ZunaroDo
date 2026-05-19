"""
Konsolen-Demo des Alltagshelfers.

Bindet die DB, die Konfiguration, alle Module, Gemini, den Scheduler und
optional die Mehrgeraete-Synchronisation zusammen.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from assistant import Assistant
from core.interface import ModuleRegistry
from database import (AssistantLogRepository, CalendarRepository,
                      ContractRepository, Database, DayEntryRepository,
                      ExpenseRepository, FamilyRepository,
                      ModuleStateRepository, PriceMemoryRepository,
                      ProposalRepository, SettingsRepository,
                      ShoppingRepository, SocialRepository)
from modules.calendar import CalendarModule
from modules.contracts import ContractModule
from modules.daystructure import DayStructureModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from modules.search import SearchModule
from modules.social import SocialModule
from modules.statistics import StatisticsModule
from services.config import AppConfig, load_config
from services.gemini import GeminiClient
from services.output import OutputService, SmtpConfig
from services.scheduler import ProactiveScheduler
from services.sync import (FileSyncProvider, HttpSyncProvider,
                            PeriodicSyncWorker, install_sync_hook)


def make_smtp_config(config: AppConfig) -> SmtpConfig | None:
    """Baut SmtpConfig nur wenn ein Host gesetzt ist."""
    if not config.smtp_host:
        return None
    return SmtpConfig(
        host=config.smtp_host, port=config.smtp_port,
        username=config.smtp_user, password=config.smtp_pass,
        sender=config.smtp_sender or config.smtp_user,
        use_starttls=config.smtp_starttls,
    )

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
    contracts_repo = ContractRepository(db)
    expense_repo = ExpenseRepository(db)
    family_repo = FamilyRepository(db)
    calendar_repo = CalendarRepository(db)
    social_repo = SocialRepository(db)
    proposal_repo = ProposalRepository(db)
    registry.register(ContractModule(contracts_repo, output))
    registry.register(FinanceModule(expense_repo, PriceMemoryRepository(db)))
    registry.register(FamilyModule(family_repo, ShoppingRepository(db)))
    registry.register(CalendarModule(calendar_repo))
    registry.register(SocialModule(social_repo, llm=llm))
    registry.register(DayStructureModule(DayEntryRepository(db)))
    registry.register(InboxModule(proposal_repo, llm=llm))
    registry.register(SearchModule(
        contracts_repo, expense_repo, calendar_repo,
        family_repo, social_repo, proposal_repo))
    registry.register(StatisticsModule(expense_repo, contracts_repo))
    return registry


def apply_persisted_module_states(registry: ModuleRegistry,
                                    repo: ModuleStateRepository) -> None:
    """Stellt beim Start die zuvor deaktivierten Module wieder her."""
    for module_id in repo.disabled_modules():
        try:
            registry.set_module_enabled(module_id, False)
        except ValueError:
            # Modul existiert nicht (mehr) - DB-Eintrag wird ignoriert
            pass


def make_sync_provider(local_state_dir: Path):
    """Waehlt HTTP- vor FileSync, beide optional."""
    http = HttpSyncProvider.from_env(local_state_dir)
    if http is not None:
        return http
    return FileSyncProvider.from_env(local_state_dir)


def main() -> None:
    db = Database("alltagshelfer_demo.db")
    settings = SettingsRepository(db)
    config: AppConfig = load_config(settings)
    output = OutputService("ausgaben", smtp=make_smtp_config(config))

    # Gemini-Client mit aufgeloester Konfiguration
    llm = GeminiClient(model=config.gemini_model,
                       api_key=config.gemini_api_key or None)
    active_llm = llm if llm.is_available else None

    registry = build_registry(db, output, llm=active_llm)
    apply_persisted_module_states(registry, ModuleStateRepository(db))

    assistant = Assistant(
        registry, llm=active_llm,
        log=AssistantLogRepository(db),
        max_iterations=config.gemini_max_iterations,
        max_output_tokens=config.gemini_max_tokens,
    )

    # Mehrgeraete-Sync
    state_dir = Path(".alltagshelfer-state")
    provider = make_sync_provider(state_dir) \
        if config.sync_enabled != "false" else None
    synced = None
    if provider is not None:
        synced = install_sync_hook(registry, provider)
        try:
            provider.compact_if_needed()
        except Exception:                                  # pragma: no cover
            pass
        applied = synced.apply_remote()
        if applied:
            print(f"Sync: {applied} Fremd-Event(s) angewendet.")

    trenner("System gestartet")
    print(f"Assistent-Modus: {assistant.mode}")
    print(f"Gemini-Modell:   {config.gemini_model}")
    print(f"DB-Modus:        {db.encryption_mode}")
    print(f"Konfig-Quelle:   Defaults + DB ({len(settings.all())} Keys) + Env")
    if provider is not None:
        print(f"Sync-Modus:      {type(provider).__name__}")
        print(f"Geraete-ID:      {provider.device_id}")
    print(f"Module: {len(registry.modules())}, "
          f"Capabilities: {len(registry.all_capabilities())}")

    # --- Beispieldaten ------------------------------------------------
    trenner("Beispieldaten anlegen (via registry.dispatch)")
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

    registry.dispatch("family.add_task", {
        "title": "Muell rausbringen", "interval_days": 7,
        "assignees": ["Anna", "Bernd"],
        "first_due": (date.today() + timedelta(days=2)).isoformat()})
    registry.dispatch("family.add_order", {
        "title": "Auto zur Inspektion bringen", "assignee": "Bernd",
        "due_date": (date.today() + timedelta(days=5)).isoformat(),
        "description": "Termin bei der Werkstatt ist vereinbart."})
    print("  Modul D: 1 wiederkehrende Aufgabe, 1 Auftrag")

    for item in [("Milch", "1 L", "Anna"), ("Apfel", "1 kg", "Bernd")]:
        registry.dispatch("family.shopping_add",
                            {"name": item[0], "quantity": item[1],
                             "added_by": item[2]})
    print("  Modul D: Einkaufsliste mit 2 Eintraegen")

    registry.dispatch("calendar.add_event", {
        "title": "TUEV Familienauto",
        "due_date": (date.today() + timedelta(days=45)).isoformat(),
        "category": "tuev", "person_id": anna_id})
    registry.dispatch("calendar.add_event", {
        "title": "Garantie Geschirrspueler",
        "due_date": (date.today() + timedelta(days=120)).isoformat(),
        "category": "garantie",
        "description": "Bei Defekt vorher pruefen lassen."})
    print("  Modul C: 2 Termine")

    registry.dispatch("social.add_contact",
                        {"name": "Oma", "relation": "Familie",
                         "cadence_days": 14})
    registry.dispatch("social.add_contact",
                        {"name": "Tobias", "relation": "Freund",
                         "cadence_days": 30})
    print("  Modul E: 2 Kontakte")

    registry.dispatch("finance.add_expense",
                        {"description": "Wocheneinkauf", "amount": 84.20,
                         "category": "lebensmittel", "owner_id": anna_id})
    registry.dispatch("finance.remember_price",
                        {"product": "Vollmilch 1L", "price": 1.39,
                         "category": "lebensmittel"})
    print("  Modul B: 1 Ausgabe, 1 Preisgedaechtnis-Eintrag")

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
        registry.dispatch("inbox.accept_proposal",
                            {"proposal_id": offen["proposals"][0]["id"]})

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
    scheduler = ProactiveScheduler(
        registry, warn_within_days=config.notify_warn_within_days)
    triggered = scheduler.check_now()
    print(f"  Notifikationen ausgeloest: {len(triggered)}")

    # --- Periodischer Sync-Worker (Demo: kurzlebig) -------------------
    if synced is not None:
        worker = PeriodicSyncWorker(synced,
                                      interval_seconds=config.sync_interval_seconds)
        # Demo: Worker startet und stoppt sofort - in der GUI laeuft er
        # dauerhaft im Hintergrund.
        worker.start()
        worker.stop()
        print("  Periodischer Sync-Worker einsatzbereit "
              f"(Intervall: {config.sync_interval_seconds}s)")

    db.close()
    print("\nFertig.")


if __name__ == "__main__":
    main()
