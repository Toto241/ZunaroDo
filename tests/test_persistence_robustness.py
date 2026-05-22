"""
Regressionstests fuer Persistenz-/Modul-Robustheit (Deep-Review-Funde).

1. CalendarRepository._next_occurrence darf bei nicht-positivem
   recurrence_days NICHT in eine Endlosschleife laufen (erreichbar ueber
   Sync-Replay / Importe, die den dispatch-seitigen >0-Check umgehen).
2. ProposalRepository laedt created_at zurueck, damit der Datumsfilter der
   system.search-Funktion Proposals nicht stillschweigend ausschliesst.
3. contracts.add / set_owner / expenses.add duerfen mit einem verwaisten
   owner_id (anderes Geraet, anderer Mitglieder-Stand) keinen
   FOREIGN-KEY-IntegrityError werfen, sondern den Owner auf NULL setzen.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, datetime

from database import (ContractRepository, Database, ExpenseRepository,
                      FamilyRepository, ProposalRepository, CalendarRepository)
from models import CalendarEvent, Contract, Expense, FamilyMember, Proposal


class TestCalendarRecurrenceGuard(unittest.TestCase):

    def test_negative_recurrence_does_not_hang(self) -> None:
        ev = CalendarEvent(title="kaputt", due_date=date(2020, 1, 1),
                           recurrence_days=-5)
        # Frueher: Endlosschleife. Jetzt: wie nicht-wiederkehrend behandelt.
        got = CalendarRepository._next_occurrence(ev, date(2026, 6, 1))
        self.assertIsNone(got)

    def test_zero_recurrence_is_safe(self) -> None:
        ev = CalendarEvent(title="x", due_date=date(2026, 6, 1),
                           recurrence_days=0)
        self.assertEqual(
            CalendarRepository._next_occurrence(ev, date(2026, 6, 1)),
            date(2026, 6, 1))

    def test_positive_recurrence_still_advances(self) -> None:
        ev = CalendarEvent(title="x", due_date=date(2026, 1, 1),
                           recurrence_days=30)
        got = CalendarRepository._next_occurrence(ev, date(2026, 3, 15))
        self.assertIsNotNone(got)
        self.assertGreaterEqual(got, date(2026, 3, 15))


class _DbCase(unittest.TestCase):

    def setUp(self) -> None:
        fd, self.path = tempfile.mkstemp(prefix="zd-persist-", suffix=".db")
        os.close(fd)
        self.db = Database(path=self.path)

    def tearDown(self) -> None:
        self.db.close()
        try:
            os.unlink(self.path)
        except OSError:
            pass


class TestProposalCreatedAt(_DbCase):

    def test_created_at_is_loaded_as_datetime(self) -> None:
        repo = ProposalRepository(self.db)
        repo.add(Proposal(source="mail", summary="Test",
                          target_capability="finance.add_expense"))
        loaded = repo.list()
        self.assertEqual(len(loaded), 1)
        self.assertIsInstance(loaded[0].created_at, datetime,
                              "created_at wurde nicht aus der DB geladen")
        # .date() darf nicht crashen (frueher: AttributeError auf str / None).
        self.assertIsInstance(loaded[0].created_at.date(), date)


class TestOrphanOwnerId(_DbCase):

    def test_contract_with_unknown_owner_stores_null(self) -> None:
        repo = ContractRepository(self.db)
        # owner_id 9999 existiert nicht -> frueher IntegrityError.
        c = repo.add(Contract(name="Strom", category="strom", owner_id=9999))
        stored = repo.get(c.id)
        self.assertIsNotNone(stored)
        self.assertIsNone(stored.owner_id)

    def test_contract_with_valid_owner_is_kept(self) -> None:
        fam = FamilyRepository(self.db)
        m = fam.add_member(FamilyMember(name="Anna"))
        repo = ContractRepository(self.db)
        c = repo.add(Contract(name="Handy", category="mobilfunk",
                              owner_id=m.id))
        self.assertEqual(repo.get(c.id).owner_id, m.id)

    def test_set_owner_with_unknown_id_clears_it(self) -> None:
        repo = ContractRepository(self.db)
        c = repo.add(Contract(name="Strom", category="strom"))
        repo.set_owner(c.id, 4242)
        self.assertIsNone(repo.get(c.id).owner_id)

    def test_expense_with_unknown_owner_stores_null(self) -> None:
        repo = ExpenseRepository(self.db)
        e = repo.add(Expense(description="Einkauf", amount=12.5,
                             owner_id=7777))
        stored = repo.list_all()
        self.assertEqual(len(stored), 1)
        self.assertIsNone(stored[0].owner_id)


if __name__ == "__main__":
    unittest.main()
