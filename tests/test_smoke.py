"""
Smoke-Tests fuer das Modulsystem.

Decken die drei Schnittstellen, Mail-Vorschlaege, destruktive Markierungen,
Modul-Enable/Disable (inkl. has_capability), Persistenz von Modul-States
und DayStructure, Sync (Datei + HTTP), Konfig und Gemini-Stub ab.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

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
from modules.social import SocialModule
from services.config import DEFAULTS, load_config, save_value
from services.llm import LLMAnswer, ToolCall, TokenUsage
from services.output import OutputService
from services.sync import (DEFAULT_SYNCED_CAPABILITIES, FileSyncProvider,
                            HttpSyncProvider, SyncEvent, SyncedRegistry,
                            install_sync_hook)


# ---------------------------------------------------------------------
#  Stub-LLM
# ---------------------------------------------------------------------
class StubLLM:
    name = "stub"
    is_available = True

    def __init__(self) -> None:
        self.model = "stub"
        self.text_answers: list[str] = []

    def analyze_text(self, instructions, text, max_output_tokens=1024):
        return (self.text_answers.pop(0)
                if self.text_answers else "STUB"), TokenUsage(10, 5)

    def ask_with_tools(self, **kwargs):
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
    registry.register(DayStructureModule(DayEntryRepository(db)))
    registry.register(InboxModule(ProposalRepository(db), llm=llm))
    return db, registry, Assistant(registry, llm=llm), tmp.name


# ---------------------------------------------------------------------
#  Bestehende Smoke-Tests
# ---------------------------------------------------------------------
class TestRegistry(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_capabilities_registered(self) -> None:
        names = {c.name for c in self.registry.all_capabilities()}
        for required in ("contracts.add", "finance.monthly_overview",
                          "family.members", "calendar.add_event",
                          "social.contacts", "inbox.analyze_mail",
                          "day.log_energy"):
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


class TestHasCapabilityHonorsDisabled(unittest.TestCase):
    """Bug-Fix: has_capability darf deaktivierte Module nicht melden."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_has_capability_false_when_disabled(self) -> None:
        self.assertTrue(self.registry.has_capability("family.members"))
        self.registry.set_module_enabled("family", False)
        self.assertFalse(self.registry.has_capability("family.members"))

    def test_has_capability_returns_after_enable(self) -> None:
        self.registry.set_module_enabled("family", False)
        self.registry.set_module_enabled("family", True)
        self.assertTrue(self.registry.has_capability("family.members"))


class TestCalendarNoMutation(unittest.TestCase):
    """Bug-Fix: list_upcoming darf keine Objekte mutieren."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_recurring_event_not_mutated_in_db(self) -> None:
        # Geburtstag in der Vergangenheit, jaehrlich -> list_upcoming
        # liefert die naechste Wiederholung; in der DB muss das Original-
        # Datum unveraendert bleiben.
        repo = CalendarRepository(self.db)
        from models import CalendarEvent
        repo.add(CalendarEvent(
            title="Hochzeitstag", due_date=date(2024, 5, 1),
            category="termin", recurrence_days=365,
        ))
        upcoming = repo.list_upcoming(horizon_days=400)
        self.assertGreater(len(upcoming), 0)
        self.assertNotEqual(upcoming[0].due_date, date(2024, 5, 1))
        # Original in DB
        stored = repo.list_all()[0]
        self.assertEqual(stored.due_date, date(2024, 5, 1))


class TestDestructiveFlags(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_critical_capabilities_are_marked(self) -> None:
        names = self.registry.destructive_capability_names()
        for expected in ("contracts.report_price_change",
                          "family.complete_task", "family.complete_order",
                          "inbox.accept_proposal", "calendar.delete_event"):
            self.assertIn(expected, names)


class TestModuleStatePersistence(unittest.TestCase):
    """Modul-Aktivierung wird ueber Neustart hinweg gespeichert."""

    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()

    def tearDown(self) -> None:
        os.unlink(self.tmp.name)

    def test_disabled_module_id_persists(self) -> None:
        db = Database(self.tmp.name)
        repo = ModuleStateRepository(db)
        repo.set_enabled("family", False)
        repo.set_enabled("calendar", True)
        self.assertEqual(repo.disabled_modules(), {"family"})
        db.close()
        # Neustart
        db2 = Database(self.tmp.name)
        repo2 = ModuleStateRepository(db2)
        self.assertEqual(repo2.disabled_modules(), {"family"})
        db2.close()


class TestDayStructurePersistence(unittest.TestCase):
    """Tagebuch-Eintraege ueberleben Neustart."""

    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()

    def tearDown(self) -> None:
        os.unlink(self.tmp.name)

    def test_entry_persists(self) -> None:
        db = Database(self.tmp.name)
        repo = DayEntryRepository(db)
        mod = DayStructureModule(repo)
        mod._cap_log_energy(4, "guter Tag")
        db.close()
        db2 = Database(self.tmp.name)
        repo2 = DayEntryRepository(db2)
        entries = repo2.list_recent()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].level, 4)
        db2.close()


class TestAssistantLogRotation(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        self.repo = AssistantLogRepository(self.db, max_entries=5)

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.tmp.name)

    def test_log_does_not_grow_unbounded(self) -> None:
        for i in range(20):
            self.repo.append("user", f"msg {i}")
        count = self.db.conn.execute(
            "SELECT COUNT(*) AS n FROM assistant_log").fetchone()["n"]
        self.assertLessEqual(count, 5)


class TestSettings(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        self.repo = SettingsRepository(self.db)

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.tmp.name)

    def test_defaults_when_empty(self) -> None:
        config = load_config(self.repo)
        self.assertEqual(config.gemini_model, DEFAULTS["gemini.model"])
        self.assertEqual(config.imap_folder, "INBOX")

    def test_db_value_overrides_default(self) -> None:
        save_value(self.repo, "gemini.model", "gemini-2.5-pro")
        config = load_config(self.repo)
        self.assertEqual(config.gemini_model, "gemini-2.5-pro")

    def test_secret_is_not_persisted(self) -> None:
        save_value(self.repo, "gemini.api_key", "secret-key")
        # Schluessel sollte trotzdem nicht in der DB stehen
        self.assertIsNone(self.repo.get("gemini.api_key"))

    def test_env_overrides_db(self) -> None:
        save_value(self.repo, "gemini.model", "gemini-pro-from-db")
        os.environ["ALLTAGSHELFER_GEMINI_MODEL"] = "gemini-pro-from-env"
        try:
            config = load_config(self.repo)
            self.assertEqual(config.gemini_model, "gemini-pro-from-env")
        finally:
            os.environ.pop("ALLTAGSHELFER_GEMINI_MODEL", None)


class TestSyncExpandedCapabilities(unittest.TestCase):
    """Sync erfasst jetzt auch Vertraege/Ausgaben/Termine."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ah_sync2_"))
        self.shared = self.root / "shared"
        self.shared.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.root)

    def _make_device(self, dev_id: str):
        state = self.root / dev_id
        provider = FileSyncProvider(str(self.shared), dev_id,
                                      local_seen_path=state / "seen.json")
        db, registry, _, db_path = _build_system()
        synced = install_sync_hook(registry, provider)
        return db, registry, synced, db_path

    def test_contract_replays_on_other_device(self) -> None:
        db_a, reg_a, sync_a, p_a = self._make_device("a")
        try:
            reg_a.dispatch("contracts.add", dict(
                name="Streaming", category="streaming",
                provider="Netflix", start_date="2025-01-01",
                minimum_term_months=1, notice_period_months=1,
                auto_renew_months=1, monthly_cost=10.0))
            self.assertEqual(reg_a.dispatch("contracts.list",
                                              {})["count"], 1)
            db_b, reg_b, sync_b, p_b = self._make_device("b")
            try:
                applied = sync_b.apply_remote()
                self.assertEqual(applied, 1)
                self.assertEqual(reg_b.dispatch("contracts.list",
                                                  {})["count"], 1)
            finally:
                db_b.close()
                os.unlink(p_b)
        finally:
            db_a.close()
            os.unlink(p_a)


class TestSyncCompaction(unittest.TestCase):

    def test_compact_drops_oldest(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="ah_compact_"))
        try:
            provider = FileSyncProvider(str(root / "shared"), "dev-c",
                                          local_seen_path=root / "seen.json")
            for i in range(20):
                provider.append(SyncEvent(
                    event_id=f"e-{i}", device_id="dev-c",
                    timestamp=f"2026-01-{i:02d}T10:00:00",
                    capability="family.shopping_add",
                    args={"name": f"item-{i}"}))
            dropped = provider.compact_if_needed(max_lines=5)
            self.assertEqual(dropped, 15)
            remaining = provider.read_all()
            self.assertEqual(len(remaining), 5)
            self.assertEqual(remaining[0].event_id, "e-15")
        finally:
            shutil.rmtree(root)


class TestHttpSyncRoundTrip(unittest.TestCase):
    """Realistischer HTTP-Sync-Test: ein Mini-Server auf 127.0.0.1."""

    @classmethod
    def setUpClass(cls) -> None:
        from services.sync_server import serve
        cls.tmp = Path(tempfile.mkdtemp(prefix="ah_http_"))
        cls.server = serve(cls.tmp / "events.jsonl", "127.0.0.1", 0, None)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                        daemon=True)
        cls.thread.start()
        # Auf Server warten
        for _ in range(20):
            try:
                urllib.request.urlopen(
                    f"http://127.0.0.1:{cls.port}/health",
                    timeout=1.0).read()
                break
            except urllib.error.URLError:
                time.sleep(0.05)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.thread.join(timeout=2)
        shutil.rmtree(cls.tmp)

    def test_http_provider_append_and_fetch(self) -> None:
        state_dir = Path(tempfile.mkdtemp(prefix="ah_httpclient_"))
        try:
            provider = HttpSyncProvider(
                f"http://127.0.0.1:{self.port}", "dev-h",
                local_state_path=state_dir / "seen.json")
            provider.append(SyncEvent(
                event_id="x1", device_id="dev-h",
                timestamp="2026-01-01T00:00:00",
                capability="family.add_member",
                args={"name": "Anna"}))
            # Geraet B holt sich dasselbe Event
            other = HttpSyncProvider(
                f"http://127.0.0.1:{self.port}", "dev-other",
                local_state_path=state_dir / "seen_other.json")
            events = other.unseen_events()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].capability, "family.add_member")
        finally:
            shutil.rmtree(state_dir)


class TestGeminiAssistantStub(unittest.TestCase):

    def setUp(self) -> None:
        self.stub = StubLLM()
        self.stub.text_answers.append("Antwort vom Stub.")
        self.db, self.registry, self.assistant, self.path = _build_system(
            llm=self.stub)

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_mode_reports_llm(self) -> None:
        self.assertEqual(self.assistant.mode, "API (stub)")

    def test_token_usage_accumulates(self) -> None:
        before = self.assistant.token_usage.input_tokens
        self.assistant.ask("Hallo")
        self.assertGreater(self.assistant.token_usage.input_tokens, before)


class TestEncryption(unittest.TestCase):
    """SQLCipher: ohne installiertes Paket muss Database mit Key
    klar verweigern."""

    def test_encryption_requires_sqlcipher3(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            try:
                import sqlcipher3                            # noqa: F401
                self.skipTest("sqlcipher3 ist installiert")
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


class TestProposalsFlow(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.registry.dispatch("contracts.add", dict(
            name="Streaming", category="streaming", provider="Netflix",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=13.99))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_price_change_round_trip(self) -> None:
        mail = ("Sehr geehrter Kunde, wir nehmen eine Preisanpassung vor. "
                "Ihr neuer monatlicher Preis betraegt 15,99 EUR. Netflix")
        self.registry.dispatch("inbox.analyze_mail", {"mail_text": mail})
        offen = self.registry.dispatch("inbox.proposals", {})["proposals"]
        self.registry.dispatch("inbox.accept_proposal",
                                {"proposal_id": offen[0]["id"]})
        self.assertAlmostEqual(
            self.registry.dispatch("contracts.list",
                                    {})["contracts"][0]["monthly_cost"],
            15.99)


if __name__ == "__main__":
    unittest.main()
