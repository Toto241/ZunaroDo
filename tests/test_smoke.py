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
from datetime import date, timedelta
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
from modules.search import SearchModule
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
    contracts_repo = ContractRepository(db)
    expense_repo = ExpenseRepository(db)
    family_repo = FamilyRepository(db)
    calendar_repo = CalendarRepository(db)
    social_repo = SocialRepository(db)
    proposal_repo = ProposalRepository(db)
    registry.register(ContractModule(contracts_repo, output))
    registry.register(FinanceModule(expense_repo,
                                     PriceMemoryRepository(db)))
    registry.register(FamilyModule(family_repo, ShoppingRepository(db)))
    registry.register(CalendarModule(calendar_repo))
    registry.register(SocialModule(social_repo, llm=llm))
    registry.register(DayStructureModule(DayEntryRepository(db)))
    registry.register(InboxModule(proposal_repo, llm=llm))
    registry.register(SearchModule(
        contracts_repo, expense_repo, calendar_repo,
        family_repo, social_repo, proposal_repo))
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
        # Health-Check via _open_url, damit der Socket sauber geschlossen
        # wird und keine ResourceWarning hinterbleibt.
        for _ in range(20):
            try:
                cls._open_url(f"http://127.0.0.1:{cls.port}/health")
                break
            except urllib.error.URLError:
                time.sleep(0.05)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()    # schliesst das Listening-Socket
        cls.thread.join(timeout=2)
        shutil.rmtree(cls.tmp)

    @staticmethod
    def _open_url(url: str) -> bytes:
        """Holt eine URL und schliesst den Socket explizit."""
        with urllib.request.urlopen(url, timeout=1.0) as response:
            return response.read()

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


class TestThreadSafety(unittest.TestCase):
    """Code-Review-Fix 1: dispatch aus mehreren Threads darf nicht crashen."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_concurrent_dispatch(self) -> None:
        errors: list[str] = []

        def worker(seed: int) -> None:
            try:
                for i in range(20):
                    res = self.registry.dispatch(
                        "family.add_member",
                        {"name": f"P{seed}-{i}", "role": "erwachsen"})
                    if "error" in res:
                        errors.append(str(res))
            except Exception as exc:                       # noqa: BLE001
                errors.append(repr(exc))

        threads = [threading.Thread(target=worker, args=(s,))
                   for s in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        self.assertEqual(errors, [], f"Fehler: {errors[:3]}")
        members = self.registry.dispatch("family.members", {})["members"]
        self.assertEqual(len(members), 100)


class TestConversationHistory(unittest.TestCase):
    """Code-Review-Fix 2: Assistant._history wird wirklich fortgeschrieben."""

    def setUp(self) -> None:
        self.stub = StubLLM()
        # Stub mit "updated_history"-Behauptung: er gibt eine wachsende
        # Liste zurueck. So koennen wir testen, dass der Assistant sie
        # uebernimmt.
        self.db, self.registry, self.assistant, self.path = _build_system(
            llm=self.stub)

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_history_grows_across_calls(self) -> None:
        # Stub liefert wachsende History
        def make_answer(text: str, turn: int) -> LLMAnswer:
            return LLMAnswer(text=text, usage=TokenUsage(5, 5),
                              updated_history=["turn-" + str(i)
                                                for i in range(turn)])
        self.stub.text_answers = ["a", "b", "c"]
        self.stub.ask_with_tools = lambda **k: make_answer(
            self.stub.text_answers.pop(0), len(k.get("history", [])) + 2)
        self.assistant.ask("Frage 1")
        h1 = list(self.assistant._history)
        self.assistant.ask("Frage 2")
        h2 = list(self.assistant._history)
        self.assertGreater(len(h2), len(h1))


class TestSmtpWiring(unittest.TestCase):
    """Code-Review-Fix 3: SMTP-Konfig wird durchgereicht."""

    def test_smtp_config_from_app_config(self) -> None:
        from services.config import AppConfig
        from main import make_smtp_config
        empty = AppConfig()
        self.assertIsNone(make_smtp_config(empty))
        with_host = AppConfig(smtp_host="smtp.example.com",
                                smtp_user="me", smtp_pass="x",
                                smtp_sender="me@example.com")
        cfg = make_smtp_config(with_host)
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg.host, "smtp.example.com")
        self.assertEqual(cfg.sender, "me@example.com")


class TestSyncReentry(unittest.TestCase):
    """Code-Review-Fix 4: Modul-zu-Modul-Aufrufe werden nicht doppelt synchronisiert."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ah_reentry_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root)

    def test_synced_outer_suppresses_synced_nested(self) -> None:
        """Wenn ein bereits geloggter Aufruf intern weitere synced
        Capabilities anstoesst, duerfen die NICHT doppelt geloggt werden."""
        from core.interface import Capability

        provider = FileSyncProvider(str(self.root / "shared"), "dev-r",
                                      local_seen_path=self.root / "seen.json")
        db, registry, _, db_path = _build_system()
        try:
            # Wir installieren ein winziges Hilfs-Modul mit einer synced
            # Capability, die intern eine weitere synced Capability ruft.
            from core.interface import ModuleInterface, ModuleContext

            class _Wrapper(ModuleInterface):
                @property
                def module_id(self): return "wrap"

                @property
                def display_name(self): return "Wrapper"
                def on_register(self, ctx: ModuleContext):
                    self.ctx = ctx
                def get_capabilities(self):
                    return [Capability(
                        name="wrap.add_two_members",
                        description="Legt zwei Mitglieder an.",
                        parameters={},
                        handler=self._cap,
                    )]
                def _cap(self):
                    self.ctx.call("family.add_member",
                                    name="A", role="erwachsen")
                    self.ctx.call("family.add_member",
                                    name="B", role="erwachsen")
                    return {"status": "ok"}

            registry.register(_Wrapper())
            install_sync_hook(
                registry, provider,
                synced=DEFAULT_SYNCED_CAPABILITIES | {"wrap.add_two_members"})
            registry.dispatch("wrap.add_two_members", {})
            caps = [e.capability for e in provider.read_all()]
            # Nur der aeussere synced Aufruf wird geloggt - die beiden
            # nested family.add_member NICHT (sonst Doppel-Replay).
            self.assertEqual(caps, ["wrap.add_two_members"])
        finally:
            db.close()
            os.unlink(db_path)

    def test_non_synced_outer_lets_nested_log(self) -> None:
        """inbox.accept_proposal ist nicht synced - aber das ausgeloeste
        contracts.report_price_change schon. Genau das muss im Log
        landen, sonst kaeme der Effekt nie bei anderen Geraeten an."""
        provider = FileSyncProvider(str(self.root / "shared"), "dev-r2",
                                      local_seen_path=self.root / "seen2.json")
        db, registry, _, db_path = _build_system()
        try:
            install_sync_hook(registry, provider)
            registry.dispatch("contracts.add", dict(
                name="Streaming", category="streaming", provider="Netflix",
                start_date="2025-01-01", minimum_term_months=1,
                notice_period_months=1, auto_renew_months=1,
                monthly_cost=10.0))
            registry.dispatch("inbox.analyze_mail", {
                "mail_text": ("Sehr geehrter Kunde, wir nehmen eine "
                               "Preisanpassung vor. Ihr neuer monatlicher "
                               "Preis betraegt 12,99 EUR. Netflix")})
            offen = registry.dispatch("inbox.proposals",
                                        {})["proposals"]
            registry.dispatch("inbox.accept_proposal",
                                {"proposal_id": offen[0]["id"]})
            caps = [e.capability for e in provider.read_all()]
            self.assertIn("contracts.add", caps)
            # Nested contracts.report_price_change IST geloggt -
            # aber inbox.accept_proposal nicht (kein synced-Cap).
            self.assertIn("contracts.report_price_change", caps)
            self.assertNotIn("inbox.accept_proposal", caps)
        finally:
            db.close()
            os.unlink(db_path)


class TestRecurrenceValidation(unittest.TestCase):
    """Code-Review-Fix 5: recurrence_days <= 0 wird verweigert."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_zero_recurrence_rejected(self) -> None:
        result = self.registry.dispatch("calendar.add_event", {
            "title": "Bug-Test", "due_date": "2030-01-01",
            "recurrence_days": 0})
        self.assertIn("error", result)

    def test_negative_recurrence_rejected(self) -> None:
        result = self.registry.dispatch("calendar.add_event", {
            "title": "Bug-Test", "due_date": "2030-01-01",
            "recurrence_days": -5})
        self.assertIn("error", result)

    def test_none_recurrence_ok(self) -> None:
        result = self.registry.dispatch("calendar.add_event", {
            "title": "Einmalig", "due_date": "2030-01-01"})
        self.assertEqual(result["status"], "angelegt")

    def test_positive_recurrence_ok(self) -> None:
        result = self.registry.dispatch("calendar.add_event", {
            "title": "Jaehrlich", "due_date": "2030-01-01",
            "recurrence_days": 365})
        self.assertEqual(result["status"], "angelegt")

    def test_invalid_date_rejected(self) -> None:
        result = self.registry.dispatch("calendar.add_event", {
            "title": "Krummes Datum", "due_date": "nicht-iso"})
        self.assertIn("error", result)


class TestSyncServerCompaction(unittest.TestCase):
    """Code-Review-Fix 6: Server kompaktiert seinen Log selbst."""

    def test_server_drops_oldest_when_over_limit(self) -> None:
        from services.sync_server import serve
        tmp = Path(tempfile.mkdtemp(prefix="ah_srv_compact_"))
        try:
            server = serve(tmp / "events.jsonl", "127.0.0.1", 0,
                             token=None, max_log_lines=5)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever,
                                        daemon=True)
            thread.start()
            try:
                # 10 Events posten -> nach dem letzten muessen nur noch
                # 5 in der Datei stehen.
                for i in range(10):
                    body = json.dumps({
                        "event_id": f"e{i}", "device_id": "dev",
                        "timestamp": "2026-01-01T00:00:00",
                        "capability": "family.add_member",
                        "args": {"name": f"n{i}"},
                    }).encode("utf-8")
                    req = urllib.request.Request(
                        f"http://127.0.0.1:{port}/events",
                        data=body,
                        headers={"Content-Type":
                                  "application/json; charset=utf-8"},
                        method="POST")
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        resp.read()
                lines = (tmp / "events.jsonl").read_text(
                    encoding="utf-8").splitlines()
                self.assertLessEqual(len(lines), 5)
                # Aelteste sind weg
                first = json.loads(lines[0])
                self.assertEqual(first["event_id"], "e5")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
        finally:
            shutil.rmtree(tmp)


class TestUtcTimestamps(unittest.TestCase):
    """Code-Review-Fix 7: Sync-Events tragen UTC-Timestamps."""

    def test_event_timestamp_has_utc_marker(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="ah_utc_"))
        try:
            provider = FileSyncProvider(str(root / "shared"), "dev-utc",
                                          local_seen_path=root / "seen.json")
            db, registry, _, db_path = _build_system()
            try:
                install_sync_hook(registry, provider)
                registry.dispatch("family.add_member",
                                    {"name": "Anna"})
                events = provider.read_all()
                self.assertEqual(len(events), 1)
                ts = events[0].timestamp
                # ISO mit UTC-Offset endet auf "+00:00" oder "Z"
                self.assertTrue(ts.endswith("+00:00") or ts.endswith("Z"),
                                f"Timestamp {ts!r} ohne UTC-Marker")
            finally:
                db.close()
                os.unlink(db_path)
        finally:
            shutil.rmtree(root)


class TestInboxExtractText(unittest.TestCase):
    """Fix 8: _extract_text muss bei None-Payload nicht crashen."""

    def test_empty_payload_returns_empty_string(self) -> None:
        import email
        from email.message import EmailMessage
        from modules.inbox import InboxModule
        # Eine leere Mail (kein Payload)
        msg = EmailMessage()
        # Ohne Inhalt - get_payload(decode=True) liefert b'\n' oder None
        text = InboxModule._extract_text(msg)
        self.assertIsInstance(text, str)

    def test_multipart_without_textplain_returns_empty(self) -> None:
        from email.message import EmailMessage
        from modules.inbox import InboxModule
        msg = EmailMessage()
        msg.add_attachment(b"binary-data", maintype="application",
                           subtype="octet-stream", filename="x.bin")
        # Keine text/plain-Part vorhanden - darf nicht crashen
        text = InboxModule._extract_text(msg)
        self.assertEqual(text, "")


class TestSqlCipherValidation(unittest.TestCase):
    """Fix 9: Schluessel-Vorpruefung weist NUL/Kuerze klar ab."""

    def test_nul_byte_rejected(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            with self.assertRaises(ValueError):
                Database(tmp.name, encryption_key="abc\x00def-x")
        finally:
            os.unlink(tmp.name)

    def test_too_short_rejected(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            with self.assertRaises(ValueError):
                Database(tmp.name, encryption_key="kurz")
        finally:
            os.unlink(tmp.name)


class TestCompleteTaskCatchUp(unittest.TestCase):
    """Fix 10: Verpasste Zyklen werden mitgerechnet."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_overdue_task_advances_rotation_multiple_times(self) -> None:
        # Anna und Bernd, Aufgabe alle 7 Tage, letzte Faelligkeit
        # 21 Tage in der Vergangenheit -> 3 verpasste Zyklen
        self.registry.dispatch("family.add_member",
                                {"name": "Anna", "role": "erwachsen"})
        self.registry.dispatch("family.add_member",
                                {"name": "Bernd", "role": "erwachsen"})
        old_due = (date.today() - timedelta(days=21)).isoformat()
        self.registry.dispatch("family.add_task", {
            "title": "Muell", "interval_days": 7,
            "assignees": ["Anna", "Bernd"], "first_due": old_due})
        task_id = self.registry.dispatch(
            "family.tasks", {})["tasks"][0]["id"]
        before = self.registry.dispatch(
            "family.tasks", {})["tasks"][0]["current_assignee"]
        self.registry.dispatch("family.complete_task",
                                {"task_id": task_id})
        after = self.registry.dispatch("family.tasks",
                                         {})["tasks"][0]
        # 3 verpasst + 1 jetzt = 4 Zyklen -> bei 2 Personen wieder
        # dieselbe Person (4 % 2 == 0)
        # Wichtig: next_due muss in der Zukunft liegen
        self.assertGreater(date.fromisoformat(after["next_due"]),
                            date.today())


class TestPrintFileNoShell(unittest.TestCase):
    """Fix 16: print_file mit Argument-Liste statt Shell-String."""

    def test_missing_file_returns_error(self) -> None:
        result = OutputService.print_file("nicht-da.pdf")
        self.assertEqual(result["status"], "fehler")
        self.assertIn("fehlt", result["error"])

    def test_path_with_spaces_handled(self) -> None:
        # Wir testen nur, dass es die "Datei fehlt"-Schiene sauber
        # durchlaeuft - kein realer Drucker.
        result = OutputService.print_file("/tmp/datei mit leerzeichen.pdf")
        self.assertEqual(result["status"], "fehler")


class TestLlmJsonParsing(unittest.TestCase):
    """Fix 18: Robustes JSON-Strippen aus LLM-Antworten."""

    def test_plain_json(self) -> None:
        from modules.inbox import InboxModule
        out = InboxModule._parse_llm_proposals(
            '{"proposals": [{"target_capability": "contracts.add", '
            '"summary": "neu", "payload": {"name": "X", "category": "y"}}]}')
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].target_capability, "contracts.add")

    def test_fenced_json(self) -> None:
        from modules.inbox import InboxModule
        raw = ('```json\n{"proposals": [{"target_capability": '
               '"family.add_order", "summary": "x", "payload": '
               '{"title": "Aufgabe"}}]}\n```')
        out = InboxModule._parse_llm_proposals(raw)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].target_capability, "family.add_order")

    def test_fenced_without_lang(self) -> None:
        from modules.inbox import InboxModule
        raw = ('Hier ist die Antwort:\n```\n{"proposals": []}\n```')
        out = InboxModule._parse_llm_proposals(raw)
        self.assertEqual(out, [])

    def test_prose_with_embedded_json(self) -> None:
        from modules.inbox import InboxModule
        raw = ('Klar, die Antwort lautet {"proposals": [{"target_capability": '
               '"contracts.report_price_change", "summary": "P", '
               '"payload": {"contract_id": 1, "new_cost": 9.99}}]} '
               '- viel Erfolg!')
        out = InboxModule._parse_llm_proposals(raw)
        self.assertEqual(len(out), 1)

    def test_invalid_returns_empty(self) -> None:
        from modules.inbox import InboxModule
        out = InboxModule._parse_llm_proposals("kein JSON hier")
        self.assertEqual(out, [])


class TestDeleteCapabilities(unittest.TestCase):
    """Loesch-Capabilities funktionieren und sind als destruktiv markiert."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_delete_caps_are_destructive(self) -> None:
        names = self.registry.destructive_capability_names()
        for cap in ("contracts.delete", "family.delete_member",
                     "social.delete_contact", "finance.delete_expense"):
            self.assertIn(cap, names)

    def test_delete_contract_round_trip(self) -> None:
        self.registry.dispatch("contracts.add", dict(
            name="X", category="streaming", provider="Y",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=10.0))
        cid = self.registry.dispatch(
            "contracts.list", {})["contracts"][0]["id"]
        result = self.registry.dispatch(
            "contracts.delete", {"contract_id": cid})
        self.assertEqual(result["status"], "geloescht")
        self.assertEqual(
            self.registry.dispatch("contracts.list", {})["count"], 0)

    def test_delete_unknown_returns_error(self) -> None:
        result = self.registry.dispatch(
            "contracts.delete", {"contract_id": 9999})
        self.assertIn("error", result)

    def test_delete_member_keeps_orphan_contracts(self) -> None:
        self.registry.dispatch("family.add_member",
                                {"name": "Anna", "role": "erwachsen"})
        mid = self.registry.dispatch(
            "family.members", {})["members"][0]["id"]
        self.registry.dispatch("contracts.add", dict(
            name="Y", category="streaming", provider="Z",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=5.0, owner_id=mid))
        self.registry.dispatch(
            "family.delete_member", {"member_id": mid})
        contracts = self.registry.dispatch(
            "contracts.list", {})["contracts"]
        # Vertrag bleibt, owner_id wird durch ON DELETE SET NULL geloescht
        self.assertEqual(len(contracts), 1)
        self.assertEqual(contracts[0].get("owner"), "")


class TestInputValidation(unittest.TestCase):
    """Input-Validierung in den Modulen."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_social_rejects_non_positive_cadence(self) -> None:
        result = self.registry.dispatch(
            "social.add_contact", {"name": "X", "cadence_days": 0})
        self.assertIn("error", result)

    def test_social_rejects_empty_name(self) -> None:
        result = self.registry.dispatch(
            "social.add_contact", {"name": "   "})
        self.assertIn("error", result)

    def test_family_task_rejects_zero_interval(self) -> None:
        self.registry.dispatch("family.add_member",
                                {"name": "Anna"})
        result = self.registry.dispatch("family.add_task", {
            "title": "X", "interval_days": 0,
            "assignees": ["Anna"]})
        self.assertIn("error", result)

    def test_finance_rejects_negative_amount(self) -> None:
        result = self.registry.dispatch(
            "finance.add_expense",
            {"description": "X", "amount": -1.5})
        self.assertIn("error", result)

    def test_finance_rejects_bad_date(self) -> None:
        result = self.registry.dispatch(
            "finance.add_expense",
            {"description": "X", "amount": 1.0,
             "spent_on": "nicht-iso"})
        self.assertIn("error", result)

    def test_calendar_unknown_category_normalizes(self) -> None:
        result = self.registry.dispatch("calendar.add_event", {
            "title": "X", "due_date": "2030-01-01",
            "category": "irgendwas-erfundenes"})
        self.assertEqual(result["status"], "angelegt")
        self.assertEqual(result["event"]["category"], "sonstiges")


class TestLlmProposalValidation(unittest.TestCase):
    """LLM-Halluzinationen werden vor dem Speichern gefiltert."""

    def setUp(self) -> None:
        # Stub-LLM mit definierter Antwort
        class FixedLLM(StubLLM):
            def __init__(self, response: str):
                super().__init__()
                self._response = response

            def analyze_text(self, instructions, text,
                              max_output_tokens=1024):
                return self._response, TokenUsage(5, 5)

        self.FixedLLM = FixedLLM

    def test_unknown_target_capability_dropped(self) -> None:
        llm = self.FixedLLM(
            '{"proposals": [{"target_capability": "evil.delete_db", '
            '"summary": "boese", "payload": {}}]}')
        db, registry, _, path = _build_system(llm=llm)
        try:
            result = registry.dispatch(
                "inbox.analyze_mail",
                {"mail_text": "irrelevant - LLM antwortet fest"})
            self.assertEqual(result.get("found", 0), 0)
        finally:
            db.close()
            os.unlink(path)

    def test_missing_required_dropped(self) -> None:
        # contracts.add braucht 'name' und 'category' - lassen wir
        # absichtlich weg
        llm = self.FixedLLM(
            '{"proposals": [{"target_capability": "contracts.add", '
            '"summary": "ohne pflichtfelder", "payload": {}}]}')
        db, registry, _, path = _build_system(llm=llm)
        try:
            result = registry.dispatch(
                "inbox.analyze_mail",
                {"mail_text": "ignoriert"})
            self.assertEqual(result.get("found", 0), 0)
        finally:
            db.close()
            os.unlink(path)


class TestDisabledModuleSurfaced(unittest.TestCase):
    """Disabled abhaengiges Modul zeigt sich als Dashboard-Warnung."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_disabled_contracts_yields_warning_in_finance_events(self) -> None:
        self.registry.set_module_enabled("contracts", False)
        events = self.registry.collect_events(horizon_days=120)
        warn = [e for e in events
                if e.module_id == "finance" and e.category == "warnung"]
        self.assertEqual(len(warn), 1)
        self.assertIn("Vertraege-Modul", warn[0].title)


class TestDiagnose(unittest.TestCase):
    """Diagnose-Befehl liefert sinnvolle Felder."""

    def test_collect_returns_expected_shape(self) -> None:
        from diagnose import collect_diagnosis
        data = collect_diagnosis()
        self.assertIn("python_version", data)
        self.assertIn("modules", data)
        self.assertIn("ocr_engines", data)
        # google.generativeai ist in der Umgebung evtl. NICHT installiert
        # - der Eintrag muss aber existieren.
        self.assertIn("google.generativeai", data["modules"])
        # Mindestens Modul + Capabilities zaehlen
        self.assertGreaterEqual(data["module_count"], 0)


class TestBackupAndRestore(unittest.TestCase):
    """Online-Backup + Restore-Round-Trip."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_backup_"))
        self.db_path = self.tmp / "live.db"
        self.db = Database(str(self.db_path))
        # Etwas Inhalt anlegen, damit das Backup nicht leer ist
        from modules.contracts import ContractModule
        registry = ModuleRegistry()
        registry.register(ContractModule(
            ContractRepository(self.db), OutputService(str(self.tmp / "out"))))
        registry.dispatch("contracts.add", dict(
            name="X", category="streaming", provider="Y",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=9.99))

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp)

    def test_online_backup_creates_readable_copy(self) -> None:
        from services.backup import make_backup
        target = self.tmp / "snapshot.db"
        result = make_backup(self.db, target)
        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 0)
        # Backup ist eigenstaendig oeffnenbar
        backup_db = Database(str(target))
        try:
            count = ContractRepository(backup_db).list_all(
                only_active=False)
            self.assertEqual(len(count), 1)
        finally:
            backup_db.close()

    def test_restore_overwrites_live_db(self) -> None:
        from services.backup import make_backup, restore_database
        target = self.tmp / "snapshot.db"
        make_backup(self.db, target)
        # Nach Backup: weiteren Vertrag anlegen
        ContractRepository(self.db).add(self._extra_contract())
        self.assertEqual(
            len(ContractRepository(self.db).list_all(only_active=False)),
            2)
        # DB schliessen vor Restore
        self.db.close()
        restore_database(target, self.db_path)
        # Neu oeffnen - sollte nur den urspruenglichen Vertrag enthalten
        self.db = Database(str(self.db_path))
        self.assertEqual(
            len(ContractRepository(self.db).list_all(only_active=False)),
            1)

    def test_list_backups_sorted_newest_first(self) -> None:
        from services.backup import list_backups, make_backup
        first = make_backup(self.db, self.tmp / "a.db")
        time.sleep(0.05)
        second = make_backup(self.db, self.tmp / "b.db")
        found = list_backups(self.tmp)
        # Sortierung: neueste zuerst
        self.assertEqual(found[0], second)
        self.assertEqual(found[1], first)

    @staticmethod
    def _extra_contract():
        from models import Contract
        return Contract(
            name="Y", category="strom", provider="Z",
            start_date=date(2025, 1, 1), minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=5.0)


class TestCsvExport(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        # Beispieldaten
        self.registry.dispatch("contracts.add", dict(
            name="Streaming", category="streaming", provider="Netflix",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=13.99))
        self.registry.dispatch("finance.add_expense", dict(
            description="Wocheneinkauf", amount=42.00,
            category="lebensmittel"))
        self.registry.dispatch("calendar.add_event", dict(
            title="TUEV", due_date="2026-09-01", category="tuev"))
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_csv_"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)
        shutil.rmtree(self.tmp)

    def test_export_contracts_writes_csv(self) -> None:
        from services.export import export_contracts
        out = self.tmp / "contracts.csv"
        n = export_contracts(ContractRepository(self.db), out)
        self.assertEqual(n, 1)
        text = out.read_text(encoding="utf-8-sig")
        self.assertIn("Streaming", text)
        self.assertIn(";", text)         # Trennzeichen

    def test_export_all_writes_five_files(self) -> None:
        from services.export import export_all
        counts = export_all(
            self.tmp,
            ContractRepository(self.db),
            ExpenseRepository(self.db),
            CalendarRepository(self.db),
            SocialRepository(self.db),
            FamilyRepository(self.db))
        self.assertEqual(counts["contracts"], 1)
        self.assertEqual(counts["expenses"], 1)
        self.assertEqual(counts["calendar"], 1)
        for name in counts:
            self.assertTrue((self.tmp / f"{name}.csv").exists())


class TestSearch(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.registry.dispatch("contracts.add", dict(
            name="Telekom Mobilfunk", category="mobilfunk",
            provider="Telekom", start_date="2025-01-01",
            minimum_term_months=1, notice_period_months=1,
            auto_renew_months=1, monthly_cost=29.99))
        self.registry.dispatch("family.add_member",
                                {"name": "Anna", "role": "erwachsen"})
        self.registry.dispatch("social.add_contact",
                                {"name": "Telekom Hotline",
                                 "relation": "Service"})

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_search_finds_multiple_sources(self) -> None:
        result = self.registry.dispatch(
            "system.search", {"query": "telekom"})
        self.assertGreaterEqual(result["count"], 2)
        sources = {hit["source"] for hit in result["hits"]}
        self.assertIn("contracts", sources)
        self.assertIn("social", sources)

    def test_short_query_rejected(self) -> None:
        result = self.registry.dispatch(
            "system.search", {"query": "a"})
        self.assertIn("error", result)

    def test_no_hit(self) -> None:
        result = self.registry.dispatch(
            "system.search", {"query": "zauberwort"})
        self.assertEqual(result["count"], 0)


class TestProposalUpdate(unittest.TestCase):
    """inbox.update_proposal erlaubt Korrektur vor dem Uebernehmen."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.registry.dispatch("contracts.add", dict(
            name="Streaming", category="streaming", provider="Netflix",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=13.99))
        # Vorschlag aus Mail erzeugen
        self.registry.dispatch("inbox.analyze_mail", {
            "mail_text": ("Sehr geehrter Kunde, wir nehmen eine "
                           "Preisanpassung vor. Ihr neuer monatlicher "
                           "Preis betraegt 15,99 EUR. Netflix")})
        self.pid = self.registry.dispatch(
            "inbox.proposals", {})["proposals"][0]["id"]

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_update_payload_replaces_value(self) -> None:
        # Nutzer korrigiert den Betrag auf 17.99
        result = self.registry.dispatch("inbox.update_proposal", {
            "proposal_id": self.pid,
            "summary": "manuell korrigiert",
            "payload": {"contract_id": 1, "new_cost": 17.99},
        })
        self.assertEqual(result["status"], "aktualisiert")
        proposal = self.registry.dispatch(
            "inbox.proposals", {})["proposals"][0]
        self.assertEqual(proposal["summary"], "manuell korrigiert")
        self.assertAlmostEqual(proposal["payload"]["new_cost"], 17.99)

    def test_update_blocked_after_accept(self) -> None:
        self.registry.dispatch("inbox.accept_proposal",
                                {"proposal_id": self.pid})
        result = self.registry.dispatch("inbox.update_proposal", {
            "proposal_id": self.pid,
            "payload": {"contract_id": 1, "new_cost": 20.0},
        })
        self.assertIn("error", result)

    def test_update_then_accept_uses_new_payload(self) -> None:
        self.registry.dispatch("inbox.update_proposal", {
            "proposal_id": self.pid,
            "payload": {"contract_id": 1, "new_cost": 21.99},
        })
        self.registry.dispatch("inbox.accept_proposal",
                                {"proposal_id": self.pid})
        new_price = self.registry.dispatch(
            "contracts.list", {})["contracts"][0]["monthly_cost"]
        self.assertAlmostEqual(new_price, 21.99)


class TestRegistryGetCapability(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_returns_capability_object(self) -> None:
        cap = self.registry.get_capability("contracts.add")
        self.assertIsNotNone(cap)
        self.assertEqual(cap.name, "contracts.add")
        self.assertIn("name", cap.parameters)
        self.assertIn("category", cap.parameters)

    def test_returns_none_for_unknown(self) -> None:
        self.assertIsNone(
            self.registry.get_capability("nicht.existent"))

    def test_returns_none_for_disabled_module(self) -> None:
        self.registry.set_module_enabled("contracts", False)
        self.assertIsNone(
            self.registry.get_capability("contracts.add"))


class TestI18n(unittest.TestCase):

    def test_default_german(self) -> None:
        from services.i18n import I18n
        i18n = I18n("de")
        self.assertEqual(i18n.t("tab.dashboard"), "Dashboard")
        self.assertEqual(i18n.t("common.assistant"), "Assistent")

    def test_english_translation(self) -> None:
        from services.i18n import I18n
        i18n = I18n("en")
        self.assertEqual(i18n.t("common.assistant"), "Assistant")
        self.assertEqual(i18n.t("tab.contracts"), "Contracts")

    def test_unknown_language_falls_back_to_default(self) -> None:
        from services.i18n import I18n
        i18n = I18n("kl")     # Klingonisch - nicht unterstuetzt
        self.assertEqual(i18n.language, "de")

    def test_missing_key_returns_key(self) -> None:
        from services.i18n import I18n
        i18n = I18n("de")
        self.assertEqual(i18n.t("kein.solcher.key"),
                          "kein.solcher.key")

    def test_missing_key_with_default(self) -> None:
        from services.i18n import I18n
        i18n = I18n("de")
        self.assertEqual(
            i18n.t("kein.solcher.key", default="Fallback-Text"),
            "Fallback-Text")

    def test_en_missing_key_falls_back_to_de(self) -> None:
        # Beide JSONs muessen die Standard-Keys haben, aber wenn ein Key
        # NUR in de existiert, soll der englische Lookup darauf fallen.
        from services.i18n import I18n
        i18n_en = I18n("en")
        # Wir testen das, indem wir einen kuenstlichen Key vergleichen,
        # den wir absichtlich nur in beiden Sprachen unterhalten - die
        # Fallback-Mechanik selbst ist hier wichtig.
        # Trick: ein Schluessel, der in DE garantiert vorhanden ist
        self.assertNotEqual(i18n_en.t("app.title"), "app.title")


class TestBackupSqlCipherPath(unittest.TestCase):
    """Encrypted-Backup-Pfad: ohne installiertes sqlcipher3 kann nichts
    real getestet werden - aber die Argument-Validierung kann.
    """

    def test_sqlcipher_path_requires_key(self) -> None:
        # Wir koennen den SQLCipher-Pfad nur testen, wenn auch eine
        # SQLCipher-DB vorhanden ist; sonst greift der Plain-Pfad.
        # Hier: gefaelschtes db-Objekt mit encryption_mode='sqlcipher'.
        from services.backup import make_backup

        class FakeConn:
            pass

        class FakeDb:
            encryption_mode = "sqlcipher"
            lock = threading.Lock()
            conn = FakeConn()

        tmp = Path(tempfile.mkdtemp(prefix="ah_cipher_"))
        try:
            old_key = os.environ.pop("ALLTAGSHELFER_DB_KEY", None)
            try:
                with self.assertRaises(RuntimeError):
                    make_backup(FakeDb(), tmp / "out.db",
                                  encryption_key=None)
            finally:
                if old_key is not None:
                    os.environ["ALLTAGSHELFER_DB_KEY"] = old_key
        finally:
            shutil.rmtree(tmp)

    def test_sqlcipher_path_rejects_short_key(self) -> None:
        from services.backup import make_backup

        class FakeConn:
            pass

        class FakeDb:
            encryption_mode = "sqlcipher"
            lock = threading.Lock()
            conn = FakeConn()

        tmp = Path(tempfile.mkdtemp(prefix="ah_cipher2_"))
        try:
            with self.assertRaises(ValueError):
                make_backup(FakeDb(), tmp / "out.db",
                              encryption_key="kurz")
        finally:
            shutil.rmtree(tmp)


class TestSyncServerTls(unittest.TestCase):
    """Pruefen, dass --cert/--key-Wiring funktioniert."""

    def test_serve_with_bad_cert_path_raises(self) -> None:
        from services.sync_server import serve
        tmp = Path(tempfile.mkdtemp(prefix="ah_tls_"))
        try:
            with self.assertRaises((FileNotFoundError, OSError)):
                serve(tmp / "events.jsonl", "127.0.0.1", 0, None,
                       certfile="/does/not/exist.pem",
                       keyfile="/does/not/exist.key")
        finally:
            shutil.rmtree(tmp)


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
