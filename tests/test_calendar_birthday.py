"""
Regressionstest fuer den Schalttag-Bug in modules.calendar.

Ein am 29. Februar geborenes Haushaltsmitglied liess
`date.replace(year=...)` in einem Nicht-Schaltjahr ein ValueError werfen,
das ausserhalb des try/except lag -> die GESAMTE Kalender-/Termin-Ansicht
kippte in einen Fehler, statt diesen einen Geburtstag sauber zu behandeln.
"""
from __future__ import annotations

import unittest
from datetime import date

from modules.calendar import CalendarModule, _birthday_in_year


class _StubContext:
    """Minimaler ModuleContext-Ersatz, der nur family.members liefert."""

    def __init__(self, members: list[dict]) -> None:
        self._members = members

    def has_capability(self, name: str) -> bool:
        return name == "family.members"

    def call(self, name: str, **kwargs):
        if name == "family.members":
            return {"members": self._members}
        return {}


class TestBirthdayInYear(unittest.TestCase):

    def test_leap_day_falls_back_to_feb_28_in_non_leap_year(self) -> None:
        bday = date(2000, 2, 29)
        # 2027 ist KEIN Schaltjahr -> darf nicht werfen.
        self.assertEqual(_birthday_in_year(bday, 2027), date(2027, 2, 28))

    def test_leap_day_kept_in_leap_year(self) -> None:
        bday = date(2000, 2, 29)
        self.assertEqual(_birthday_in_year(bday, 2028), date(2028, 2, 29))

    def test_ordinary_day_unchanged(self) -> None:
        self.assertEqual(_birthday_in_year(date(1990, 7, 1), 2026),
                         date(2026, 7, 1))


class TestBirthdayEventsDoesNotCrashOnLeapDay(unittest.TestCase):

    def test_feb_29_member_does_not_break_view(self) -> None:
        module = CalendarModule.__new__(CalendarModule)
        module._ctx = _StubContext([
            {"name": "Schalttagskind", "birthday": "2000-02-29"},
            {"name": "Normal", "birthday": "1990-07-01"},
        ])
        # Grosser Horizont, damit beide Geburtstage sicher im Fenster liegen.
        events = list(module._birthday_events(horizon_days=400))
        names = {e.title for e in events}
        self.assertIn("Geburtstag: Schalttagskind", names)
        self.assertIn("Geburtstag: Normal", names)


if __name__ == "__main__":
    unittest.main()
