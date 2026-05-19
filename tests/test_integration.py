"""
Integrations-Tests mit Mocks fuer Drittsysteme.

Echte Drittsysteme (Gemini-API, SMTP-Server, IMAP-Server, Drucker,
Tesseract) sind hier nicht vorausgesetzt - wir testen die Protokoll-
Aufrufe gegen unittest.mock und das Verhalten unserer App, wenn das
Gegenueber bestimmte Antworten liefert.

Wo eine echte Bibliothek installiert ist UND ein API-Key in der
Umgebung gesetzt ist (GOOGLE_API_KEY / SMTP_TEST_*), kommen ergaenzende
Tests dazu - sonst skipped die Suite sie automatisch.
"""
from __future__ import annotations

import os
import socket
import ssl
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest import mock


# ---------------------------------------------------------------------
#  A: SMTP-Versand mit gemockter smtplib
# ---------------------------------------------------------------------
class TestSmtpVersand(unittest.TestCase):

    def test_send_smtp_calls_protocol(self) -> None:
        from services.output import OutputService, SmtpConfig
        cfg = SmtpConfig(host="smtp.example.com", port=587,
                          username="me", password="secret",
                          sender="me@example.com",
                          use_starttls=True)
        svc = OutputService(tempfile.mkdtemp(prefix="ah_smtp_"), smtp=cfg)
        with mock.patch("smtplib.SMTP") as mock_smtp:
            instance = mock.MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance
            result = svc.send_smtp("you@example.com", "Betreff", "Body")
        self.assertEqual(result["status"], "gesendet")
        instance.starttls.assert_called_once()
        instance.login.assert_called_once_with("me", "secret")
        instance.send_message.assert_called_once()

    def test_send_smtp_skips_starttls_when_disabled(self) -> None:
        from services.output import OutputService, SmtpConfig
        cfg = SmtpConfig(host="smtp.example.com", port=25,
                          username="", password="",
                          sender="me@example.com",
                          use_starttls=False)
        svc = OutputService(tempfile.mkdtemp(prefix="ah_smtp_"), smtp=cfg)
        with mock.patch("smtplib.SMTP") as mock_smtp:
            instance = mock.MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance
            svc.send_smtp("you@example.com", "Betreff", "Body")
        instance.starttls.assert_not_called()
        instance.login.assert_not_called()

    def test_send_smtp_handles_server_error(self) -> None:
        from services.output import OutputService, SmtpConfig
        cfg = SmtpConfig(host="smtp.example.com", port=587,
                          username="me", password="x", sender="me@x")
        svc = OutputService(tempfile.mkdtemp(prefix="ah_smtp_"), smtp=cfg)
        with mock.patch("smtplib.SMTP", side_effect=OSError("connect failed")):
            result = svc.send_smtp("you@example.com", "Betreff", "Body")
        self.assertEqual(result["status"], "fehler")
        self.assertIn("connect failed", result["error"])

    def test_send_smtp_without_config_returns_skip(self) -> None:
        from services.output import OutputService
        svc = OutputService(tempfile.mkdtemp(prefix="ah_smtp_"))
        result = svc.send_smtp("you@example.com", "Betreff", "Body")
        self.assertEqual(result["status"], "uebersprungen")


# ---------------------------------------------------------------------
#  A: IMAP-Abruf mit gemockter imaplib
# ---------------------------------------------------------------------
class TestImapAbruf(unittest.TestCase):

    def setUp(self) -> None:
        self.env_keys = ["ALLTAGSHELFER_IMAP_HOST",
                          "ALLTAGSHELFER_IMAP_USER",
                          "ALLTAGSHELFER_IMAP_PASS"]
        self.saved = {k: os.environ.get(k) for k in self.env_keys}
        for k in self.env_keys:
            os.environ[k] = "set"

    def tearDown(self) -> None:
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_fetch_imap_loops_through_unseen(self) -> None:
        from database import (Database, ProposalRepository)
        from modules.inbox import InboxModule
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name)
            mod = InboxModule(ProposalRepository(db))
            with mock.patch("imaplib.IMAP4_SSL") as imap_cls:
                client = mock.MagicMock()
                imap_cls.return_value = client
                client.search.return_value = (
                    "OK", [b"1 2"])
                # Fetch liefert eine Mail mit harmlosem Text
                client.fetch.return_value = (
                    "OK", [(b"1 (RFC822 {12}", b"From: a@b\r\n\r\nHi\r\n")])
                result = mod._cap_fetch_imap()
            self.assertEqual(result["status"], "abgerufen")
            self.assertEqual(result["checked"], 2)
            client.login.assert_called_once()
            client.select.assert_called_once_with("INBOX")
            client.search.assert_called_once_with(None, "UNSEEN")
        finally:
            db.close()
            os.unlink(tmp.name)


# ---------------------------------------------------------------------
#  A: OCR auf synthetischem Tesseract-Output
# ---------------------------------------------------------------------
class TestOcrParsing(unittest.TestCase):

    def test_receipt_text_extraction(self) -> None:
        # Wir mocken _try_tesseract + Pillow weg und liefern direkt Text.
        from services import ocr
        fake_text = """REWE Markt
        Tomaten              2.49
        Brot                 1.89
        Vollmilch            1.39
        Summe                5.77
        """
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(b"fake-image-data")
        tmp.close()
        try:
            with mock.patch.object(ocr, "_select_engine",
                                     return_value=("mock",
                                                    lambda p: fake_text)):
                result = ocr.scan_receipt(tmp.name)
            self.assertEqual(result["status"], "Kassenbon analysiert")
            self.assertIsNotNone(result["total"])
            self.assertAlmostEqual(result["total"], 5.77)
            labels = [item["label"] for item in result["items"]]
            self.assertIn("Tomaten", labels)
            self.assertIn("Brot", labels)
            self.assertIn("Vollmilch", labels)
        finally:
            os.unlink(tmp.name)

    def test_missing_engine_returns_hint(self) -> None:
        from services import ocr
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(b"x")
        tmp.close()
        try:
            with mock.patch.object(ocr, "_select_engine", return_value=None):
                result = ocr.scan_receipt(tmp.name)
            self.assertIn("error", result)
            self.assertIn("hinweis", result)
        finally:
            os.unlink(tmp.name)


# ---------------------------------------------------------------------
#  A: Drucken (Windows: os.startfile; Unix: subprocess.run [lp/lpr])
# ---------------------------------------------------------------------
class TestPrinten(unittest.TestCase):

    def test_print_file_missing_returns_error(self) -> None:
        from services.output import OutputService
        result = OutputService.print_file("nicht-existent.pdf")
        self.assertEqual(result["status"], "fehler")

    def test_print_file_calls_subprocess_on_unix(self) -> None:
        from services.output import OutputService
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(b"%PDF-1.4\n")
        tmp.close()
        try:
            # Wir tun so, als waeren wir auf Linux/macOS
            with mock.patch("sys.platform", "linux"):
                with mock.patch("subprocess.run") as run:
                    run.return_value = mock.MagicMock(returncode=0, stderr="")
                    result = OutputService.print_file(tmp.name)
            self.assertEqual(result["status"], "an Drucker geschickt")
            args = run.call_args[0][0]
            self.assertEqual(args[0], "lp")
            self.assertEqual(args[1], tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_print_file_calls_lpr_on_macos(self) -> None:
        from services.output import OutputService
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(b"%PDF-1.4\n")
        tmp.close()
        try:
            with mock.patch("sys.platform", "darwin"):
                with mock.patch("subprocess.run") as run:
                    run.return_value = mock.MagicMock(returncode=0, stderr="")
                    OutputService.print_file(tmp.name)
            args = run.call_args[0][0]
            self.assertEqual(args[0], "lpr")
        finally:
            os.unlink(tmp.name)


# ---------------------------------------------------------------------
#  A: HTTPS-Sync mit selbst-signiertem Zert (echter Handshake)
# ---------------------------------------------------------------------
class TestHttpsSyncServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
        except Exception:
            raise unittest.SkipTest(
                "cryptography fehlt - HTTPS-Test ausgelassen")
        cls.tmp = Path(tempfile.mkdtemp(prefix="ah_https_"))
        cls.cert_path = cls.tmp / "cert.pem"
        cls.key_path = cls.tmp / "key.pem"
        cls._generate_self_signed(cls.cert_path, cls.key_path)
        from services.sync_server import serve
        cls.server = serve(cls.tmp / "events.jsonl", "127.0.0.1", 0,
                             token=None,
                             certfile=str(cls.cert_path),
                             keyfile=str(cls.key_path))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                        daemon=True)
        cls.thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()
        if hasattr(cls, "thread"):
            cls.thread.join(timeout=2)
        if hasattr(cls, "tmp"):
            import shutil as _sh
            _sh.rmtree(cls.tmp)

    @staticmethod
    def _generate_self_signed(cert_path: Path, key_path: Path) -> None:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        from datetime import datetime, timedelta, timezone
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
        now = datetime.now(timezone.utc)
        cert = (x509.CertificateBuilder()
                .subject_name(name)
                .issuer_name(name)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + timedelta(days=1))
                .sign(key, hashes.SHA256()))
        key_path.write_bytes(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()))
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    def test_tls_handshake_with_self_signed_cert(self) -> None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(
                f"https://127.0.0.1:{self.port}/health",
                context=ctx, timeout=2) as response:
            data = response.read()
        self.assertIn(b"true", data)


# ---------------------------------------------------------------------
#  A: SQLCipher real (skipped if Bibliothek fehlt)
# ---------------------------------------------------------------------
class TestSqlCipherRealRoundTrip(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        try:
            import sqlcipher3                              # noqa: F401
        except Exception:
            raise unittest.SkipTest(
                "sqlcipher3 fehlt - Real-Test ausgelassen")

    def test_encrypt_write_close_reopen(self) -> None:
        from database import Database
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = Database(tmp.name, encryption_key="my-secret-12345")
            self.assertEqual(db.encryption_mode, "sqlcipher")
            db.conn.execute(
                "INSERT INTO family_members (name, role, created_at)"
                " VALUES (?,?,?)", ("Anna", "erwachsen",
                                       "2026-01-01T00:00:00+00:00"))
            db.conn.commit()
            db.close()
            # Re-open mit demselben Key
            db2 = Database(tmp.name, encryption_key="my-secret-12345")
            row = db2.conn.execute(
                "SELECT name FROM family_members").fetchone()
            self.assertEqual(row["name"], "Anna")
            db2.close()
        finally:
            os.unlink(tmp.name)


# ---------------------------------------------------------------------
#  A: Gemini real (skipped if Key nicht gesetzt)
# ---------------------------------------------------------------------
class TestGeminiRealApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        if not (os.environ.get("GOOGLE_API_KEY") or
                os.environ.get("GEMINI_API_KEY")):
            raise unittest.SkipTest(
                "GOOGLE_API_KEY nicht gesetzt - Gemini-Real-Test "
                "ausgelassen")
        try:
            import google.generativeai                     # noqa: F401
        except Exception:
            raise unittest.SkipTest(
                "google-generativeai nicht installiert")

    def test_simple_ask_returns_text(self) -> None:
        from services.gemini import GeminiClient
        client = GeminiClient(model="gemini-2.5-flash")
        self.assertTrue(client.is_available)
        text, usage = client.analyze_text(
            "Antworte auf Deutsch in genau einem Wort.",
            "Was ist 2+2?")
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        self.assertGreaterEqual(usage.input_tokens, 0)
