"""
Performance/Load-Tests fuer die wichtigsten Hot-Pfade.

Diese Tests haben grosszuegige Zeitbudgets - sie sollen nicht
Mikro-Benchmarks sein, sondern *Regressionen* erkennen (z.B. eine
quadratische Schleife dort, wo lineare Komplexitaet erwartet wird).
"""
from __future__ import annotations

import os
import tempfile
import time
import unittest
import sys
from datetime import date

from database import (CalendarRepository, ContractRepository, Database,
                     ExpenseRepository, NoteRepository)
from models import Contract, Event, Expense, Note
from modules.contracts import ContractModule, next_cancellation_date


_SKIP_BULK_INSERT_ON_WINDOWS_CI = (
    sys.platform == "win32" and os.environ.get("CI") == "true"
)


@unittest.skipIf(
    _SKIP_BULK_INSERT_ON_WINDOWS_CI,
    "Disk-I/O auf GitHub-Hosted-Windows-Runnern schwankt zu stark "
    "(Faktor 3x+ ueber Laeufe hinweg), siehe CI-Logs. "
    "Regressionsschutz erfolgt auf Linux-CI.",
)
class TestBulkInsertPerformance(unittest.TestCase):
    """Massenanlage von Eintraegen sollte linear skalieren."""

    def setUp(self) -> None:
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db = Database(self.path)

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_insert_500_contracts_under_15s(self) -> None:
        repo = ContractRepository(self.db)
        start = time.perf_counter()
        for i in range(500):
            repo.add(Contract(
                name=f"V{i}", category="streaming", provider="P",
                start_date=date(2025, 1, 1),
                minimum_term_months=12, notice_period_months=3,
                auto_renew_months=12, monthly_cost=9.99))
        elapsed = time.perf_counter() - start
        # Grosszuegiges Budget - dieser Test erkennt nur Regressionen
        # in Groessenordnungen, kein Mikro-Benchmark.
        self.assertLess(elapsed, 15.0,
                          f"500 Inserts dauerten {elapsed:.2f}s "
                          "(Budget: 15s) - Regressionsverdacht")

    def test_insert_500_expenses_under_15s(self) -> None:
        repo = ExpenseRepository(self.db)
        start = time.perf_counter()
        for i in range(500):
            repo.add(Expense(description=f"E{i}", amount=1.0))
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 15.0,
                          f"500 Expense-Inserts dauerten {elapsed:.2f}s")

    def test_list_200_contracts_under_2s(self) -> None:
        repo = ContractRepository(self.db)
        for i in range(200):
            repo.add(Contract(
                name=f"V{i}", category="strom", provider="P",
                start_date=date(2025, 1, 1),
                minimum_term_months=12, notice_period_months=3,
                auto_renew_months=12, monthly_cost=9.99))
        start = time.perf_counter()
        rows = repo.list_all()
        elapsed = time.perf_counter() - start
        self.assertEqual(len(rows), 200)
        self.assertLess(elapsed, 2.0,
                          f"List 200 dauerte {elapsed*1000:.0f}ms "
                          "- Regressionsverdacht")


class TestDeadlineCalculationPerformance(unittest.TestCase):
    """next_cancellation_date sollte O(1) pro Vertrag sein."""

    def test_deadline_calculation_scales(self) -> None:
        contract = Contract(
            name="X", category="strom", provider="",
            start_date=date(2010, 1, 1),
            minimum_term_months=12, notice_period_months=3,
            auto_renew_months=12, monthly_cost=10.0)
        # Vertrag laeuft seit ueber 15 Jahren -> viele Renew-Zyklen
        start = time.perf_counter()
        for _ in range(10000):
            next_cancellation_date(contract, today=date(2025, 6, 15))
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0,
                          f"10000 Deadline-Berechnungen: {elapsed:.2f}s")


class TestNotesListingPerformance(unittest.TestCase):
    """list_attached muss INDEX-gestuetzt sein, nicht Full-Scan."""

    def setUp(self) -> None:
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db = Database(self.path)

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def test_list_attached_in_large_dataset(self) -> None:
        repo = NoteRepository(self.db)
        # 1000 Notizen, davon 20 fuer Vertrag 42
        for i in range(1000):
            entity_type = "contracts" if i % 50 == 0 else None
            entity_id = 42 if i % 50 == 0 else None
            repo.add(Note(title=f"N{i}", content="x",
                            entity_type=entity_type, entity_id=entity_id))
        start = time.perf_counter()
        attached = repo.list_attached("contracts", 42)
        elapsed = time.perf_counter() - start
        self.assertEqual(len(attached), 20)
        self.assertLess(elapsed, 2.0,
                          f"Gefiltertes Listing: {elapsed*1000:.0f}ms")


if __name__ == "__main__":                       # pragma: no cover
    unittest.main()
