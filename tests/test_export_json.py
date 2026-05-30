"""JSON-Gesamtexport (DSGVO / Mobile)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, SocialRepository)
from models import Contract
from services.export import export_all_json


class TestExportJson(unittest.TestCase):

    def test_export_all_json_writes_bundle(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db = Database(tmp.name)
        try:
            contracts = ContractRepository(db)
            contracts.add(Contract(
                name="Test", category="streaming", provider="X",
                monthly_cost=9.99,
            ))
            out_dir = Path(tmp.name).parent / "json_export"
            path = export_all_json(
                out_dir,
                contracts, ExpenseRepository(db), CalendarRepository(db),
                SocialRepository(db), FamilyRepository(db),
            )
            self.assertTrue(path.is_file())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["format"], "zunarodo-export-v1")
            self.assertEqual(len(data["contracts"]), 1)
        finally:
            db.close()
            Path(tmp.name).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
