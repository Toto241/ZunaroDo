"""
Smoke-Tests fuer das Modulsystem.

Sie pruefen die drei Schnittstellen End-to-End, ohne externe Dienste:
  1. Registry-Dispatch
  2. Modul-zu-Modul ueber ModuleContext (Modul B holt Vertragskosten von A)
  3. Dashboard-Aggregation
"""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, timedelta

from assistant import Assistant
from core.interface import ModuleRegistry
from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, ProposalRepository,
                      ShoppingRepository, SocialRepository)
from modules.calendar import CalendarModule
from modules.contracts import ContractModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from modules.social import SocialModule
from services.output import OutputService


def _build_system() -> tuple[Database, ModuleRegistry, Assistant, str]:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = Database(tmp.name)
    output = OutputService(tempfile.mkdtemp(prefix="ah_out_"))
    registry = ModuleRegistry()
    registry.register(ContractModule(ContractRepository(db), output))
    registry.register(FinanceModule(ExpenseRepository(db)))
    registry.register(FamilyModule(FamilyRepository(db), ShoppingRepository(db)))
    registry.register(CalendarModule(CalendarRepository(db)))
    registry.register(SocialModule(SocialRepository(db)))
    registry.register(InboxModule(ProposalRepository(db)))
    return db, registry, Assistant(registry), tmp.name


class TestRegistry(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, self.assistant, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_capabilities_registered(self) -> None:
        names = {c.name for c in self.registry.all_capabilities()}
        for required in ("contracts.add", "contracts.list", "finance.monthly_overview",
                          "family.members", "calendar.add_event", "social.contacts",
                          "inbox.analyze_mail"):
            self.assertIn(required, names)

    def test_unknown_capability_returns_error(self) -> None:
        result = self.registry.dispatch("nicht.existent", {})
        self.assertIn("error", result)

    def test_module_to_module_via_context(self) -> None:
        # Modul B muss Modul A ueber den Context erreichen
        self.registry.dispatch("contracts.add", dict(
            name="X", category="streaming", provider="Y",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=10.0))
        overview = self.registry.dispatch("finance.monthly_overview", {})
        self.assertEqual(overview["contract_costs_source"], "modul_a")
        self.assertAlmostEqual(overview["recurring_contracts"], 10.0)

    def test_dashboard_aggregates_events(self) -> None:
        self.registry.dispatch("contracts.add", dict(
            name="X", category="streaming", provider="Y",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=10.0))
        events = self.registry.collect_events(horizon_days=60)
        self.assertGreater(len(events), 0)
        # chronologisch sortiert
        self.assertEqual(events, sorted(events, key=lambda e: e.due_date))


class TestProposalsFlow(unittest.TestCase):
    """Mail-Analyse -> Vorschlag -> Uebernahme -> Modul A traegt ein."""

    def setUp(self) -> None:
        self.db, self.registry, self.assistant, self.path = _build_system()
        self.registry.dispatch("contracts.add", dict(
            name="Streaming", category="streaming", provider="Netflix",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1, monthly_cost=13.99))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_price_change_proposal_round_trip(self) -> None:
        mail = ("Sehr geehrter Kunde, wir nehmen eine Preisanpassung vor. "
                "Ihr neuer monatlicher Preis betraegt 15,99 EUR. Ihr Netflix-Team")
        analysis = self.registry.dispatch("inbox.analyze_mail", {"mail_text": mail})
        self.assertEqual(analysis["found"], 1)
        offen = self.registry.dispatch("inbox.proposals", {})["proposals"]
        result = self.registry.dispatch("inbox.accept_proposal",
                                          {"proposal_id": offen[0]["id"]})
        self.assertEqual(result["status"], "Vorschlag uebernommen")
        contracts = self.registry.dispatch("contracts.list", {})["contracts"]
        self.assertAlmostEqual(contracts[0]["monthly_cost"], 15.99)


class TestPersonAssignment(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, self.assistant, self.path = _build_system()
        self.registry.dispatch("family.add_member",
                                {"name": "Anna", "role": "erwachsen"})
        self.anna_id = self.registry.dispatch("family.members",
                                               {})["members"][0]["id"]

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_contract_carries_owner(self) -> None:
        self.registry.dispatch("contracts.add", dict(
            name="X", category="streaming", provider="Y",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=10.0, owner_id=self.anna_id))
        contract = self.registry.dispatch("contracts.list", {})["contracts"][0]
        self.assertEqual(contract.get("owner"), "Anna")

    def test_expense_carries_owner(self) -> None:
        self.registry.dispatch("finance.add_expense", dict(
            description="Buecher", amount=29.50, owner_id=self.anna_id))
        expense = self.registry.dispatch(
            "finance.list_expenses", {})["expenses"][0]
        self.assertEqual(expense.get("owner"), "Anna")


if __name__ == "__main__":
    unittest.main()
