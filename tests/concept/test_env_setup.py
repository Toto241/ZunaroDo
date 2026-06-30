"""
Tests fuer tools/env_setup.py - die gefuehrte .env-Erzeugung und der
maskierte Status-Bericht (einfache Konfiguration, App/Laufzeit-Ebene).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools import env_setup


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


EXAMPLE_TEXT = """\
# Kopfkommentar
GOOGLE_API_KEY=                      # [SECRET] Google-AI-Studio/Gemini API-Key
ALLTAGSHELFER_GEMINI_MODEL=          # Default: gemini-2.5-flash
ALLTAGSHELFER_SMTP_PASS=             # [SECRET] SMTP-Passwort

# --- Sektion ---
ALLTAGSHELFER_SYNC_DIR=              # Pfad zu geteiltem Ordner
"""


def test_parse_example_detects_vars_and_secrets():
    rows = env_setup.parse_example(EXAMPLE_TEXT)
    names = [n for n, _ in rows]
    assert names == [
        "GOOGLE_API_KEY", "ALLTAGSHELFER_GEMINI_MODEL",
        "ALLTAGSHELFER_SMTP_PASS", "ALLTAGSHELFER_SYNC_DIR",
    ]
    secret = dict(rows)
    assert secret["GOOGLE_API_KEY"] is True
    assert secret["ALLTAGSHELFER_SMTP_PASS"] is True
    assert secret["ALLTAGSHELFER_GEMINI_MODEL"] is False


def test_real_example_lists_smtp_pass_as_secret():
    """Regressionsschutz fuer den Phase-3-Fix: smtp.pass ist ein Secret."""
    example = Path(env_setup.REPO_ROOT) / ".env.example"
    rows = dict(env_setup.parse_example(example.read_text(encoding="utf-8")))
    assert rows.get("ALLTAGSHELFER_SMTP_PASS") is True
    assert rows.get("GOOGLE_API_KEY") is True
    assert rows.get("ALLTAGSHELFER_DB_KEY") is True


def test_parse_env_values_strips_inline_comment_but_keeps_hash_in_value():
    # Aus .env.example kopiert, Wert noch leer -> als leer erkennen.
    vals = env_setup.parse_env_values(
        "GOOGLE_API_KEY=        # [SECRET] Key\n")
    assert vals["GOOGLE_API_KEY"] == ""
    # '#' ohne fuehrenden Whitespace (z.B. im Passwort) bleibt erhalten;
    # ' # note' wird als Inline-Kommentar abgeschnitten.
    vals2 = env_setup.parse_env_values("PWD=ab#cd\nX=val # note\n")
    assert vals2["PWD"] == "ab#cd"
    assert vals2["X"] == "val"


def test_init_creates_env_and_never_overwrites(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text(EXAMPLE_TEXT, encoding="utf-8")
    target = tmp_path / ".env"

    code, _msg = env_setup.init_env(example, target)
    assert code == 0
    assert target.exists()
    assert target.read_text(encoding="utf-8") == EXAMPLE_TEXT

    # Zweiter Lauf darf eine bestehende .env NICHT ueberschreiben.
    target.write_text("SENTINEL=1\n", encoding="utf-8")
    code2, msg2 = env_setup.init_env(example, target)
    assert code2 == 0
    assert target.read_text(encoding="utf-8") == "SENTINEL=1\n"
    assert "existiert bereits" in msg2


def test_init_fails_without_example(tmp_path):
    code, msg = env_setup.init_env(tmp_path / "missing.example",
                                   tmp_path / ".env")
    assert code == 1
    assert "FEHLER" in msg


def test_check_reports_set_from_environ_and_masks_secret(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text(EXAMPLE_TEXT, encoding="utf-8")
    target = tmp_path / ".env"           # existiert (noch) nicht

    code, lines = env_setup.check_env(
        example, target, environ={"GOOGLE_API_KEY": "supersecretvalue"})
    text = "\n".join(lines)

    assert code == 0
    # Der Wert darf NIE im Bericht auftauchen.
    assert "supersecretvalue" not in text
    assert "GOOGLE_API_KEY" in text and "gesetzt" in text
    assert "1/4 dokumentierte Variablen gesetzt" in text
    assert "fehlt - 'Init' erzeugt sie" in text


def test_check_reads_values_from_env_file_and_masks(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text(EXAMPLE_TEXT, encoding="utf-8")
    target = tmp_path / ".env"
    target.write_text("ALLTAGSHELFER_SYNC_DIR=/data/sync\n", encoding="utf-8")

    code, lines = env_setup.check_env(example, target, environ={})
    text = "\n".join(lines)
    assert code == 0
    assert "1/4 dokumentierte Variablen gesetzt" in text
    # Auch Nicht-Secrets werden maskiert (kein Wert im Bericht).
    assert "/data/sync" not in text


def test_check_fails_without_example(tmp_path):
    code, lines = env_setup.check_env(tmp_path / "nope.example",
                                      tmp_path / ".env", environ={})
    assert code == 1
    assert any("FEHLER" in ln for ln in lines)
