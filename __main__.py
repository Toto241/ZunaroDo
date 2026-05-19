"""
Erlaubt `python -m alltagshelfer` als CLI-Einstieg.

Subcommands:
  (kein)                    startet die Konsolen-Demo (main.py)
  --diagnose                druckt einen Statusbericht
  --gui                     startet die GUI
  --sync-server [...]       startet den HTTP-Sync-Server
  --backup [pfad]           sichert die DB online nach pfad (Default:
                             backups/alltagshelfer-<datum>.db)
  --restore <pfad>          stellt die DB aus einem Backup wieder her
                             (App muss vorher beendet sein)
  --list-backups [verz]     listet vorhandene Backups
  --export [verz]           exportiert alle Entitaeten als CSV
                             (Default: ausgaben/export-<datum>/)
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path("alltagshelfer_demo.db")
DEFAULT_BACKUP_DIR = Path("backups")
DEFAULT_EXPORT_DIR = Path("ausgaben")


def _cmd_backup(target: str | None) -> int:
    from database import Database
    from services.backup import default_backup_name, make_backup
    if not DEFAULT_DB.exists():
        print(f"Keine DB '{DEFAULT_DB}' gefunden - nichts zu sichern.")
        return 1
    db = Database(str(DEFAULT_DB))
    try:
        path = Path(target) if target else (
            DEFAULT_BACKUP_DIR / default_backup_name())
        result = make_backup(db, path)
        print(f"Backup geschrieben: {result}")
    except RuntimeError as exc:
        print(f"Fehler: {exc}")
        return 1
    finally:
        db.close()
    return 0


def _cmd_restore(source: str) -> int:
    from services.backup import restore_database
    src = Path(source)
    if not src.exists():
        print(f"Backup '{src}' existiert nicht.")
        return 1
    restore_database(src, DEFAULT_DB)
    print(f"DB wiederhergestellt aus {src}")
    return 0


def _cmd_list_backups(directory: str | None) -> int:
    from services.backup import list_backups
    target = Path(directory) if directory else DEFAULT_BACKUP_DIR
    found = list_backups(target)
    if not found:
        print(f"Keine Backups in {target}.")
        return 0
    print(f"Backups in {target}:")
    for path in found:
        size_kb = path.stat().st_size / 1024
        mtime = datetime.fromtimestamp(
            path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {path.name}  ({size_kb:.0f} kB, {mtime})")
    return 0


def _cmd_export(directory: str | None) -> int:
    from database import (CalendarRepository, ContractRepository, Database,
                            ExpenseRepository, FamilyRepository,
                            SocialRepository)
    from services.export import export_all
    if not DEFAULT_DB.exists():
        print(f"Keine DB '{DEFAULT_DB}' gefunden - nichts zu exportieren.")
        return 1
    target = Path(directory) if directory else (
        DEFAULT_EXPORT_DIR
        / f"export-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    db = Database(str(DEFAULT_DB))
    try:
        counts = export_all(
            target,
            ContractRepository(db), ExpenseRepository(db),
            CalendarRepository(db), SocialRepository(db),
            FamilyRepository(db))
    finally:
        db.close()
    print(f"Export geschrieben nach {target}:")
    for key, count in counts.items():
        print(f"  {key:12s} {count} Zeile(n)")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        from main import main as run_demo
        run_demo()
        return 0
    if args[0] == "--diagnose":
        from diagnose import print_diagnosis
        return print_diagnosis()
    if args[0] == "--gui":
        from gui import main as run_gui
        run_gui()
        return 0
    if args[0] == "--sync-server":
        sys.argv = ["alltagshelfer-sync-server"] + args[1:]
        from services.sync_server import main as run_server
        run_server()
        return 0
    if args[0] == "--backup":
        return _cmd_backup(args[1] if len(args) > 1 else None)
    if args[0] == "--restore":
        if len(args) < 2:
            print("Fehler: --restore <pfad> wird benoetigt.")
            return 2
        return _cmd_restore(args[1])
    if args[0] == "--list-backups":
        return _cmd_list_backups(args[1] if len(args) > 1 else None)
    if args[0] == "--export":
        return _cmd_export(args[1] if len(args) > 1 else None)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
