"""
Tests fuer die Voll-Loeschung (services/data_deletion.py +
Database.wipe_all_data). Kein Kivy noetig.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database import Database, SettingsRepository
from services.data_deletion import (DEFAULT_DATA_SUBDIRS, DeletionReport,
                                      delete_all_user_data, purge_directories,
                                      sandbox_data_dirs)


def _count(db: Database, table: str) -> int:
    return db.conn.execute(
        f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()["n"]


class _TempDb:
    """Context-Manager: frische Datei-DB in einem Temp-Verzeichnis."""

    def __enter__(self) -> Database:
        self._tmp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self._tmp.name) / "test.db"))
        return self.db

    def __exit__(self, *exc) -> None:
        self.db.close()
        self._tmp.cleanup()


class TestWipeAllData(unittest.TestCase):

    def _seed(self, db: Database) -> None:
        db.conn.execute(
            "INSERT INTO contracts (name, category, monthly_cost, currency, "
            "status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            ("Strom", "energy", 50.0, "EUR", "active",
             "2026-01-01", "2026-01-01"))
        db.conn.execute(
            "INSERT INTO family_members (name, role) VALUES (?,?)",
            ("Anna", "child"))
        db.conn.execute(
            "INSERT INTO notes (title, content, created_at, updated_at) "
            "VALUES (?,?,?,?)", ("Notiz", "Inhalt", "2026-01-01", "2026-01-01"))
        SettingsRepository(db).set("i18n.language", "fr")
        db.conn.commit()

    def test_clears_all_tables(self) -> None:
        with _TempDb() as db:
            self._seed(db)
            self.assertEqual(_count(db, "contracts"), 1)
            report = db.wipe_all_data()
            self.assertEqual(_count(db, "contracts"), 0)
            self.assertEqual(_count(db, "family_members"), 0)
            self.assertEqual(_count(db, "notes"), 0)
            self.assertEqual(_count(db, "app_settings"), 0)
            # Report meldet die geloeschten Zeilen.
            self.assertEqual(report["contracts"], 1)
            self.assertGreaterEqual(report["app_settings"], 1)

    def test_schema_survives_wipe(self) -> None:
        with _TempDb() as db:
            self._seed(db)
            version_before = db.schema_version
            db.wipe_all_data()
            # Schema-Version unveraendert; neue Inserts moeglich.
            self.assertEqual(
                db.conn.execute("PRAGMA user_version").fetchone()[0],
                version_before)
            db.conn.execute(
                "INSERT INTO notes (title, content, created_at, updated_at) "
                "VALUES (?,?,?,?)", ("Neu", "x", "2026-01-02", "2026-01-02"))
            db.conn.commit()
            self.assertEqual(_count(db, "notes"), 1)

    def test_include_settings_false_keeps_settings(self) -> None:
        with _TempDb() as db:
            self._seed(db)
            report = db.wipe_all_data(include_settings=False)
            self.assertEqual(_count(db, "contracts"), 0)
            # app_settings unangetastet
            self.assertEqual(
                SettingsRepository(db).get("i18n.language"), "fr")
            self.assertNotIn("app_settings", report)


class TestPurgeDirectories(unittest.TestCase):

    def test_removes_files_keeps_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "ausgaben"
            (base / "sub").mkdir(parents=True)
            (base / "a.pdf").write_text("x", encoding="utf-8")
            (base / "sub" / "b.csv").write_text("y", encoding="utf-8")
            deleted, errors = purge_directories([base])
            self.assertEqual(deleted, 2)
            self.assertEqual(errors, [])
            self.assertTrue(base.is_dir())          # Wurzel bleibt
            self.assertEqual(list(base.iterdir()), [])

    def test_missing_dir_is_skipped(self) -> None:
        deleted, errors = purge_directories([Path("does/not/exist")])
        self.assertEqual(deleted, 0)
        self.assertEqual(errors, [])


class TestSandboxDataDirs(unittest.TestCase):

    def test_builds_subdir_paths(self) -> None:
        dirs = sandbox_data_dirs("/data/app")
        names = {p.name for p in dirs}
        self.assertEqual(names, set(DEFAULT_DATA_SUBDIRS))


class TestDeleteAllUserData(unittest.TestCase):

    def test_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, _TempDb() as db:
            db.conn.execute(
                "INSERT INTO notes (title, content, created_at, updated_at) "
                "VALUES (?,?,?,?)", ("N", "x", "2026-01-01", "2026-01-01"))
            db.conn.commit()
            outdir = Path(tmp) / "ausgaben"
            outdir.mkdir()
            (outdir / "export.csv").write_text("data", encoding="utf-8")

            report = delete_all_user_data(db, data_dirs=[outdir])
            self.assertIsInstance(report, DeletionReport)
            self.assertEqual(_count(db, "notes"), 0)
            self.assertEqual(report.files_deleted, 1)
            self.assertGreaterEqual(report.rows_deleted, 1)
            self.assertEqual(report.errors, [])
            # as_dict ist serialisierbar fuer die UI.
            self.assertIn("rows_deleted", report.as_dict())


if __name__ == "__main__":                           # pragma: no cover
    unittest.main()
