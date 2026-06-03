"""
Tests fuer den HTML-Dashboard-Generator (tools/dashboard.py).

Das Dashboard ist die lauffaehige Prototyp-Visualisierung des in
UI_CONCEPT.md beschriebenen QA-/Release-/Compliance-Cockpits. Diese
Tests stellen sicher, dass

  * der Generator deterministisch dieselbe Struktur erzeugt,
  * Pills und Statusfarben korrekt vergeben werden,
  * die Suchfunktion (Client-Side-JS) eingebettet ist,
  * alle Tests aus protocol.json als Zeilen im Dashboard erscheinen.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.dashboard import (DEFAULT_HTML, DEFAULT_JSON, MARKER_LABEL,
                              _bucket_status, _decision_status, main,
                              render_dashboard)


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


def _synth_protocol() -> dict:
    return {
        "decision": "GO",
        "reasons": [],
        "elapsed_s": 12.34,
        "generated_at": "2026-05-20T10:00:00+00:00",
        "totals": {"passed": 4, "failed": 0, "error": 0, "skipped": 1,
                    "duration_s": 12.34, "count": 5},
        "by_marker": {
            "members": {"count": 2, "passed": 2, "failed": 0, "error": 0,
                         "skipped": 0, "duration_s": 0.5},
            "negative": {"count": 1, "passed": 1, "failed": 0, "error": 0,
                          "skipped": 0, "duration_s": 0.1},
            "privacy": {"count": 1, "passed": 1, "failed": 0, "error": 0,
                         "skipped": 0, "duration_s": 0.1},
            "release_gate": {"count": 1, "passed": 0, "failed": 0,
                              "error": 0, "skipped": 1, "duration_s": 0.0},
        },
        "records": [
            {"id": "x::test_members_a", "classname": "x",
             "name": "test_members_a", "status": "passed",
             "time_s": 0.2, "message": ""},
            {"id": "x::test_members_b", "classname": "x",
             "name": "test_members_b", "status": "passed",
             "time_s": 0.3, "message": ""},
            {"id": "x::test_negative_c", "classname": "x",
             "name": "test_negative_c", "status": "passed",
             "time_s": 0.1, "message": ""},
            {"id": "x::test_privacy_d", "classname": "x",
             "name": "test_privacy_d", "status": "passed",
             "time_s": 0.1, "message": ""},
            {"id": "x::test_release_gate_e", "classname": "x",
             "name": "test_release_gate_e", "status": "skipped",
             "time_s": 0.0, "message": "no env"},
        ],
    }


@pytest.fixture
def synth_html() -> str:
    # Realistischer Quellpfad - die Artefakt-Karten berechnen relative
    # Links auf TESTING.md/UI_CONCEPT.md aus diesem Speicherort.
    from tools.dashboard import DEFAULT_JSON
    return render_dashboard(_synth_protocol(),
                             source_path=DEFAULT_JSON)


def test_decision_status_mapping():
    assert _decision_status("GO") == "go"
    assert _decision_status("NO-GO") == "block"
    assert _decision_status("HOLD") == "hold"
    assert _decision_status("xx") == "unknown"


@pytest.mark.parametrize("bucket,expected", [
    ({"count": 10, "passed": 10, "failed": 0, "error": 0, "skipped": 0}, "go"),
    ({"count": 10, "passed": 9, "failed": 1, "error": 0, "skipped": 0}, "block"),
    ({"count": 10, "passed": 9, "failed": 0, "error": 1, "skipped": 0}, "block"),
    ({"count": 5,  "passed": 1, "failed": 0, "error": 0, "skipped": 4}, "hold"),
    ({"count": 0,  "passed": 0, "failed": 0, "error": 0, "skipped": 0}, "unknown"),
])
def test_bucket_status(bucket, expected):
    assert _bucket_status(bucket) == expected


def test_html_is_self_contained(synth_html):
    # Self-contained = kein externes Script/Link
    assert "<script" in synth_html and "</script>" in synth_html
    assert "src=" not in synth_html, "Dashboard darf KEIN externes JS laden"
    assert "<style>" in synth_html
    # Pflicht-Elemente
    assert "QA / Release / Compliance" in synth_html
    assert "Release-Reifegrad" in synth_html
    assert "Vollständige Test-Liste" in synth_html
    assert "id=\"test-filter\"" in synth_html
    assert "id=\"test-list\"" in synth_html


def test_html_contains_all_records(synth_html):
    p = _synth_protocol()
    for rec in p["records"]:
        assert rec["id"] in synth_html, (
            f"Test-ID {rec['id']} fehlt im Dashboard")


def test_html_has_kpi_for_each_marker(synth_html):
    for marker, label in MARKER_LABEL.items():
        if marker in _synth_protocol()["by_marker"]:
            assert label in synth_html, (
                f"KPI-Karte fuer {marker} ({label}) fehlt")


def test_html_renders_decision_pill(synth_html):
    assert "pill go" in synth_html


def test_html_has_navigation(synth_html):
    """Die TOC oben verlinkt auf die Hauptbereiche - das macht
    dashboard.html erst zu einer richtigen Uebersicht."""
    assert "<nav class=\"toc\">" in synth_html
    for anchor in ("uebersicht", "artefakte", "kpis", "bereiche",
                    "fehler", "tests"):
        assert f'href="#{anchor}"' in synth_html, (
            f"TOC-Link auf #{anchor} fehlt")
        assert f'id="{anchor}"' in synth_html, (
            f"Sprungmarke id={anchor} fehlt")


def test_html_links_to_companion_artifacts(synth_html):
    """Artefakt-Karten muessen die *gerenderten HTML-Versionen* von
    TESTING/UI_CONCEPT/PLAYSTORE/protocol verlinken (im Browser
    lesbar), zusaetzlich die lokalen Report-Rohdateien."""
    # Die HTML-Versionen sind das eigentliche Ziel - so wird das
    # Markdown im Browser nicht als roher Text angezeigt.
    for href in ("TESTING.html", "UI_CONCEPT.html", "PLAYSTORE.html",
                  "protocol.html", "protocol.json", "junit.xml",
                  "pairwise-matrix.tsv"):
        assert href in synth_html, (
            f"Artefakt-Link {href} fehlt im Dashboard")
    assert "artifact-link" in synth_html
    assert synth_html.count("artifact-link") >= 9


def test_html_does_not_contain_nested_anchors(synth_html):
    """Verschachtelte <a>-Tags sind invalides HTML und verursachen,
    dass innere Links nicht klickbar sind."""
    import re
    # Eine Heuristik: jeder schließende </a> sollte einen passenden
    # öffnenden <a haben, ohne dass davor ein weiteres <a kommt.
    open_count = 0
    in_a = False
    pos = 0
    for m in re.finditer(r"<a\b|</a>", synth_html):
        tag = m.group(0)
        if tag == "</a>":
            in_a = False
        else:
            assert not in_a, (
                f"Verschachteltes <a>-Tag bei Pos {m.start()} - "
                f"Kontext: {synth_html[max(0,m.start()-80):m.start()+80]}")
            in_a = True


def test_html_renders_skipped_as_hold(synth_html):
    # Release-Gate-Bereich hat nur skipped -> HOLD
    assert "pill hold" in synth_html


def test_html_escapes_html_in_test_id():
    data = _synth_protocol()
    data["records"].append({
        "id": "<script>alert('xss')</script>",
        "classname": "x", "name": "test_xss",
        "status": "passed", "time_s": 0.0, "message": "",
    })
    html_out = render_dashboard(data, Path("synth.json"))
    assert "<script>alert('xss')</script>" not in html_out, (
        "HTML-Escaping wurde durchbrochen - XSS-Lücke")
    assert "&lt;script&gt;alert(" in html_out


def test_main_runs_against_real_protocol(tmp_path: Path):
    if not DEFAULT_JSON.is_file():
        pytest.skip("Noch kein protocol.json - 'tools.test_protocol' zuerst laufen lassen.")
    out = tmp_path / "dash.html"
    rc = main(["--json", str(DEFAULT_JSON), "--out", str(out),
               "--no-index"])
    assert rc == 0
    assert out.is_file()
    assert out.stat().st_size > 5000
    text = out.read_text(encoding="utf-8")
    assert "Release-Reifegrad" in text
    assert "QA / Release / Compliance" in text


def test_main_handles_missing_input(tmp_path: Path):
    rc = main(["--json", str(tmp_path / "does-not-exist.json"),
               "--out", str(tmp_path / "x.html")])
    assert rc != 0


def test_default_paths_inside_reports_dir():
    assert "reports" in DEFAULT_HTML.as_posix()
    assert "reports" in DEFAULT_JSON.as_posix()


def test_render_dashboard_is_deterministic():
    p = _synth_protocol()
    a = render_dashboard(p, Path("a.json"))
    b = render_dashboard(p, Path("a.json"))
    assert a == b


def test_failure_section_shows_when_records_failed():
    data = _synth_protocol()
    data["records"].append({
        "id": "x::test_breaking",
        "classname": "x", "name": "test_breaking",
        "status": "failed", "time_s": 0.0,
        "message": "AssertionError: foo != bar",
    })
    data["totals"]["failed"] = 1
    data["totals"]["count"] = 6
    html_out = render_dashboard(data, Path("synth.json"))
    assert "Fehlgeschlagene Tests (1)" in html_out
    assert "AssertionError: foo != bar" in html_out
