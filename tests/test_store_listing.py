"""
Tests fuer tools/store_listing.py.
"""
from __future__ import annotations

import unittest

from tools import store_listing as sl


class TestValidateLocalizations(unittest.TestCase):

    def test_clean_curated_passes(self) -> None:
        self.assertEqual(sl.validate_localizations(sl.CURATED), [])

    def test_empty_is_error(self) -> None:
        issues = sl.validate_localizations({})
        self.assertTrue(any(sev == "error" for sev, *_ in issues))

    def test_missing_field_is_error(self) -> None:
        loc = {"de-DE": {"title": "X", "short_description": "Y"}}
        issues = sl.validate_localizations(loc)
        self.assertTrue(any("full_description" in path for _, path, _ in issues))

    def test_too_long_title_is_error(self) -> None:
        loc = {"de-DE": {"title": "X" * 31, "short_description": "Y",
                          "full_description": "Z"}}
        issues = sl.validate_localizations(loc)
        self.assertTrue(any("title" in path and sev == "error"
                            for sev, path, _ in issues))

    def test_limits_match_play(self) -> None:
        self.assertEqual(sl.LIMITS["title"], 30)
        self.assertEqual(sl.LIMITS["short_description"], 80)
        self.assertEqual(sl.LIMITS["full_description"], 4000)


class TestGenerateLocalizations(unittest.TestCase):

    def test_merges_curated_into_base(self) -> None:
        base = {"de-DE": {"title": "Alltagshelfer", "short_description": "s",
                           "full_description": "f"}}
        out = sl.generate_localizations(base)
        self.assertIn("de-DE", out)
        self.assertIn("fr-FR", out)

    def test_does_not_overwrite_existing(self) -> None:
        base = {"fr-FR": {"title": "EIGEN", "short_description": "s",
                           "full_description": "f"}}
        out = sl.generate_localizations(base)
        self.assertEqual(out["fr-FR"]["title"], "EIGEN")

    def test_generated_is_valid(self) -> None:
        out = sl.generate_localizations()
        self.assertEqual(sl.validate_localizations(out), [])


class TestCuratedQuality(unittest.TestCase):

    def test_all_curated_within_limits(self) -> None:
        for loc, fields in sl.CURATED.items():
            for fld, limit in sl.LIMITS.items():
                self.assertLessEqual(
                    len(fields[fld]), limit,
                    f"{loc}.{fld} ueberschreitet {limit}")


class TestRealRepo(unittest.TestCase):

    def test_real_localizations_valid(self) -> None:
        loc = sl._load_localizations()
        errors = [i for i in sl.validate_localizations(loc) if i[0] == "error"]
        self.assertEqual(errors, [])

    def test_real_has_major_languages(self) -> None:
        loc = sl._load_localizations()
        for code in ("de-DE", "en-US", "fr-FR", "es-ES", "it-IT",
                     "nl-NL", "pl-PL", "pt-PT"):
            self.assertIn(code, loc)


if __name__ == "__main__":                            # pragma: no cover
    unittest.main()
