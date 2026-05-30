"""Mobile paritaet: install_gate blockiert Pro-Module ohne Lizenz."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from database import Database, ExpenseRepository, SettingsRepository
from services.license_gate import install_gate
from services.licensing import load_license


class TestMobileLicenseGate(unittest.TestCase):

    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        self._db_path = tmp.name
        self.db = Database(self._db_path)
        self.settings = SettingsRepository(self.db)

    def tearDown(self) -> None:
        self.db.close()
        Path(self._db_path).unlink(missing_ok=True)

    def test_free_tier_blocks_finance_like_mobile(self) -> None:
        from core.interface import ModuleRegistry
        from modules.finance import FinanceModule

        registry = ModuleRegistry()
        registry.register(FinanceModule(ExpenseRepository(self.db)))
        install_gate(registry, lambda: load_license(self.settings))

        result = registry.dispatch("finance.monthly_overview", {})
        self.assertTrue(result.get("tier_locked"))

    def test_mobile_app_source_installs_gate(self) -> None:
        """Statischer Check: mobile/app.py bindet install_gate ein."""
        from pathlib import Path

        src = Path("mobile/app.py").read_text(encoding="utf-8")
        self.assertIn("install_gate", src)
        self.assertIn("load_license", src)


if __name__ == "__main__":
    unittest.main()
