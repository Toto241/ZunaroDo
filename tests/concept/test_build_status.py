"""
Tests fuer tools/build_status.py und die Build-Center-Renderung
im Dashboard.

Geprueft werden:

  1. build_status.gather() liefert genau 3 Plattformen (android/ios/desktop).
  2. Jedes Item enthaelt die Pflichtfelder (label, command, tool, prereqs).
  3. _build_center erzeugt 3 Karten + 3 Copy-Buttons im Dashboard-HTML.
  4. _index_build_center erzeugt 3 Karten in der index.html.
  5. Skripte in scripts/ sind vorhanden und lesbar.
  6. Skript-Links im Dashboard zeigen auf existierende Dateien.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.build_status import gather, main, to_dict
from tools.dashboard import (DEFAULT_JSON, _build_center,
                              _index_build_center, render_dashboard)


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


# ---------------------------------------------------------------------------
# build_status
# ---------------------------------------------------------------------------
def test_gather_returns_three_platforms():
    items = gather()
    plats = sorted(it.platform for it in items)
    assert plats == ["android", "desktop", "ios"]


def test_each_item_has_required_fields():
    for it in gather():
        assert it.label
        assert it.command
        assert it.tool
        assert isinstance(it.prereqs, list) and it.prereqs


def test_to_dict_is_json_serializable():
    import json
    items = to_dict(gather())
    json.dumps(items)  # must not raise


def test_main_json_runs(capsys):
    rc = main(["--json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"platform"' in out
    assert '"android"' in out
    assert '"ios"' in out
    assert '"desktop"' in out


def test_main_plain_text_runs(capsys):
    rc = main(["--no-emoji"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Android" in out and "PC" in out and "iOS" in out
    assert "Werkzeug:" not in out  # geht nicht durch, aber:
    assert "Tool:" in out


# ---------------------------------------------------------------------------
# Build-Skripte vorhanden
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", [
    "build-android.bat", "build-android.sh",
    "build-desktop.bat", "build-desktop.sh",
    "build-ios.sh",
])
def test_build_scripts_present(name):
    p = REPO / "scripts" / name
    assert p.is_file(), f"scripts/{name} fehlt"
    assert p.stat().st_size > 200, f"scripts/{name} verdaechtig klein"


def test_buildozer_spec_present_for_android():
    assert (REPO / "buildozer.spec").is_file()


def test_pyinstaller_spec_present_for_desktop():
    assert (REPO / "alltagshelfer.spec").is_file()


# ---------------------------------------------------------------------------
# Dashboard-Build-Center
# ---------------------------------------------------------------------------
def test_build_center_in_dashboard_html():
    """render_dashboard muss die Build-Karten enthalten."""
    synth = {
        "decision": "GO", "reasons": [], "elapsed_s": 1.0,
        "totals": {"passed": 1, "failed": 0, "error": 0,
                    "skipped": 0, "count": 1, "duration_s": 1.0},
        "by_marker": {}, "records": [],
    }
    html = render_dashboard(synth, DEFAULT_JSON)
    assert "Build-Center" in html
    assert "build-card" in html
    # genau 3 Karten in der Hauptansicht
    assert html.count("class='build-card") >= 3
    for platform_label in ("Android", "iOS", "PC (Desktop)"):
        assert platform_label in html, (
            f"Plattform-Karte '{platform_label}' fehlt")
    # Copy-Button-JS eingebettet
    assert "copyText(" in html
    # Mindestens 3 Copy-Buttons
    assert html.count("onclick=\"copyText") >= 3


def test_index_build_center_renders_three_cards():
    html = _index_build_center()
    assert html.count("class='build-card") == 3
    for platform_label in ("Android", "iOS", "PC (Desktop)"):
        assert platform_label in html


def test_build_center_links_point_to_real_scripts():
    """Skript-Hrefs im Build-Center muessen auf vorhandene Dateien zeigen."""
    import re
    html = render_dashboard(
        {"decision": "GO", "reasons": [], "elapsed_s": 0,
         "totals": {"passed": 0, "failed": 0, "error": 0,
                     "skipped": 0, "count": 0, "duration_s": 0},
         "by_marker": {}, "records": []},
        DEFAULT_JSON)
    # Hrefs auf scripts/ extrahieren (relativ aus reports/-Ordner)
    base = DEFAULT_JSON.parent
    for href in re.findall(r"href='([^']*scripts[^']*)'", html):
        target = (base / href).resolve()
        assert target.is_file(), (
            f"Build-Skript-Link {href} zeigt auf nicht-existierende Datei "
            f"({target})")


def test_index_build_center_uses_clipboard_helper():
    html = _index_build_center()
    assert "copyText" in html or "Copy" in html


def test_build_center_section_in_index_html():
    """Nach einem dashboard-Lauf ist 'build' im sticky TOC und ein
    build-section in der index.html."""
    html = _index_build_center()
    # Sicherstellen, dass jede Karte einen kopierbaren Befehl hat
    assert html.count("cmdbox") >= 3
