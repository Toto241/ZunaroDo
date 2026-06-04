"""
Tests fuer services/datadir.py - Aufloesung & Migration des
Datenverzeichnisses, das beim Erststart der App gewaehlt wird.

Die Tests isolieren sich vom echten OS-Konfigurationsordner ueber
ALLTAGSHELFER_CONFIG_DIR (Zeiger-Datei) und ALLTAGSHELFER_DATA_DIR.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from services import datadir


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path, monkeypatch):
    """Konfig-Ordner in tmp, keine Data-Dir-Env - sauberer Erststart."""
    monkeypatch.setenv(datadir.CONFIG_DIR_ENV, str(tmp_path / "cfg"))
    monkeypatch.delenv(datadir.DATA_DIR_ENV, raising=False)
    yield


def test_config_dir_honors_override(tmp_path):
    assert datadir.config_dir() == (tmp_path / "cfg")
    assert datadir.pointer_file() == (tmp_path / "cfg" / "datadir.json")


def test_first_run_is_unconfigured():
    assert datadir.configured_data_dir() is None


def test_env_var_wins_over_pointer(tmp_path, monkeypatch):
    # Zeiger zeigt auf A, Env auf B -> Env gewinnt.
    datadir.remember_data_dir(tmp_path / "A")
    monkeypatch.setenv(datadir.DATA_DIR_ENV, str(tmp_path / "B"))
    assert datadir.configured_data_dir() == (tmp_path / "B")


def test_remember_and_read_roundtrip(tmp_path):
    target = tmp_path / "mydata"
    saved = datadir.remember_data_dir(target)
    assert saved == target.resolve()
    assert datadir.configured_data_dir() == target.resolve()
    # Zeiger liegt im Konfig-Ordner, NICHT im Datenverzeichnis selbst.
    assert datadir.pointer_file().is_file()
    assert datadir.config_dir() not in target.resolve().parents


def test_remember_writes_valid_json(tmp_path):
    datadir.remember_data_dir(tmp_path / "d")
    data = json.loads(datadir.pointer_file().read_text(encoding="utf-8"))
    assert data["data_dir"] == str((tmp_path / "d").resolve())


def test_corrupt_pointer_is_treated_as_unconfigured(tmp_path):
    cfg = tmp_path / "cfg"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "datadir.json").write_text("{ not json", encoding="utf-8")
    assert datadir.configured_data_dir() is None


def test_blank_pointer_value_is_unconfigured(tmp_path):
    cfg = tmp_path / "cfg"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "datadir.json").write_text(
        json.dumps({"data_dir": "  "}), encoding="utf-8")
    assert datadir.configured_data_dir() is None


def _seed_old_workdir(src: Path) -> None:
    """Legt typische Datenartefakte + eine Fremddatei in src an."""
    (src / "alltagshelfer.db").write_text("db", encoding="utf-8")
    (src / "alltagshelfer_anna.db").write_text("db2", encoding="utf-8")
    (src / "ausgaben").mkdir()
    (src / "ausgaben" / "export.csv").write_text("x", encoding="utf-8")
    (src / "backups").mkdir()
    (src / ".alltagshelfer-state").mkdir()
    (src / ".alltagshelfer-state" / "sync.json").write_text(
        "{}", encoding="utf-8")
    (src / ".alltagshelfer-state-anna").mkdir()
    (src / ".alltagshelfer-active-profile").write_text(
        json.dumps({"active": "anna"}), encoding="utf-8")
    (src / "irrelevant.txt").write_text("nope", encoding="utf-8")


def test_migrate_into_copies_known_artifacts(tmp_path):
    src = tmp_path / "old"
    dst = tmp_path / "new"
    src.mkdir()
    _seed_old_workdir(src)

    copied = datadir.migrate_into(src, dst)

    assert "alltagshelfer.db" in copied
    assert "alltagshelfer_anna.db" in copied
    assert "ausgaben" in copied
    assert "backups" in copied
    assert ".alltagshelfer-state" in copied
    assert ".alltagshelfer-state-anna" in copied
    assert ".alltagshelfer-active-profile" in copied
    # Fremddatei wird NICHT mitgenommen.
    assert "irrelevant.txt" not in copied
    assert not (dst / "irrelevant.txt").exists()
    # Inhalt wirklich kopiert (rekursiv).
    assert (dst / "ausgaben" / "export.csv").read_text(encoding="utf-8") == "x"
    assert (dst / "alltagshelfer.db").read_text(encoding="utf-8") == "db"


def test_migrate_into_skips_existing_targets(tmp_path):
    src = tmp_path / "old"
    dst = tmp_path / "new"
    src.mkdir()
    dst.mkdir()
    _seed_old_workdir(src)
    # Ziel hat die DB schon (mit anderem Inhalt) -> nicht ueberschreiben.
    (dst / "alltagshelfer.db").write_text("KEEP", encoding="utf-8")

    copied = datadir.migrate_into(src, dst)

    assert "alltagshelfer.db" not in copied
    assert (dst / "alltagshelfer.db").read_text(encoding="utf-8") == "KEEP"
    # Zweiter Lauf kopiert nichts mehr.
    assert datadir.migrate_into(src, dst) == []


def test_migrate_into_noop_when_same_dir(tmp_path):
    src = tmp_path / "same"
    src.mkdir()
    _seed_old_workdir(src)
    assert datadir.migrate_into(src, src) == []


def test_prepare_data_dir_creates_and_migrates(tmp_path):
    src = tmp_path / "old"
    src.mkdir()
    _seed_old_workdir(src)
    target = tmp_path / "fresh" / "nested"

    resolved, copied = datadir.prepare_data_dir(target, migrate_from=src)

    assert resolved == target.resolve()
    assert resolved.is_dir()
    assert "alltagshelfer.db" in copied


def test_activate_changes_cwd(tmp_path):
    target = tmp_path / "active"
    prev = Path.cwd()
    try:
        resolved = datadir.activate(target)
        assert resolved == target.resolve()
        assert Path.cwd() == target.resolve()
    finally:
        os.chdir(prev)
