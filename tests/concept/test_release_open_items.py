"""
Tests fuer die zentrale Liste offener manueller Release-Schritte.

Die Liste ist bewusst Code statt freier Text, weil Control Panel,
Dashboard und Markdown-Doku dieselbe Quelle verwenden sollen.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools import release_open_items as roi


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]

REPO = Path(__file__).resolve().parents[2]


def test_manual_items_cover_required_release_topics():
    text = roi.to_markdown().lower()
    for needle in (
        "android-gerät",
        "keystore",
        "play console",
        "closed testing",
        "data-safety",
        "ios-build",
    ):
        assert needle in text, f"Thema {needle!r} fehlt in den offenen Punkten"


def test_each_manual_item_explains_why_and_next_steps():
    items = roi.items()
    assert len(items) >= 8
    ids = [item.id for item in items]
    assert ids == sorted(ids), "Liste muss deterministisch sortiert sein"
    assert len(ids) == len(set(ids)), "OpenItem-IDs muessen eindeutig sein"
    for item in items:
        assert item.title
        assert item.category
        assert item.status
        assert len(item.why_manual) >= 40
        assert item.what_to_do, f"{item.id} hat keine naechsten Schritte"
        assert item.local_docs or item.official_links, (
            f"{item.id} hat keine Links")


def test_local_document_references_exist():
    for item in roi.items():
        for ref in item.local_docs:
            rel = ref.target.split("#", 1)[0]
            assert rel, f"{item.id}: leerer lokaler Link"
            assert (REPO / rel).exists(), (
                f"{item.id}: lokaler Link {ref.target!r} existiert nicht")


def test_official_links_are_https():
    for item in roi.items():
        assert item.official_links, f"{item.id} hat keinen offiziellen Link"
        for ref in item.official_links:
            assert ref.is_https, (
                f"{item.id}: offizieller Link muss HTTPS sein: {ref.target}")


def test_markdown_contains_links_and_commands():
    out = roi.to_markdown()
    assert out.startswith("# Offene manuelle Release-Schritte")
    assert "[Android Debug Bridge (adb)](https://developer.android.com/tools/adb)" in out
    assert "python -m tools.verify_android_device" in out
    assert "python -m tools.data_safety --markdown" in out
    assert "release/PLAY_CONSOLE_SETUP.md" in out


def test_automated_checks_have_valid_modules_and_commands():
    checks = roi.automated_checks()
    assert checks
    modules = {check.module for check in checks}
    expected = {
        "tools.playstore_check",
        "tools.data_safety",
        "tools.privacy_policy",
        "tools.legal_status",
        "tools.build_status",
        "tools.verify_android_device",
        "tools.release_open_items",
    }
    assert expected <= modules
    for check in checks:
        cmd = check.command("python")
        assert cmd[:3] == ["python", "-m", check.module]
        assert check.label
        assert check.description


def test_cli_markdown_and_json_modes(capsys):
    assert roi.main(["--markdown"]) == 0
    md = capsys.readouterr().out
    assert "Offene manuelle Release-Schritte" in md

    assert roi.main(["--json"]) == 0
    js = capsys.readouterr().out
    assert '"manual_items"' in js
    assert '"automated_checks"' in js
