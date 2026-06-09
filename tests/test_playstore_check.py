"""
Tests fuer tools/playstore_check.py.

Der Compliance-Checker selbst muss verifiziert sein, sonst erkennt
niemand, wenn er still bricht. Diese Suite deckt die Hauptregeln
isoliert ab (kein Repo-Scan, keine globale Konfiguration).
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import playstore_check as pc


class TestParseBuildozerSpec(unittest.TestCase):

    def test_extracts_app_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "buildozer.spec"
            spec.write_text(
                "[app]\n"
                "version = 1.2.3\n"
                "android.api = 35\n"
                "android.permissions = INTERNET, ACCESS_NETWORK_STATE\n"
                "\n[buildozer]\n"
                "log_level = 2\n",
                encoding="utf-8")
            got = pc.parse_buildozer_spec(spec)
        self.assertEqual(got["version"], "1.2.3")
        self.assertEqual(got["android.api"], "35")
        self.assertNotIn("log_level", got)  # nicht im [app]-Block

    def test_handles_missing_file(self) -> None:
        self.assertEqual(pc.parse_buildozer_spec(Path("/no/such/file")), {})

    def test_ignores_comments_and_blanks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "buildozer.spec"
            spec.write_text(
                "[app]\n"
                "# kommentar\n"
                "\n"
                "version = 0.1.0\n",
                encoding="utf-8")
            got = pc.parse_buildozer_spec(spec)
        self.assertEqual(got, {"version": "0.1.0"})


class TestCheckSdkLevels(unittest.TestCase):

    def test_fails_below_min_target(self) -> None:
        rep = pc.Report()
        pc.check_sdk_levels(rep, {"android.api": "33", "android.minapi": "24"})
        fails = rep.by_level(pc.Level.FAIL)
        self.assertTrue(any("MIN_TARGET_SDK" in f.message for f in fails))

    def test_passes_at_or_above_target(self) -> None:
        rep = pc.Report()
        pc.check_sdk_levels(rep, {"android.api": "35", "android.minapi": "24"})
        self.assertEqual(rep.by_level(pc.Level.FAIL), [])

    def test_flags_too_low_minapi(self) -> None:
        rep = pc.Report()
        pc.check_sdk_levels(rep, {"android.api": "35", "android.minapi": "21"})
        msgs = [f.message for f in rep.by_level(pc.Level.FAIL)]
        self.assertTrue(any("minapi" in m for m in msgs))


class TestCheckPermissions(unittest.TestCase):

    def test_whitelisted_passes(self) -> None:
        rep = pc.Report()
        pc.check_permissions(rep, {"android.permissions": "INTERNET"})
        self.assertEqual(rep.by_level(pc.Level.FAIL), [])
        self.assertTrue(rep.by_level(pc.Level.PASS))

    def test_denied_permission_fails(self) -> None:
        rep = pc.Report()
        pc.check_permissions(rep,
            {"android.permissions": "INTERNET, MANAGE_EXTERNAL_STORAGE"})
        fails = [f.message for f in rep.by_level(pc.Level.FAIL)]
        self.assertTrue(any("MANAGE_EXTERNAL_STORAGE" in m for m in fails))

    def test_unknown_permission_warns(self) -> None:
        rep = pc.Report()
        pc.check_permissions(rep,
            {"android.permissions": "BLUETOOTH"})
        warns = [f.message for f in rep.by_level(pc.Level.WARN)]
        self.assertTrue(any("BLUETOOTH" in m for m in warns))

    def test_empty_permissions_passes(self) -> None:
        rep = pc.Report()
        pc.check_permissions(rep, {})
        self.assertTrue(rep.by_level(pc.Level.PASS))


class TestCheckVersioning(unittest.TestCase):

    def test_semver_passes(self) -> None:
        rep = pc.Report()
        pc.check_versioning(rep, {"version": "1.2.3"})
        self.assertEqual(rep.by_level(pc.Level.FAIL), [])

    def test_invalid_warns(self) -> None:
        rep = pc.Report()
        pc.check_versioning(rep, {"version": "v1"})
        self.assertTrue(rep.by_level(pc.Level.WARN))

    def test_missing_fails(self) -> None:
        rep = pc.Report()
        pc.check_versioning(rep, {})
        self.assertTrue(rep.by_level(pc.Level.FAIL))

    def test_numeric_version_consistent_passes(self) -> None:
        rep = pc.Report()
        pc.check_versioning(
            rep,
            {"version": "1.0.0", "android.numeric_version": "2"},
            {"identity": {"version_name": "1.0.0", "version_code": 2}})
        self.assertEqual(rep.by_level(pc.Level.FAIL), [])

    def test_numeric_version_missing_fails(self) -> None:
        # Ohne android.numeric_version leitet buildozer den versionCode aus
        # 'version' ab und weicht vom Store-Listing ab -> muss FAIL sein.
        rep = pc.Report()
        pc.check_versioning(
            rep,
            {"version": "1.0.0"},
            {"identity": {"version_name": "1.0.0", "version_code": 2}})
        fails = [f.message for f in rep.by_level(pc.Level.FAIL)]
        self.assertTrue(any("numeric_version" in m for m in fails))

    def test_numeric_version_mismatch_fails(self) -> None:
        rep = pc.Report()
        pc.check_versioning(
            rep,
            {"version": "1.0.0", "android.numeric_version": "3"},
            {"identity": {"version_name": "1.0.0", "version_code": 2}})
        self.assertTrue(rep.by_level(pc.Level.FAIL))

    def test_version_name_mismatch_fails(self) -> None:
        rep = pc.Report()
        pc.check_versioning(
            rep,
            {"version": "1.0.1", "android.numeric_version": "2"},
            {"identity": {"version_name": "1.0.0", "version_code": 2}})
        self.assertTrue(rep.by_level(pc.Level.FAIL))

    def test_without_playstore_cfg_skips_comparison(self) -> None:
        rep = pc.Report()
        pc.check_versioning(rep, {"version": "1.0.0"}, {})
        self.assertEqual(rep.by_level(pc.Level.FAIL), [])


class TestCheckSecrets(unittest.TestCase):

    def _temp_file(self, tmp: Path, name: str, content: str) -> Path:
        p = tmp / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_detects_google_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            p = self._temp_file(tmp, "leak.py", 'KEY = "AIza' + "x" * 35 + '"\n')
            rep = pc.Report()
            # ueberschreibe REPO_ROOT, damit relative_to klappt
            orig = pc.REPO_ROOT
            pc.REPO_ROOT = tmp
            try:
                pc.check_secrets(rep, [p])
            finally:
                pc.REPO_ROOT = orig
            fails = rep.by_level(pc.Level.FAIL)
            self.assertTrue(any("Secret" in f.message for f in fails))

    def test_clean_repo_passes(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            p = self._temp_file(tmp, "ok.py", 'value = "harmless"\n')
            rep = pc.Report()
            orig = pc.REPO_ROOT
            pc.REPO_ROOT = tmp
            try:
                pc.check_secrets(rep, [p])
            finally:
                pc.REPO_ROOT = orig
            self.assertTrue(rep.by_level(pc.Level.PASS))


class TestCheckDemoData(unittest.TestCase):

    def test_passes_when_db_and_sqlite_excluded(self) -> None:
        rep = pc.Report()
        pc.check_demo_data_excluded(rep,
            {"source.exclude_exts": "spec,db,sqlite,log"})
        self.assertTrue(rep.by_level(pc.Level.PASS))

    def test_fails_when_db_missing(self) -> None:
        rep = pc.Report()
        pc.check_demo_data_excluded(rep,
            {"source.exclude_exts": "spec,log"})
        self.assertTrue(rep.by_level(pc.Level.FAIL))


class TestCodeSmells(unittest.TestCase):

    def test_print_only_in_mobile_path(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            (tmp / "mobile").mkdir()
            (tmp / "tools").mkdir()
            mobile_file = tmp / "mobile" / "screen.py"
            mobile_file.write_text("print('hi')\n", encoding="utf-8")
            cli_file = tmp / "tools" / "cli.py"
            cli_file.write_text("print('hi')\n", encoding="utf-8")
            rep = pc.Report()
            orig = pc.REPO_ROOT
            pc.REPO_ROOT = tmp
            try:
                pc.check_smells(rep, [mobile_file, cli_file])
            finally:
                pc.REPO_ROOT = orig
            fails = rep.by_level(pc.Level.FAIL)
            # Es muss mindestens einen FAIL fuer den mobile-Pfad geben
            # und KEINEN FAIL fuer den tools-Pfad.
            self.assertTrue(any("mobile" in (f.file or "") for f in fails))
            self.assertFalse(any("tools" in (f.file or "") for f in fails))

    def test_requests_verify_false_is_smell(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            (tmp / "services").mkdir()
            bad = tmp / "services" / "client.py"
            bad.write_text("import requests\nrequests.get('https://x', verify=False)\n",
                           encoding="utf-8")
            rep = pc.Report()
            orig = pc.REPO_ROOT
            pc.REPO_ROOT = tmp
            try:
                pc.check_smells(rep, [bad])
            finally:
                pc.REPO_ROOT = orig
            self.assertTrue(any("REQUESTS_VERIFY_FALSE" in f.message
                                for f in rep.by_level(pc.Level.FAIL)))


class TestCheckDataDeletion(unittest.TestCase):

    def test_passes_when_mechanism_present(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            (tmp / "services").mkdir()
            (tmp / "services" / "data_deletion.py").write_text(
                "x = 1\n", encoding="utf-8")
            (tmp / "database.py").write_text(
                "class Database:\n    def wipe_all_data(self): ...\n",
                encoding="utf-8")
            rep = pc.Report()
            orig = pc.REPO_ROOT
            pc.REPO_ROOT = tmp
            try:
                pc.check_data_deletion(rep)
            finally:
                pc.REPO_ROOT = orig
            self.assertTrue(rep.by_level(pc.Level.PASS))
            self.assertEqual(rep.by_level(pc.Level.FAIL), [])

    def test_fails_when_service_missing(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            (tmp / "database.py").write_text(
                "def wipe_all_data(): ...\n", encoding="utf-8")
            rep = pc.Report()
            orig = pc.REPO_ROOT
            pc.REPO_ROOT = tmp
            try:
                pc.check_data_deletion(rep)
            finally:
                pc.REPO_ROOT = orig
            self.assertTrue(any("data_deletion.py" in f.message
                                for f in rep.by_level(pc.Level.FAIL)))

    def test_fails_when_wipe_method_missing(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            (tmp / "services").mkdir()
            (tmp / "services" / "data_deletion.py").write_text(
                "x = 1\n", encoding="utf-8")
            (tmp / "database.py").write_text(
                "class Database: ...\n", encoding="utf-8")
            rep = pc.Report()
            orig = pc.REPO_ROOT
            pc.REPO_ROOT = tmp
            try:
                pc.check_data_deletion(rep)
            finally:
                pc.REPO_ROOT = orig
            self.assertTrue(any("wipe_all_data" in f.message
                                for f in rep.by_level(pc.Level.FAIL)))


class TestCheckI18n(unittest.TestCase):
    """Laeuft gegen das echte Repo - die Locales sind paritaetisch."""

    def test_real_repo_parity_passes(self) -> None:
        rep = pc.Report()
        pc.check_i18n(rep)
        self.assertEqual(rep.by_level(pc.Level.FAIL), [])
        self.assertTrue(rep.by_level(pc.Level.PASS))


class TestReportFormats(unittest.TestCase):

    def test_summary_counts(self) -> None:
        rep = pc.Report()
        rep.add(check="x", level=pc.Level.PASS, message="a")
        rep.add(check="x", level=pc.Level.WARN, message="b")
        rep.add(check="x", level=pc.Level.FAIL, message="c")
        self.assertEqual(rep.summary(),
                         {"pass": 1, "warn": 1, "fail": 1, "total": 3})

    def test_json_format_valid(self) -> None:
        rep = pc.Report()
        rep.add(check="x", level=pc.Level.PASS, message="a")
        out = pc.format_json(rep)
        data = json.loads(out)
        self.assertEqual(data["summary"]["pass"], 1)
        self.assertEqual(len(data["findings"]), 1)


class TestRunChecksIntegration(unittest.TestCase):
    """Smoke-Test gegen das echte Repo - garantiert Lauffaehigkeit."""

    def test_runs_without_exception(self) -> None:
        rep = pc.run_checks(only=None)
        self.assertGreater(rep.summary()["total"], 0)

    def test_subset_only(self) -> None:
        rep = pc.run_checks(only=["versioning", "permissions"])
        checks_seen = {f.check for f in rep.findings}
        self.assertTrue(checks_seen <= {"versioning", "permissions"})


if __name__ == "__main__":                            # pragma: no cover
    unittest.main()
