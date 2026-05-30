"""Tests fuer Pro-Sync-Gate in services/sync_runtime.py."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from database import Database, SettingsRepository
from services.config import AppConfig
from services.licensing import load_license
from services.config import save_value
from services.sync_runtime import (gate_sync_enabled_value, resolve_sync_provider,
                                   sync_allowed)


class TestSyncRuntime(unittest.TestCase):

    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        self._db_path = tmp.name
        self.db = Database(self._db_path)
        self.settings = SettingsRepository(self.db)

    def tearDown(self) -> None:
        self.db.close()
        Path(self._db_path).unlink(missing_ok=True)

    def test_free_license_blocks_sync(self) -> None:
        config = AppConfig(sync_enabled="auto")
        self.assertFalse(sync_allowed(config, self.settings))
        with mock.patch("services.sync_runtime.make_sync_provider") as m:
            m.return_value = object()
            self.assertIsNone(
                resolve_sync_provider(config, self.settings, Path("/tmp/state")))
            m.assert_not_called()

    def test_save_value_blocks_sync_without_pro(self) -> None:
        from services.licensing import start_trial

        start_trial(self.settings)
        self.settings.set("sync.enabled", "false")
        save_value(self.settings, "sync.enabled", "true")
        self.assertEqual(self.settings.get("sync.enabled"), "true")

        # Free tier after trial logic - use fresh db without license
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db2 = Database(tmp.name)
        try:
            repo2 = SettingsRepository(db2)
            blocked = save_value(repo2, "sync.enabled", "true")
            self.assertTrue(blocked)
            self.assertIn(repo2.get("sync.enabled"), (None, "false"))
        finally:
            db2.close()
            Path(tmp.name).unlink(missing_ok=True)

    def test_gate_sync_enabled_value(self) -> None:
        from services.licensing import start_trial

        start_trial(self.settings)
        val, blocked = gate_sync_enabled_value(self.settings, "true")
        self.assertFalse(blocked)
        self.assertEqual(val, "true")

    def test_ui_enable_sync_uses_license_not_stale_config(self) -> None:
        """GUI darf Sync aktivieren, auch wenn self.config noch sync.enabled=false hat."""
        from services.licensing import start_trial

        config = AppConfig(sync_enabled="false")
        start_trial(self.settings)
        self.assertFalse(sync_allowed(config, self.settings))
        self.assertTrue(load_license(self.settings).allows_sync())

    def test_pro_license_allows_sync_when_configured(self) -> None:
        from services.licensing import start_trial

        start_trial(self.settings)
        config = AppConfig(sync_enabled="auto")
        self.assertTrue(sync_allowed(config, self.settings))
        sentinel = object()
        with mock.patch("services.sync_runtime.make_sync_provider",
                        return_value=sentinel) as m:
            got = resolve_sync_provider(config, self.settings, Path("/tmp/state"))
            self.assertIs(got, sentinel)
            m.assert_called_once()

    def test_sync_disabled_via_config(self) -> None:
        from services.licensing import start_trial

        start_trial(self.settings)
        config = AppConfig(sync_enabled="false")
        self.assertFalse(sync_allowed(config, self.settings))


if __name__ == "__main__":
    unittest.main()
