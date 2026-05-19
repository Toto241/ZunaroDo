"""
Konfigurations-System des Alltagshelfers.

Quellen, in dieser Reihenfolge (spaetere ueberschreiben fruehere):
  1. Defaults (im Code)
  2. SettingsRepository (DB)
  3. Umgebungsvariablen

So bleibt die App per Env-Var steuerbar (CI, Server, Container), die
GUI darf zugleich Einstellungen persistieren, und der Default ist immer
das, was 'einfach laeuft' (Offline-Modus).

Schluessel:
  gemini.api_key, gemini.model, gemini.max_iterations, gemini.max_tokens
  imap.host, imap.user, imap.pass, imap.folder
  smtp.host, smtp.port, smtp.user, smtp.pass, smtp.sender, smtp.starttls
  sync.dir, sync.interval_seconds, sync.enabled
  db.key                      (SQLCipher-Schluessel)
  notify.warn_within_days
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from database import SettingsRepository


# Default-Werte und Mapping zu Umgebungsvariablen
DEFAULTS: dict[str, str] = {
    "gemini.api_key": "",
    "gemini.model": "gemini-2.5-flash",
    "gemini.max_iterations": "12",
    "gemini.max_tokens": "2048",
    "imap.host": "",
    "imap.user": "",
    "imap.pass": "",
    "imap.folder": "INBOX",
    "smtp.host": "",
    "smtp.port": "587",
    "smtp.user": "",
    "smtp.pass": "",
    "smtp.sender": "",
    "smtp.starttls": "true",
    "sync.dir": "",
    "sync.interval_seconds": "300",
    "sync.enabled": "auto",                # auto | true | false
    "db.key": "",
    "notify.warn_within_days": "14",
    "i18n.language": "de",
}

ENV_MAP: dict[str, str] = {
    "gemini.api_key": "GOOGLE_API_KEY",
    "gemini.model": "ALLTAGSHELFER_GEMINI_MODEL",
    "imap.host": "ALLTAGSHELFER_IMAP_HOST",
    "imap.user": "ALLTAGSHELFER_IMAP_USER",
    "imap.pass": "ALLTAGSHELFER_IMAP_PASS",
    "imap.folder": "ALLTAGSHELFER_IMAP_FOLDER",
    "sync.dir": "ALLTAGSHELFER_SYNC_DIR",
    "db.key": "ALLTAGSHELFER_DB_KEY",
}

# Schluessel, deren Wert nicht in der DB stehen sollte (zu sensibel oder
# besser per Env)
SECRET_KEYS = {"gemini.api_key", "imap.pass", "smtp.pass", "db.key"}


@dataclass
class AppConfig:
    """Aufgeloeste Konfiguration als Datenobjekt."""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_max_iterations: int = 12
    gemini_max_tokens: int = 2048

    imap_host: str = ""
    imap_user: str = ""
    imap_pass: str = ""
    imap_folder: str = "INBOX"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_sender: str = ""
    smtp_starttls: bool = True

    sync_dir: str = ""
    sync_interval_seconds: int = 300
    sync_enabled: str = "auto"

    db_key: str = ""
    notify_warn_within_days: int = 14
    i18n_language: str = "de"


def _coerce(key: str, raw: str, config: AppConfig) -> None:
    """Schreibt den geparsten Wert in das passende Feld von AppConfig."""
    attr = key.replace(".", "_")
    # GOOGLE_API_KEY heisst intern gemini.api_key -> gemini_api_key
    if not hasattr(config, attr):
        return
    current = getattr(config, attr)
    if isinstance(current, bool):
        setattr(config, attr, raw.strip().lower() in ("1", "true", "yes", "on"))
    elif isinstance(current, int):
        try:
            setattr(config, attr, int(raw))
        except ValueError:
            pass
    else:
        setattr(config, attr, raw)


def load_config(repo: Optional[SettingsRepository]) -> AppConfig:
    """Loest die App-Konfiguration aus Defaults + DB + Umgebung auf."""
    config = AppConfig()
    # 1) Defaults
    for key, raw in DEFAULTS.items():
        _coerce(key, raw, config)
    # 2) DB
    if repo is not None:
        for key, raw in repo.all().items():
            _coerce(key, raw, config)
    # 3) Env
    for key, env_var in ENV_MAP.items():
        env_val = os.environ.get(env_var)
        if env_val:
            _coerce(key, env_val, config)
    return config


def save_value(repo: SettingsRepository, key: str, value: str) -> None:
    """Speichert einen Wert in der DB (Geheime werden nicht persistiert)."""
    if key in SECRET_KEYS:
        # Geheime Felder werden bewusst nicht persistiert - sie kommen
        # ausschliesslich aus Env-Var oder OS-Keyring.
        return
    if value == DEFAULTS.get(key, ""):
        repo.set(key, None)
        return
    repo.set(key, value)
