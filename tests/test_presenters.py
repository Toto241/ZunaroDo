"""
Vollautomatische Tests des UI-Verhaltens über die Presenter-Schicht.

Treibt die toolkit-freie ``HeadlessApp`` (echte Registry, Temp-DB) und
prüft genau die Flows, die sich an der Widget-UI nur schwer automatisieren
lassen: Filter, Anlegen/Abhaken, Leer-/Fehlerzustände, Suche mit/ohne
Stichwort. Kein Display, kein Kivy, kein Emulator nötig.
"""
from __future__ import annotations

import unittest

from app_core.headless_app import HeadlessApp


class TestPresenters(unittest.TestCase):

    def setUp(self) -> None:
        self.app = HeadlessApp()

    def tearDown(self) -> None:
        self.app.close()

    # ---- Verträge ------------------------------------------------------
    def test_contracts_add_list_filter_detail_delete(self) -> None:
        c = self.app.contracts
        c.add(name="Strom", category="strom", provider="SW", monthly_cost=30)
        c.add(name="Handy", category="mobilfunk", monthly_cost=20)
        self.assertEqual(c.list()["count"], 2)
        strom = c.list(category="strom")
        self.assertEqual(strom["count"], 1)
        self.assertEqual(strom["items"][0]["name"], "Strom")
        cid = strom["items"][0]["id"]
        self.assertEqual(c.detail(cid)["name"], "Strom")
        c.delete(cid)
        self.assertEqual(c.list(category="strom")["count"], 0)

    def test_contracts_empty_state(self) -> None:
        view = self.app.contracts.list()
        self.assertTrue(view["empty"])
        self.assertIn("Vertraege", view["empty_text"])
        # i18n-Key fuer lokalisierbare Leer-Anzeige (deutscher Default bleibt).
        self.assertEqual(view["empty_text_key"], "contracts.empty")

    def test_list_views_expose_i18n_keys(self) -> None:
        self.assertEqual(self.app.orders.list()["empty_text_key"],
                         "orders.empty")
        self.assertEqual(self.app.contacts.list()["empty_text_key"],
                         "contacts.empty")
        self.assertEqual(self.app.finance.list()["empty_text_key"],
                         "finance.empty")

    def test_interpolated_empty_views_expose_key_and_params(self) -> None:
        cal = self.app.calendar.list(horizon_days=14)
        self.assertEqual(cal["empty_text_key"], "calendar.empty")
        self.assertEqual(cal["empty_text_params"], {"days": 14})
        fin = self.app.finance.recent(days=7)
        self.assertEqual(fin["empty_text_key"], "finance.recent_empty")
        self.assertEqual(fin["empty_text_params"], {"days": 7})

    def test_search_states_expose_message_keys(self) -> None:
        self.assertEqual(self.app.search.search("a")["message_key"],
                         "search.too_short")
        self.assertEqual(
            self.app.search.search("zzzgibtsnicht")["message_key"],
            "search.no_hits")

    # ---- Aufträge ------------------------------------------------------
    def test_orders_add_priority_category_and_complete(self) -> None:
        o = self.app.orders
        self.assertNotIn("error",
                         o.add("Rasen", priority="hoch", category="garten"))
        order = o.list()["items"][0]
        self.assertEqual(order["priority"], "hoch")
        self.assertEqual(order["category"], "garten")
        o.complete(order["id"])
        self.assertEqual(o.list()["items"][0]["status"], "erledigt")

    def test_orders_invalid_priority_defaults_normal(self) -> None:
        self.app.orders.add("Ohne Prio", priority="quatsch")
        self.assertEqual(self.app.orders.list()["items"][0]["priority"],
                         "normal")

    def test_orders_requires_title(self) -> None:
        self.assertIn("error", self.app.orders.add("   "))

    # ---- Kontakte ------------------------------------------------------
    def test_contacts_relation_filter_and_options(self) -> None:
        self.app.dispatch("social.add_contact",
                          {"name": "Oma", "relation": "Familie"})
        self.app.dispatch("social.add_contact",
                          {"name": "Chef", "relation": "Kollege"})
        view = self.app.contacts.list()
        self.assertEqual(view["count"], 2)
        self.assertEqual(view["relations"], ["Familie", "Kollege"])
        fam = self.app.contacts.list(relation="Familie")
        self.assertEqual(fam["count"], 1)
        self.assertEqual(fam["items"][0]["name"], "Oma")

    # ---- Suche ---------------------------------------------------------
    def test_search_too_short(self) -> None:
        self.assertEqual(self.app.search.search("a")["status"], "too_short")

    def test_search_filter_only_without_query(self) -> None:
        self.app.contracts.add(name="Stromvertrag", category="strom",
                               monthly_cost=10)
        result = self.app.search.search("", category="strom")
        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["count"], 1)

    def test_search_hits_and_empty(self) -> None:
        self.app.contracts.add(name="Stromvertrag", category="strom",
                               monthly_cost=10)
        self.assertEqual(self.app.search.search("Strom")["status"], "ok")
        self.assertEqual(self.app.search.search("zzzgibtsnicht")["status"],
                         "empty")

    # ---- Kalender ------------------------------------------------------
    def test_calendar_add_and_list(self) -> None:
        self.app.calendar.add("Zahnarzt", due_date="2030-01-01")
        view = self.app.calendar.list(horizon_days=3650)
        self.assertGreaterEqual(view["count"], 1)
        self.assertTrue(any("Zahnarzt" in (e.get("title") or "")
                            for e in view["items"]))

    # ---- Finanzen ------------------------------------------------------
    def test_finance_list_empty_then_filled(self) -> None:
        self.assertTrue(self.app.finance.list()["empty"])
        self.app.dispatch("finance.add_expense",
                          {"description": "Kaffee", "amount": 3.5})
        self.assertEqual(self.app.finance.list()["count"], 1)

    def test_finance_add_and_recent_total(self) -> None:
        f = self.app.finance
        self.assertNotIn("error", f.add("Kaffee", "3.50", "essen"))
        self.assertNotIn("error", f.add("Bahn", 9, ""))
        recent = f.recent(days=30)
        self.assertEqual(recent["count"], 2)
        self.assertEqual(recent["total"], 12.5)
        self.assertFalse(recent["empty"])

    def test_finance_add_rejects_bad_amount(self) -> None:
        self.assertIn("error", self.app.finance.add("X", "keine-zahl"))

    def test_calendar_add_via_presenter_defaults_title(self) -> None:
        self.app.calendar.add("", due_date="2030-05-01")
        titles = [e.get("title", "")
                  for e in self.app.calendar.list(horizon_days=3650)["items"]]
        self.assertTrue(any("Termin" in t for t in titles))

    # ---- Dashboard -----------------------------------------------------
    def test_dashboard_summary_and_week(self) -> None:
        summary = self.app.dashboard.summary()
        for key in ("contracts_count", "monthly_total",
                    "upcoming_deadlines", "upcoming_events"):
            self.assertIn(key, summary)
        week = self.app.dashboard.week()
        self.assertEqual(len(week["days"]), 7)


if __name__ == "__main__":
    unittest.main()
