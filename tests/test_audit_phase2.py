"""
Regressionstests fuer die Befunde des Sicherheits-/Korrektheits-Audits
(Phase 2 der Release-Readiness-Arbeit).

Abgedeckt:

  * database.complete_task klemmt interval_days defensiv auf >=1
    (frueher Endlosschleife / Thread-Freeze bei <=0 aus Sync/Manuell).
  * payment_adapter_play verhindert Tier-Escalation auch dann, wenn die
    Play-Verifikation KEINE Produkt-ID liefert (leere product_id wurde
    bisher durchgewunken -> Monthly-Token als Family einreichbar).
  * license_token.verify_token weist persons < 1 ab (Issuer-Bug-Schutz).
  * payment_issuer: Idempotenz faellt bei Lese-Fehlern CLOSED und ein
    paralleler Retry derselben transaction_id stellt nicht doppelt aus.
  * export._write neutralisiert CSV-Formel-Injection (=,+,-,@,Tab,CR).
  * inbox._extract_euro liest Betraege mit Tausender-Trenner korrekt
    (1.299,99 EUR -> 1299.99 statt 299.99).
  * scheduler dedupliziert Erinnerungen auch unter parallelem check_now()
    (Lock um _seen).

Die DB-Atomicity-Klammern (add_task/delete_member/update_cost/wipe_all_data
unter db.lock) sind verhaltenswahrend und werden funktional von den
bestehenden Suiten (test_smoke/test_integration, test_audit_fixes) gedeckt.
"""
from __future__ import annotations

import csv
import shutil
import tempfile
import threading
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


# ---------------------------------------------------------------------
# database.complete_task: kein Freeze bei interval_days <= 0
# ---------------------------------------------------------------------
class TestCompleteTaskIntervalClamp(unittest.TestCase):
    def setUp(self) -> None:
        from database import Database, FamilyRepository
        self.root = Path(tempfile.mkdtemp(prefix="ah_p2_iv_"))
        self.db = Database(str(self.root / "t.db"))
        self.fam = FamilyRepository(self.db)

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.root, ignore_errors=True)

    def _task_with_interval(self, interval: int):
        from models import FamilyMember, HouseholdTask
        m = self.fam.add_member(FamilyMember(name="Anna", role="adult"))
        # Basis-Datum EINMAL festhalten, damit die Assertion nicht von einem
        # erneuten date.today() (Mitternachtsgrenze) abhaengt.
        self._base = date.today()
        # add_task validiert interval_days NICHT (nur die Capability-Layer
        # tun das) - hier simulieren wir bewusst einen aus Sync/Manuell
        # stammenden Bad-Value.
        return self.fam.add_task(HouseholdTask(
            title="Muell", interval_days=interval,
            rotation=[m.id], current_index=0,
            next_due=self._base))

    def _complete_with_timeout(self, task_id: int, timeout: float = 10.0):
        out: dict = {}

        def run():
            out["task"] = self.fam.complete_task(task_id)

        th = threading.Thread(target=run, daemon=True)
        th.start()
        th.join(timeout)
        self.assertFalse(
            th.is_alive(),
            "complete_task darf bei interval_days<=0 nicht endlos laufen")
        return out["task"]

    def test_zero_interval_does_not_hang(self) -> None:
        task = self._task_with_interval(0)
        updated = self._complete_with_timeout(task.id)
        self.assertGreaterEqual(updated.next_due, self._base + timedelta(days=1),
                                "next_due muss um >=1 Tag vorruecken")

    def test_negative_interval_does_not_hang(self) -> None:
        task = self._task_with_interval(-5)
        updated = self._complete_with_timeout(task.id)
        self.assertGreaterEqual(updated.next_due, self._base + timedelta(days=1))


# ---------------------------------------------------------------------
# Play-Adapter: Anti-Tier-Escalation auch bei leerer product_id
# ---------------------------------------------------------------------
class TestPlayNoEscalationOnEmptyProduct(unittest.TestCase):
    def test_empty_verified_product_rejected(self) -> None:
        from services.payment_adapter_play import (DEFAULT_PLAY_SKU_MAPPING,
                                                    PlayVerification,
                                                    parse_play_purchase)

        # Verifikation ist gueltig, meldet aber KEINE Produkt-ID
        # (z.B. lineItems leer). Client behauptet das teure Family-SKU.
        def verifier(pkg, pid, tok):
            return PlayVerification(valid=True, product_id="",
                                    order_id="GPA.X")

        event = parse_play_purchase(
            {"productId": "zunarodo_pro_family", "purchaseToken": "tok"},
            package_name="de.alltagshelfer.alltagshelfer",
            sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
            verifier=verifier)
        self.assertIsNone(
            event, "leere product_id darf KEIN (eskaliertes) Token erzeugen")

    def test_matching_product_still_accepted(self) -> None:
        from services.payment_adapter_play import (DEFAULT_PLAY_SKU_MAPPING,
                                                    PlayVerification,
                                                    parse_play_purchase)

        def verifier(pkg, pid, tok):
            return PlayVerification(valid=True, product_id=pid,
                                    order_id="GPA.Y")

        event = parse_play_purchase(
            {"productId": "zunarodo_pro_monthly", "purchaseToken": "tok"},
            package_name="de.alltagshelfer.alltagshelfer",
            sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
            verifier=verifier)
        self.assertIsNotNone(event)


# ---------------------------------------------------------------------
# license_token: persons < 1 wird abgewiesen
# ---------------------------------------------------------------------
class TestTokenPersonsLowerBound(unittest.TestCase):
    def test_zero_persons_rejected(self) -> None:
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                             TokenError, generate_keypair,
                                             sign_token, verify_token)
        from services.licensing import Platform, Tier
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        token = LicenseToken(
            tier=Tier.PRO_FAMILY, persons=0,
            purchased_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            customer_id="x@example.com", platform=Platform.DESKTOP)
        token_str = sign_token(token, priv)
        with self.assertRaises(TokenError):
            verify_token(token_str, pub)

    def test_valid_persons_accepted(self) -> None:
        from services.license_token import (CRYPTO_AVAILABLE, LicenseToken,
                                             generate_keypair, sign_token,
                                             verify_token)
        from services.licensing import Platform, Tier
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        priv, pub = generate_keypair()
        token = LicenseToken(
            tier=Tier.PRO_FAMILY, persons=2,
            purchased_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            customer_id="x@example.com", platform=Platform.DESKTOP)
        verified = verify_token(sign_token(token, priv), pub)
        self.assertEqual(verified.persons, 2)


# ---------------------------------------------------------------------
# payment_issuer: Idempotenz fail-closed + kein Doppel-Issue parallel
# ---------------------------------------------------------------------
class TestIssuerIdempotency(unittest.TestCase):
    def setUp(self) -> None:
        from services.license_token import CRYPTO_AVAILABLE, generate_keypair
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography nicht verfuegbar")
        self.root = Path(tempfile.mkdtemp(prefix="ah_p2_iss_"))
        self.priv, _pub = generate_keypair()

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _event(self, tx: str):
        from services.licensing import Tier
        from services.payment import EventKind, PaymentEvent
        return PaymentEvent(
            kind=EventKind.SUBSCRIPTION_CREATED, provider="paddle",
            customer_email="alice@example.com", customer_id="ctm_1",
            tier=Tier.PRO_ANNUAL, persons=2,
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            transaction_id=tx)

    def test_unreadable_audit_log_fails_closed(self) -> None:
        from services.payment_issuer import IssuerConfig, handle_event
        # Audit-Pfad ist ein Verzeichnis -> open("r") wirft OSError.
        log_path = self.root / "audit_dir"
        log_path.mkdir()
        cfg = IssuerConfig(private_key_hex=self.priv, audit_log_path=log_path,
                           send_mail=None)
        result = handle_event(self._event("tx_io"), cfg)
        self.assertFalse(result.success,
                         "bei nicht lesbarem Audit-Log NICHT ausstellen")
        self.assertIsNone(result.token_str)

    def test_parallel_retries_issue_only_once(self) -> None:
        from services.payment_issuer import IssuerConfig, handle_event
        log_path = self.root / "audit.jsonl"
        entered = threading.Event()
        release = threading.Event()
        sent: list = []

        def slow_mail(to, subj, body):
            entered.set()
            release.wait(5)
            sent.append(body)
            return {"status": "ok"}

        cfg = IssuerConfig(private_key_hex=self.priv, audit_log_path=log_path,
                           send_mail=slow_mail)
        event = self._event("tx_dup")
        results: dict = {}

        def call(name):
            results[name] = handle_event(event, cfg)

        ta = threading.Thread(target=call, args=("a",), daemon=True)
        ta.start()
        # Warten, bis A im (langsamen) Mail-Versand steckt und die
        # Transaktion damit bereits "geclaimed" hat.
        self.assertTrue(entered.wait(5), "Thread A erreichte den Mail-Versand nicht")
        tb = threading.Thread(target=call, args=("b",), daemon=True)
        tb.start()
        tb.join(5)
        self.assertFalse(tb.is_alive(), "Thread B haengt - Claim greift nicht")
        release.set()
        ta.join(5)

        issued = [r for r in results.values() if r.token_str]
        self.assertEqual(len(issued), 1, "nur EIN Token darf ausgestellt werden")
        self.assertEqual(len(sent), 1, "nur EINE Mail darf versendet werden")
        self.assertIsNone(results["b"].token_str)
        self.assertTrue(results["b"].success)

    def test_play_path_reissues_token_on_duplicate(self) -> None:
        # Synchroner Play-Pfad (dedupe=False): das Token IST die Antwort,
        # also MUSS auch ein erneuter Aufruf mit derselben transaction_id ein
        # Token liefern - sonst bekaeme der Client eine 201-Erfolgsantwort
        # ohne Token und koennte die Lizenz nie aktivieren.
        from services.payment_issuer import IssuerConfig, handle_event
        cfg = IssuerConfig(private_key_hex=self.priv,
                           audit_log_path=self.root / "audit_play.jsonl",
                           send_mail=None)
        event = self._event("tx_play")
        r1 = handle_event(event, cfg, dedupe=False)
        r2 = handle_event(event, cfg, dedupe=False)
        self.assertIsNotNone(r1.token_str)
        self.assertIsNotNone(
            r2.token_str,
            "Play-Duplikat muss erneut ein Token liefern (kein Null-Token)")


# ---------------------------------------------------------------------
# export: CSV-Formel-Injection wird neutralisiert
# ---------------------------------------------------------------------
class TestCsvInjection(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ah_p2_csv_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_sanitize_cell(self) -> None:
        from services.export import _sanitize_cell
        for danger in ("=SUM(A1)", "+1", "-2", "@cmd", "\tx", "\rx"):
            self.assertEqual(_sanitize_cell(danger)[0], "'",
                             f"{danger!r} muss neutralisiert werden")
        self.assertEqual(_sanitize_cell("normal"), "normal")
        self.assertEqual(_sanitize_cell("ok=mid"), "ok=mid")  # = nicht am Anfang
        self.assertEqual(_sanitize_cell(12.5), 12.5)          # Zahlen unveraendert
        self.assertEqual(_sanitize_cell(""), "")

    def test_write_neutralizes_formula(self) -> None:
        from services.export import _write
        path = self.root / "out.csv"
        _write(path, ["name"], [["=HYPERLINK(<url>)"], ["harmlos"]])
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh, delimiter=";"))
        self.assertEqual(rows[1][0][0], "'",
                         "Formel-Zelle muss mit Hochkomma beginnen")
        self.assertEqual(rows[2][0], "harmlos")

    def test_export_import_roundtrip_is_lossless(self) -> None:
        # Die Hochkomma-Neutralisierung darf den App-eigenen Re-Import nicht
        # verfaelschen: negative Betraege und Lead-Zeichen-Texte muessen 1:1
        # zurueckkommen (Regression: '-5.00' wurde sonst zu 0.0).
        from services.export import _sanitize_cell, _write
        from services.import_csv import (_read_rows, _safe_float,
                                          _unsanitize_cell)
        for v in ["-5.00", "@home", "+49 170", "=cmd", "\tx", "normal",
                  "'tis", "12.50"]:
            self.assertEqual(_unsanitize_cell(_sanitize_cell(v)), v,
                             f"Roundtrip fuer {v!r} nicht verlustfrei")
        self.assertEqual(
            _safe_float(_unsanitize_cell(_sanitize_cell("-5.00"))), -5.0,
            "negativer Betrag muss nach Re-Import erhalten bleiben")
        # End-to-End ueber Datei: Schreiben (sanitisiert) -> Lesen (entschaerft)
        path = self.root / "rt.csv"
        _write(path, ["betrag", "name"], [["-5.00", "@home"], ["3.00", "ok"]])
        rows = _read_rows(path)
        self.assertEqual(rows[0]["betrag"], "-5.00")
        self.assertEqual(rows[0]["name"], "@home")


# ---------------------------------------------------------------------
# inbox._extract_euro: Tausender-Trenner
# ---------------------------------------------------------------------
class TestExtractEuro(unittest.TestCase):
    def test_amounts(self) -> None:
        from modules.inbox import _extract_euro
        cases = {
            "Ihr neuer Preis: 1.299,99 EUR": 1299.99,
            "Summe 1.299,00 EUR": 1299.0,
            "Betrag 12,99 EUR": 12.99,
            "EUR 12.99": 12.99,
            "Kosten 1.000,50 EUR": 1000.5,
            "EUR 1.299": 1299.0,            # deutscher Tausender, ohne Dezimal
            "Total 2.675,00 EUR": 2675.0,
        }
        for text, expected in cases.items():
            self.assertAlmostEqual(_extract_euro(text), expected, places=2,
                                   msg=f"falscher Betrag fuer {text!r}")

    def test_no_amount(self) -> None:
        from modules.inbox import _extract_euro
        self.assertIsNone(_extract_euro("kein Betrag hier"))


# ---------------------------------------------------------------------
# scheduler: Dedup haelt auch unter parallelem check_now()
# ---------------------------------------------------------------------
class TestSchedulerSeenLock(unittest.TestCase):
    class _SlowSeen(set):
        """set, dessen Mitgliedschaftspruefung kurz blockiert.

        Vergroessert das Fenster zwischen `key in _seen` und `_seen.add(key)`,
        sodass der Test ohne Lock (alter Code) tatsaechlich doppelt meldet -
        und nur mit Lock (neuer Code) deterministisch genau einmal. So pinnt
        der Test den Fix, statt auf der alten Version ebenfalls zu bestehen.
        """

        def __contains__(self, item):
            import time
            time.sleep(0.05)
            return super().__contains__(item)

    def _make(self):
        from services.scheduler import ProactiveScheduler

        class _FakeRegistry:
            def collect_events(self, warn_within_days):
                from models import Event
                return [Event(module_id="mod", module_name="Modul",
                              title="Erinnerung", due_date=date.today(),
                              days_remaining=0)]

        calls: list = []
        lock = threading.Lock()

        class _FakeNotifier:
            def notify(self, title, message=""):
                with lock:
                    calls.append(title)

        sched = ProactiveScheduler(_FakeRegistry(), notifier=_FakeNotifier())
        # Langsame Mitgliedschaftspruefung injizieren (erzwingt die Race).
        sched._seen = self._SlowSeen(sched._seen)
        return sched, calls

    def test_parallel_check_now_notifies_once(self) -> None:
        sched, calls = self._make()
        threads = [threading.Thread(target=sched.check_now) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(5)
        self.assertEqual(len(calls), 1,
                         "dieselbe Erinnerung darf trotz paralleler Laeufe "
                         "nur einmal gemeldet werden")


if __name__ == "__main__":
    unittest.main()
