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
                    urllib.request.urlopen(req, timeout=2).read()
                lines = (tmp / "events.jsonl").read_text(
                    encoding="utf-8").splitlines()
                self.assertLessEqual(len(lines), 5)
                # Aelteste sind weg
                first = json.loads(lines[0])
                self.assertEqual(first["event_id"], "e5")
            finally:
                server.shutdown()
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
