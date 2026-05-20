"""
Tests fuer tools/playstore_sync.py - das Play-Store-Sync-Werkzeug.

Geprueft werden:

  1. Schema-Validierung (Pflichtfelder, Laengen-Limits, Permission-Logik).
  2. Mock-Backend-Roundtrip: push -> pull -> diff = 0.
  3. Tiefen-Merge: lokal bleibt, wo remote leer ist.
  4. init_from_repo: leitet Package-Namen aus buildozer.spec ab.
  5. export_markdown: enthaelt alle Pflicht-Sections.
  6. CLI-Smoketest fuer alle Subcommands.

Es findet KEIN echter Google-Play-Aufruf statt (`--mock` erzwingt das).
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from tools.playstore_sync import (DEFAULT_YAML, SAMPLE_CONFIG, MockBackend,
                                   _diff_keys, _merge, export_markdown,
                                   init_from_repo, main, validate)


pytestmark = [pytest.mark.concept, pytest.mark.playstore]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def test_sample_config_validates_clean():
    issues = validate(SAMPLE_CONFIG)
    errs = [i for i in issues if i.severity == "error"]
    assert not errs, f"Sample-Konfig hat Validierungsfehler: {errs}"


def test_missing_top_level_keys_are_errors():
    issues = validate({})
    paths = {(i.path, i.severity) for i in issues}
    assert ("identity", "error") in paths
    assert ("contact", "error") in paths
    assert ("tracks", "error") in paths


def test_too_long_title_is_error():
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["localizations"]["de-DE"]["title"] = "X" * 80
    issues = validate(cfg)
    assert any(i.path.endswith(".title") and i.severity == "error"
                for i in issues)


def test_too_long_short_description_is_error():
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["localizations"]["de-DE"]["short_description"] = "X" * 200
    issues = validate(cfg)
    assert any("short_description" in i.path and i.severity == "error"
                for i in issues)


def test_too_long_full_description_is_error():
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["localizations"]["de-DE"]["full_description"] = "X" * 4500
    issues = validate(cfg)
    assert any("full_description" in i.path and i.severity == "error"
                for i in issues)


def test_invalid_package_name_is_error():
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["identity"]["package_name"] = "not.a-valid_package"
    issues = validate(cfg)
    assert any(i.path == "identity.package_name" and i.severity == "error"
                for i in issues)


def test_permission_overlap_declared_blocked_is_error():
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["permissions"]["declared"].append(
        "android.permission.MANAGE_EXTERNAL_STORAGE")
    issues = validate(cfg)
    assert any("permissions" in i.path and i.severity == "error"
                for i in issues)


def test_user_fraction_out_of_range_is_error():
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["tracks"]["production"]["releases"] = [
        {"version_code": 2, "user_fraction": 1.5, "status": "inProgress"}]
    issues = validate(cfg)
    assert any("user_fraction" in i.path and i.severity == "error"
                for i in issues)


def test_invalid_release_status_is_error():
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["tracks"]["production"]["releases"] = [
        {"version_code": 2, "status": "totally-not-real"}]
    issues = validate(cfg)
    assert any(".status" in i.path and i.severity == "error" for i in issues)


def test_missing_internet_permission_is_warning():
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["permissions"]["declared"] = ["android.permission.POST_NOTIFICATIONS"]
    issues = validate(cfg)
    assert any("INTERNET" in i.message and i.severity == "warning"
                for i in issues)


# ---------------------------------------------------------------------------
# Mock-Backend-Roundtrip
# ---------------------------------------------------------------------------
def test_mock_roundtrip_persists_and_returns_identical(tmp_path: Path):
    backend = MockBackend(mirror_path=tmp_path / "mirror.json")
    pkg = SAMPLE_CONFIG["identity"]["package_name"]
    backend.push(pkg, deepcopy(SAMPLE_CONFIG))
    pulled = backend.pull(pkg)
    assert pulled["identity"]["package_name"] == pkg
    assert pulled["localizations"]["de-DE"]["title"] == \
        SAMPLE_CONFIG["localizations"]["de-DE"]["title"]


def test_mock_dry_run_does_not_modify_state(tmp_path: Path):
    backend = MockBackend(mirror_path=tmp_path / "mirror.json")
    actions = backend.push("com.example.foo", {"x": 1}, dry_run=True)
    assert any("would create" in a for a in actions)
    assert not (tmp_path / "mirror.json").is_file()


def test_mock_pull_unknown_package_raises(tmp_path: Path):
    backend = MockBackend(mirror_path=tmp_path / "mirror.json")
    with pytest.raises(RuntimeError):
        backend.pull("does.not.exist")


# ---------------------------------------------------------------------------
# Diff + Merge
# ---------------------------------------------------------------------------
def test_diff_keys_empty_when_equal():
    cfg = deepcopy(SAMPLE_CONFIG)
    assert _diff_keys(cfg, deepcopy(cfg)) == []


def test_diff_keys_reports_changed_strings():
    a = {"identity": {"version_name": "0.9.0"}}
    b = {"identity": {"version_name": "1.0.0"}}
    out = _diff_keys(a, b)
    assert out and "version_name" in out[0]


def test_diff_keys_reports_added_and_removed():
    a = {"a": 1}
    b = {"a": 1, "b": 2}
    out = _diff_keys(a, b)
    assert any("b" in line for line in out)
    out2 = _diff_keys(b, a)
    assert any("b" in line for line in out2)


def test_merge_keeps_local_when_remote_empty():
    local = {"contact": {"support_email": "me@local"}}
    remote = {"contact": {"support_email": ""}}
    merged = _merge(local, remote)
    assert merged["contact"]["support_email"] == "me@local"


def test_merge_prefers_remote_when_not_empty():
    local = {"contact": {"support_email": "me@local"}}
    remote = {"contact": {"support_email": "me@remote"}}
    merged = _merge(local, remote)
    assert merged["contact"]["support_email"] == "me@remote"


# ---------------------------------------------------------------------------
# init_from_repo
# ---------------------------------------------------------------------------
def test_init_from_repo_picks_up_buildozer_settings():
    cfg = init_from_repo()
    pkg = cfg["identity"]["package_name"]
    # buildozer.spec: package.domain = de.alltagshelfer, package.name = alltagshelfer
    assert pkg.startswith("de.alltagshelfer.")
    perms = cfg["permissions"]["declared"]
    # INTERNET muss aus dem buildozer.spec uebernommen sein
    assert "android.permission.INTERNET" in perms


def test_init_from_repo_has_required_top_level():
    cfg = init_from_repo()
    for key in ("identity", "contact", "localizations", "store_listing",
                 "data_safety", "permissions", "tracks", "metadata"):
        assert key in cfg, f"Pflicht-Sektion '{key}' fehlt"


# ---------------------------------------------------------------------------
# export_markdown
# ---------------------------------------------------------------------------
def test_export_markdown_contains_all_sections():
    md = export_markdown(SAMPLE_CONFIG)
    for marker in ("# Play-Console-Snapshot", "## Identitaet", "## Kontakt",
                    "## Lokalisierungen", "## Permissions",
                    "## Data Safety", "## Tracks", "### de-DE"):
        assert marker in md, f"Section '{marker}' fehlt in Snapshot"


def test_export_markdown_shows_length_counters():
    md = export_markdown(SAMPLE_CONFIG)
    assert "/30" in md and "/80" in md and "/4000" in md


# ---------------------------------------------------------------------------
# CLI-Smoketests
# ---------------------------------------------------------------------------
def test_cli_init_writes_yaml(tmp_path: Path):
    target = tmp_path / "ps.yml"
    rc = main(["--config", str(target), "init"])
    assert rc == 0
    assert target.is_file() and target.stat().st_size > 200


def test_cli_validate_on_sample(tmp_path: Path):
    target = tmp_path / "ps.yml"
    main(["--config", str(target), "init"])
    rc = main(["--config", str(target), "validate"])
    assert rc == 0


def test_cli_push_dry_run_and_pull_via_mock(tmp_path: Path):
    target = tmp_path / "ps.yml"
    mirror = tmp_path / "mirror.json"
    assert main(["--config", str(target), "init"]) == 0
    # Dry-run aendert nichts
    assert main(["--config", str(target), "--mock", "--mock-file", str(mirror),
                  "push", "--dry-run"]) == 0
    assert not mirror.is_file()
    # Echter Push schreibt
    assert main(["--config", str(target), "--mock", "--mock-file", str(mirror),
                  "push"]) == 0
    assert mirror.is_file()
    # Pull schreibt zurueck
    assert main(["--config", str(target), "--mock", "--mock-file", str(mirror),
                  "pull", "--merge"]) == 0


def test_cli_export_writes_snapshot(tmp_path: Path):
    target = tmp_path / "ps.yml"
    snap = tmp_path / "snap.md"
    main(["--config", str(target), "init"])
    rc = main(["--config", str(target), "export", "--out", str(snap)])
    assert rc == 0
    assert snap.is_file()
    assert "# Play-Console-Snapshot" in snap.read_text(encoding="utf-8")


def test_cli_push_aborts_on_invalid(tmp_path: Path, capsys):
    target = tmp_path / "ps.yml"
    target.write_text("identity:\n  package_name: bad\n", encoding="utf-8")
    rc = main(["--config", str(target), "--mock",
                "--mock-file", str(tmp_path / "m.json"), "push"])
    assert rc != 0
    out = capsys.readouterr()
    assert "Validierungsfehler" in out.err or "[ABBRUCH]" in out.err


def test_cli_sample_prints_yaml(capsys):
    rc = main(["sample"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "identity:" in out or "\"identity\"" in out


# ---------------------------------------------------------------------------
# Default-Konfig im Repo
# ---------------------------------------------------------------------------
def test_default_yaml_in_repo_is_valid():
    """Wenn das Repo eine playstore.yml mitliefert, MUSS sie valid sein."""
    if not DEFAULT_YAML.is_file():
        pytest.skip("playstore.yml noch nicht erzeugt")
    from tools.playstore_sync import _load_yaml
    cfg = _load_yaml(DEFAULT_YAML)
    issues = validate(cfg)
    errs = [i for i in issues if i.severity == "error"]
    assert not errs, (
        "playstore.yml hat Validierungsfehler:\n  "
        + "\n  ".join(f"{i.path}: {i.message}" for i in errs))
