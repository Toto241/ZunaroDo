"""
Tests fuer mobile/helpers.py.

Diese Tests brauchen *kein* Kivy und sind deshalb auf CI ohne extra
Abhaengigkeiten lauffaehig.
"""
from __future__ import annotations

import unittest
from datetime import date, timedelta

from mobile.helpers import (AUTO_LANGUAGE_LABEL, dashboard_summary,
                              days_until, format_currency, group_by_module,
                              language_menu_items, relative_when, truncate,
                              urgency_color)


class TestFormatCurrency(unittest.TestCase):

    def test_normal(self) -> None:
        self.assertEqual(format_currency(12.5), "12,50 €")

    def test_thousands_separator(self) -> None:
        self.assertEqual(format_currency(1234.56), "1.234,56 €")

    def test_zero(self) -> None:
        self.assertEqual(format_currency(0), "0,00 €")

    def test_invalid(self) -> None:
        self.assertEqual(format_currency("nicht-zahl"), "")
        self.assertEqual(format_currency(None), "")

    def test_other_currency(self) -> None:
        self.assertEqual(format_currency(10, currency="USD"),
                          "10,00 USD")


class TestDaysUntil(unittest.TestCase):

    def test_today(self) -> None:
        self.assertEqual(days_until(date.today().isoformat()), 0)

    def test_future(self) -> None:
        target = (date.today() + timedelta(days=5)).isoformat()
        self.assertEqual(days_until(target), 5)

    def test_past(self) -> None:
        target = (date.today() - timedelta(days=3)).isoformat()
        self.assertEqual(days_until(target), -3)

    def test_invalid(self) -> None:
        self.assertIsNone(days_until("nicht-iso"))
        self.assertIsNone(days_until(None))
        self.assertIsNone(days_until(""))


class TestRelativeWhen(unittest.TestCase):

    def test_today(self) -> None:
        self.assertEqual(relative_when(date.today().isoformat()), "heute")

    def test_tomorrow(self) -> None:
        target = (date.today() + timedelta(days=1)).isoformat()
        self.assertEqual(relative_when(target), "morgen")

    def test_yesterday(self) -> None:
        target = (date.today() - timedelta(days=1)).isoformat()
        self.assertEqual(relative_when(target), "gestern")

    def test_future(self) -> None:
        target = (date.today() + timedelta(days=7)).isoformat()
        self.assertEqual(relative_when(target), "in 7 Tagen")

    def test_past(self) -> None:
        target = (date.today() - timedelta(days=4)).isoformat()
        self.assertEqual(relative_when(target), "vor 4 Tagen")

    def test_invalid_returns_empty(self) -> None:
        self.assertEqual(relative_when(None), "")
        self.assertEqual(relative_when(""), "")


class TestUrgencyColor(unittest.TestCase):

    def test_overdue_is_error(self) -> None:
        self.assertEqual(urgency_color(-2), "error")

    def test_within_week_is_error(self) -> None:
        self.assertEqual(urgency_color(3), "error")
        self.assertEqual(urgency_color(7), "error")

    def test_within_month_is_warning(self) -> None:
        self.assertEqual(urgency_color(15), "warning")
        self.assertEqual(urgency_color(30), "warning")

    def test_far_future_is_normal(self) -> None:
        self.assertEqual(urgency_color(60), "normal")

    def test_none_is_normal(self) -> None:
        self.assertEqual(urgency_color(None), "normal")


class TestTruncate(unittest.TestCase):

    def test_short_unchanged(self) -> None:
        self.assertEqual(truncate("Hallo", 10), "Hallo")

    def test_long_gets_ellipsis(self) -> None:
        result = truncate("Das ist ein sehr langer Text", 12)
        self.assertTrue(result.endswith("…"))
        self.assertLessEqual(len(result), 12)

    def test_empty(self) -> None:
        self.assertEqual(truncate("", 10), "")


class TestGroupByModule(unittest.TestCase):

    def test_groups_by_module_id(self) -> None:
        items = [
            {"module_id": "contracts", "title": "A"},
            {"module_id": "contracts", "title": "B"},
            {"module_id": "calendar", "title": "C"},
        ]
        groups = group_by_module(items)
        self.assertEqual(len(groups["contracts"]), 2)
        self.assertEqual(len(groups["calendar"]), 1)

    def test_unknown_falls_back(self) -> None:
        items = [{"title": "X"}]
        groups = group_by_module(items)
        self.assertIn("sonstiges", groups)


class TestDashboardSummary(unittest.TestCase):
    """dashboard_summary akzeptiert ein dispatch-Callable als Argument."""

    def test_aggregates_three_sources(self) -> None:
        def mock_dispatch(name: str, _args: dict) -> dict:
            if name == "contracts.list":
                return {"count": 4, "total_monthly_cost": 89.5}
            if name == "contracts.upcoming_deadlines":
                return {"deadlines": [
                    {"contract_name": "Strom",
                     "due_date": "2099-01-01",
                     "days_remaining": 30}]}
            if name == "calendar.list_upcoming":
                return {"events": [
                    {"title": "Zahnarzt",
                     "due_date": "2099-01-02"}]}
            return {}
        out = dashboard_summary(mock_dispatch)
        self.assertEqual(out["contracts_count"], 4)
        self.assertEqual(out["monthly_total"], 89.5)
        self.assertEqual(len(out["upcoming_deadlines"]), 1)
        self.assertEqual(len(out["upcoming_events"]), 1)

    def test_robust_against_errors(self) -> None:
        def broken_dispatch(_name: str, _args: dict) -> dict:
            raise RuntimeError("boom")
        out = dashboard_summary(broken_dispatch)
        # Keine Exception, alle Felder mit Default befuellt
        self.assertEqual(out["contracts_count"], 0)
        self.assertEqual(out["monthly_total"], 0.0)
        self.assertEqual(out["upcoming_deadlines"], [])
        self.assertEqual(out["upcoming_events"], [])

    def test_truncates_to_phone_friendly_count(self) -> None:
        def many_dispatch(name: str, _args: dict) -> dict:
            if name == "contracts.upcoming_deadlines":
                return {"deadlines": [{"contract_name": f"V{i}",
                                          "due_date": "2099-01-01",
                                          "days_remaining": i}
                                         for i in range(20)]}
            if name == "calendar.list_upcoming":
                return {"events": [{"title": f"E{i}",
                                       "due_date": "2099-01-01"}
                                       for i in range(20)]}
            if name == "contracts.list":
                return {"count": 0, "total_monthly_cost": 0.0}
            return {}
        out = dashboard_summary(many_dispatch)
        # Phone-Limits: 3 Fristen, 5 Termine
        self.assertEqual(len(out["upcoming_deadlines"]), 3)
        self.assertEqual(len(out["upcoming_events"]), 5)


class TestLanguageMenuItems(unittest.TestCase):

    def test_first_entry_is_auto(self) -> None:
        items = language_menu_items("de")
        self.assertEqual(items[0]["code"], "auto")
        self.assertEqual(items[0]["label"], AUTO_LANGUAGE_LABEL)

    def test_exactly_one_selected(self) -> None:
        for current in ("de", "auto", "fr", None, "es-ES", "xx"):
            with self.subTest(current=current):
                items = language_menu_items(current)
                selected = [i for i in items if i["selected"]]
                self.assertEqual(len(selected), 1)

    def test_default_selects_german(self) -> None:
        items = language_menu_items(None)
        sel = next(i for i in items if i["selected"])
        self.assertEqual(sel["code"], "de")

    def test_auto_selected(self) -> None:
        items = language_menu_items("auto")
        self.assertTrue(items[0]["selected"])

    def test_region_code_normalized(self) -> None:
        items = language_menu_items("fr-FR")
        sel = next(i for i in items if i["selected"])
        self.assertEqual(sel["code"], "fr")

    def test_unknown_setting_falls_back_to_german(self) -> None:
        items = language_menu_items("xx")
        sel = next(i for i in items if i["selected"])
        self.assertEqual(sel["code"], "de")

    def test_contains_all_available_languages(self) -> None:
        from services.i18n import I18n
        codes = {i["code"] for i in language_menu_items("de")}
        for code, _name in I18n.available_languages():
            self.assertIn(code, codes)
        self.assertIn("auto", codes)


if __name__ == "__main__":                       # pragma: no cover
    unittest.main()
