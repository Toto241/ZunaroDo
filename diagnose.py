"""
Diagnose des Alltagshelfers - liefert einen schnellen Statusbericht.

Verwendung:
    python -m alltagshelfer --diagnose
    python diagnose.py

Zeigt: Python-Version, Plattform, geladene optionale Bibliotheken,
verfuegbare OCR-Engines, DB-Verschluesselungs-Modus, Sync-Provider,
Gemini-Verfuegbarkeit, Anzahl Module/Capabilities und einen kurzen
Konfigurations-Auszug.
"""
from __future__ import annotations

import importlib
import os
import platform
import sys
from pathlib import Path
from typing import Optional


def _check_module(name: str) -> tuple[bool, Optional[str]]:
    """Liefert (vorhanden, Version) fuer ein optionales Paket."""
    try:
        mod = importlib.import_module(name)
        ver = getattr(mod, "__version__", None)
        return True, ver
    except Exception:
        return False, None


def _line(label: str, value: str) -> str:
    return f"  {label:<26} {value}"


def collect_diagnosis() -> dict:
    """Sammelt die Diagnose-Daten als Dictionary (nuetzlich fuer Tests)."""
    optional_modules = [
        "google.generativeai",
        "customtkinter",
        "fpdf",
        "apscheduler",
        "plyer",
        "pytesseract",
        "PIL",
        "easyocr",
        "sqlcipher3",
        "anthropic",
    ]
    mods = {}
    for name in optional_modules:
        ok, ver = _check_module(name)
        mods[name] = {"present": ok, "version": ver}

    env = {
        "GOOGLE_API_KEY": bool(os.environ.get("GOOGLE_API_KEY")
                                or os.environ.get("GEMINI_API_KEY")),
        "ALLTAGSHELFER_DB_KEY": bool(os.environ.get("ALLTAGSHELFER_DB_KEY")),
        "ALLTAGSHELFER_SYNC_DIR": os.environ.get(
            "ALLTAGSHELFER_SYNC_DIR", ""),
        "ALLTAGSHELFER_SYNC_URL": os.environ.get(
            "ALLTAGSHELFER_SYNC_URL", ""),
        "ALLTAGSHELFER_IMAP_HOST": os.environ.get(
            "ALLTAGSHELFER_IMAP_HOST", ""),
    }

    # OCR-Engines durch den eigenen Helper testen
    try:
        from services.ocr import available_engines
        ocr_engines = available_engines()
    except Exception as exc:                              # pragma: no cover
        ocr_engines = [f"(Fehler: {exc})"]

    # Module + Capabilities ohne DB zu oeffnen abzaehlen: lazy
    module_count = 0
    capability_count = 0
    try:
        from database import (CalendarRepository, ContractRepository,
                                Database, DayEntryRepository, ExpenseRepository,
                                FamilyRepository, PriceMemoryRepository,
                                ProposalRepository, ShoppingRepository,
                                SocialRepository)
        from main import build_registry
        from services.output import OutputService
        tmp_db = Path("alltagshelfer_diag.tmpdb")
        db = Database(str(tmp_db))
        registry = build_registry(db, OutputService("ausgaben_diag"))
        module_count = len(registry.modules())
        capability_count = len(registry.all_capabilities())
        db.close()
        tmp_db.unlink(missing_ok=True)
        Path("ausgaben_diag").rmdir() if Path("ausgaben_diag").exists() \
            and not any(Path("ausgaben_diag").iterdir()) else None
    except Exception as exc:
        module_count = -1
        capability_count = -1
        print(f"  (Modul-Zaehlung uebersprungen: {exc})", file=sys.stderr)

    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "modules": mods,
        "env": env,
        "ocr_engines": ocr_engines,
        "module_count": module_count,
        "capability_count": capability_count,
    }


def print_diagnosis() -> int:
    """Druckt die Diagnose menschenlesbar. Liefert 0 bei OK."""
    data = collect_diagnosis()
    print("=" * 64)
    print("  Alltagshelfer-Diagnose")
    print("=" * 64)
    print(_line("Python", data["python_version"]))
    print(_line("Plattform", data["platform"]))
    print(_line("Module / Capabilities",
                  f"{data['module_count']} / {data['capability_count']}"))
    print()
    print("Optionale Pakete:")
    for name, info in data["modules"].items():
        status = ("OK " + (info["version"] or "")
                   if info["present"] else "fehlt")
        print(_line(name, status))
    print()
    print("Umgebung:")
    for key, value in data["env"].items():
        if isinstance(value, bool):
            print(_line(key, "gesetzt" if value else "leer"))
        else:
            print(_line(key, value or "(leer)"))
    print()
    print("OCR-Engines verfuegbar:")
    print(_line("", ", ".join(data["ocr_engines"]) or "keine"))
    return 0


if __name__ == "__main__":
    sys.exit(print_diagnosis())
