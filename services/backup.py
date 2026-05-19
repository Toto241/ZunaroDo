"""
Backup und Restore der Alltagshelfer-DB.

Verwendet bei Plain-SQLite die offizielle Online-Backup-API
(`sqlite3.Connection.backup`) - die kann mit laufenden Schreib-
transaktionen umgehen und liefert eine konsistente Kopie, ohne
dass die App heruntergefahren werden muss.

Fuer SQLCipher waere ein Inline-Backup-Pfad nur mit
`ATTACH DATABASE ... KEY '...'; SELECT sqlcipher_export('encrypted');`
moeglich. Damit das Modul nicht von SQLCipher-Internas abhaengt,
faellt der SQLCipher-Pfad auf einen einfachen Datei-Snapshot zurueck
und verlangt vorab das Schliessen der DB. Der Aufrufer bekommt eine
klare Meldung statt halb-konsistente Backups.
"""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from database import Database


def make_backup(db: Database, target: Path) -> Path:
    """
    Schreibt eine Sicherung der laufenden DB nach 'target'.

    Bei Plain-SQLite: Online-Backup (sicher waehrend Schreiboperationen).
    Bei SQLCipher:    der Aufrufer wird angewiesen, die DB zuerst
                      mit close() zu schliessen und dann
                      backup_file_copy() zu verwenden.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    if db.encryption_mode == "sqlcipher":
        raise RuntimeError(
            "SQLCipher-DB kann nicht online gesichert werden. "
            "Beende die App und nutze backup_file_copy() oder "
            "kopiere die DB-Datei direkt - der Schluessel bleibt im "
            "Backup gleich.")
    # Plain SQLite Online-Backup
    with db.lock:
        # _SafeConnection legt die echte Connection unter _conn ab.
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
