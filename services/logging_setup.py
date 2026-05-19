"""
Strukturiertes Logging fuer den Alltagshelfer.

Bislang war 'print()' an vielen Stellen verstreut - schlecht zu
filtern, kein Log-Level, kein rotierendes Log-File. Dieses Modul
zentralisiert die Konfiguration:

  - Default-Level: INFO (per ALLTAGSHELFER_LOG_LEVEL aenderbar)
  - Konsole + optional rotating Datei-Log
  - Formatter mit Modulname, Zeit, Level
  - get_logger() liefert immer den gleichen, konfigurierten Logger

Anwendung:
    from services.logging_setup import get_logger
    log = get_logger(__name__)
    log.info("...")

Wird bei der App-Start-Initialisierung einmal ueber configure_logging()
aufgerufen; spaeter genuegt get_logger.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


_CONFIGURED = False


def configure_logging(log_dir: Optional[Path] = None,
                      level: Optional[str] = None,
                      console: bool = True) -> None:
    """
    Konfiguriert den Root-Logger.

    Muss einmal beim App-Start aufgerufen werden. Spaetere Aufrufe sind
    idempotent (kein doppeltes Handler-Anhaengen).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    resolved_level = (level or os.environ.get("ALLTAGSHELFER_LOG_LEVEL")
                       or "INFO").upper()
    numeric = getattr(logging, resolved_level, logging.INFO)
    root = logging.getLogger("alltagshelfer")
    root.setLevel(numeric)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S")
    if console:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.setLevel(numeric)
        root.addHandler(ch)
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_dir / "alltagshelfer.log",
            maxBytes=2 * 1024 * 1024,    # 2 MB
            backupCount=5, encoding="utf-8")
        fh.setFormatter(formatter)
        fh.setLevel(numeric)
        root.addHandler(fh)
    # Propagation verhindern, damit nicht doppelte Ausgaben entstehen
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Liefert einen Logger, der unter dem 'alltagshelfer'-Root haengt.
    Auch ohne configure_logging() liefert er eine funktionierende
    Instance (mit Default-Stream-Handler).
    """
    if not _CONFIGURED:
        configure_logging()
    if not name.startswith("alltagshelfer"):
        name = f"alltagshelfer.{name}"
    return logging.getLogger(name)
