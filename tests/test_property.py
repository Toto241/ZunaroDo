"""
Property-based Tests via 'hypothesis' (optional).

Wird komplett uebersprungen, wenn das Paket nicht installiert ist -
damit das Test-Setup auch ohne Extra-Dependencies gruen ist.
"""
from __future__ import annotations

import unittest


try:
    from hypothesis import given, settings, strategies as st
    HAS_HYPOTHESIS = True
except ImportError:                              # pragma: no cover
    HAS_HYPOTHESIS = False


if HAS_HYPOTHESIS:

    from datetime import date, timedelta

    class TestEscapingRoundtrip(unittest.TestCase):
        """services/escaping.py: escape -> unescape ist Identitaet."""

        @settings(max_examples=200)
        @given(st.text(min_size=0, max_size=200))
        def test_roundtrip(self, raw: str) -> None:
            from services.escaping import escape_text, unescape_text
            normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
            self.assertEqual(unescape_text(escape_text(normalized)),
                             normalized)

    class TestNextCancellationDateInvariant(unittest.TestCase):
        """next_cancellation_date liegt im gueltigen Bereich."""

        @settings(max_examples=100)
        @given(
            start_offset_days=st.integers(min_value=-3650, max_value=3650),
            minimum_term=st.integers(min_value=1, max_value=60),
            notice=st.integers(min_value=1, max_value=12),
            renew=st.integers(min_value=1, max_value=24),
        )
        def test_deadline_makes_sense(self, start_offset_days: int,
                                       minimum_term: int, notice: int,
                                       renew: int) -> None:
            from models import Contract
            from modules.contracts import next_cancellation_date
            today = date(2025, 6, 15)
            contract = Contract(
                name="X", category="streaming", provider="",
                start_date=today + timedelta(days=start_offset_days),
                minimum_term_months=minimum_term,
                notice_period_months=notice,
                auto_renew_months=renew,
                monthly_cost=10.0,
            )
            deadline = next_cancellation_date(contract, today=today)
            self.assertIsNotNone(deadline)
            self.assertGreaterEqual(deadline, today)
            max_future = today + timedelta(
                days=(minimum_term + renew * 2 + notice) * 32)
            self.assertLessEqual(deadline, max_future)

    class TestSlugifyInvariant(unittest.TestCase):
        """slugify(...) erzeugt nur erlaubte Zeichen."""

        @settings(max_examples=200)
        @given(st.text(min_size=0, max_size=100))
        def test_only_safe_chars(self, raw: str) -> None:
            from services.output import slugify
            result = slugify(raw)
            for ch in result:
                self.assertTrue(ch.isalnum() or ch == "_",
                                  f"Unerlaubtes Zeichen '{ch}' in '{result}'")
            self.assertGreater(len(result), 0)

else:                                            # pragma: no cover

    class TestPropertyBasedSkipped(unittest.TestCase):
        @unittest.skip("hypothesis nicht installiert")
        def test_skipped(self) -> None:
            pass


if __name__ == "__main__":                       # pragma: no cover
    unittest.main()
