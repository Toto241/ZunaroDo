"""
Vollstaendige Loeschung aller Nutzerdaten (DSGVO Art. 17 / Play Store
Data-Deletion-Anforderung).

Zwei Ebenen:
  1. DB-Inhalte leeren  -> Database.wipe_all_data()
  2. erzeugte Dateien entfernen (Exporte, Backups, Logs, Anhaenge,
     Cache im App-Sandbox-Verzeichnis) -> purge_directories()

`delete_all_user_data()` fasst beides zusammen und liefert einen
Report, den die UI anzeigen kann. Die Datei-Logik ist bewusst
Kivy-frei und damit unter unittest einzeln testbar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

#: Unterverzeichnisse im App-Datenverzeichnis, die generierte Nutzer-
#: dateien enthalten und beim Voll-Reset geleert werden.
DEFAULT_DATA_SUBDIRS = ("ausgaben", "backups", "logs", "attachments", "cache")


@dataclass
class DeletionReport:
    """Ergebnis einer Voll-Loeschung."""
    tables_cleared: dict[str, int] = field(default_factory=dict)
    files_deleted: int = 0
    dirs_processed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def rows_deleted(self) -> int:
        return sum(self.tables_cleared.values())

    def as_dict(self) -> dict:
        return {
            "tables_cleared": self.tables_cleared,
            "rows_deleted": self.rows_deleted,
            "files_deleted": self.files_deleted,
            "dirs_processed": self.dirs_processed,
            "errors": self.errors,
        }


def purge_directories(dirs: Iterable[Path]) -> tuple[int, list[str]]:
    """
    Loescht rekursiv den *Inhalt* der angegebenen Verzeichnisse, laesst
    die Verzeichnisse selbst aber bestehen (damit die App ohne erneutes
    Anlegen weiterlaeuft).

    Nicht existierende Verzeichnisse werden uebersprungen. Liefert
    (anzahl_geloeschter_dateien, fehlerliste). Robuste Einzelfehler-
    behandlung: ein nicht loeschbares File bricht den Rest nicht ab.
    """
    deleted = 0
    errors: list[str] = []
    for directory in dirs:
        directory = Path(directory)
        if not directory.is_dir():
            continue
        # Erst Dateien (tiefste zuerst), dann leere Unterordner.
        for path in sorted(directory.rglob("*"),
                           key=lambda p: len(p.parts), reverse=True):
            try:
                if path.is_file() or path.is_symlink():
                    path.unlink()
                    deleted += 1
                elif path.is_dir():
                    path.rmdir()
            except OSError as exc:
                errors.append(f"{path}: {exc}")
    return deleted, errors


def delete_all_user_data(
    db,
    *,
    data_dirs: Iterable[Path] = (),
    include_settings: bool = True,
) -> DeletionReport:
    """
    Fuehrt die komplette Loeschung durch: DB leeren + Dateien purgen.

    `db` ist eine Database-Instanz (offen). `data_dirs` sind die zu
    leerenden Verzeichnisse (z.B. App-Sandbox-Unterordner). Die Reihen-
    folge ist robust: Tritt beim Datei-Purge ein Fehler auf, ist die DB
    trotzdem bereits geleert.
    """
    report = DeletionReport()
    report.tables_cleared = db.wipe_all_data(include_settings=include_settings)

    dirs = [Path(d) for d in data_dirs]
    report.dirs_processed = [str(d) for d in dirs]
    deleted, errors = purge_directories(dirs)
    report.files_deleted = deleted
    report.errors = errors
    return report


def sandbox_data_dirs(user_data_dir: str | Path,
                      subdirs: Iterable[str] = DEFAULT_DATA_SUBDIRS) -> list[Path]:
    """Baut die Liste der zu leerenden Sandbox-Unterordner."""
    base = Path(user_data_dir)
    return [base / name for name in subdirs]
