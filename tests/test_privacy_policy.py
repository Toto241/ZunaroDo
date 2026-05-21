"""
Tests fuer tools/privacy_policy.py.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import privacy_policy as pp


class TestFindPlaceholders(unittest.TestCase):

    def test_detects_template_tokens(self) -> None:
        text = "Anbieter: [ANBIETER_NAME], Ort [PLZ_ORT]."
        self.assertEqual(pp.find_placeholders(text),
                         ["[ANBIETER_NAME]", "[PLZ_ORT]"])

    def test_ignores_markdown_links(self) -> None:
        text = "Siehe [services/gate.py](../services/gate.py) und [ANBIETER]."
        self.assertEqual(pp.find_placeholders(text), ["[ANBIETER]"])

    def test_unique_and_sorted(self) -> None:
        text = "[B] [A] [B]"
        self.assertEqual(pp.find_placeholders(text), ["[A]", "[B]"])

    def test_clean_text_returns_empty(self) -> None:
        self.assertEqual(pp.find_placeholders("Alles ausgefuellt."), [])


class TestBuildHtml(unittest.TestCase):

    def test_self_contained_document(self) -> None:
        out = pp.build_html("# Titel\n\nText.", title="Datenschutz")
        self.assertIn("<!doctype html>", out)
        self.assertIn('<article class="doc">', out)
        self.assertIn("<title>Datenschutz</title>", out)
        # DOC_CSS eingebettet -> kein externer Request
        self.assertIn(".doc", out)
        self.assertNotIn("href=\"http", out.split("<article")[0]
                         .replace('content="index,follow"', ""))

    def test_renders_markdown(self) -> None:
        out = pp.build_html("## Abschnitt\n\n- Punkt eins")
        self.assertIn("<h2", out)
        self.assertIn("<li>Punkt eins</li>", out)


class TestCheck(unittest.TestCase):

    def _repo_with_policy(self, tmp: Path, body: str) -> Path:
        (tmp / "legal").mkdir()
        (tmp / "legal" / "DATENSCHUTZ.md").write_text(body, encoding="utf-8")
        return tmp

    def test_missing_file_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            issues = pp.check(Path(t))
            self.assertTrue(any(sev == "error" for sev, _ in issues))

    def test_placeholders_warn(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo_with_policy(Path(t), "Anbieter [ANBIETER_NAME].")
            issues = pp.check(repo)
            self.assertTrue(any("Vorlagen-Platzhalter" in m for _, m in issues))
            self.assertFalse(any(sev == "error" for sev, _ in issues))

    def test_finalized_policy_no_warning_about_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo_with_policy(Path(t), "Vollstaendig ausgefuellt.")
            issues = pp.check(repo)
            self.assertFalse(any("Vorlagen-Platzhalter" in m for _, m in issues))


class TestRealRepo(unittest.TestCase):

    def test_real_check_has_no_errors(self) -> None:
        # Vorlage -> Warnungen erlaubt, aber keine harten Fehler.
        issues = pp.check()
        self.assertEqual([i for i in issues if i[0] == "error"], [])

    def test_real_build_produces_article(self) -> None:
        md = pp.POLICY_MD.read_text(encoding="utf-8")
        out = pp.build_html(md)
        self.assertIn('<article class="doc">', out)


if __name__ == "__main__":                            # pragma: no cover
    unittest.main()
