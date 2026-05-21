"""
Tests der HeadlessApp-Fassade: Navigation, Verdrahtung der Presenter und
ein end-to-end-Flow über mehrere Screens hinweg - vollautomatisch, ohne UI.
"""
from __future__ import annotations

import unittest

from mobile.headless_app import HeadlessApp


class TestHeadlessApp(unittest.TestCase):

    def test_navigation_between_tabs(self) -> None:
        with HeadlessApp() as app:
            self.assertEqual(app.current_tab, "dashboard")
            for tab in app.TABS:
                self.assertEqual(app.navigate(tab), tab)
                self.assertEqual(app.current_tab, tab)

    def test_unknown_tab_rejected(self) -> None:
        with HeadlessApp() as app:
            with self.assertRaises(ValueError):
                app.navigate("gibtsnicht")

    def test_all_presenters_wired(self) -> None:
        with HeadlessApp() as app:
            for name in ("dashboard", "contracts", "orders", "contacts",
                         "search", "calendar", "finance"):
                self.assertTrue(hasattr(app, name), name)

    def test_end_to_end_flow_reflects_in_dashboard(self) -> None:
        with HeadlessApp() as app:
            app.navigate("contracts")
            app.contracts.add(name="Netflix", category="streaming",
                              monthly_cost=12.0)
            self.assertEqual(
                app.contracts.list(category="streaming")["count"], 1)
            # Derselbe Datensatz erscheint im Dashboard-Summary.
            self.assertGreaterEqual(
                app.dashboard.summary()["contracts_count"], 1)

    def test_close_is_idempotent(self) -> None:
        app = HeadlessApp()
        app.close()
        app.close()        # darf nicht werfen


if __name__ == "__main__":
    unittest.main()
