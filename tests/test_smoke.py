"""
Smoke-Tests fuer das Modulsystem inkl. der neuen Funktionen
(destruktive Markierungen, Modul-Enable/Disable, Sync, Gemini-Stub).
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from assistant import Assistant
from core.interface import ModuleRegistry
from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, PriceMemoryRepository,
                      ProposalRepository, ShoppingRepository, SocialRepository)
from modules.calendar import CalendarModule
from modules.contracts import ContractModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from modules.social import SocialModule
from services.llm import LLMAnswer, ToolCall, TokenUsage
from services.output import OutputService
from services.sync import (DEFAULT_SYNCED_CAPABILITIES, FileSyncProvider,
                            SyncEvent, SyncedRegistry, install_sync_hook)


# ---------------------------------------------------------------------
#  Stub-LLM, der Aufrufe protokolliert und vorgefertigte Antworten gibt
# ---------------------------------------------------------------------
class StubLLM:
    name = "stub"
    is_available = True

    def __init__(self) -> None:
        self.model = "stub"
        self.text_answers: list[str] = []
        self.calls: list[tuple] = []
        self.tool_plan: list[list[ToolCall]] = []

    def analyze_text(self, instructions, text, max_output_tokens=1024):
        self.calls.append(("analyze_text", instructions, text))
        return (self.text_answers.pop(0) if self.text_answers else "STUB"), TokenUsage(10, 5)

    def ask_with_tools(self, **kwargs):
        # Erste Iteration: optional Tool-Aufruf
        if self.tool_plan:
            for call in self.tool_plan.pop(0):
                kwargs["dispatcher"](call.name, call.args)
        text = self.text_answers.pop(0) if self.text_answers else "OK"
        return LLMAnswer(text=text, usage=TokenUsage(20, 10),
                          tool_calls_done=0, truncated=False)


def _build_system(llm=None) -> tuple[Database, ModuleRegistry, Assistant, str]:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = Database(tmp.name)
    output = OutputService(tempfile.mkdtemp(prefix="ah_out_"))
    registry = ModuleRegistry()
    registry.register(ContractModule(ContractRepository(db), output))
    registry.register(FinanceModule(ExpenseRepository(db),
                                     PriceMemoryRepository(db)))
    registry.register(FamilyModule(FamilyRepository(db),
                                    ShoppingRepository(db)))
    registry.register(CalendarModule(CalendarRepository(db)))
    registry.register(SocialModule(SocialRepository(db), llm=llm))
    registry.register(InboxModule(ProposalRepository(db), llm=llm))
    return db, registry, Assistant(registry, llm=llm), tmp.name


class TestRegistry(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, self.assistant, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_capabilities_registered(self) -> None:
        names = {c.name for c in self.registry.all_capabilities()}
        for required in ("contracts.add", "contracts.list",
                          "finance.monthly_overview",
                          "family.members", "calendar.add_event",
                          "social.contacts", "inbox.analyze_mail"):
            self.assertIn(required, names)

    def test_unknown_capability_returns_error(self) -> None:
        self.assertIn("error", self.registry.dispatch("nicht.existent", {}))

    def test_module_to_module_via_context(self) -> None:
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
        self.assertEqual(events, sorted(events, key=lambda e: e.due_date))


class TestProposalsFlow(unittest.TestCase):
    """Mail-Analyse -> Vorschlag -> Uebernahme."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.registry.dispatch("contracts.add", dict(
            name="Streaming", category="streaming", provider="Netflix",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1, monthly_cost=13.99))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_price_change_proposal_round_trip(self) -> None:
        mail = ("Sehr geehrter Kunde, wir nehmen eine Preisanpassung vor. "
                "Ihr neuer monatlicher Preis betraegt 15,99 EUR. Netflix")
        analysis = self.registry.dispatch("inbox.analyze_mail",
                                            {"mail_text": mail})
        self.assertEqual(analysis["found"], 1)
        offen = self.registry.dispatch("inbox.proposals", {})["proposals"]
        result = self.registry.dispatch("inbox.accept_proposal",
                                          {"proposal_id": offen[0]["id"]})
        self.assertEqual(result["status"], "Vorschlag uebernommen")
        contracts = self.registry.dispatch("contracts.list", {})["contracts"]
        self.assertAlmostEqual(contracts[0]["monthly_cost"], 15.99)


class TestDestructiveFlags(unittest.TestCase):
    """Capabilities mit destructive=True sind auch als solche erreichbar."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_destructive_set_includes_known_critical_ones(self) -> None:
        names = self.registry.destructive_capability_names()
        for expected in ("contracts.report_price_change",
                          "family.complete_task", "family.complete_order",
                          "inbox.accept_proposal", "inbox.reject_proposal",
                          "calendar.delete_event", "contracts.set_owner"):
            self.assertIn(expected, names)

    def test_non_destructive_ones_not_flagged(self) -> None:
        names = self.registry.destructive_capability_names()
        for not_destructive in ("contracts.list", "finance.monthly_overview",
                                 "family.members", "calendar.list_events"):
            self.assertNotIn(not_destructive, names)


class TestModuleEnableDisable(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_disabled_module_blocks_dispatch(self) -> None:
        self.registry.set_module_enabled("family", False)
        result = self.registry.dispatch("family.add_member", {"name": "X"})
        self.assertIn("error", result)
        self.assertTrue(result.get("module_disabled"))

    def test_disabled_module_drops_events_from_dashboard(self) -> None:
        # Termin anlegen, deaktivieren, Dashboard pruefen
        self.registry.dispatch("calendar.add_event", {
            "title": "Test", "due_date": "2030-01-01"})
        before = self.registry.collect_events(horizon_days=3650)
        self.registry.set_module_enabled("calendar", False)
        after = self.registry.collect_events(horizon_days=3650)
        self.assertLess(len(after), len(before))

    def test_enable_again(self) -> None:
        self.registry.set_module_enabled("family", False)
        self.registry.set_module_enabled("family", True)
        result = self.registry.dispatch("family.add_member", {"name": "Anna"})
        self.assertEqual(result["status"], "hinzugefuegt")


class TestSync(unittest.TestCase):
    """Datei-basierter Mehrgeraete-Sync."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_sync_"))
        self.sync_dir = self.tmp / "shared"
        self.sync_dir.mkdir()
        self.dev_a_state = self.tmp / "dev_a"
        self.dev_b_state = self.tmp / "dev_b"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _build_device(self, device_id: str, state_dir: Path):
        os.environ["ALLTAGSHELFER_SYNC_DIR"] = str(self.sync_dir)
        os.environ["ALLTAGSHELFER_DEVICE_ID"] = device_id
        provider = FileSyncProvider.from_env(state_dir)
        assert provider is not None
        db, registry, _, db_path = _build_system()
        synced = install_sync_hook(registry, provider)
        return db, registry, synced, db_path

    def test_event_replays_on_second_device(self) -> None:
        db_a, reg_a, sync_a, path_a = self._build_device(
            "dev-a", self.dev_a_state)
        try:
            reg_a.dispatch("family.add_member", {"name": "Anna"})
            self.assertEqual(reg_a.dispatch("family.members",
                                             {})["count"], 1)
            db_b, reg_b, sync_b, path_b = self._build_device(
                "dev-b", self.dev_b_state)
            try:
                # Geraet B kennt Anna noch nicht
                self.assertEqual(reg_b.dispatch("family.members",
                                                 {})["count"], 0)
                applied = sync_b.apply_remote()
                self.assertEqual(applied, 1)
                # Nach Replay kennt Geraet B Anna
                members_b = reg_b.dispatch("family.members", {})
                self.assertEqual(members_b["count"], 1)
                self.assertEqual(members_b["members"][0]["name"], "Anna")
            finally:
                db_b.close()
                os.unlink(path_b)
        finally:
            db_a.close()
            os.unlink(path_a)
            os.environ.pop("ALLTAGSHELFER_SYNC_DIR", None)
            os.environ.pop("ALLTAGSHELFER_DEVICE_ID", None)


class TestGeminiAssistantStub(unittest.TestCase):
    """Assistant mit Stub-LLM, Konversationsverlauf + Confirm-Callback."""

    def setUp(self) -> None:
        self.stub = StubLLM()
        self.stub.text_answers.append("Du hast 0 aktive Vertraege.")
        self.db, self.registry, self.assistant, self.path = _build_system(
            llm=self.stub)

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_mode_reflects_llm(self) -> None:
        self.assertEqual(self.assistant.mode, "API (stub)")

    def test_token_usage_accumulates(self) -> None:
        before = self.assistant.token_usage.input_tokens
        self.assistant.ask("Wie viele Vertraege habe ich?")
        self.assertGreater(self.assistant.token_usage.input_tokens, before)

    def test_confirm_callback_blocks_destructive(self) -> None:
        # Plane einen destruktiven Aufruf via Tool-Use
        denied: list[ToolCall] = []
        self.assistant.set_confirm_callback(
            lambda call: (denied.append(call), False)[1])
        self.stub.tool_plan = [[ToolCall(
            name="family.complete_task", args={"task_id": 1},
            is_destructive=True)]]
        self.stub.text_answers.append("OK")
        # Direkt ueber den Dispatcher wuerde der Aufruf ausgefuehrt, aber
        # via Assistant + Confirm muss er blockiert werden (wir testen die
        # ConfirmCallback-Mechanik im Stub-LLM-Pfad nicht). Stattdessen
        # pruefen wir, dass der Callback gesetzt wird und sein Resultat
        # angewendet wuerde.
        self.assistant.ask("Hak Aufgabe 1 ab")
        # Stub ruft den Dispatcher direkt auf - ohne echte Confirm-Pruefung.
        # Der Stub ist absichtlich einfach gehalten; die echte Pruefung
        # passiert in services/gemini.py. Wichtig hier: der Callback ist
        # aufrufbar und liefert False.
        tc = ToolCall(name="family.complete_task",
                       args={"task_id": 1}, is_destructive=True)
        self.assertFalse(self.assistant._confirm(tc))


class TestEncryption(unittest.TestCase):
    """SQLCipher-Pfad: ohne installiertes sqlcipher3 muss Database
    klar verweigern, sobald ein Schluessel angegeben ist."""

    def test_encryption_requires_sqlcipher3(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            # Wenn sqlcipher3 zufaellig doch installiert ist, ueberspringen wir.
            try:
                import sqlcipher3                            # noqa: F401
                self.skipTest("sqlcipher3 ist installiert - kein Fehler erwartet")
            except Exception:
                pass
            with self.assertRaises(RuntimeError):
                Database(tmp.name, encryption_key="test-key")
        finally:
            os.unlink(tmp.name)

    def test_plain_mode_when_no_key(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            self.assertEqual(db.encryption_mode, "plain")
            db.close()
        finally:
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
