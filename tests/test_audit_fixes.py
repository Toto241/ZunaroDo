"""
Regressionstests fuer die Befunde des Sicherheits-/Korrektheits-Audits
(Phase 1 der Release-Readiness-Arbeit).

Abgedeckt:

  * sync_server._State.check_rate raeumt verwaiste Client-IPs auf
    (frueher unbegrenztes Dict-Wachstum -> Speicher-/DoS-Vektor).
  * sync_server._Handler._check_token nutzt einen Konstantzeit-Vergleich
    und verhaelt sich fuer richtige/falsche/fehlende Tokens korrekt.

Die uebrigen Audit-Fixes (HttpSyncProvider._seen-Snapshot, backup.verify_backup
ohne os.environ-Mutation, gemini.py Empty-Candidate-Guards) sind
verhaltenswahrend und werden von den bestehenden Suiten (test_sync_*,
test_smoke/test_integration) mitabgedeckt.
"""
from __future__ import annotations

import shutil
import tempfile
import time
import unittest
from pathlib import Path

from services.sync_server import _Handler, _State


class TestRateLimiterEviction(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ah_rate_"))
        self.state = _State(self.root / "log.jsonl", token=None,
                            rate_limit=5, rate_window_sec=60)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_stale_ips_are_evicted(self) -> None:
        # Eine IP, die nur einmal (vor langer Zeit) angefragt hat.
        self.state._request_log["10.0.0.1"] = [time.time() - 10_000]
        self.state._request_log["10.0.0.2"] = []  # bereits leer
        # Eine frische Anfrage einer anderen IP loest das Aufraeumen aus.
        self.assertTrue(self.state.check_rate("203.0.113.9"))
        self.assertNotIn("10.0.0.1", self.state._request_log,
                          "abgelaufene IP muss entfernt werden")
        self.assertNotIn("10.0.0.2", self.state._request_log,
                          "leere IP muss entfernt werden")
        self.assertIn("203.0.113.9", self.state._request_log)

    def test_active_ip_is_kept(self) -> None:
        # Aktive IP innerhalb des Fensters bleibt erhalten.
        self.assertTrue(self.state.check_rate("198.51.100.1"))
        self.assertTrue(self.state.check_rate("198.51.100.2"))
        self.assertIn("198.51.100.1", self.state._request_log)
        self.assertIn("198.51.100.2", self.state._request_log)

    def test_rate_limit_still_blocks_burst(self) -> None:
        ip = "192.0.2.50"
        allowed = [self.state.check_rate(ip) for _ in range(5)]
        self.assertTrue(all(allowed))
        self.assertFalse(self.state.check_rate(ip),
                          "6. Anfrage im Fenster muss abgelehnt werden")


class TestCheckToken(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ah_token_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _handler(self, token, header_value=None):
        h = object.__new__(_Handler)        # ohne Socket-Setup instanziieren
        h.state = _State(self.root / "log.jsonl", token=token)
        h.headers = {} if header_value is None else {"X-Sync-Token": header_value}
        return h

    def test_correct_token_accepted(self) -> None:
        self.assertTrue(self._handler("s3cr3t", "s3cr3t")._check_token())

    def test_wrong_token_rejected(self) -> None:
        self.assertFalse(self._handler("s3cr3t", "nope")._check_token())

    def test_missing_token_header_rejected(self) -> None:
        self.assertFalse(self._handler("s3cr3t", None)._check_token())

    def test_no_token_configured_allows_all(self) -> None:
        # Ohne konfiguriertes Token (z.B. 127.0.0.1-Bind) ist offen.
        self.assertTrue(self._handler("", None)._check_token())


if __name__ == "__main__":
    unittest.main()
