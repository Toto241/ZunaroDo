"""
Tests: Rechtstexte sind aus der Mobile-App heraus erreichbar
(Play-Store-Anforderung) und die Verdrahtung ist konsistent.

Kivy/KivyMD sind in der Test-Umgebung nicht zwingend installiert,
deshalb pruefen die Tests die Quelltexte (wie
tests/test_compliance_gates.py) plus die kivyfreie Logik
(legal_menu_entries-Vertrag, services/legal-Aufloesung, i18n-Keys).
"""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from services.legal import LEGAL_DOCS, resolve_legal

_REPO = Path(__file__).resolve().parent.parent


class TestLegalReachableFromUi(unittest.TestCase):
    """Der Mehr-Screen bindet die vier Rechtstexte ein."""

    def test_more_screen_wires_legal_entries(self) -> None:
        more = (_REPO / "mobile" / "screens" / "more.py").read_text(
            encoding="utf-8")
        self.assertIn("legal_menu_entries", more)
        self.assertIn("_open_legal_page", more)
        self.assertIn("LegalDocScreen", more)

    def test_legal_screen_uses_resolver(self) -> None:
        src = (_REPO / "mobile" / "screens" / "legal_doc.py").read_text(
            encoding="utf-8")
        self.assertIn("resolve_legal", src)


class TestMenuEntriesContract(unittest.TestCase):
    """legal_menu_entries deckt alle LEGAL_DOCS ab (ohne Kivy-Import)."""

    def _entries(self) -> list[tuple[str, str, str, str]]:
        # AST-Auswertung statt Import: legal_doc.py zieht KivyMD.
        src = (_REPO / "mobile" / "screens" / "legal_doc.py").read_text(
            encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if (isinstance(node, ast.FunctionDef)
                    and node.name == "legal_menu_entries"):
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Return):
                        return ast.literal_eval(stmt.value)
        raise AssertionError("legal_menu_entries nicht gefunden")

    def test_all_legal_docs_have_menu_entry(self) -> None:
        docs = {doc for _i, _k, _f, doc in self._entries()}
        self.assertEqual(docs, set(LEGAL_DOCS))

    def test_all_referenced_docs_resolve(self) -> None:
        for _icon, _key, _fallback, doc in self._entries():
            res = resolve_legal(doc, "de")
            self.assertIsNotNone(res, f"{doc} fehlt in legal/")
            text, lang = res
            self.assertEqual(lang, "de")
            self.assertTrue(text.strip())

    def test_i18n_keys_exist_in_de_and_en(self) -> None:
        keys = {key for _i, key, _f, _d in self._entries()}
        for locale in ("de", "en"):
            data = json.loads((_REPO / "locales" / f"{locale}.json")
                              .read_text(encoding="utf-8"))
            missing = keys - set(data)
            self.assertFalse(
                missing, f"{locale}.json fehlen Keys: {sorted(missing)}")


class TestLegalDocsPackaged(unittest.TestCase):
    """buildozer.spec packt legal/*.md ins APK (sonst leere Screens)."""

    def test_include_patterns_contain_legal(self) -> None:
        spec = (_REPO / "buildozer.spec").read_text(encoding="utf-8")
        for line in spec.splitlines():
            if line.strip().startswith("source.include_patterns"):
                self.assertIn("legal/*.md", line)
                return
        raise AssertionError("source.include_patterns fehlt in buildozer.spec")


if __name__ == "__main__":                           # pragma: no cover
    unittest.main()
