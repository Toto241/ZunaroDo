"""
Tests fuer den minimalen Markdown-Renderer (tools/md_to_html.py).

Der Renderer wird vom Dashboard genutzt, um TESTING.md, UI_CONCEPT.md,
PLAYSTORE.md und protocol.md als HTML neben dashboard.html zu legen.
Wenn er bricht, sind die Doku-Karten im Dashboard nicht klickbar.
"""
from __future__ import annotations

import pytest

from tools.md_to_html import markdown_to_html, render_doc


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


def test_renders_headings_with_anchors():
    html = markdown_to_html("# Hello World")
    assert '<h1 id="hello-world">' in html
    assert 'href="#hello-world"' in html


def test_renders_h2_to_h6():
    out = markdown_to_html("## A\n### B\n#### C\n##### D\n###### E")
    for level in range(2, 7):
        assert f"<h{level} " in out


def test_renders_paragraphs():
    out = markdown_to_html("First paragraph.\n\nSecond paragraph.")
    assert "<p>First paragraph.</p>" in out
    assert "<p>Second paragraph.</p>" in out


def test_renders_bold_italic_code():
    out = markdown_to_html("a **b** c *d* e `f` g ***bi***")
    assert "<strong>b</strong>" in out
    assert "<em>d</em>" in out
    assert "<code>f</code>" in out
    assert "<strong><em>bi</em></strong>" in out


def test_inline_code_protects_from_bold():
    out = markdown_to_html("text with `**not bold**` inside")
    assert "<code>**not bold**</code>" in out
    assert "<strong>not bold</strong>" not in out


def test_renders_unordered_list():
    out = markdown_to_html("- a\n- b\n- c")
    assert out.count("<li>") == 3
    assert "<ul>" in out


def test_renders_ordered_list():
    out = markdown_to_html("1. one\n2. two\n3. three")
    assert "<ol>" in out and out.count("<li>") == 3


def test_renders_table():
    md = "| A | B |\n| --- | --- |\n| 1 | 2 |\n| 3 | 4 |"
    out = markdown_to_html(md)
    assert "<table>" in out
    assert "<th>A</th>" in out and "<th>B</th>" in out
    assert "<td>1</td>" in out and "<td>4</td>" in out


def test_renders_fenced_code_block():
    md = "```python\nprint('hi')\n```"
    out = markdown_to_html(md)
    assert "<pre><code" in out
    assert 'class="lang-python"' in out
    assert "print(" in out


def test_escapes_html_in_paragraphs():
    out = markdown_to_html("<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out


def test_renders_link():
    out = markdown_to_html("[click](https://example.com)")
    assert '<a href="https://example.com">click</a>' in out


def test_renders_blockquote():
    out = markdown_to_html("> first line\n> second line")
    assert "<blockquote>" in out
    assert "first line" in out and "second line" in out


def test_renders_hr():
    out = markdown_to_html("a\n\n---\n\nb")
    assert "<hr />" in out


def test_doc_wrapper_includes_dashboard_css():
    out = render_doc("title", "# h\n\nbody")
    # Wrapper laedt die gleiche CSS-Variablen-Sammlung wie das Dashboard
    assert "--surface" in out
    assert "<article class=\"doc\">" in out


def test_doc_wrapper_back_link():
    out = render_doc("title", "# h", back_link="dashboard.html")
    assert 'href="dashboard.html"' in out
