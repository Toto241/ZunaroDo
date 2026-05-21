"""
Tests fuer Prioritaeten & Kategorie-Filter (R3).

Deckt ab:
  - Kategorie-Filter fuer Vertraege, Kontakte (Beziehung) und Auftraege,
  - Prioritaets-Vergabe und stabile Sortierung der Auftraege,
  - additive Schema-Migration v2 -> v3 (priority/category auf
    household_orders) ohne Datenverlust.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from database import Database, FamilyRepository
from models import HouseholdOrder

from tests.test_smoke import _build_system


class TestPriorityAndCategoryFilters(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    # ---- Kategorie-Filter ---------------------------------------------
    def test_contracts_filter_by_category(self) -> None:
        self.registry.dispatch("contracts.add", dict(
            name="Handy", category="mobilfunk", provider="Telekom",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1, monthly_cost=20.0))
        self.registry.dispatch("contracts.add", dict(
            name="Haftpflicht", category="versicherung", provider="Allianz",
            start_date="2025-01-01", minimum_term_months=1,
            notice_period_months=1, auto_renew_months=1, monthly_cost=10.0))
        result = self.registry.dispatch("contracts.list",
                                        {"category": "versicherung"})
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["contracts"][0]["name"], "Haftpflicht")
        # ohne Filter: beide
        self.assertEqual(
            self.registry.dispatch("contracts.list", {})["count"], 2)

    def test_contacts_filter_by_relation(self) -> None:
        self.registry.dispatch("social.add_contact",
                               {"name": "Oma", "relation": "Familie"})
        self.registry.dispatch("social.add_contact",
                               {"name": "Chef", "relation": "Kollege"})
        result = self.registry.dispatch("social.contacts",
                                        {"relation": "familie"})
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["contacts"][0]["name"], "Oma")

    def test_orders_filter_by_category(self) -> None:
        self.registry.dispatch("family.add_member",
                               {"name": "Max", "role": "erwachsen"})
        self.registry.dispatch("family.add_order",
                               {"title": "Steuer abgeben", "assignee": "Max",
                                "category": "finanzen"})
        self.registry.dispatch("family.add_order",
                               {"title": "Rasen maehen", "assignee": "Max",
                                "category": "garten"})
        result = self.registry.dispatch("family.orders",
                                        {"category": "garten"})
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["orders"][0]["title"], "Rasen maehen")

    # ---- Prioritaeten --------------------------------------------------
    def test_order_priority_sort_order(self) -> None:
        """hoch vor mittel vor normal; bei Gleichstand nach Faelligkeit."""
        self.registry.dispatch("family.add_order",
                               {"title": "C-normal", "priority": "normal",
                                "due_date": "2025-01-01"})
        self.registry.dispatch("family.add_order",
                               {"title": "A-hoch", "priority": "hoch",
                                "due_date": "2025-12-31"})
        self.registry.dispatch("family.add_order",
                               {"title": "B-mittel", "priority": "mittel",
                                "due_date": "2025-06-01"})
        orders = self.registry.dispatch("family.orders", {})["orders"]
        titles = [o["title"] for o in orders]
        self.assertEqual(titles, ["A-hoch", "B-mittel", "C-normal"])

    def test_order_default_priority_is_normal(self) -> None:
        self.registry.dispatch("family.add_order", {"title": "Ohne Prio"})
        order = self.registry.dispatch("family.orders", {})["orders"][0]
        self.assertEqual(order["priority"], "normal")

    def test_add_order_rejects_invalid_priority(self) -> None:
        result = self.registry.dispatch("family.add_order",
                                        {"title": "X", "priority": "egal"})
        self.assertIn("error", result)


class TestOrderSchemaMigration(unittest.TestCase):
    """Eine v2-DB ohne priority/category wird verlustfrei auf v3 gehoben."""

    def setUp(self) -> None:
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        # Alte household_orders-Tabelle OHNE priority/category anlegen.
        conn = sqlite3.connect(self.path)
        conn.executescript("""
            CREATE TABLE household_orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                assignee_id INTEGER,
                due_date    TEXT,
                description TEXT DEFAULT '',
                status      TEXT DEFAULT 'offen',
                created_at  TEXT,
                deleted_at  TEXT
            );
            INSERT INTO household_orders (title, status) VALUES ('Altauftrag', 'offen');
            PRAGMA user_version = 2;
        """)
        conn.commit()
        conn.close()

    def tearDown(self) -> None:
        os.unlink(self.path)

    def test_migration_adds_columns_and_keeps_rows(self) -> None:
        db = Database(self.path)
        self.assertEqual(
            db.conn.execute("PRAGMA user_version").fetchone()[0], 3)
        orders = FamilyRepository(db).list_orders()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].title, "Altauftrag")
        # Default greift fuer Bestandszeilen
        self.assertEqual(orders[0].priority, "normal")
        self.assertEqual(orders[0].category, "")
        db.close()


if __name__ == "__main__":
    unittest.main()
