"""
Backup und Restore der Alltagshelfer-DB.

Zwei Pfade je nach Verschluesselung:
  - Plain SQLite: offizielle Online-Backup-API
    (`sqlite3.Connection.backup`). Konsistent waehrend laufender
    Schreiboperationen, kein App-Stopp noetig.
  - SQLCipher:    Online-Verschluesseltes Backup ueber
    `ATTACH DATABASE ... KEY '...'; SELECT sqlcipher_export(...)`. Das
    Backup ist seinerseits eine SQLCipher-Datei mit demselben oder
    einem neuen Schluessel.

`backup_file_copy()` bleibt als roher Datei-Snapshot, falls die DB
ohnehin geschlossen ist.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from database import Database


def make_backup(db: Database, target: Path,
                 encryption_key: Optional[str] = None) -> Path:
    """
    Schreibt eine Sicherung der laufenden DB nach 'target'.

    Bei Plain-SQLite: Online-Backup via Connection.backup().
    Bei SQLCipher:    Online-Backup via sqlcipher_export(). Der
                      'encryption_key'-Parameter (oder Env-Var
                      ALLTAGSHELFER_DB_KEY) wird auf das Backup
                      angewendet - so kann das Backup mit demselben oder
                      einem neuen Schluessel verschluesselt werden.
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    if db.encryption_mode == "sqlcipher":
        key = encryption_key or os.environ.get("ALLTAGSHELFER_DB_KEY")
        if not key:
            raise RuntimeError(
                "SQLCipher-Backup: 'encryption_key' fehlt. Entweder "
                "Parameter setzen oder ALLTAGSHELFER_DB_KEY in der "
                "Umgebung.")
        if "\x00" in key:
            raise ValueError("Schluessel darf kein NUL-Byte enthalten")
        if len(key) < 8:
            raise ValueError("Schluessel ist zu kurz (mindestens 8 Zeichen)")
        # Sicher gehen, dass kein bestehendes Backup-File im Weg liegt -
        # sqlcipher_export legt die ATTACH-Datei selbst an.
        if target.exists():
            target.unlink()
        hex_key = key.encode("utf-8").hex()
        with db.lock:
            src = db.conn._conn                            # type: ignore[attr-defined]
            # Pfad-Quoting in ATTACH: einfache Anfuehrungszeichen
            # verdoppeln. Hex-Key braucht kein Quoting.
            safe_path = str(target).replace("'", "''")
            src.execute(
                f"ATTACH DATABASE '{safe_path}' AS backup_db "
                f"KEY \"x'{hex_key}'\"")
            try:
                src.execute("SELECT sqlcipher_export('backup_db')")
                src.commit()
            finally:
                src.execute("DETACH DATABASE backup_db")
        return target

    # Plain SQLite Online-Backup
    with db.lock:
        src = db.conn._conn                                # type: ignore[attr-defined]
        dest = sqlite3.connect(str(target))
        try:
            with dest:
                src.backup(dest)
        finally:
            dest.close()
    return target


def backup_file_copy(db_path: Path, target: Path) -> Path:
    """Roher Datei-Snapshot fuer geschlossene DBs (auch SQLCipher)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, target)
    return target


def restore_database(source: Path, db_path: Path) -> None:
    """
    Stellt eine DB aus einem Backup wieder her.

    Nur sicher, wenn die App ZUVOR geschlossen wurde. Ueberschreibt
    'db_path' mit dem Inhalt von 'source'.
    """
    if not source.exists():
        raise FileNotFoundError(f"Backup '{source}' existiert nicht")
    # Erst in temp schreiben, dann atomar tauschen
    tmp = db_path.with_suffix(db_path.suffix + ".restoring")
    shutil.copy2(source, tmp)
    tmp.replace(db_path)


def list_backups(directory: Path) -> list[Path]:
    """Sortierte Liste aller Backup-Dateien in einem Verzeichnis."""
    if not directory.exists():
        return []
    return sorted(directory.glob("*.db"),
                   key=lambda p: p.stat().st_mtime, reverse=True)


def default_backup_name(prefix: str = "alltagshelfer") -> str:
    """Aktuell-zeitstempel-basierter Dateiname (sortierbar)."""
    return f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
