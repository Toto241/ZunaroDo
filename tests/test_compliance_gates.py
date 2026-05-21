"""
Tests fuer zwei Play-Store-Compliance-Gates:

  - Daten-Loeschung (Punkt 8): die App bietet einen In-App-Voll-Loeschpfad,
    die Datenschutzerklaerung beschreibt ihn, und die Mobile-UI ruft den
    Loesch-Service auf.
  - Closed-Testing-Nachweis (Punkt 11): das Release-Gate verlangt vor 'GO'
    sowohl die Mindestkonfiguration (>=12 Tester / >=14 Tage) als auch ein
    Nachweisdokument.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import playstore_check as pc

_REPO = Path(__file__).resolve().parents[1]


class TestDataDeletionReachable(unittest.TestCase):

    def test_privacy_policy_documents_inapp_deletion(self) -> None:
        text = (_REPO / "legal" / "DATENSCHUTZ.md").read_text(encoding="utf-8")
        self.assertIn("Alle Daten loeschen", text)
        self.assertIn("Loeschung", text)

    def test_data_deletion_reachable_from_ui(self) -> None:
        # Der Mobile-"Mehr"-Screen ruft den Voll-Loesch-Service auf.
        more = (_REPO / "mobile" / "screens" / "more.py").read_text(
            encoding="utf-8")
        self.assertIn("delete_all_user_data", more)
        self.assertIn("sandbox_data_dirs", more)

    def test_checker_reports_deletion_path_present(self) -> None:
        report = pc.Report()
        pc.check_data_deletion(report)
        self.assertEqual(report.by_level(pc.Level.FAIL), [])


class TestClosedTestGate(unittest.TestCase):

    _GOOD_CONFIG = {"tracks": {"closed": {"min_testers": 12, "min_days": 14}}}

    def test_requires_evidence_before_go(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            gate = pc.evaluate_closed_test_gate(self._GOOD_CONFIG, Path(t))
            self.assertTrue(gate["config_ok"])
            self.assertFalse(gate["evidence_present"])
            self.assertFalse(gate["ready"])           # ohne Nachweis kein GO

    def test_ready_with_config_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "closed-test-2026-05.md").write_text(
                "12 Tester, 14 Tage.\n", encoding="utf-8")
            gate = pc.evaluate_closed_test_gate(self._GOOD_CONFIG, Path(t))
            self.assertTrue(gate["ready"])
            self.assertIn("closed-test-2026-05.md", gate["evidence_files"])

    def test_rejects_weak_config(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "closed-test.md").write_text("x", encoding="utf-8")
            weak = {"tracks": {"closed": {"min_testers": 5, "min_days": 3}}}
            gate = pc.evaluate_closed_test_gate(weak, Path(t))
            self.assertFalse(gate["config_ok"])
            self.assertFalse(gate["ready"])

    def test_live_config_meets_minimums(self) -> None:
        # Die echte playstore.yml verlangt mindestens 12 Tester / 14 Tage.
        cfg = pc._load_playstore_yml()
        gate = pc.evaluate_closed_test_gate(cfg, _REPO / "release")
        self.assertTrue(gate["config_ok"], gate["reasons"])

    def test_checker_does_not_fail_on_missing_evidence(self) -> None:
        # Fehlender Nachweis ist WARN (vor Produktion noetig), kein FAIL.
        report = pc.Report()
        pc.check_closed_test_evidence(report)
        self.assertEqual(report.by_level(pc.Level.FAIL), [])


if __name__ == "__main__":
    unittest.main()
