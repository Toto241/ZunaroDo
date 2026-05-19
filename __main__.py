"""
Erlaubt `python -m alltagshelfer` als CLI-Einstieg.

Globale Optionen:
  --profile <name>          aktives Profil setzen (siehe services/profile.py).
                             Default: leer = urspruengliche Dateinamen.

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
  --list-profiles           listet erkennbare Profile (anhand State-Dirs)
  --export [verz]           exportiert alle Entitaeten als CSV
                             (Default: ausgaben/export-<datum>/)
  --import <verz>           importiert CSV-Dateien aus einem Verzeichnis
                             (Spiegel des Exports)
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path("alltagshelfer_demo.db")
DEFAULT_BACKUP_DIR = Path("backups")
DEFAULT_EXPORT_DIR = Path("ausgaben")


def _profile_aware_db_path() -> Path:
    """DB-Pfad fuer das aktuell aktive Profil (Env: ALLTAGSHELFER_PROFILE)."""
    from services.profile import db_path, resolve_profile
    return Path(db_path(resolve_profile(), str(DEFAULT_DB)))


def _cmd_backup(target: str | None) -> int:
    from database import Database
    from services.backup import default_backup_name, make_backup
    db_file = _profile_aware_db_path()
    if not db_file.exists():
        print(f"Keine DB '{db_file}' gefunden - nichts zu sichern.")
        return 1
    db = Database(str(db_file))
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
    target = _profile_aware_db_path()
    restore_database(src, target)
    print(f"DB wiederhergestellt aus {src} nach {target}")
    return 0


def _cmd_list_profiles() -> int:
    from services.profile import list_profiles, resolve_profile
    current = resolve_profile()
    profiles = list_profiles()
    if not profiles:
        print("Keine Profile erkannt. (Profile entstehen, sobald ein "
              "State-Verzeichnis angelegt wird.)")
        return 0
    print("Erkannte Profile (anhand State-Verzeichnisse):")
    for p in profiles:
        marker = " <-- aktiv" if p == current else ""
        name = p or "(default)"
        print(f"  {name}{marker}")
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


def _cmd_import(directory: str) -> int:
    from database import (CalendarRepository, ContractRepository, Database,
                            ExpenseRepository, FamilyRepository,
                            SocialRepository)
    from services.import_csv import import_all
    src = Path(directory)
    if not src.is_dir():
        print(f"Quellverzeichnis '{src}' existiert nicht.")
        return 1
    db = Database(str(_profile_aware_db_path()))
    try:
        counts = import_all(
            src,
            ContractRepository(db), ExpenseRepository(db),
            CalendarRepository(db), SocialRepository(db),
            FamilyRepository(db))
    finally:
        db.close()
    if not counts:
        print(f"Keine bekannten CSV-Dateien in {src} gefunden.")
        return 1
    print(f"Import aus {src}:")
    for name, count in counts.items():
        print(f"  {name:18s} {count} Zeile(n)")
    return 0


def _cmd_export(directory: str | None) -> int:
    from database import (CalendarRepository, ContractRepository, Database,
                            ExpenseRepository, FamilyRepository,
                            SocialRepository)
    from services.export import export_all
    db_file = _profile_aware_db_path()
    if not db_file.exists():
        print(f"Keine DB '{db_file}' gefunden - nichts zu exportieren.")
        return 1
    target = Path(directory) if directory else (
        DEFAULT_EXPORT_DIR
        / f"export-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    db = Database(str(db_file))
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
    # Globales --profile <name> aus der Argumentliste extrahieren und
    # in die Umgebung schreiben - alle Subcommands lesen daraus.
    new_args: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--profile" and i + 1 < len(args):
            from services.profile import sanitize_profile
            os.environ["ALLTAGSHELFER_PROFILE"] = sanitize_profile(args[i + 1])
            i += 2
        else:
            new_args.append(args[i])
            i += 1
    args = new_args
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
    if args[0] == "--list-profiles":
        return _cmd_list_profiles()
    if args[0] == "--export":
        return _cmd_export(args[1] if len(args) > 1 else None)
    if args[0] == "--import":
        if len(args) < 2:
            print("Fehler: --import <verz> wird benoetigt.")
            return 2
        return _cmd_import(args[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
