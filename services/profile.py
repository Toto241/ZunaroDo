"""
Multi-User-Profile fuer den Alltagshelfer.

Konzept: ein Profil = eigene DB-Datei + eigener Sync-State-Ordner.

Quellen fuer den aktiven Profilnamen, in Reihenfolge:
  1. expliziter Parameter (z.B. aus CLI '--profile')
  2. Umgebungsvariable ALLTAGSHELFER_PROFILE
  3. leerer String -> Default-Profil (urspruengliche Dateinamen)

Profilnamen werden auf [A-Za-z0-9_-] reduziert, damit sie sicher in
Dateinamen verwendet werden koennen. Ein leerer/saeurer Name faellt auf
das Default-Profil zurueck.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional


_SAFE_NAME = re.compile(r"[^A-Za-z0-9_-]")


def sanitize_profile(name: Optional[str]) -> str:
    if not name:
        return ""
    cleaned = _SAFE_NAME.sub("", name.strip())
    return cleaned[:32]                              # harte Obergrenze


def resolve_profile(explicit: Optional[str] = None) -> str:
    """Loest den aktiven Profilnamen auf - leer = Default."""
    name = explicit if explicit is not None \
        else os.environ.get("ALLTAGSHELFER_PROFILE", "")
    return sanitize_profile(name)


def db_path(profile: str, default_filename: str) -> str:
    """Liefert den DB-Pfad fuer ein Profil (oder Default ohne Profil)."""
    if not profile:
        return default_filename
    base = Path(default_filename).stem
    suffix = Path(default_filename).suffix or ".db"
    # alltagshelfer_demo + _anna -> alltagshelfer_demo_anna.db
    return f"{base}_{profile}{suffix}"


def state_dir(profile: str,
              default_dir: str = ".alltagshelfer-state") -> Path:
    """Liefert das State-Verzeichnis fuer ein Profil."""
    if not profile:
        return Path(default_dir)
    return Path(f"{default_dir}-{profile}")


def list_profiles(base_dir: str = ".") -> list[str]:
    """
    Liefert die in 'base_dir' erkennbaren Profile (anhand von
    .alltagshelfer-state-<name> Verzeichnissen). Default-Profil
    erscheint als leerer String, wenn vorhanden.
    """
    base = Path(base_dir)
    found: set[str] = set()
    for entry in base.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        if name == ".alltagshelfer-state":
            found.add("")
        elif name.startswith(".alltagshelfer-state-"):
            profile = name[len(".alltagshelfer-state-"):]
            if sanitize_profile(profile) == profile:
                found.add(profile)
    return sorted(found)
