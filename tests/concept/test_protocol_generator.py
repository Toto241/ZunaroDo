"""
Konzept-Test: der Protokoll-Generator selbst.

Stellt sicher, dass tools/test_protocol.py die JUnit-XML-Ausgabe von
pytest in ein konsistentes Markdown- + JSON-Protokoll uebersetzt und
die Go/No-Go-Logik anhand der Marker zuverlaessig entscheidet.

Wir testen *isoliert* gegen synthetisches XML, ohne pytest erneut
auszufuehren.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.test_protocol import (_classify, _format_protocol_md, _go_no_go,
                                  _parse_junit, _stats_by_marker)


SYNTH_XML = """<?xml version="1.0"?>
<testsuites>
  <testsuite name="pytest">
    <testcase classname="tests.concept.test_release_gate"
              name="test_J1_version_code_is_positive_integer"
              time="0.01"/>
    <testcase classname="tests.concept.test_members_scenarios"
              name="test_M05_meets_play_minimum_12"
              time="2.5"/>
    <testcase classname="tests.concept.test_roles_permissions"
              name="test_admin_can_invite_but_not_delete_group"
              time="0.01">
      <failure message="assertion failed">AssertionError</failure>
    </testcase>
    <testcase classname="tests.concept.test_pairwise_matrix"
              name="test_matrix_has_acceptable_size"
              time="0.0">
      <skipped message="hypothesis fehlt"/>
    </testcase>
  </testsuite>
</testsuites>
"""


@pytest.mark.concept
@pytest.mark.release_gate
def test_protocol_parses_junit(tmp_path: Path):
    xml = tmp_path / "junit.xml"
    xml.write_text(SYNTH_XML, encoding="utf-8")
    records = _parse_junit(xml)
    assert len(records) == 4
    statuses = {r["status"] for r in records}
    assert statuses == {"passed", "failed", "skipped"}


@pytest.mark.concept
@pytest.mark.release_gate
def test_protocol_classifies_and_decides(tmp_path: Path):
    xml = tmp_path / "junit.xml"
    xml.write_text(SYNTH_XML, encoding="utf-8")
    records = _parse_junit(xml)
    classified = _classify(records)
    marker_stats = _stats_by_marker(records)
    # Hier muss NO-GO herauskommen, weil ein Test failed
    decision, reasons = _go_no_go(classified["totals"], marker_stats)
    assert decision == "NO-GO"
    assert reasons, "NO-GO ohne Begruendung waere ein Bug"


@pytest.mark.concept
@pytest.mark.release_gate
def test_protocol_formats_markdown(tmp_path: Path):
    xml = tmp_path / "junit.xml"
    xml.write_text(SYNTH_XML, encoding="utf-8")
    records = _parse_junit(xml)
    classified = _classify(records)
    marker_stats = _stats_by_marker(records)
    decision, reasons = _go_no_go(classified["totals"], marker_stats)
    md = _format_protocol_md(records, classified, marker_stats, decision,
                              reasons, "tests/concept", None, 1.23)
    assert "# Test-Protokoll" in md
    assert "Gesamtuebersicht" in md
    assert "## Fehlgeschlagene Tests" in md
    assert "test_admin_can_invite_but_not_delete_group" in md


@pytest.mark.concept
@pytest.mark.release_gate
def test_protocol_artifacts_present_after_run():
    """Nach einem Lauf von tools.test_protocol muss das Markdown- und
    JSON-Artefakt vorhanden und konsistent sein."""
    repo = Path(__file__).resolve().parents[2]
    md = repo / "tests" / "concept" / "reports" / "protocol.md"
    js = repo / "tests" / "concept" / "reports" / "protocol.json"
    if not md.is_file() or not js.is_file():
        pytest.skip(
            "Protokoll noch nicht erzeugt - 'python -m tools.test_protocol' "
            "ausfuehren")
    data = json.loads(js.read_text(encoding="utf-8"))
    assert "decision" in data
    assert "totals" in data
    assert data["totals"]["count"] >= 100
