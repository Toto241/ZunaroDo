"""
Tests fuer tools/data_safety.py - die wahrheitsgemaesse Ableitung und
Konsistenzpruefung der Play-Store-Data-Safety-Angaben.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import data_safety as ds


def _make_repo(tmp: Path, *, requirements: str = "",
               with_deletion: bool = True) -> Path:
    (tmp / "requirements.txt").write_text(requirements, encoding="utf-8")
    if with_deletion:
        (tmp / "services").mkdir(exist_ok=True)
        (tmp / "services" / "data_deletion.py").write_text(
            "x = 1\n", encoding="utf-8")
        (tmp / "database.py").write_text(
            "class Database:\n    def wipe_all_data(self): ...\n",
            encoding="utf-8")
    return tmp


class TestDetectTrackingSdks(unittest.TestCase):

    def test_none_for_clean_deps(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t),
                              requirements="kivy\ncryptography\nrequests\n")
            self.assertEqual(ds.detect_tracking_sdks(repo), [])

    def test_detects_firebase(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t),
                              requirements="kivy\nfirebase-admin==6.0\n")
            found = ds.detect_tracking_sdks(repo)
            self.assertTrue(any("firebase" in f for f in found))

    def test_detects_sentry(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), requirements="sentry-sdk\n")
            self.assertTrue(ds.detect_tracking_sdks(repo))


class TestDeletionSupported(unittest.TestCase):

    def test_true_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), with_deletion=True)
            self.assertTrue(ds.deletion_supported(repo))

    def test_false_without_service(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), with_deletion=False)
            self.assertFalse(ds.deletion_supported(repo))


class TestGenerate(unittest.TestCase):

    def test_clean_app_shares_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), requirements="kivy\n")
            out = ds.generate(repo)
            self.assertFalse(out["data_shared"])
            self.assertEqual(out["sdk_inventory"], [])
            self.assertTrue(out["users_can_request_deletion"])
            self.assertIn("user_content", out["types"])
            # kein Analytics-Zweck
            purposes = {e["purpose"] for e in out["types"].values()}
            self.assertEqual(purposes, {"APP_FUNCTIONALITY"})

    def test_tracking_dep_flips_shared(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), requirements="kivy\nfirebase-admin\n")
            self.assertTrue(ds.generate(repo)["data_shared"])

    def test_deletion_missing_reflected(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), with_deletion=False)
            self.assertFalse(ds.generate(repo)["users_can_request_deletion"])


class TestCheckConsistency(unittest.TestCase):

    def test_clean_declaration_passes(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), requirements="kivy\n")
            declared = ds.generate(repo)
            self.assertEqual(ds.check_consistency(declared, repo), [])

    def test_false_sharing_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), requirements="kivy\n")
            declared = {
                "data_shared": True,
                "types": {"crash_logs": {"shared": True,
                                          "shared_with": ["google_firebase"],
                                          "purpose": "APP_FUNCTIONALITY"}},
                "sdk_inventory": [{"name": "Firebase Crashlytics"}],
                "users_can_request_deletion": True,
            }
            errors = [i for i in ds.check_consistency(declared, repo)
                      if i[0] == "error"]
            self.assertGreaterEqual(len(errors), 3)

    def test_analytics_purpose_without_sdk_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), requirements="kivy\n")
            declared = {
                "data_shared": False,
                "types": {"app_interactions": {"purpose": "ANALYTICS"}},
                "users_can_request_deletion": True,
            }
            errors = [i for i in ds.check_consistency(declared, repo)
                      if i[0] == "error"]
            self.assertTrue(any("ANALYTICS" in m for _, _, m in errors))

    def test_missing_deletion_warns(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = _make_repo(Path(t), requirements="kivy\n",
                              with_deletion=False)
            declared = {"data_shared": False, "types": {}}
            warns = [i for i in ds.check_consistency(declared, repo)
                     if i[0] == "warning"]
            self.assertTrue(warns)


class TestRealRepo(unittest.TestCase):
    """Die echte playstore.yml muss konsistent zur App sein."""

    def test_real_playstore_yml_is_consistent(self) -> None:
        declared = ds._load_declared()
        errors = [i for i in ds.check_consistency(declared) if i[0] == "error"]
        self.assertEqual(errors, [], f"Inkonsistenzen: {errors}")

    def test_real_app_has_no_tracking(self) -> None:
        self.assertEqual(ds.detect_tracking_sdks(), [])


class TestFormatMarkdown(unittest.TestCase):

    def test_contains_table(self) -> None:
        out = ds.format_markdown(ds.generate())
        self.assertIn("Data Safety", out)
        self.assertIn("| Typ |", out)


if __name__ == "__main__":                            # pragma: no cover
    unittest.main()
