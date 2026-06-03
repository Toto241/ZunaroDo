"""
Tests fuer die Tages-/Wochenuebersicht (R1).

`system.agenda` buendelt die Fristen aller Module und gruppiert sie nach
Kalendertag. Deckt ab: Gruppierung mehrerer Eintraege am selben Tag, die
Sieben-Tage-Spanne der Wochenuebersicht, Ausschluss von Eintraegen
ausserhalb des Fensters und die Parameter-Validierung.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import unittest

from tests.test_smoke import _build_system


class TestAgendaOverview(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def _add_event(self, title: str, offset_days: int) -> None:
        due = (date.today() + timedelta(days=offset_days)).isoformat()
        self.registry.dispatch("calendar.add_event",
                               {"title": title, "due_date": due,
                                "category": "termin"})

    def test_week_view_spans_seven_days(self) -> None:
        result = self.registry.dispatch("system.agenda", {})
        self.assertEqual(result["horizon_days"], 7)
        self.assertEqual(len(result["days"]), 7)
        self.assertEqual(result["from"], date.today().isoformat())
        self.assertEqual(
            result["to"], (date.today() + timedelta(days=6)).isoformat())

    def test_total_matches_buckets(self) -> None:
        # Interne Konsistenz: total == Summe der Tages-Counts + Ueberfaellige.
        self._add_event("Zahnarzt", 2)
        result = self.registry.dispatch("system.agenda", {})
        self.assertEqual(
            result["total"],
            sum(d["count"] for d in result["days"]) + result["overdue_count"])

    def test_day_view_groups_due_items(self) -> None:
        # Dynamisch erzeugte Basis-Ereignisse (Monatsabschluss-Erinnerung,
        # gesetzliche Steuerfristen) sind datumsabhaengig und koennen je nach
        # heutigem Datum auf Offset 2/4 fallen. Daher wird das Delta gegen
        # einen Vorher-Snapshot geprueft statt absoluter Counts.
        before = self.registry.dispatch("system.agenda", {})
        base2 = before["days"][2]["count"]
        base4 = before["days"][4]["count"]
        self._add_event("Zahnarzt", 2)
        self._add_event("Steuerberater", 2)
        self._add_event("Paket abholen", 4)
        result = self.registry.dispatch("system.agenda", {})
        day2 = result["days"][2]
        self.assertEqual(day2["count"], base2 + 2)
        titles = {e["title"] for e in day2["events"]}
        # Das Kalendermodul stellt das Kategorie-Label voran ("Termin: ...").
        # Die selbst hinzugefuegten Termine muessen in der Tagesgruppe stehen.
        self.assertTrue(
            {"Termin: Zahnarzt", "Termin: Steuerberater"} <= titles)
        self.assertEqual(result["days"][4]["count"], base4 + 1)

    def test_events_outside_horizon_excluded_then_included(self) -> None:
        week_before = self.registry.dispatch("system.agenda", {})["total"]
        self._add_event("Fern-Termin", 20)
        week_after = self.registry.dispatch("system.agenda", {})["total"]
        self.assertEqual(week_after, week_before)     # +20 liegt ausserhalb 7d
        month = self.registry.dispatch("system.agenda", {"horizon_days": 30})
        self.assertEqual(len(month["days"]), 30)
        self.assertEqual(month["days"][20]["count"], 1)
        self.assertEqual(month["days"][20]["events"][0]["title"],
                         "Termin: Fern-Termin")

    def test_weekday_label_matches_date(self) -> None:
        result = self.registry.dispatch("system.agenda", {})
        names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
                 "Freitag", "Samstag", "Sonntag"]
        first = result["days"][0]
        self.assertEqual(first["weekday"], names[date.today().weekday()])

    def test_invalid_horizon_rejected(self) -> None:
        self.assertIn("error",
                      self.registry.dispatch("system.agenda",
                                             {"horizon_days": 0}))


if __name__ == "__main__":
    unittest.main()
