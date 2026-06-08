"""Desktop-Tests fuer die plattformabhaengigen Native-Bruecken.

Auf dem Desktop (kein Android, kein jnius) muessen alle Bruecken sauber
'nicht verfuegbar' melden, ohne zu crashen - das ist die Voraussetzung
dafuer, dass dieselbe Codebasis auf Desktop und Android laeuft.
"""
from __future__ import annotations

from services import db_key, ocr, ocr_android


def test_ocr_android_unavailable_on_desktop():
    assert ocr_android.is_available() is False
    assert ocr_android.recognize("whatever.png") is None


def test_ocr_selection_skips_mlkit_on_desktop():
    # ML Kit darf auf dem Desktop nicht als Engine erscheinen.
    assert "mlkit" not in ocr.available_engines()


def test_db_key_env_override(monkeypatch):
    monkeypatch.setenv("ALLTAGSHELFER_DB_KEY", "supersecretkey")
    assert db_key.resolve_db_key() == "supersecretkey"


def test_db_key_none_without_engine(monkeypatch):
    # Ohne Env-Key und ohne sqlcipher3 (Desktop-Default) -> None,
    # damit database.py nicht hart abbricht.
    monkeypatch.delenv("ALLTAGSHELFER_DB_KEY", raising=False)
    monkeypatch.setattr(db_key, "_sqlcipher_available", lambda: False)
    assert db_key.resolve_db_key() is None


def test_db_key_env_wins_even_with_engine(monkeypatch):
    monkeypatch.setenv("ALLTAGSHELFER_DB_KEY", "envkey")
    monkeypatch.setattr(db_key, "_sqlcipher_available", lambda: True)
    monkeypatch.setattr(db_key, "_on_android", lambda: False)
    assert db_key.resolve_db_key() == "envkey"
