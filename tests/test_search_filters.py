"""
Tests fuer die optionalen Such-Filter (R4): Zeitraum, Status, Kategorie.

Ergaenzt die Querbeet-Suche (`system.search`) um Filter und prueft, dass
ein gesetzter Filter Treffer ohne das jeweilige Feld ausschliesst und auch
ohne Suchwort funktioniert.
"""
from __future__ import annotations

import os
import unittest

from database import ProposalRepository
from models import Proposal

from tests.test_smoke import _build_system


class TestSearchFilters(unittest.TestCase):

    def setUp(self) -> None:
        self.db, self.registry, _, self.path = _build_system()
        # Vertrag (Kategorie mobilfunk, Status active, Start 2025-01-01)
        self.registry.dispatch("contracts.add", dict(
            name="Telekom Mobilfunk", category="mobilfunk",
            provider="Telekom", start_date="2025-01-01",
            minimum_term_months=1, notice_period_months=1,
            auto_renew_months=1, monthly_cost=29.99))
        # Termin (Kategorie termin, Faelligkeit 2025-06-15)
        self.registry.dispatch("calendar.add_event", dict(
            title="Buergeramt Telekom-Sache", due_date="2025-06-15",
            category="termin"))
        # Ausgaben mit unterschiedlichen Daten/Kategorien
        self.registry.dispatch("finance.add_expense", dict(
            description="Telekom Roaming", amount=12.0,
            category="mobilfunk", spent_on="2025-01-20"))
        self.registry.dispatch("finance.add_expense", dict(
            description="Telekom Hardware", amount=99.0,
            category="elektronik", spent_on="2025-08-10"))
        # Familienmitglied (kein Status, keine Kategorie, kein Datum)
        self.registry.dispatch("family.add_member",
                                {"name": "Telekom-Anna", "role": "erwachsen"})
        # Offener Vorschlag (Status offen)
        ProposalRepository(self.db).add(Proposal(
            source="mail", summary="Telekom Tarifwechsel",
            target_capability="contracts.add"))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.path)

    def _search(self, **params) -> dict:
        return self.registry.dispatch("system.search", params)

    def test_search_filters_by_category(self) -> None:
        """Kategorie-Filter liefert nur Treffer der gewaehlten Kategorie."""
        result = self._search(query="telekom", category="termin")
        sources = {h["source"] for h in result["hits"]}
        self.assertEqual(sources, {"calendar"})
        # mobilfunk trifft Vertrag UND Ausgabe, sonst nichts
        result = self._search(query="telekom", category="mobilfunk")
        sources = {h["source"] for h in result["hits"]}
        self.assertEqual(sources, {"contracts", "expenses"})

    def test_search_filters_by_date_range(self) -> None:
        """Termine/Ausgaben ausserhalb des Zeitraums fehlen."""
        result = self._search(query="telekom",
                              date_from="2025-06-01", date_to="2025-12-31")
        # Im Fenster: Termin (06-15) und Hardware-Ausgabe (08-10).
        ids = {(h["source"], h["title"]) for h in result["hits"]}
        self.assertIn(("calendar", "Buergeramt Telekom-Sache"), ids)
        self.assertIn(("expenses", "Telekom Hardware"), ids)
        # Ausserhalb: Vertrag (01-01), Roaming (01-20), und alle Quellen
        # ohne Datum (family, proposals) werden ausgeschlossen.
        self.assertNotIn(("expenses", "Telekom Roaming"), ids)
        sources = {h["source"] for h in result["hits"]}
        self.assertNotIn("contracts", sources)
        self.assertNotIn("family", sources)
        self.assertNotIn("proposals", sources)

    def test_search_filters_by_status(self) -> None:
        """Status-Filter liefert z.B. nur offene Vorschlaege."""
        result = self._search(query="telekom", status="offen")
        sources = {h["source"] for h in result["hits"]}
        self.assertEqual(sources, {"proposals"})
        # active trifft nur den Vertrag
        result = self._search(query="telekom", status="active")
        sources = {h["source"] for h in result["hits"]}
        self.assertEqual(sources, {"contracts"})

    def test_search_empty_query_with_filter_lists_filtered(self) -> None:
        """Filter ohne Suchwort listet die gefilterten Treffer."""
        result = self._search(category="elektronik")
        self.assertNotIn("error", result)
        sources = {h["source"] for h in result["hits"]}
        self.assertEqual(sources, {"expenses"})
        self.assertEqual(result["count"], 1)

    def test_search_combines_query_and_filter(self) -> None:
        """Suchwort und Filter wirken als UND-Verknuepfung."""
        result = self._search(query="hardware", category="mobilfunk")
        # 'hardware' trifft nur die Elektronik-Ausgabe -> Kategorie passt nicht
        self.assertEqual(result["count"], 0)

    def test_search_short_query_without_filter_rejected(self) -> None:
        """Ohne Filter bleibt das 2-Zeichen-Minimum bestehen."""
        self.assertIn("error", self._search(query="a"))

    def test_search_invalid_date_rejected(self) -> None:
        """Unparsbares Datum liefert einen klaren Fehler."""
        result = self._search(query="telekom", date_from="01.01.2025")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
