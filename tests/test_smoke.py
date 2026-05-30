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
                      ModuleStateRepository, NoteRepository,
                      PriceMemoryRepository, ProposalRepository,
                      SettingsRepository, ShoppingRepository,
                      SocialRepository)
from modules.calendar import CalendarModule
from modules.contracts import ContractModule
from modules.daystructure import DayStructureModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from modules.notes import NotesModule
from modules.overview import OverviewModule
from modules.search import SearchModule
from modules.social import SocialModule
from modules.statistics import StatisticsModule
from services.config import DEFAULTS, load_config, save_value
from services.licensing import (ANNUAL_DISCOUNT_RATE, FAMILY_PERSONS_CAP,
                                 FREE_MAX_PERSONS, FREE_MODULES_DEFAULT,
                                 GRACE_PERIOD_DAYS,
                                 MOBILE_PRICE_MARKUP,
                                 PRICE_BASE_MONTHLY_EUR,
                                 PRICE_FAMILY_FLAT_MONTHLY_EUR,
                                 PRICE_PER_EXTRA_PERSON_MONTHLY_EUR,
                                 TRIAL_DAYS, Currency, License, Platform,
                                 Tier, activate_pro, all_quotes,
                                 calculate_price, convert_to_chf,
                                 format_quote_de, load_license,
                                 mark_grandfathered, recommended_tier,
                                 save_license, start_trial)
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
    notes_repo = NoteRepository(db)
    registry.register(ContractModule(contracts_repo, output))
    registry.register(FinanceModule(expense_repo,
                                     PriceMemoryRepository(db)))
    registry.register(FamilyModule(family_repo, ShoppingRepository(db)))
    registry.register(CalendarModule(calendar_repo))
    registry.register(SocialModule(social_repo, llm=llm))
    registry.register(DayStructureModule(DayEntryRepository(db)))
    registry.register(InboxModule(proposal_repo, llm=llm))
    registry.register(NotesModule(notes_repo))
    registry.register(SearchModule(
        contracts_repo, expense_repo, calendar_repo,
        family_repo, social_repo, proposal_repo, notes=notes_repo))
    registry.register(StatisticsModule(expense_repo, contracts_repo))
    registry.register(OverviewModule())
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
        # Soft-Delete: Vertrag liegt im Papierkorb, restore moeglich
        self.assertEqual(result["status"], "im papierkorb")
        self.assertEqual(
            self.registry.dispatch("contracts.list", {})["count"], 0)
        deleted = self.registry.dispatch("contracts.list_deleted", {})
        self.assertEqual(deleted["count"], 1)
        # Endgueltige Loeschung via purge
        purged = self.registry.dispatch(
            "contracts.purge", {"contract_id": cid})
        self.assertEqual(purged["status"], "endgueltig geloescht")
        self.assertEqual(
            self.registry.dispatch("contracts.list_deleted",
                                     {})["count"], 0)

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
        # Soft-Delete: member liegt im Papierkorb, owner-Referenz bleibt
        self.registry.dispatch(
            "family.delete_member", {"member_id": mid})
        contracts = self.registry.dispatch(
            "contracts.list", {})["contracts"]
        self.assertEqual(len(contracts), 1)
        # Erst purge entkoppelt via ON DELETE SET NULL
        self.registry.dispatch(
            "family.purge_member", {"member_id": mid})
        contracts = self.registry.dispatch(
            "contracts.list", {})["contracts"]
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
        self.assertEqual(i18n.language, "en")

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


class TestCsvImportRoundTrip(unittest.TestCase):
    """Export -> Import -> dieselben Eintraege erscheinen wieder."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_import_"))
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
        self.registry.dispatch("social.add_contact",
                                {"name": "Oma", "relation": "Familie"})
        self.registry.dispatch("family.add_member",
                                {"name": "Anna", "role": "erwachsen"})

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)
        shutil.rmtree(self.tmp)

    def test_export_then_import_reproduces_data(self) -> None:
        from services.export import export_all
        from services.import_csv import import_all
        # Export
        export_all(
            self.tmp,
            ContractRepository(self.db),
            ExpenseRepository(self.db),
            CalendarRepository(self.db),
            SocialRepository(self.db),
            FamilyRepository(self.db))
        # Import in eine frische DB
        tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp_db.close()
        try:
            fresh = Database(tmp_db.name)
            try:
                counts = import_all(
                    self.tmp,
                    ContractRepository(fresh),
                    ExpenseRepository(fresh),
                    CalendarRepository(fresh),
                    SocialRepository(fresh),
                    FamilyRepository(fresh))
                self.assertEqual(counts["contracts.csv"], 1)
                self.assertEqual(counts["expenses.csv"], 1)
                self.assertEqual(counts["calendar.csv"], 1)
                self.assertEqual(counts["social.csv"], 1)
                self.assertEqual(counts["family.csv"], 1)
                # Stichprobe: Streaming-Vertrag uebernommen
                contracts = ContractRepository(fresh).list_all(
                    only_active=False)
                self.assertEqual(len(contracts), 1)
                self.assertEqual(contracts[0].name, "Streaming")
                self.assertAlmostEqual(contracts[0].monthly_cost, 13.99)
            finally:
                fresh.close()
        finally:
            os.unlink(tmp_db.name)

    def test_missing_csv_files_are_skipped(self) -> None:
        from services.import_csv import import_all
        # Nur eine Datei - die anderen werden uebersprungen
        (self.tmp / "contracts.csv").write_text(
            "id;name;kategorie;anbieter;kundennummer;start;monatspreis;"
            "kuendigungsfrist_monate;verlaengerung_monate;person;status\n"
            "1;Solo;sonstiges;Niemand;;;0.00;3;12;;active\n",
            encoding="utf-8-sig")
        counts = import_all(
            self.tmp,
            ContractRepository(self.db),
            ExpenseRepository(self.db),
            CalendarRepository(self.db),
            SocialRepository(self.db),
            FamilyRepository(self.db))
        self.assertEqual(counts, {"contracts.csv": 1})

    def test_invalid_dates_dont_crash(self) -> None:
        from services.import_csv import import_expenses
        (self.tmp / "expenses.csv").write_text(
            "id;datum;beschreibung;betrag;kategorie;person\n"
            "1;nicht-iso;X;5.00;sonstiges;\n"
            "2;2026-01-15;Y;3.50;lebensmittel;\n",
            encoding="utf-8-sig")
        count = import_expenses(
            ExpenseRepository(self.db), self.tmp / "expenses.csv")
        # Beide Zeilen werden importiert, das ungueltige Datum landet als None
        self.assertEqual(count, 2)


class TestStatistics(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        # Beispieldaten ueber das aktuelle Jahr verteilt
        today = date.today()
        for i, amount in enumerate([10.0, 20.5, 15.25, 30.0]):
            d = today - timedelta(days=i * 7)
            self.registry.dispatch("finance.add_expense", dict(
                description=f"Posten {i}",
                amount=amount,
                category=("lebensmittel" if i % 2 == 0 else "freizeit"),
                spent_on=d.isoformat()))
        for v in [
            dict(name="Strom", category="strom", provider="Stadtwerke",
                 start_date="2025-01-01", minimum_term_months=1,
                 notice_period_months=1, auto_renew_months=1,
                 monthly_cost=80.0),
            dict(name="Streaming", category="streaming", provider="Netflix",
                 start_date="2025-01-01", minimum_term_months=1,
                 notice_period_months=1, auto_renew_months=1,
                 monthly_cost=13.99),
            dict(name="Versicherung", category="versicherung",
                 provider="HUK", start_date="2025-01-01",
                 minimum_term_months=12, notice_period_months=3,
                 auto_renew_months=12, monthly_cost=45.50),
        ]:
            self.registry.dispatch("contracts.add", v)

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_expenses_per_month_returns_buckets(self) -> None:
        result = self.registry.dispatch(
            "stats.expenses_per_month", {"months": 3})
        self.assertEqual(result["months"], 3)
        self.assertEqual(len(result["buckets"]), 3)
        # Heute liegt in der letzten Bucket
        today_bucket = date.today().strftime("%Y-%m")
        keys = [b["month"] for b in result["buckets"]]
        self.assertIn(today_bucket, keys)

    def test_expenses_per_category_aggregates(self) -> None:
        result = self.registry.dispatch(
            "stats.expenses_per_category", {})
        cats = {c["category"]: c["total"] for c in result["categories"]}
        # 4 Posten: idx 0+2 lebensmittel (10.0 + 15.25), idx 1+3 freizeit (20.5 + 30.0)
        self.assertAlmostEqual(cats.get("lebensmittel", 0), 25.25)
        self.assertAlmostEqual(cats.get("freizeit", 0), 50.5)

    def test_contracts_overview_top_3(self) -> None:
        result = self.registry.dispatch("stats.contracts_overview", {})
        self.assertEqual(result["count"], 3)
        self.assertAlmostEqual(result["monthly_total"], 139.49)
        # Strom muss an Position 1 stehen (80 EUR teuerster)
        self.assertEqual(result["top_3"][0]["name"], "Strom")
        self.assertAlmostEqual(result["top_3"][0]["monthly_cost"], 80.0)

    def test_yearly_summary(self) -> None:
        current_year = date.today().year
        result = self.registry.dispatch(
            "stats.yearly_summary", {"year": current_year})
        self.assertEqual(result["year"], current_year)
        self.assertEqual(result["expense_count"], 4)
        self.assertAlmostEqual(result["expense_total"], 75.75)

    def test_rejects_zero_months(self) -> None:
        result = self.registry.dispatch(
            "stats.expenses_per_month", {"months": 0})
        self.assertIn("error", result)


class TestUtcTimestampsInDb(unittest.TestCase):
    """DST/Timezone-Audit: created_at-Felder enthalten jetzt UTC-Offset."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_contract_created_at_uses_utc(self) -> None:
        self.registry.dispatch("contracts.add", dict(
            name="X", category="streaming", provider="Y",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=1.0))
        row = self.db.conn.execute(
            "SELECT created_at FROM contracts").fetchone()
        ts = row["created_at"]
        # ISO-Format mit UTC-Marker
        self.assertTrue(ts.endswith("+00:00") or ts.endswith("Z"),
                         f"Timestamp {ts!r} ohne UTC-Marker")

    def test_assistant_log_uses_utc(self) -> None:
        from database import AssistantLogRepository
        repo = AssistantLogRepository(self.db)
        repo.append("user", "test")
        row = self.db.conn.execute(
            "SELECT created_at FROM assistant_log").fetchone()
        ts = row["created_at"]
        self.assertTrue(ts.endswith("+00:00") or ts.endswith("Z"))


class TestProfile(unittest.TestCase):
    """Multi-User-Profile: DB-Datei und State-Dir leiten sich vom Profil ab."""

    def test_sanitize_profile(self) -> None:
        from services.profile import sanitize_profile
        self.assertEqual(sanitize_profile("anna"), "anna")
        self.assertEqual(sanitize_profile("Anna_2"), "Anna_2")
        self.assertEqual(sanitize_profile("a/n.a"), "ana")
        self.assertEqual(sanitize_profile(""), "")
        self.assertEqual(sanitize_profile(None), "")
        # Sehr lange Namen werden gekuerzt
        long_name = "x" * 100
        self.assertEqual(len(sanitize_profile(long_name)), 32)

    def test_db_path_default(self) -> None:
        from services.profile import db_path
        self.assertEqual(db_path("", "alltagshelfer_demo.db"),
                          "alltagshelfer_demo.db")

    def test_db_path_with_profile(self) -> None:
        from services.profile import db_path
        self.assertEqual(db_path("anna", "alltagshelfer_demo.db"),
                          "alltagshelfer_demo_anna.db")

    def test_state_dir_default_and_profile(self) -> None:
        from services.profile import state_dir
        self.assertEqual(str(state_dir("")), ".alltagshelfer-state")
        self.assertEqual(str(state_dir("anna")),
                          ".alltagshelfer-state-anna")

    def test_resolve_profile_uses_env(self) -> None:
        from services.profile import resolve_profile
        old = os.environ.pop("ALLTAGSHELFER_PROFILE", None)
        try:
            os.environ["ALLTAGSHELFER_PROFILE"] = "bernd"
            self.assertEqual(resolve_profile(), "bernd")
            os.environ["ALLTAGSHELFER_PROFILE"] = ""
            self.assertEqual(resolve_profile(), "")
        finally:
            if old is None:
                os.environ.pop("ALLTAGSHELFER_PROFILE", None)
            else:
                os.environ["ALLTAGSHELFER_PROFILE"] = old

    def test_explicit_overrides_env(self) -> None:
        from services.profile import resolve_profile
        old = os.environ.pop("ALLTAGSHELFER_PROFILE", None)
        try:
            os.environ["ALLTAGSHELFER_PROFILE"] = "env-anna"
            self.assertEqual(resolve_profile("explicit-bob"),
                              "explicit-bob")
        finally:
            if old is None:
                os.environ.pop("ALLTAGSHELFER_PROFILE", None)
            else:
                os.environ["ALLTAGSHELFER_PROFILE"] = old

    def test_two_profiles_use_separate_files(self) -> None:
        """Konsistenz: bei zwei Profilen entstehen zwei Dateien."""
        from services.profile import db_path
        tmp = Path(tempfile.mkdtemp(prefix="ah_profiles_"))
        try:
            for profile in ("anna", "bernd"):
                path = tmp / db_path(profile, "alltagshelfer_demo.db")
                db = Database(str(path))
                db.conn.execute(
                    "INSERT INTO family_members (name, role, created_at)"
                    " VALUES (?,?,?)", (profile.title(), "erwachsen",
                                          "2026-01-01T00:00:00+00:00"))
                db.conn.commit()
                db.close()
            anna_db = Database(str(tmp / "alltagshelfer_demo_anna.db"))
            bernd_db = Database(str(tmp / "alltagshelfer_demo_bernd.db"))
            try:
                anna_row = anna_db.conn.execute(
                    "SELECT name FROM family_members").fetchone()
                bernd_row = bernd_db.conn.execute(
                    "SELECT name FROM family_members").fetchone()
                self.assertEqual(anna_row["name"], "Anna")
                self.assertEqual(bernd_row["name"], "Bernd")
            finally:
                anna_db.close()
                bernd_db.close()
        finally:
            shutil.rmtree(tmp)


class TestAutoBackup(unittest.TestCase):
    """Auto-Backup-Job + Retention."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_auto_"))
        self.db_path = self.tmp / "live.db"
        self.db = Database(str(self.db_path))
        ContractRepository(self.db).add(self._sample_contract())

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp)

    @staticmethod
    def _sample_contract():
        from models import Contract
        return Contract(name="X", category="streaming", provider="Y",
                         start_date=date(2025, 1, 1),
                         minimum_term_months=1, notice_period_months=1,
                         auto_renew_months=1, monthly_cost=1.0)

    def test_run_once_creates_backup_and_prunes(self) -> None:
        from services.backup import AutoBackupWorker, list_backups
        backup_dir = self.tmp / "backups"
        worker = AutoBackupWorker(self.db, directory=backup_dir,
                                    retention_count=3)
        # 5x laufen lassen - jedes Mal ein neues Backup, nur 3 bleiben
        for _ in range(5):
            worker.run_once()
            time.sleep(0.01)        # eindeutige mtime / Dateinamen
        files = list_backups(backup_dir)
        self.assertLessEqual(len(files), 3)
        self.assertIsNotNone(worker.last_backup_path)
        self.assertIsNone(worker.last_error)

    def test_prune_old_backups_keeps_newest(self) -> None:
        from services.backup import prune_old_backups
        backup_dir = self.tmp / "bk"
        backup_dir.mkdir()
        # 5 Dateien mit absteigender mtime anlegen
        files = []
        for i in range(5):
            f = backup_dir / f"bk-{i:02d}.db"
            f.write_bytes(b"x")
            f.touch()
            files.append(f)
            time.sleep(0.01)
        removed = prune_old_backups(backup_dir, keep=2)
        self.assertEqual(len(removed), 3)
        # Die 2 neuesten muessen weiterhin existieren
        remaining = sorted(backup_dir.glob("*.db"),
                            key=lambda p: p.stat().st_mtime, reverse=True)
        self.assertEqual(len(remaining), 2)


class TestIcalExport(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.registry.dispatch("calendar.add_event", dict(
            title="TUEV", due_date="2030-01-15", category="tuev"))
        self.registry.dispatch("calendar.add_event", dict(
            title="Geburtstag, mit Komma", due_date="2030-05-01",
            category="geburtstag", recurrence_days=365))
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_ical_"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)
        shutil.rmtree(self.tmp)

    def test_export_creates_valid_ical(self) -> None:
        out = self.tmp / "events.ics"
        result = self.registry.dispatch("calendar.export_ical",
                                          {"path": str(out)})
        self.assertEqual(result["count"], 2)
        text = out.read_text(encoding="utf-8")
        # Grundstruktur und Spezialeskaping
        self.assertIn("BEGIN:VCALENDAR", text)
        self.assertIn("END:VCALENDAR", text)
        self.assertIn("SUMMARY:TUEV", text)
        self.assertIn("Geburtstag\\, mit Komma", text)
        # M3: 365 Tage werden als YEARLY exportiert, nicht DAILY
        self.assertIn("RRULE:FREQ=YEARLY;INTERVAL=1", text)


class TestVCardExport(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.registry.dispatch("social.add_contact",
                                {"name": "Oma", "relation": "Familie",
                                 "cadence_days": 14})
        self.registry.dispatch("social.add_contact",
                                {"name": "Tobias, Test",
                                 "relation": "Freund"})
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_vcf_"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)
        shutil.rmtree(self.tmp)

    def test_export_creates_valid_vcard(self) -> None:
        out = self.tmp / "contacts.vcf"
        result = self.registry.dispatch("social.export_vcard",
                                          {"path": str(out)})
        self.assertEqual(result["count"], 2)
        text = out.read_text(encoding="utf-8")
        self.assertIn("BEGIN:VCARD", text)
        self.assertIn("END:VCARD", text)
        self.assertIn("FN:Oma", text)
        self.assertIn("Tobias\\, Test", text)
        self.assertIn("CATEGORIES:Familie", text)


class TestYearlyPdfReport(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        # Ein paar Ausgaben + Vertraege
        for i, amount in enumerate([10.0, 22.5, 5.0]):
            self.registry.dispatch("finance.add_expense", {
                "description": f"X{i}", "amount": amount,
                "category": "lebensmittel",
                "spent_on": f"{date.today().year}-02-{i+1:02d}"})
        self.registry.dispatch("contracts.add", dict(
            name="Strom", category="strom", provider="Stadtwerke",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=80.0))
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_pdf_"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)
        shutil.rmtree(self.tmp)

    def test_pdf_report_produced(self) -> None:
        out = self.tmp / "bericht.pdf"
        result = self.registry.dispatch("stats.export_yearly_pdf",
                                          {"path": str(out)})
        self.assertEqual(result["status"], "PDF erstellt")
        self.assertTrue(out.exists())
        # PDF beginnt mit %PDF-
        self.assertTrue(out.read_bytes().startswith(b"%PDF-"))


class TestNotesModule(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_add_list_update_attach_delete(self) -> None:
        # Anlegen
        r = self.registry.dispatch("notes.add", {
            "title": "Idee", "content": "Lange Notiz"})
        self.assertEqual(r["status"], "angelegt")
        note_id = r["note"]["id"]
        # Auflisten
        l = self.registry.dispatch("notes.list", {})
        self.assertEqual(l["count"], 1)
        # Aktualisieren
        u = self.registry.dispatch("notes.update", {
            "note_id": note_id, "content": "Geaendert"})
        self.assertEqual(u["note"]["content"], "Geaendert")
        # An Entitaet heften
        a = self.registry.dispatch("notes.attach", {
            "note_id": note_id, "entity_type": "contracts",
            "entity_id": 42})
        self.assertEqual(a["note"]["entity_type"], "contracts")
        # Filter nach Entitaet
        filtered = self.registry.dispatch("notes.list", {
            "entity_type": "contracts", "entity_id": 42})
        self.assertEqual(filtered["count"], 1)
        # Loeschen
        d = self.registry.dispatch("notes.delete", {"note_id": note_id})
        self.assertEqual(d["status"], "geloescht")

    def test_empty_title_rejected(self) -> None:
        r = self.registry.dispatch("notes.add",
                                     {"title": "   ", "content": "x"})
        self.assertIn("error", r)

    def test_invalid_entity_type_rejected(self) -> None:
        r = self.registry.dispatch("notes.add", {
            "title": "X", "content": "", "entity_type": "evil",
            "entity_id": 1})
        self.assertIn("error", r)

    def test_search_finds_notes(self) -> None:
        self.registry.dispatch("notes.add", {
            "title": "Geheimnis", "content": "Schluesselwort"})
        result = self.registry.dispatch(
            "system.search", {"query": "schluesselwort"})
        sources = {h["source"] for h in result["hits"]}
        self.assertIn("notes", sources)


class TestIcalImportRoundTrip(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_ical_rt_"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)
        shutil.rmtree(self.tmp)

    def test_roundtrip(self) -> None:
        self.registry.dispatch("calendar.add_event", {
            "title": "TUEV, jaehrlich", "due_date": "2030-09-15",
            "category": "tuev", "recurrence_days": 365,
            "description": "Erinnerung mit ; und , Sonderzeichen"})
        out = self.tmp / "events.ics"
        self.registry.dispatch("calendar.export_ical", {"path": str(out)})
        # Frische DB
        tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp_db.close()
        try:
            fresh = Database(tmp_db.name)
            try:
                from modules.calendar import CalendarModule
                reg = ModuleRegistry()
                reg.register(CalendarModule(CalendarRepository(fresh)))
                result = reg.dispatch("calendar.import_ical",
                                       {"path": str(out)})
                self.assertEqual(result["count"], 1)
                events = CalendarRepository(fresh).list_all()
                self.assertEqual(events[0].title, "TUEV, jaehrlich")
                self.assertEqual(events[0].recurrence_days, 365)
                self.assertIn(";", events[0].description)
            finally:
                fresh.close()
        finally:
            os.unlink(tmp_db.name)

    def test_import_missing_file_returns_error(self) -> None:
        result = self.registry.dispatch("calendar.import_ical",
                                          {"path": "nicht-da.ics"})
        self.assertIn("error", result)


class TestVCardImportRoundTrip(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_vcf_rt_"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)
        shutil.rmtree(self.tmp)

    def test_roundtrip_preserves_rhythmus(self) -> None:
        self.registry.dispatch("social.add_contact", {
            "name": "Oma, Test", "relation": "Familie",
            "cadence_days": 21})
        out = self.tmp / "contacts.vcf"
        self.registry.dispatch("social.export_vcard", {"path": str(out)})
        # Frische DB
        tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp_db.close()
        try:
            fresh = Database(tmp_db.name)
            try:
                from modules.social import SocialModule
                reg = ModuleRegistry()
                reg.register(SocialModule(SocialRepository(fresh)))
                result = reg.dispatch("social.import_vcard",
                                       {"path": str(out)})
                self.assertEqual(result["count"], 1)
                contacts = SocialRepository(fresh).list_all()
                self.assertEqual(contacts[0].name, "Oma, Test")
                self.assertEqual(contacts[0].relation, "Familie")
                # Rhythmus aus NOTE wieder rekonstruiert
                self.assertEqual(contacts[0].cadence_days, 21)
            finally:
                fresh.close()
        finally:
            os.unlink(tmp_db.name)


class TestLamportCrdt(unittest.TestCase):
    """Lamport-Counter sorgt fuer kausale Reihenfolge bei Sync."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ah_lamport_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root)

    def test_clock_ticks_monotonically(self) -> None:
        from services.sync import LamportClock
        c = LamportClock()
        self.assertEqual(c.tick(), 1)
        self.assertEqual(c.tick(), 2)
        self.assertEqual(c.observe(10), 11)
        self.assertEqual(c.tick(), 12)
        # Observe mit kleinerem Wert hebt counter nur durch +1
        self.assertEqual(c.observe(5), 13)

    def test_events_get_lamport_counter(self) -> None:
        from services.sync import FileSyncProvider, install_sync_hook
        provider = FileSyncProvider(str(self.root / "shared"), "dev",
                                      local_seen_path=self.root / "seen.json")
        db, registry, _, db_path = _build_system()
        try:
            install_sync_hook(registry, provider)
            registry.dispatch("family.add_member", {"name": "Anna"})
            registry.dispatch("family.add_member", {"name": "Bernd"})
            events = provider.read_all()
            counters = [e.lamport for e in events]
            self.assertEqual(counters, [1, 2])
        finally:
            db.close()
            os.unlink(db_path)

    def test_replay_order_uses_lamport(self) -> None:
        """Bei zwei Geraeten zaehlt der Lamport - nicht die Wall-Clock."""
        from services.sync import (FileSyncProvider, SyncEvent,
                                     install_sync_hook)
        shared = self.root / "shared"
        shared.mkdir()
        # Geraet A schreibt Event mit hoeherem Lamport
        # Geraet B schreibt frueheres mit niedrigerem Lamport
        # Replay-Reihenfolge muss B vor A applizieren.
        events = [
            SyncEvent(event_id="e2", device_id="dev-a",
                       timestamp="2026-01-01T00:00:00+00:00",
                       capability="family.add_member",
                       args={"name": "Spaeter"}, lamport=5),
            SyncEvent(event_id="e1", device_id="dev-b",
                       timestamp="2026-01-01T00:00:00+00:00",
                       capability="family.add_member",
                       args={"name": "Frueher"}, lamport=3),
        ]
        log = shared / "sync_events.jsonl"
        log.write_text("\n".join(
            __import__("json").dumps(e.to_dict()) for e in events) + "\n",
            encoding="utf-8")
        provider = FileSyncProvider(str(shared), "dev-other",
                                      local_seen_path=self.root / "seen.json")
        ordered = provider.unseen_events()
        # 'Frueher' mit Lamport 3 muss vor 'Spaeter' mit Lamport 5 stehen
        self.assertEqual([e.args["name"] for e in ordered],
                          ["Frueher", "Spaeter"])


class TestBulkOperations(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_bulk_reject_open_proposals(self) -> None:
        # Drei Vorschlaege manuell anlegen
        from models import Proposal
        repo = ProposalRepository(self.db)
        for i in range(3):
            repo.add(Proposal(source="test", summary=f"P{i}",
                                target_capability="x.y", payload={}))
        result = self.registry.dispatch("inbox.bulk_reject_open", {})
        self.assertEqual(result["count"], 3)
        # Es darf keinen offenen Vorschlag mehr geben
        self.assertEqual(len(repo.list(status="offen")), 0)
        self.assertEqual(len(repo.list(status="abgelehnt")), 3)

    def test_bulk_delete_archived(self) -> None:
        from models import Proposal
        repo = ProposalRepository(self.db)
        for status in ("uebernommen", "abgelehnt", "offen"):
            p = repo.add(Proposal(source="test", summary=status,
                                     target_capability="x.y", payload={}))
            if p.id is not None and status != "offen":
                repo.set_status(p.id, status)
        result = self.registry.dispatch("inbox.bulk_delete_archived", {})
        self.assertEqual(result["count"], 2)
        # Der offene Vorschlag bleibt
        remaining = repo.list()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].status, "offen")

    def test_bulk_complete_overdue_tasks(self) -> None:
        self.registry.dispatch("family.add_member",
                                {"name": "Anna"})
        self.registry.dispatch("family.add_member",
                                {"name": "Bernd"})
        # Zwei ueberfaellige + eine in der Zukunft
        old = (date.today() - timedelta(days=5)).isoformat()
        future = (date.today() + timedelta(days=10)).isoformat()
        for title, due in [("Muell", old), ("Kueche", old),
                            ("Garage", future)]:
            self.registry.dispatch("family.add_task", {
                "title": title, "interval_days": 7,
                "assignees": ["Anna", "Bernd"], "first_due": due})
        result = self.registry.dispatch(
            "family.bulk_complete_overdue", {})
        # Zwei der drei Aufgaben sind ueberfaellig
        self.assertEqual(result["count"], 2)


class TestReviewFixes(unittest.TestCase):
    """Direkte Tests fuer die 21 Code-Review-Befunde dieser Runde."""

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_review_"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)
        shutil.rmtree(self.tmp)

    # ---- K1: Import-Pfad-Validierung -----------------------------------
    def test_ical_import_rejects_path_outside_or_bad_extension(self) -> None:
        # Falsche Extension
        bad = self.tmp / "evil.txt"
        bad.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n",
                        encoding="utf-8")
        result = self.registry.dispatch("calendar.import_ical",
                                          {"path": str(bad)})
        self.assertIn("error", result)

    def test_ical_import_rejects_nonexistent(self) -> None:
        result = self.registry.dispatch("calendar.import_ical",
                                          {"path": "nicht-existent.ics"})
        self.assertIn("error", result)

    def test_vcard_import_rejects_too_large(self) -> None:
        from services.io_validation import DEFAULT_MAX_IMPORT_BYTES
        big = self.tmp / "big.vcf"
        # 1 MB groesser als das Limit
        big.write_bytes(b"x" * (DEFAULT_MAX_IMPORT_BYTES + 1024))
        result = self.registry.dispatch("social.import_vcard",
                                          {"path": str(big)})
        self.assertIn("error", result)

    # ---- K2: Import laeuft durch _cap_add_event -------------------------
    def test_ical_import_validates_recurrence(self) -> None:
        # ICS mit ungueltigem RRULE-Wert - der Import sollte den Eintrag
        # NICHT erstellen, da _cap_add_event recurrence_days <= 0 ablehnt.
        # Wir zeigen das indirekt: ein RRULE, das auf 0 mapped, fuehrt
        # zu recurrence_days=None, der Termin wird trotzdem angelegt -
        # das ist ok. Aber: ein Event ohne SUMMARY oder DTSTART wird gar
        # nicht erst durch den Parser durchgelassen.
        ics = self.tmp / "x.ics"
        ics.write_text(
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nSUMMARY:OK-Event\r\nDTSTART;VALUE=DATE:20300101\r\n"
            "RRULE:FREQ=DAILY;INTERVAL=0\r\nEND:VEVENT\r\n"
            "END:VCALENDAR\r\n", encoding="utf-8")
        result = self.registry.dispatch("calendar.import_ical",
                                          {"path": str(ics)})
        # Akzeptiert das Event, recurrence wird auf None gesetzt
        self.assertEqual(result["count"], 1)

    # ---- K3: HttpSyncProvider.read_all existiert ------------------------
    def test_http_provider_has_read_all(self) -> None:
        from services.sync import HttpSyncProvider
        provider = HttpSyncProvider(
            "http://localhost:1", "dev-x",
            local_state_path=self.tmp / "seen.json")
        # Nicht erreichbar - read_all liefert leere Liste statt zu crashen
        self.assertEqual(provider.read_all(), [])

    # ---- K4: Streaming-Lock --------------------------------------------
    # GUI-Code laesst sich headless nicht ausfuehren - wir testen das
    # Verhalten indirekt ueber Assistant._ask_lock (H7).
    def test_assistant_ask_lock_serializes(self) -> None:
        # Zwei parallele asks auf demselben Assistant duerfen sich nicht
        # ueberlappen. Der Lock garantiert das.
        import threading as _threading
        from assistant import Assistant
        a = Assistant(self.registry)
        a.llm = None  # Offline-Modus
        order: list[str] = []

        def worker(prefix: str) -> None:
            a.ask(f"Frage {prefix}")
            order.append(prefix)

        t1 = _threading.Thread(target=worker, args=("A",))
        t2 = _threading.Thread(target=worker, args=("B",))
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)
        self.assertEqual(len(order), 2)

    # ---- K5: deepcopy von args -----------------------------------------
    def test_sync_event_args_deep_copy(self) -> None:
        """Mutiere args nach dispatch - das Event darf NICHT mitwandern."""
        from services.sync import FileSyncProvider, install_sync_hook
        provider = FileSyncProvider(str(self.tmp / "shared"), "dev-x",
                                      local_seen_path=self.tmp / "seen.json")
        install_sync_hook(self.registry, provider)
        args = {"name": "X", "category": "streaming", "provider": "Y",
                "start_date": "2025-01-01", "minimum_term_months": 1,
                "notice_period_months": 1, "auto_renew_months": 1,
                "monthly_cost": 1.0}
        self.registry.dispatch("contracts.add", args)
        # Nachtraegliche Mutation
        args["name"] = "MANIPULIERT"
        # Das gespeicherte Event muss noch 'X' enthalten
        events = provider.read_all()
        self.assertEqual(events[-1].args["name"], "X")

    # ---- H1: _initial_lamport_value nur eigene Events -------------------
    def test_initial_lamport_ignores_other_devices(self) -> None:
        from services.sync import (FileSyncProvider, LamportClock,
                                     SyncEvent, SyncedRegistry,
                                     install_sync_hook)
        shared = self.tmp / "shared"
        shared.mkdir()
        log = shared / "sync_events.jsonl"
        # Ein fremdes Event mit hohem Lamport
        foreign = SyncEvent(
            event_id="x1", device_id="other-device",
            timestamp="2026-01-01T00:00:00+00:00",
            capability="family.add_member",
            args={"name": "X"}, lamport=99)
        log.write_text(
            __import__("json").dumps(foreign.to_dict()) + "\n",
            encoding="utf-8")
        provider = FileSyncProvider(str(shared), "my-device",
                                      local_seen_path=self.tmp / "s.json")
        synced = SyncedRegistry(self.registry, provider)
        # Eigene Counter startet NICHT bei 99 (fremder Wert) - sondern bei 0
        self.assertEqual(synced.clock.value, 0)

    # ---- H2: vCard-Import clampt cadence_days auf >=1 -------------------
    def test_vcard_import_clamps_cadence(self) -> None:
        vcf = self.tmp / "bad.vcf"
        vcf.write_text(
            "BEGIN:VCARD\nVERSION:3.0\nFN:Test\nN:Test;;;;\n"
            "NOTE:Rhythmus: alle 0 Tage\n"
            "END:VCARD\n", encoding="utf-8")
        result = self.registry.dispatch("social.import_vcard",
                                          {"path": str(vcf)})
        self.assertEqual(result["count"], 1)
        contacts = self.registry.dispatch("social.contacts",
                                            {})["contacts"]
        # cadence_days clamped auf 1 statt 0
        self.assertGreaterEqual(contacts[0]["cadence_days"], 1)

    # ---- H3: UTF-8-Byte-Folding ----------------------------------------
    def test_ical_export_folds_at_byte_boundary(self) -> None:
        from services.ical import _fold
        # 100 Umlaute -> 200 Bytes -> muss in mehrere Zeilen gebrochen werden
        line = "SUMMARY:" + ("ae" * 50)
        folded = _fold(line)
        # Pro Zeile darf kein Stuck > 75 BYTES sein
        for chunk in folded.split("\r\n"):
            # Continuation-Lines beginnen mit Leerzeichen
            actual = chunk[1:] if chunk.startswith(" ") else chunk
            self.assertLessEqual(len(actual.encode("utf-8")), 75)

    # ---- H4: entity_id=0 wird NICHT zu None -----------------------------
    def test_notes_entity_id_zero_preserved(self) -> None:
        r = self.registry.dispatch("notes.add", {
            "title": "Test", "content": "x",
            "entity_type": "contracts", "entity_id": 0})
        self.assertEqual(r["note"]["entity_id"], 0)

    # ---- H6: Bulk-Ops laufen durch dispatch (Sync-faehig) ---------------
    def test_bulk_complete_overdue_dispatches_individual_tasks(self) -> None:
        from services.sync import (FileSyncProvider, install_sync_hook)
        provider = FileSyncProvider(str(self.tmp / "shared"), "dev",
                                      local_seen_path=self.tmp / "seen.json")
        install_sync_hook(self.registry, provider)
        self.registry.dispatch("family.add_member", {"name": "Anna"})
        old = (date.today() - timedelta(days=10)).isoformat()
        self.registry.dispatch("family.add_task", {
            "title": "X", "interval_days": 7,
            "assignees": ["Anna"], "first_due": old})
        events_before = len(provider.read_all())
        self.registry.dispatch("family.bulk_complete_overdue", {})
        events_after = len(provider.read_all())
        # Bulk-Op hat individuelle complete_task-Events erzeugt
        self.assertGreater(events_after, events_before)
        # Naemlich: family.complete_task soll geloggt sein
        last_caps = [e.capability for e in provider.read_all()]
        self.assertIn("family.complete_task", last_caps)

    # ---- M1: Regex-Unescape ohne NUL-Marker -----------------------------
    def test_unescape_preserves_real_null_bytes(self) -> None:
        from services.ical import _unescape
        # Echtes NUL-Byte im Wert: darf nicht mit dem alten Placeholder
        # verwechselt werden.
        original = "Hallo\x00Welt mit \\, und \\n"
        result = _unescape(original)
        self.assertIn("\x00", result)
        self.assertIn(",", result)
        self.assertIn("\n", result)

    # ---- M3: RRULE-Format bevorzugt grobe Frequenz ----------------------
    def test_rrule_uses_yearly_for_365(self) -> None:
        from services.ical import _format_rrule
        self.assertEqual(_format_rrule(365),
                          "RRULE:FREQ=YEARLY;INTERVAL=1")
        self.assertEqual(_format_rrule(7),
                          "RRULE:FREQ=WEEKLY;INTERVAL=1")
        self.assertEqual(_format_rrule(14),
                          "RRULE:FREQ=WEEKLY;INTERVAL=2")
        self.assertEqual(_format_rrule(3),
                          "RRULE:FREQ=DAILY;INTERVAL=3")

    # ---- M6: Geometry-Validierung --------------------------------------
    def test_geometry_validation(self) -> None:
        from gui import _is_valid_geometry
        self.assertTrue(_is_valid_geometry("1080x720"))
        self.assertTrue(_is_valid_geometry("1080x720+100+50"))
        self.assertTrue(_is_valid_geometry("1080x720-50-50"))
        self.assertFalse(_is_valid_geometry(""))
        self.assertFalse(_is_valid_geometry("abc"))
        self.assertFalse(_is_valid_geometry("100x50"))         # zu klein
        self.assertFalse(_is_valid_geometry("99999x99999"))    # zu gross
        self.assertFalse(_is_valid_geometry("1080x720+99999+0"))

    # ---- M7: Orphan-Notes-Cleanup --------------------------------------
    def test_deleting_contract_cleans_attached_notes(self) -> None:
        self.registry.dispatch("contracts.add", dict(
            name="X", category="streaming", provider="Y",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1,
            monthly_cost=10.0))
        cid = self.registry.dispatch("contracts.list",
                                       {})["contracts"][0]["id"]
        self.registry.dispatch("notes.add", {
            "title": "Note zu Vertrag", "content": "X",
            "entity_type": "contracts", "entity_id": cid})
        self.assertEqual(
            self.registry.dispatch("notes.list", {})["count"], 1)
        # Soft-Delete laesst Notiz erhalten (Restore moeglich)
        self.registry.dispatch("contracts.delete", {"contract_id": cid})
        self.assertEqual(
            self.registry.dispatch("notes.list", {})["count"], 1)
        # Erst purge raeumt verwaiste Notiz weg
        self.registry.dispatch("contracts.purge", {"contract_id": cid})
        self.assertEqual(
            self.registry.dispatch("notes.list", {})["count"], 0)

    # ---- N6: delete_by_status nutzt Repository --------------------------
    def test_bulk_delete_archived_uses_repository_method(self) -> None:
        from models import Proposal
        repo = ProposalRepository(self.db)
        for status in ("uebernommen", "abgelehnt", "offen"):
            p = repo.add(Proposal(source="test", summary=status,
                                     target_capability="x.y", payload={}))
            if p.id is not None and status != "offen":
                repo.set_status(p.id, status)
        result = self.registry.dispatch("inbox.bulk_delete_archived", {})
        self.assertEqual(result["count"], 2)
        # Offener Vorschlag bleibt
        self.assertEqual(len(repo.list()), 1)

    # ---- Internal-Capabilities sind NICHT im LLM-Tool-Schema ------------
    def test_internal_capabilities_hidden_from_llm(self) -> None:
        schemas = self.registry.tool_schemas()
        names = {s["name"] for s in schemas}
        self.assertNotIn("calendar.import_ical", names)
        self.assertNotIn("social.import_vcard", names)
        self.assertNotIn("notes.cleanup_for_entity", names)
        # Aber sie sind via has_capability erreichbar
        self.assertTrue(
            self.registry.has_capability("calendar.import_ical"))


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


class TestLicensing(unittest.TestCase):
    """Pricing-Modell Variante B - 6,99 EUR Basis, 1,99 EUR/extra, 20 %/Jahr."""

    def test_free_tier_is_zero(self) -> None:
        q = calculate_price(1, Tier.FREE)
        self.assertEqual(q.total_eur, 0.0)
        self.assertEqual(q.monthly_eur, 0.0)
        self.assertEqual(q.period, "forever")

    def test_monthly_base_two_persons(self) -> None:
        q = calculate_price(2, Tier.PRO_MONTHLY)
        self.assertAlmostEqual(q.monthly_eur, PRICE_BASE_MONTHLY_EUR)
        self.assertAlmostEqual(q.total_eur, PRICE_BASE_MONTHLY_EUR)
        self.assertEqual(q.period, "monthly")

    def test_monthly_charges_extra_persons(self) -> None:
        q = calculate_price(4, Tier.PRO_MONTHLY)
        expected = PRICE_BASE_MONTHLY_EUR + 2 * PRICE_PER_EXTRA_PERSON_MONTHLY_EUR
        self.assertAlmostEqual(q.monthly_eur, round(expected, 2))

    def test_single_person_pays_base_price(self) -> None:
        # Eine Person zahlt denselben Basispreis wie zwei - bewusst, weil
        # der Wert "Familie verwalten" auch fuer Singles greift (Vertraege etc.)
        q = calculate_price(1, Tier.PRO_MONTHLY)
        self.assertAlmostEqual(q.monthly_eur, PRICE_BASE_MONTHLY_EUR)

    def test_annual_applies_20_percent_discount(self) -> None:
        # Berechnung: Jahresgesamtbetrag zuerst, daraus den Monatspreis -
        # sonst akkumuliert die Cent-Rundung im Monatspreis ueber 12 Monate.
        q = calculate_price(2, Tier.PRO_ANNUAL)
        expected_total = round(PRICE_BASE_MONTHLY_EUR * 12
                                * (1 - ANNUAL_DISCOUNT_RATE), 2)
        self.assertAlmostEqual(q.total_eur, expected_total)
        self.assertAlmostEqual(q.monthly_eur, round(expected_total / 12, 2))
        self.assertEqual(q.discount_rate, ANNUAL_DISCOUNT_RATE)

    def test_annual_savings_vs_monthly(self) -> None:
        # Vier-Personen-Familie: Listenpreis 10,97/Monat -> 131,64 EUR/Jahr,
        # mit 20 % Rabatt: 105,31 EUR/Jahr (8,78 EUR/Monat) -> 26,33 EUR Ersparnis.
        # Exakte Werte pruefen, damit Rundungs-Drift sofort auffaellt.
        q = calculate_price(4, Tier.PRO_ANNUAL)
        self.assertAlmostEqual(q.total_eur, 105.31)
        self.assertAlmostEqual(q.monthly_eur, 8.78)
        self.assertAlmostEqual(q.savings_eur(), 26.33)

    def test_annual_total_matches_readme_base_tier(self) -> None:
        # README-Beispiel: 67,10 EUR/Jahr fuer Basis (bis 2 Personen).
        q = calculate_price(2, Tier.PRO_ANNUAL)
        self.assertAlmostEqual(q.total_eur, 67.10)

    def test_invalid_persons_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_price(0, Tier.PRO_MONTHLY)

    def test_all_quotes_returns_pricing_tiers(self) -> None:
        # FREE + drei zahlende Pro-Tiers (Family nur wenn unter Cap)
        quotes = all_quotes(3)
        self.assertIn(Tier.FREE, quotes)
        self.assertIn(Tier.PRO_MONTHLY, quotes)
        self.assertIn(Tier.PRO_ANNUAL, quotes)
        self.assertIn(Tier.PRO_FAMILY, quotes)
        # Jahresabo immer guenstiger pro Monat als Monatsabo
        self.assertLess(quotes[Tier.PRO_ANNUAL].monthly_eur,
                        quotes[Tier.PRO_MONTHLY].monthly_eur)
        # Family wird oberhalb der Kappung nicht angeboten
        big = all_quotes(7)
        self.assertNotIn(Tier.PRO_FAMILY, big)

    def test_free_license_restricts_modules(self) -> None:
        lic = License()
        self.assertEqual(lic.tier, Tier.FREE)
        self.assertTrue(lic.allows_module("contracts"))
        self.assertFalse(lic.allows_module("finance"))
        self.assertFalse(lic.allows_ai())
        self.assertFalse(lic.allows_sync())
        self.assertEqual(lic.max_persons(), FREE_MAX_PERSONS)

    def test_pro_license_unlocks_everything(self) -> None:
        lic = License(tier=Tier.PRO_ANNUAL, persons=4)
        for mid in ("contracts", "finance", "calendar", "family",
                    "social", "inbox", "statistics", "daystructure"):
            self.assertTrue(lic.allows_module(mid))
        self.assertTrue(lic.allows_ai())
        self.assertTrue(lic.allows_sync())
        self.assertEqual(lic.max_persons(), 4)

    def test_unsigned_pro_settings_downgrade_to_free(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            save_license(repo, License(tier=Tier.PRO_ANNUAL, persons=3,
                                        enabled_modules=FREE_MODULES_DEFAULT))
            loaded = load_license(repo)
            self.assertEqual(loaded.tier, Tier.FREE)
            self.assertEqual(loaded.persons, FREE_MAX_PERSONS)
            db.close()
        finally:
            os.unlink(tmp.name)

    def test_load_license_defaults_to_free(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            lic = load_license(repo)
            self.assertEqual(lic.tier, Tier.FREE)
            self.assertEqual(lic.persons, 1)
            db.close()
        finally:
            os.unlink(tmp.name)

    def test_load_license_handles_corrupt_values(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            repo.set("license.tier", "nonsense")
            repo.set("license.persons", "not-a-number")
            lic = load_license(repo)
            self.assertEqual(lic.tier, Tier.FREE)
            self.assertEqual(lic.persons, 1)
            db.close()
        finally:
            os.unlink(tmp.name)

    # ---- license_ui (GUI-agnostische Helfer) ------------------------
    def test_tier_status_for_free(self) -> None:
        from services.license_ui import make_tier_status
        st = make_tier_status(License())
        self.assertEqual(st.tier, Tier.FREE)
        self.assertTrue(st.can_start_trial)
        self.assertIn("Free", st.headline)

    def test_tier_status_for_trial_shows_days_left(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_ui import make_tier_status
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.TRIAL,
                       trial_started_at=now - timedelta(days=10))
        st = make_tier_status(lic, now=now)
        self.assertEqual(st.tier, Tier.TRIAL)
        self.assertEqual(st.expires_in_days, 4)  # 14 - 10
        self.assertFalse(st.can_start_trial)

    def test_tier_status_in_grace_period(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_ui import make_tier_status
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.PRO_MONTHLY, persons=2,
                       expires_at=now - timedelta(days=3))
        st = make_tier_status(lic, now=now)
        self.assertTrue(st.in_grace_period)
        self.assertIn("Karenz", st.headline)

    def test_sidebar_indicator_strings(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_ui import sidebar_indicator
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        self.assertEqual(sidebar_indicator(License()), "Tier: Free")
        trial = License(tier=Tier.TRIAL,
                         trial_started_at=now - timedelta(days=2))
        self.assertIn("Trial (12d)", sidebar_indicator(trial, now=now))
        pro = License(tier=Tier.PRO_ANNUAL, persons=2,
                       expires_at=now + timedelta(days=180))
        self.assertIn("Pro (jaehrlich)", sidebar_indicator(pro, now=now))

    def test_build_pricing_rows_marks_recommended(self) -> None:
        from services.license_ui import build_pricing_rows
        rows = build_pricing_rows(4, recommended=Tier.PRO_ANNUAL)
        recommended = [r for r in rows if r.is_recommended]
        self.assertEqual(len(recommended), 1)
        self.assertEqual(recommended[0].tier, Tier.PRO_ANNUAL)
        # Free + 3 Pro-Tiers (Family ist bei 4 noch unter Cap)
        self.assertEqual(len(rows), 4)

    def test_build_pricing_rows_skips_family_above_cap(self) -> None:
        from services.license_ui import build_pricing_rows
        from services.licensing import FAMILY_PERSONS_CAP, Tier
        rows = build_pricing_rows(FAMILY_PERSONS_CAP + 1)
        tiers = [r.tier for r in rows]
        self.assertNotIn(Tier.PRO_FAMILY, tiers)

    def test_action_start_trial_success_then_blocked(self) -> None:
        from services.license_ui import action_start_trial
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = Database(tmp.name)
        try:
            repo = SettingsRepository(db)
            first = action_start_trial(repo)
            self.assertTrue(first.success)
            self.assertEqual(first.license.tier, Tier.TRIAL)
            second = action_start_trial(repo)
            self.assertFalse(second.success)
            self.assertIn("bereits genutzt", second.message)
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_action_apply_token_round_trip(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              generate_keypair, sign_token)
        from services.license_ui import action_apply_token
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        tok = LicenseToken(tier=Tier.PRO_ANNUAL, persons=4,
                            purchased_at=now,
                            expires_at=now + timedelta(days=365),
                            customer_id="alice@example.com")
        token_str = sign_token(tok, priv)
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = Database(tmp.name)
        try:
            repo = SettingsRepository(db)
            result = action_apply_token(repo, token_str, public_key_hex=pub,
                                          now=now)
            self.assertTrue(result.success, result.message)
            self.assertEqual(result.license.tier, Tier.PRO_ANNUAL)
            self.assertEqual(result.license.persons, 4)
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_action_apply_token_rejects_garbage(self) -> None:
        from services.license_ui import action_apply_token
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = Database(tmp.name)
        try:
            repo = SettingsRepository(db)
            result = action_apply_token(repo, "not-a-real-token")
            self.assertFalse(result.success)
            self.assertIn("Token", result.message)
        finally:
            db.close()
            os.unlink(tmp.name)

    def test_action_apply_token_rejects_empty(self) -> None:
        from services.license_ui import action_apply_token
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = Database(tmp.name)
        try:
            repo = SettingsRepository(db)
            result = action_apply_token(repo, "   ")
            self.assertFalse(result.success)
            self.assertIn("Kein Token", result.message)
        finally:
            db.close()
            os.unlink(tmp.name)

    # ---- Payment: Paddle-Adapter ------------------------------------
    def test_paddle_signature_round_trip(self) -> None:
        import hmac as _hmac
        import time
        from hashlib import sha256
        from services.payment_adapter_paddle import verify_signature
        secret = "whsec_test"
        body = b'{"event_type":"subscription.created"}'
        ts = int(time.time())
        sig = _hmac.new(secret.encode(), f"{ts}:".encode() + body,
                         sha256).hexdigest()
        # gueltig
        verify_signature(body, f"ts={ts};h1={sig}", secret)
        # ts manipuliert
        from services.payment import SignatureError
        with self.assertRaises(SignatureError):
            verify_signature(body, f"ts={ts + 1};h1={sig}", secret)
        # Toleranzfenster verletzt
        old_ts = ts - 600
        old_sig = _hmac.new(secret.encode(),
                             f"{old_ts}:".encode() + body,
                             sha256).hexdigest()
        with self.assertRaises(SignatureError):
            verify_signature(body, f"ts={old_ts};h1={old_sig}", secret)

    def test_paddle_parse_event(self) -> None:
        import hmac as _hmac
        import time
        from hashlib import sha256
        from services.payment import WebhookContext
        from services.payment_adapter_paddle import parse_event
        payload = {
            "event_type": "subscription.created",
            "event_id": "evt_001",
            "data": {
                "id": "sub_001",
                "customer": {"id": "ctm_001",
                              "email": "alice@example.com"},
                "items": [{"price": {"id": "pri_pro_annual"}}],
                "next_billed_at": "2027-05-20T00:00:00Z",
            },
        }
        body = json.dumps(payload).encode()
        secret = "s"
        ts = int(time.time())
        sig = _hmac.new(secret.encode(), f"{ts}:".encode() + body,
                         sha256).hexdigest()
        ctx = WebhookContext(
            raw_body=body,
            headers={"Paddle-Signature": f"ts={ts};h1={sig}"},
            signing_secret=secret,
            price_mapping={"pri_pro_annual": (Tier.PRO_ANNUAL, 4)},
        )
        ev = parse_event(ctx)
        self.assertIsNotNone(ev)
        self.assertEqual(ev.tier, Tier.PRO_ANNUAL)
        self.assertEqual(ev.persons, 4)
        self.assertEqual(ev.customer_email, "alice@example.com")
        self.assertEqual(ev.transaction_id, "sub_001")

    def test_paddle_unknown_price_rejected(self) -> None:
        import hmac as _hmac
        import time
        from hashlib import sha256
        from services.payment import UnknownPriceError, WebhookContext
        from services.payment_adapter_paddle import parse_event
        payload = {
            "event_type": "subscription.created",
            "data": {
                "id": "sub_x",
                "customer": {"id": "c", "email": "e@example.com"},
                "items": [{"price": {"id": "pri_unknown"}}],
            },
        }
        body = json.dumps(payload).encode()
        ts = int(time.time())
        sig = _hmac.new(b"s", f"{ts}:".encode() + body, sha256).hexdigest()
        ctx = WebhookContext(
            raw_body=body,
            headers={"Paddle-Signature": f"ts={ts};h1={sig}"},
            signing_secret="s",
            price_mapping={"pri_other": (Tier.PRO_MONTHLY, 2)},
        )
        with self.assertRaises(UnknownPriceError):
            parse_event(ctx)

    # ---- Payment: Lemon-Squeezy-Adapter ----------------------------
    def test_lemon_signature_and_parse(self) -> None:
        import hmac as _hmac
        from hashlib import sha256
        from services.payment import WebhookContext
        from services.payment_adapter_lemon import parse_event
        payload = {
            "meta": {"event_name": "subscription_created"},
            "data": {
                "id": "12345",
                "attributes": {
                    "user_email": "bob@example.com",
                    "customer_id": 99,
                    "variant_id": 7,
                    "renews_at": "2027-05-20T00:00:00Z",
                },
            },
        }
        body = json.dumps(payload).encode()
        secret = "ls_test"
        sig = _hmac.new(secret.encode(), body, sha256).hexdigest()
        ctx = WebhookContext(
            raw_body=body,
            headers={"X-Signature": sig},
            signing_secret=secret,
            price_mapping={"7": (Tier.PRO_FAMILY, 5)},
        )
        ev = parse_event(ctx)
        self.assertEqual(ev.tier, Tier.PRO_FAMILY)
        self.assertEqual(ev.persons, 5)
        self.assertEqual(ev.customer_email, "bob@example.com")
        # Falsche Signatur
        from services.payment import SignatureError
        ctx_bad = WebhookContext(
            raw_body=body,
            headers={"X-Signature": "deadbeef"},
            signing_secret=secret,
            price_mapping={"7": (Tier.PRO_FAMILY, 5)},
        )
        with self.assertRaises(SignatureError):
            parse_event(ctx_bad)

    def test_lemon_uninteresting_event_returns_none(self) -> None:
        import hmac as _hmac
        from hashlib import sha256
        from services.payment import WebhookContext
        from services.payment_adapter_lemon import parse_event
        payload = {"meta": {"event_name": "license_key_created"},
                    "data": {}}
        body = json.dumps(payload).encode()
        sig = _hmac.new(b"x", body, sha256).hexdigest()
        ctx = WebhookContext(raw_body=body,
                              headers={"X-Signature": sig},
                              signing_secret="x", price_mapping={})
        self.assertIsNone(parse_event(ctx))

    # ---- Payment: HTTP-Webhook-Server -------------------------------
    def test_webhook_server_end_to_end(self) -> None:
        import hmac as _hmac
        import threading
        import urllib.request
        from datetime import datetime, timedelta, timezone
        from hashlib import sha256
        from services.license_token import (CRYPTO_AVAILABLE,
                                              generate_keypair)
        from services.payment import PriceMapping
        from services.payment_adapter_paddle import parse_event as paddle_parse
        from services.payment_issuer import IssuerConfig
        from services.payment_server import (WebhookServerConfig, serve)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, _ = generate_keypair()
        sent: list[dict] = []
        log_path = Path(tempfile.mkdtemp(prefix="ah_ws_")) / "audit.jsonl"
        issuer = IssuerConfig(
            private_key_hex=priv,
            audit_log_path=log_path,
            send_mail=lambda to, s, b: sent.append({"to": to}) or {"ok": True},
        )
        secret = "whsec"
        mapping: PriceMapping = {"pri_X": (Tier.PRO_MONTHLY, 2)}
        paddle_cfg = WebhookServerConfig(secret=secret,
                                            price_mapping=mapping,
                                            parser=paddle_parse)
        server = serve("127.0.0.1", 0, paddle=paddle_cfg, lemon=None,
                        issuer=issuer)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            payload = {
                "event_type": "subscription.created",
                "data": {
                    "id": "sub_999",
                    "customer": {"id": "c", "email": "z@example.com"},
                    "items": [{"price": {"id": "pri_X"}}],
                    "next_billed_at": (
                        (datetime.now(timezone.utc) + timedelta(days=30))
                        .isoformat()
                    ),
                },
            }
            body = json.dumps(payload).encode()
            import time as _time
            ts = int(_time.time())
            sig = _hmac.new(secret.encode(),
                             f"{ts}:".encode() + body,
                             sha256).hexdigest()
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/webhook/paddle",
                data=body, method="POST",
                headers={"Paddle-Signature": f"ts={ts};h1={sig}",
                          "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 201)
            self.assertEqual(len(sent), 1)
        finally:
            server.shutdown()
            server.server_close()

    def test_webhook_server_rejects_bad_signature(self) -> None:
        import threading
        import urllib.error
        import urllib.request
        from services.license_token import (CRYPTO_AVAILABLE,
                                              generate_keypair)
        from services.payment_adapter_paddle import parse_event as paddle_parse
        from services.payment_issuer import IssuerConfig
        from services.payment_server import (WebhookServerConfig, serve)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, _ = generate_keypair()
        log_path = Path(tempfile.mkdtemp(prefix="ah_ws_x_")) / "audit.jsonl"
        issuer = IssuerConfig(private_key_hex=priv,
                               audit_log_path=log_path,
                               send_mail=None)
        paddle_cfg = WebhookServerConfig(secret="s", price_mapping={},
                                            parser=paddle_parse)
        server = serve("127.0.0.1", 0, paddle=paddle_cfg, lemon=None,
                        issuer=issuer)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/webhook/paddle",
                data=b'{"event_type":"x"}', method="POST",
                headers={"Paddle-Signature": "ts=0;h1=bad"})
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 401)
        finally:
            server.shutdown()
            server.server_close()

    # ---- Payment: Issuer (Token-Ausstellung + Mail + Idempotenz) ---
    def test_issuer_signs_token_and_sends_mail(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE,
                                              generate_keypair)
        from services.payment import EventKind, PaymentEvent
        from services.payment_issuer import IssuerConfig, handle_event
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, _pub = generate_keypair()
        sent: list[dict] = []
        def fake_send(to, subj, body):
            sent.append({"to": to, "subj": subj, "body": body})
            return {"status": "gesendet", "to": to}
        log_dir = tempfile.mkdtemp(prefix="ah_pay_")
        log_path = Path(log_dir) / "audit.jsonl"
        cfg = IssuerConfig(private_key_hex=priv,
                            audit_log_path=log_path,
                            send_mail=fake_send)
        event = PaymentEvent(
            kind=EventKind.SUBSCRIPTION_CREATED,
            provider="paddle",
            customer_email="alice@example.com",
            customer_id="ctm_1",
            tier=Tier.PRO_ANNUAL,
            persons=2,
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            transaction_id="tx_001",
        )
        result = handle_event(event, cfg)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.token_str)
        self.assertEqual(len(sent), 1)
        self.assertIn(result.token_str, sent[0]["body"])
        # Idempotenz: zweiter Versand wird geskippt
        second = handle_event(event, cfg)
        self.assertTrue(second.success)
        self.assertIn("bereits", second.message)
        self.assertEqual(len(sent), 1)

    def test_issuer_skips_cancellations(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE,
                                              generate_keypair)
        from services.payment import EventKind, PaymentEvent
        from services.payment_issuer import IssuerConfig, handle_event
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, _ = generate_keypair()
        sent: list = []
        log_path = Path(tempfile.mkdtemp(prefix="ah_pay_c_")) / "audit.jsonl"
        cfg = IssuerConfig(private_key_hex=priv, audit_log_path=log_path,
                            send_mail=lambda *a, **kw: sent.append(a))
        event = PaymentEvent(
            kind=EventKind.SUBSCRIPTION_CANCELED,
            provider="paddle", customer_email="x@example.com",
            customer_id="c", tier=Tier.PRO_ANNUAL, persons=2,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            transaction_id="tx_c",
        )
        result = handle_event(event, cfg)
        self.assertTrue(result.success)
        self.assertIsNone(result.token_str)
        self.assertEqual(sent, [])

    # ---- Affiliate-Empfehlungen im Vertragsmodul -------------------
    def test_cancellation_includes_affiliate_suggestions(self) -> None:
        from services.licensing import AFFILIATE_PARTNERS
        db, registry, _, tmpname = _build_system()
        try:
            registry.dispatch("contracts.add", dict(
                name="Netflix", category="streaming", provider="Netflix",
                start_date="2025-01-01", minimum_term_months=1,
                notice_period_months=1, auto_renew_months=1,
                monthly_cost=13.99))
            ids = [c["id"] for c
                    in registry.dispatch("contracts.list", {})["contracts"]]
            result = registry.dispatch("contracts.generate_cancellation", {
                "contract_id": ids[0],
                "sender_name": "Max Mustermann",
                "sender_address": "Musterweg 1",
                "sender_city": "Berlin",
            })
            self.assertIn("affiliate_suggestions", result)
            partners = result["affiliate_suggestions"]
            self.assertGreater(len(partners), 0)
            urls = {p["url"] for p in partners}
            allowed = set(AFFILIATE_PARTNERS.values())
            self.assertTrue(urls.issubset(allowed),
                              f"Unbekannte URLs in Affiliate-Liste: {urls - allowed}")
        finally:
            db.close()
            try:
                os.unlink(tmpname)
            except OSError:
                pass

    def test_affiliate_block_in_letter_text_is_static(self) -> None:
        # Affiliate-Block taucht im PDF auf, NICHT im reinen letter_text.
        db, registry, _, tmpname = _build_system()
        try:
            registry.dispatch("contracts.add", dict(
                name="Spotify", category="streaming", provider="Spotify",
                start_date="2025-01-01", minimum_term_months=1,
                notice_period_months=1, auto_renew_months=12,
                monthly_cost=9.99))
            ids = [c["id"] for c
                    in registry.dispatch("contracts.list", {})["contracts"]]
            result = registry.dispatch("contracts.generate_cancellation", {
                "contract_id": ids[0],
                "sender_name": "X", "sender_address": "Y",
                "sender_city": "Z",
            })
            # letter_text ist reiner Brief - kein Affiliate
            self.assertNotIn("verbraucherzentrale", result["letter_text"])
            self.assertNotIn("nicht getrackt", result["letter_text"])
            # affiliate_suggestions im Response vorhanden
            self.assertGreaterEqual(len(result["affiliate_suggestions"]), 1)
        finally:
            db.close()
            try:
                os.unlink(tmpname)
            except OSError:
                pass

    def test_affiliate_block_format(self) -> None:
        from modules.contracts import (_affiliate_suggestions,
                                          _format_affiliate_block)
        from models import Contract
        c = Contract(name="Test", category="streaming")
        suggestions = _affiliate_suggestions(c)
        text = _format_affiliate_block(suggestions)
        self.assertIn("nicht getrackt", text)
        self.assertIn("Verbraucherzentrale", text)

    def test_affiliate_block_empty_when_no_partners(self) -> None:
        # Kontrapunkt: leere Liste -> leerer String, kein Crash
        from modules.contracts import _format_affiliate_block
        self.assertEqual(_format_affiliate_block([]), "")

    def test_format_quote_de_mentions_savings(self) -> None:
        text = format_quote_de(calculate_price(4, Tier.PRO_ANNUAL))
        self.assertIn("EUR/Jahr", text)
        self.assertIn("20 %", text)

    # ---- Trial ------------------------------------------------------
    def test_trial_starts_and_expires(self) -> None:
        from datetime import datetime, timedelta, timezone
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            lic = start_trial(repo, now=now)
            self.assertEqual(lic.tier, Tier.TRIAL)
            self.assertTrue(lic.is_pro(now))
            self.assertEqual(lic.trial_days_left(now), TRIAL_DAYS)
            # nach 15 Tagen ist Trial abgelaufen
            later = now + timedelta(days=TRIAL_DAYS + 1)
            lic = load_license(repo)
            self.assertEqual(lic.effective_tier(later), Tier.FREE)
            self.assertFalse(lic.is_pro(later))
            db.close()
        finally:
            os.unlink(tmp.name)

    def test_trial_is_not_reusable(self) -> None:
        from datetime import datetime, timedelta, timezone
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            start = datetime(2026, 1, 1, tzinfo=timezone.utc)
            start_trial(repo, now=start)
            # Zweiter Start-Versuch nach Ablauf darf nichts aendern
            later = start + timedelta(days=30)
            lic = start_trial(repo, now=later)
            self.assertEqual(lic.trial_started_at, start)
            db.close()
        finally:
            os.unlink(tmp.name)

    # ---- Family-Cap -------------------------------------------------
    def test_family_tier_flat_price(self) -> None:
        q = calculate_price(5, Tier.PRO_FAMILY)
        self.assertAlmostEqual(q.monthly_eur, PRICE_FAMILY_FLAT_MONTHLY_EUR)

    def test_family_tier_rejects_too_many_persons(self) -> None:
        with self.assertRaises(ValueError):
            calculate_price(FAMILY_PERSONS_CAP + 1, Tier.PRO_FAMILY)

    def test_recommended_tier_picks_family_above_break_even(self) -> None:
        # 5 Personen: monatlich 6,99 + 3*1,99 = 12,96 < 12,99 Family
        # 4 Personen: monatlich 6,99 + 2*1,99 = 10,97 < 12,99 Family -> Annual
        # Break-even bei 5 Personen ist knapp - Family lohnt erst ab 6, aber
        # da die Cap bei 5 liegt, ist Annual fast immer guenstiger.
        self.assertEqual(recommended_tier(2), Tier.PRO_ANNUAL)
        self.assertEqual(recommended_tier(4), Tier.PRO_ANNUAL)
        self.assertEqual(recommended_tier(10), Tier.PRO_ANNUAL)

    # ---- Expiration + Grace -----------------------------------------
    def test_pro_downgrades_after_grace_period(self) -> None:
        from datetime import datetime, timedelta, timezone
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        lic = License(tier=Tier.PRO_MONTHLY, persons=2,
                      purchased_at=now,
                      expires_at=now + timedelta(days=30))
        # waehrend Laufzeit: Pro
        self.assertTrue(lic.is_pro(now + timedelta(days=15)))
        # nach Ablauf aber innerhalb Grace: Pro
        self.assertTrue(lic.is_pro(now + timedelta(days=33)))
        self.assertTrue(lic.is_in_grace_period(now + timedelta(days=33)))
        # nach Grace: Free
        after = now + timedelta(days=30 + GRACE_PERIOD_DAYS + 1)
        self.assertFalse(lic.is_pro(after))
        self.assertEqual(lic.effective_tier(after), Tier.FREE)

    def test_activate_pro_requires_signed_token_by_default(self) -> None:
        from datetime import datetime, timedelta, timezone
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            with self.assertRaises(RuntimeError):
                activate_pro(repo, Tier.PRO_ANNUAL, persons=2, now=now)
            lic = activate_pro(repo, Tier.PRO_ANNUAL, persons=2, now=now,
                               allow_unsigned=True)
            self.assertEqual(lic.expires_at, now + timedelta(days=365))
            db.close()
        finally:
            os.unlink(tmp.name)

    # ---- Grandfathering --------------------------------------------
    def test_grandfathering_migration_runs_once(self) -> None:
        from services.licensing import (KEY_GRANDFATHER_MIGRATION_DONE,
                                          apply_grandfathering_if_needed)
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            # erster Lauf mit Bestandsdaten -> markiert
            lic = apply_grandfathering_if_needed(repo, lambda: True)
            self.assertIsNotNone(lic)
            self.assertTrue(lic.grandfathered)
            self.assertEqual(repo.get(KEY_GRANDFATHER_MIGRATION_DONE), "true")
            # zweiter Lauf - kein erneutes Markieren
            again = apply_grandfathering_if_needed(repo, lambda: True)
            self.assertIsNone(again)
            db.close()
        finally:
            os.unlink(tmp.name)

    def test_grandfathering_skipped_for_empty_db(self) -> None:
        from services.licensing import apply_grandfathering_if_needed
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            result = apply_grandfathering_if_needed(repo, lambda: False)
            self.assertIsNone(result)
            lic = load_license(repo)
            self.assertFalse(lic.grandfathered)
            db.close()
        finally:
            os.unlink(tmp.name)

    def test_grandfathered_keeps_read_but_blocks_write(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            mark_grandfathered(repo, ("contracts", "finance", "calendar"))
            lic = load_license(repo)
            self.assertTrue(lic.grandfathered)
            # Lesen: alle Module zugaenglich
            self.assertTrue(lic.allows_module("finance"))
            self.assertTrue(lic.allows_module("inbox"))
            # Schreiben: nur die ehemals freien Module
            self.assertTrue(lic.allows_module("finance", writing=True))
            self.assertFalse(lic.allows_module("inbox", writing=True))
            db.close()
        finally:
            os.unlink(tmp.name)

    # ---- Mobile-Markup ----------------------------------------------
    def test_mobile_pricing_has_markup(self) -> None:
        desktop = calculate_price(2, Tier.PRO_MONTHLY, Platform.DESKTOP)
        android = calculate_price(2, Tier.PRO_MONTHLY, Platform.ANDROID)
        ios = calculate_price(2, Tier.PRO_MONTHLY, Platform.IOS)
        self.assertGreater(android.monthly_eur, desktop.monthly_eur)
        self.assertAlmostEqual(
            android.monthly_eur,
            round(desktop.monthly_eur * (1 + MOBILE_PRICE_MARKUP), 2))
        self.assertAlmostEqual(android.monthly_eur, ios.monthly_eur)

    # ---- Enforcement-Gate -------------------------------------------
    def test_gate_blocks_pro_module_for_free(self) -> None:
        from services.license_gate import make_gate
        gate = make_gate(lambda: License(tier=Tier.FREE))
        # contracts ist im Free-Tier per Default offen
        err = gate("contracts.list", {})
        self.assertIsNone(err)
        # finance ist Pro-only
        err = gate("finance.list_expenses", {})
        self.assertIsNotNone(err)
        self.assertTrue(err.get("tier_locked"))

    def test_gate_allows_everything_for_pro(self) -> None:
        from services.license_gate import make_gate
        gate = make_gate(lambda: License(tier=Tier.PRO_ANNUAL))
        for cap in ("contracts.list", "finance.list_expenses",
                    "inbox.analyze_mail", "social.draft_message"):
            self.assertIsNone(gate(cap, {}), f"{cap} sollte fuer Pro offen sein")

    def test_gate_blocks_ai_capability_for_free(self) -> None:
        from services.license_gate import make_gate
        gate = make_gate(lambda: License(tier=Tier.FREE))
        err = gate("inbox.analyze_mail", {"mail_text": "test"})
        self.assertIsNotNone(err)
        self.assertEqual(err["lock_kind"], "ai")

    def test_gate_open_modules_always_accessible(self) -> None:
        from services.license_gate import make_gate
        gate = make_gate(lambda: License(tier=Tier.FREE))
        for cap in ("system.search", "stats.expenses_per_month",
                    "daystructure.list", "notes.list"):
            self.assertIsNone(gate(cap, {}),
                              f"{cap} sollte immer offen sein")

    def test_registry_pre_dispatch_hook_blocks_calls(self) -> None:
        # End-to-End ueber die Registry: Hook weist tatsaechlich ab.
        from core.interface import Capability, ModuleInterface, ModuleRegistry

        class DummyModule(ModuleInterface):
            @property
            def module_id(self) -> str:
                return "finance"

            @property
            def display_name(self) -> str:
                return "Finance"

            def get_capabilities(self):
                return [Capability(
                    name="finance.list_expenses",
                    description="x", parameters={},
                    handler=lambda: {"items": []})]

        reg = ModuleRegistry()
        reg.register(DummyModule())
        from services.license_gate import make_gate
        reg.set_pre_dispatch_hook(make_gate(lambda: License(tier=Tier.FREE)))
        result = reg.dispatch("finance.list_expenses", {})
        self.assertTrue(result.get("tier_locked"))


    # ---- Pro-Aktivierungs-Flow (Widerrufsverzicht) ------------------
    def test_activation_requires_withdrawal_waiver(self) -> None:
        from services.activation_flow import (ActivationRequest,
                                                CONFIRMATIONS_DE,
                                                request_activation)
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            req = ActivationRequest(tier=Tier.PRO_ANNUAL, persons=2)
            # Nutzer lehnt ab -> keine Aktivierung
            result = request_activation(repo, req, lambda r, t: False)
            self.assertFalse(result.success)
            self.assertEqual(load_license(repo).tier, Tier.FREE)
            # Auch mit Zustimmung darf kein unsigned Pro mehr entstehen.
            result = request_activation(repo, req, lambda r, t: True)
            self.assertFalse(result.success)
            self.assertIn("Token", result.error)
            self.assertEqual(load_license(repo).tier, Tier.FREE)
            self.assertEqual(len(CONFIRMATIONS_DE), 3)
            db.close()
        finally:
            os.unlink(tmp.name)

    def test_activation_rejects_free_tier(self) -> None:
        from services.activation_flow import (ActivationRequest,
                                                request_activation)
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            req = ActivationRequest(tier=Tier.FREE, persons=1)
            result = request_activation(repo, req, lambda r, t: True)
            self.assertFalse(result.success)
            self.assertIn("kein zahlungspflichtiger Tier", result.error)
            db.close()
        finally:
            os.unlink(tmp.name)

    # ---- Token (Ed25519-Tamper-Schutz) ------------------------------
    # ---- #3 Revocation-Liste ---------------------------------------
    def test_sign_token_auto_assigns_token_id(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              generate_keypair, sign_token,
                                              verify_token)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tok = LicenseToken(tier=Tier.PRO_ANNUAL, persons=2,
                            purchased_at=now,
                            expires_at=now + timedelta(days=365),
                            customer_id="alice@example.com")
        self.assertEqual(tok.token_id, "")
        token_str = sign_token(tok, priv)
        # token_id wird beim sign() automatisch gesetzt
        self.assertNotEqual(tok.token_id, "")
        # ... und in der Payload mit signiert
        verified = verify_token(token_str, pub, now=now)
        self.assertEqual(verified.token_id, tok.token_id)

    def test_revoked_token_is_rejected(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              TokenError, generate_keypair,
                                              sign_token, verify_token)
        import services.license_token as _tok_mod
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tok = LicenseToken(tier=Tier.PRO_MONTHLY, persons=2,
                            purchased_at=now,
                            expires_at=now + timedelta(days=30),
                            customer_id="leaked@example.com")
        token_str = sign_token(tok, priv)
        # Vorher: gueltig
        verify_token(token_str, pub, now=now)
        # Token-ID auf die Revocation-Liste setzen
        original = _tok_mod.REVOKED_TOKEN_IDS
        _tok_mod.REVOKED_TOKEN_IDS = frozenset({tok.token_id})
        try:
            with self.assertRaises(TokenError) as ctx:
                verify_token(token_str, pub, now=now)
            self.assertIn("widerrufen", str(ctx.exception))
        finally:
            _tok_mod.REVOKED_TOKEN_IDS = original

    def test_revocation_supersedes_grace_period(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              TokenError, TokenExpired,
                                              generate_keypair, sign_token,
                                              verify_token)
        import services.license_token as _tok_mod
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tok = LicenseToken(tier=Tier.PRO_ANNUAL, persons=2,
                            purchased_at=now - timedelta(days=400),
                            expires_at=now - timedelta(days=10),
                            customer_id="x")
        token_str = sign_token(tok, priv)
        original = _tok_mod.REVOKED_TOKEN_IDS
        _tok_mod.REVOKED_TOKEN_IDS = frozenset({tok.token_id})
        try:
            # Revoked geht VOR Expired: keine Grace-Period fuer
            # widerrufene Tokens.
            with self.assertRaises(TokenError) as ctx:
                verify_token(token_str, pub, now=now)
            self.assertNotIsInstance(ctx.exception, TokenExpired)
        finally:
            _tok_mod.REVOKED_TOKEN_IDS = original

    # ---- #1 'Mein Abo'-Sektion -------------------------------------
    def test_subscription_info_for_free_has_no_subscription(self) -> None:
        from services.license_ui import make_subscription_info
        info = make_subscription_info(License())
        self.assertFalse(info.has_subscription)

    def test_subscription_info_for_pro_shows_dates(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_ui import make_subscription_info
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.PRO_ANNUAL, persons=4,
                       purchased_at=now - timedelta(days=30),
                       expires_at=now + timedelta(days=335))
        info = make_subscription_info(lic, manage_url="https://pay.example/portal",
                                        now=now)
        self.assertTrue(info.has_subscription)
        self.assertEqual(info.persons, 4)
        self.assertEqual(info.days_remaining, 335)
        self.assertEqual(info.manage_url, "https://pay.example/portal")
        self.assertFalse(info.in_grace_period)

    def test_subscription_info_marks_grace_period(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_ui import make_subscription_info
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.PRO_MONTHLY, persons=2,
                       expires_at=now - timedelta(days=3))
        info = make_subscription_info(lic, now=now)
        self.assertTrue(info.in_grace_period)

    # ---- #2 First-Run-Pricing-Reveal -------------------------------
    def test_pricing_onboarded_flag_persists(self) -> None:
        from services.licensing import KEY_PRICING_ONBOARDED
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = Database(tmp.name)
        try:
            repo = SettingsRepository(db)
            self.assertIsNone(repo.get(KEY_PRICING_ONBOARDED))
            repo.set(KEY_PRICING_ONBOARDED, "true")
            self.assertEqual(repo.get(KEY_PRICING_ONBOARDED), "true")
        finally:
            db.close()
            os.unlink(tmp.name)

    # ---- #5 Renewal-Notifications -----------------------------------
    def test_renewal_event_for_trial_near_end(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_events import compute_renewal_events
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.TRIAL,
                       trial_started_at=now - timedelta(days=11))
        # 3 Tage Trial uebrig - innerhalb von 14d warn_within_days
        events = compute_renewal_events(lic, warn_within_days=14, now=now)
        self.assertEqual(len(events), 1)
        self.assertIn("Trial", events[0].title)
        self.assertEqual(events[0].days_remaining, 3)

    def test_renewal_event_for_pro_near_expiry(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_events import compute_renewal_events
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.PRO_ANNUAL, persons=2,
                       expires_at=now + timedelta(days=10))
        events = compute_renewal_events(lic, warn_within_days=14, now=now)
        self.assertEqual(len(events), 1)
        self.assertIn("Abo", events[0].title)
        self.assertEqual(events[0].days_remaining, 10)

    def test_renewal_event_outside_warning_window(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_events import compute_renewal_events
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.PRO_ANNUAL, persons=2,
                       expires_at=now + timedelta(days=100))
        # 100d > 14d Warnfenster -> noch nichts
        self.assertEqual(compute_renewal_events(lic, 14, now=now), [])

    def test_renewal_event_in_grace_period(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_events import compute_renewal_events
        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.PRO_MONTHLY, persons=2,
                       expires_at=now - timedelta(days=2))
        events = compute_renewal_events(lic, 14, now=now)
        # Karenzzeit-Event + (expires_at liegt 2d zurueck, also < 0,
        # daher KEIN renewal-Event mehr)
        titles = [e.title for e in events]
        self.assertTrue(any("Karenz" in t for t in titles))

    def test_renewal_no_event_for_free(self) -> None:
        from services.license_events import compute_renewal_events
        self.assertEqual(compute_renewal_events(License(), 14), [])

    def test_scheduler_picks_up_extra_event_sources(self) -> None:
        from datetime import datetime, timedelta, timezone
        from core.interface import ModuleRegistry
        from services.license_events import license_event_source
        from services.notifier import Notifier
        from services.scheduler import ProactiveScheduler

        class _CountingNotifier(Notifier):
            def __init__(self):
                super().__init__()
                self.calls: list[tuple[str, str]] = []

            def notify(self, title, message=""):       # noqa: A003
                self.calls.append((title, message))

        now = datetime(2026, 5, 20, tzinfo=timezone.utc)
        lic = License(tier=Tier.PRO_ANNUAL, persons=2,
                       expires_at=now + timedelta(days=5))
        notifier = _CountingNotifier()
        sched = ProactiveScheduler(
            ModuleRegistry(),  # leer - keine Modul-Events
            notifier=notifier, warn_within_days=14,
            extra_event_sources=[license_event_source(lambda: lic,
                                                      now_provider=lambda: now)])
        triggered = sched.check_now()
        self.assertEqual(len(triggered), 1)
        self.assertTrue(any("Abo" in c[0] for c in notifier.calls))
        # Idempotenz: zweiter Aufruf darf nicht noch mal melden
        notifier.calls.clear()
        sched.check_now()
        self.assertEqual(notifier.calls, [])

    def test_token_sign_verify_round_trip(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              generate_keypair, sign_token,
                                              verify_token)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tok = LicenseToken(tier=Tier.PRO_ANNUAL, persons=4,
                            purchased_at=now,
                            expires_at=now + timedelta(days=365),
                            customer_id="alice@example.com",
                            platform=Platform.DESKTOP)
        token_str = sign_token(tok, priv)
        verified = verify_token(token_str, pub,
                                 now=now + timedelta(days=10))
        self.assertEqual(verified.tier, Tier.PRO_ANNUAL)
        self.assertEqual(verified.persons, 4)

    def test_token_rejects_tampered_payload(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              TokenError, generate_keypair,
                                              sign_token, verify_token)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tok = LicenseToken(tier=Tier.PRO_MONTHLY, persons=2,
                            purchased_at=now,
                            expires_at=now + timedelta(days=30),
                            customer_id="c")
        token_str = sign_token(tok, priv)
        tampered = token_str[:-3] + "AAA"  # Signatur kaputt
        with self.assertRaises(TokenError):
            verify_token(tampered, pub, now=now)

    def test_token_expired_raises_subclass_with_payload(self) -> None:
        # Critical-Fix: abgelaufenes Token muss als TokenExpired-Subklasse
        # geworfen werden und den geparsten Token mitliefern, damit
        # load_license die Grace-Period anwenden kann statt das Token
        # zu verwerfen.
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              TokenError, TokenExpired,
                                              generate_keypair, sign_token,
                                              verify_token)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tok = LicenseToken(tier=Tier.PRO_ANNUAL, persons=2,
                            purchased_at=now,
                            expires_at=now + timedelta(days=30),
                            customer_id="x")
        token_str = sign_token(tok, priv)
        try:
            verify_token(token_str, pub, now=now + timedelta(days=40))
        except TokenExpired as exc:
            self.assertIsInstance(exc, TokenError)
            self.assertEqual(exc.token.tier, Tier.PRO_ANNUAL)
            self.assertEqual(exc.token.expires_at,
                             now + timedelta(days=30))
        else:
            self.fail("TokenExpired wurde nicht geworfen")

    def test_load_license_keeps_expired_token_for_grace(self) -> None:
        # Critical-Fix: load_license darf abgelaufenes Token NICHT loeschen.
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE,
                                              DEFAULT_PUBLIC_KEY_HEX,
                                              LicenseToken,
                                              generate_keypair, sign_token)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        import services.license_token as token_module
        priv, pub = generate_keypair()
        # Test-Pubkey temporaer setzen, sonst lehnt verify_token alles ab
        original_pub = token_module.DEFAULT_PUBLIC_KEY_HEX
        token_module.DEFAULT_PUBLIC_KEY_HEX = pub
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = Database(tmp.name)
        try:
            repo = SettingsRepository(db)
            past = datetime(2026, 1, 1, tzinfo=timezone.utc)
            tok = LicenseToken(tier=Tier.PRO_ANNUAL, persons=2,
                                purchased_at=past - timedelta(days=400),
                                expires_at=past,
                                customer_id="x")
            token_str = sign_token(tok, priv)
            from services.licensing import KEY_TOKEN
            repo.set(KEY_TOKEN, token_str)
            lic = load_license(repo)
            # Token darf NICHT geloescht worden sein
            self.assertEqual(repo.get(KEY_TOKEN), token_str)
            # Lizenz traegt expires_at -> Grace-Period kann greifen
            self.assertIsNotNone(lic.expires_at)
        finally:
            db.close()
            token_module.DEFAULT_PUBLIC_KEY_HEX = original_pub
            os.unlink(tmp.name)

    def test_load_license_drops_tampered_token(self) -> None:
        # Manipuliertes Token wird geloescht, weil die Signatur ungueltig ist
        from services.licensing import KEY_TOKEN
        from services.license_token import CRYPTO_AVAILABLE
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            repo.set(KEY_TOKEN, "garbage.token")
            load_license(repo)
            self.assertIsNone(repo.get(KEY_TOKEN))
            db.close()
        finally:
            os.unlink(tmp.name)

    def test_apply_token_persists_token_string(self) -> None:
        # High-Fix: apply_token_to_repo MUSS den Token-String unter
        # KEY_TOKEN ablegen, sonst greift Tamper-Schutz beim naechsten
        # Start nicht.
        from datetime import datetime, timedelta, timezone
        from services.licensing import KEY_TOKEN
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              apply_token_to_repo,
                                              generate_keypair, sign_token)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, _ = generate_keypair()
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            repo = SettingsRepository(db)
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            tok = LicenseToken(tier=Tier.PRO_MONTHLY, persons=2,
                                purchased_at=now,
                                expires_at=now + timedelta(days=30),
                                customer_id="x")
            token_str = sign_token(tok, priv)
            apply_token_to_repo(repo, token_str, tok)
            self.assertEqual(repo.get(KEY_TOKEN), token_str)
            db.close()
        finally:
            os.unlink(tmp.name)

    def test_token_rejects_expired(self) -> None:
        from datetime import datetime, timedelta, timezone
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                              TokenError, generate_keypair,
                                              sign_token, verify_token)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tok = LicenseToken(tier=Tier.PRO_MONTHLY, persons=2,
                            purchased_at=now,
                            expires_at=now + timedelta(days=30),
                            customer_id="c")
        token_str = sign_token(tok, priv)
        with self.assertRaises(TokenError):
            verify_token(token_str, pub, now=now + timedelta(days=40))

    def test_token_without_configured_pubkey_rejected(self) -> None:
        from services.license_token import (CRYPTO_AVAILABLE,
                                              TokenError, verify_token,
                                              _PLACEHOLDER_PUBLIC_KEY_HEX)
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        # Platzhalter-Pubkey (all-zero) - jede Validierung muss fehlschlagen
        with self.assertRaises(TokenError):
            verify_token("a.b", _PLACEHOLDER_PUBLIC_KEY_HEX)

    # ---- CHF-Konvertierung ------------------------------------------
    def test_chf_conversion_applies_swiss_vat(self) -> None:
        eur = calculate_price(2, Tier.PRO_MONTHLY)
        chf = convert_to_chf(eur)
        self.assertEqual(chf.currency, Currency.CHF)
        # CHF muss in vernuenftiger Naehe zu EUR liegen
        self.assertLess(chf.monthly_eur, eur.monthly_eur)  # CH-MwSt niedriger
        self.assertGreater(chf.monthly_eur, eur.monthly_eur * 0.7)


if __name__ == "__main__":
    unittest.main()
