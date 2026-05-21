"""
Robustheit der Importer (R6).

  - CSV-Import ueberspringt fehlerhafte Zeilen (fehlendes Pflichtfeld) und
    faellt bei kaputten Zahlen/Daten auf Defaults zurueck, statt zu crashen
    oder den ganzen Import zu verlieren - fuer alle Entitaeten.
  - iCal-Import behandelt Wiederholungen rund um die Sommerzeit-Umstellung
    (DST) korrekt: floating/TZID-Zeiten verschieben das Kalenderdatum nicht.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, SocialRepository)
from services import import_csv
from services.ical import import_events


class TestCsvImportRejectsMalformed(unittest.TestCase):

    def setUp(self) -> None:
        fd, self.dbpath = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db = Database(self.dbpath)
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_csv_"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.dbpath)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, name: str, header: str, *rows: str) -> Path:
        p = self.tmp / name
        p.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8-sig")
        return p

    def test_contracts_skips_rows_without_name(self) -> None:
        p = self._write("contracts.csv", "name;kategorie;monatspreis",
                        "Strom;strom;30,50", ";versicherung;10")
        n = import_csv.import_contracts(ContractRepository(self.db), p)
        self.assertEqual(n, 1)
        names = [c.name for c in
                 ContractRepository(self.db).list_all(only_active=False)]
        self.assertEqual(names, ["Strom"])

    def test_expenses_skips_rows_without_description(self) -> None:
        p = self._write("expenses.csv", "beschreibung;betrag;datum",
                        "Kaffee;3,50;2026-05-21", ";9,99;2026-05-22")
        n = import_csv.import_expenses(ExpenseRepository(self.db), p)
        self.assertEqual(n, 1)

    def test_calendar_skips_rows_without_title_or_date(self) -> None:
        p = self._write("calendar.csv", "titel;datum",
                        "Zahnarzt;2026-05-21", "OhneDatum;",
                        ";2026-06-01")
        n = import_csv.import_calendar(CalendarRepository(self.db), p)
        self.assertEqual(n, 1)

    def test_social_skips_rows_without_name(self) -> None:
        p = self._write("social.csv", "name;beziehung",
                        "Oma;Familie", ";Freund")
        n = import_csv.import_social(SocialRepository(self.db), p)
        self.assertEqual(n, 1)

    def test_family_skips_rows_without_name(self) -> None:
        p = self._write("family.csv", "name;rolle",
                        "Max;erwachsen", ";kind")
        n = import_csv.import_family(FamilyRepository(self.db), p)
        self.assertEqual(n, 1)

    def test_bad_number_and_date_fall_back_to_defaults(self) -> None:
        # Kaputte Zahl/Datum darf nicht crashen - Zeile importiert mit Default.
        p = self._write("expenses.csv", "beschreibung;betrag;datum",
                        "Kaffee;keine-zahl;kein-datum")
        n = import_csv.import_expenses(ExpenseRepository(self.db), p)
        self.assertEqual(n, 1)
        e = ExpenseRepository(self.db).list_all()[0]
        self.assertEqual(e.amount, 0.0)
        self.assertIsNone(e.spent_on)


class TestIcsImportDstRecurrence(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ah_ics_dst_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ics(self, name: str, dtstart_line: str,
             rrule: str = "FREQ=YEARLY") -> Path:
        body = ("BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\n"
                "SUMMARY:DST-Termin\n"
                f"{dtstart_line}\nRRULE:{rrule}\n"
                "END:VEVENT\nEND:VCALENDAR\n")
        p = self.tmp / name
        p.write_text(body, encoding="utf-8")
        return p

    def test_floating_time_on_dst_day_keeps_calendar_date(self) -> None:
        # 2026-03-29 ist die EU-Sommerzeit-Umstellung; floating 02:30 "gibt es"
        # in einigen Zonen nicht - das Datum muss dennoch stabil bleiben.
        events = import_events(self._ics("dst.ics", "DTSTART:20260329T023000"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].due_date, date(2026, 3, 29))
        self.assertEqual(events[0].recurrence_days, 365)

    def test_tzid_parameter_is_stripped_date_stable(self) -> None:
        # Herbst-Umstellung 2026-10-25, mit TZID-Parameter (kein 'Z').
        events = import_events(self._ics(
            "tz.ics", "DTSTART;TZID=Europe/Berlin:20261025T023000"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].due_date, date(2026, 10, 25))
        self.assertEqual(events[0].recurrence_days, 365)

    def test_pure_date_yearly_recurrence_preserved(self) -> None:
        events = import_events(self._ics("pure.ics", "DTSTART:20260329"))
        self.assertEqual(events[0].due_date, date(2026, 3, 29))
        self.assertEqual(events[0].recurrence_days, 365)


if __name__ == "__main__":
    unittest.main()
