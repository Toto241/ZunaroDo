"""
Tests fuer services/legal.py (lokalisierte Rechtstexte mit Fallback).
"""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from services import legal


class TestRealRepoFallback(unittest.TestCase):
    """Gegen das echte Repo: deutsche Originale existieren, kein Crash."""

    def test_all_docs_resolve_to_german(self) -> None:
        for doc in legal.LEGAL_DOCS:
            res = legal.resolve_legal(doc, "de")
            self.assertIsNotNone(res, f"{doc} fehlt")
            text, lang = res
            self.assertEqual(lang, "de")
            self.assertTrue(text.strip())

    def test_unknown_language_falls_back_to_german(self) -> None:
        # Es gibt (noch) keine franzoesische Fassung -> Deutsch.
        res = legal.resolve_legal("DATENSCHUTZ", "fr")
        self.assertIsNotNone(res)
        _text, lang = res
        self.assertEqual(lang, "de")

    def test_legal_path_points_at_existing_file(self) -> None:
        p = legal.legal_path("IMPRESSUM", "de")
        self.assertIsNotNone(p)
        self.assertTrue(p.is_file())

    def test_coverage_lists_german(self) -> None:
        cov = legal.coverage()
        for doc in legal.LEGAL_DOCS:
            self.assertIn("de", cov[doc])


class TestTranslationResolution(unittest.TestCase):
    """Mit simulierter Uebersetzung in einem Temp-legal-Verzeichnis."""

    def _patched(self, tmp: Path):
        return mock.patch.object(legal, "_LEGAL_DIR", tmp)

    def test_prefers_translation_when_present(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            (tmp / "DATENSCHUTZ.md").write_text("Deutsch", encoding="utf-8")
            (tmp / "fr").mkdir()
            (tmp / "fr" / "DATENSCHUTZ.md").write_text("Francais",
                                                       encoding="utf-8")
            with self._patched(tmp):
                text, lang = legal.resolve_legal("DATENSCHUTZ", "fr")
                self.assertEqual(lang, "fr")
                self.assertEqual(text, "Francais")
                self.assertEqual(
                    legal.available_translations("DATENSCHUTZ"), ["de", "fr"])

    def test_missing_doc_returns_none(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            with self._patched(Path(t)):
                self.assertIsNone(legal.resolve_legal("AGB", "de"))
                self.assertIsNone(legal.legal_path("AGB", "de"))

    def test_translation_dir_without_doc_falls_back(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            (tmp / "AGB.md").write_text("Deutsche AGB", encoding="utf-8")
            (tmp / "es").mkdir()  # Ordner da, aber AGB.md fehlt
            with self._patched(tmp):
                text, lang = legal.resolve_legal("AGB", "es")
                self.assertEqual(lang, "de")
                self.assertEqual(text, "Deutsche AGB")


if __name__ == "__main__":                           # pragma: no cover
    unittest.main()
