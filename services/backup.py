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


def prune_old_backups(directory: Path, keep: int) -> list[Path]:
    """
    Loescht alle Backups in 'directory' bis auf die juengsten 'keep'
    Dateien. Liefert die Liste der entfernten Pfade.
    """
    if keep <= 0:
        return []
    files = list_backups(directory)
    if len(files) <= keep:
        return []
    to_remove = files[keep:]
    for path in to_remove:
        try:
            path.unlink()
        except OSError:                                # pragma: no cover
            pass
    return to_remove


def default_backup_name(prefix: str = "alltagshelfer") -> str:
    """Aktuell-zeitstempel-basierter Dateiname (sortierbar, lokal)."""
    return f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"


class AutoBackupWorker:
    """
    Periodischer Auto-Backup-Hintergrundjob.

    Startet einen Thread, der alle 'interval_hours' Stunden ein Backup
    zieht und alte Eintraege bis auf 'retention_count' aufraeumt.
    """

    def __init__(self, db: "Database",
                 directory: Path,
                 retention_count: int = 10,
                 interval_hours: int = 24,
                 encryption_key: Optional[str] = None):
        import threading
        self.db = db
        self.directory = Path(directory)
        self.retention_count = max(1, retention_count)
        self.interval_seconds = max(60, int(interval_hours * 3600))
        self.encryption_key = encryption_key
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.last_backup_path: Optional[Path] = None
        self.last_error: Optional[str] = None

    def start(self) -> None:
        if self._thread is not None:
            return
        import threading
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def run_once(self) -> Optional[Path]:
        """Manueller Auto-Backup-Lauf: Backup + Pruning."""
        try:
            target = self.directory / default_backup_name()
            make_backup(self.db, target, encryption_key=self.encryption_key)
            prune_old_backups(self.directory, self.retention_count)
            self.last_backup_path = target
            self.last_error = None
            return target
        except Exception as exc:                       # noqa: BLE001
            self.last_error = str(exc)
            return None

    def _loop(self) -> None:
        # Erstes Backup ein paar Sekunden nach dem Start, damit nicht
        # gleichzeitig mit Demo/Seed-Aufrufen.
        first_delay = min(60, self.interval_seconds)
        if self._stop.wait(first_delay):
            return
        while not self._stop.is_set():
            self.run_once()
            if self._stop.wait(self.interval_seconds):
                return
