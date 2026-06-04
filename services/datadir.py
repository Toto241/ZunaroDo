"""
Datenverzeichnis-Aufloesung fuer den Alltagshelfer.

Beim Start waehlt der Nutzer (einmalig) ein Verzeichnis, in dem ALLE
laufzeit-erzeugten Dateien liegen: die SQLite-DB (``alltagshelfer*.db``),
Exporte (``ausgaben/``), Backups (``backups/``), Sync-State
(``.alltagshelfer-state*``), der Profil-Zeiger und Logs.

Die Wahl wird in einer kleinen Zeiger-Datei im OS-Konfigurationsordner
gemerkt - NICHT im Datenverzeichnis selbst, das muessten wir ja erst
finden. Aufloesungsreihenfolge:

  1. Umgebungsvariable ALLTAGSHELFER_DATA_DIR (hat immer Vorrang)
  2. gemerkte Zeiger-Datei (``datadir.json`` im Konfig-Ordner)
  3. None -> Erststart; der Aufrufer muss ein Verzeichnis erfragen

Der Konfig-Ordner ist plattformabhaengig und laesst sich fuer Tests oder
portable Setups via ALLTAGSHELFER_CONFIG_DIR ueberschreiben.

Das eigentliche Routing geschieht per :func:`activate` (Wechsel des
Arbeitsverzeichnisses): die App legt ihre Dateien CWD-relativ ab, waehrend
Ressourcen (``locales/``, ``assets/``) ueber ``__file__`` geladen werden und
vom Verzeichniswechsel unberuehrt bleiben.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional


APP_DIRNAME = "Alltagshelfer"
DATA_DIR_ENV = "ALLTAGSHELFER_DATA_DIR"
CONFIG_DIR_ENV = "ALLTAGSHELFER_CONFIG_DIR"
POINTER_FILENAME = "datadir.json"

# Bekannte Datenartefakte im (alten) Arbeitsverzeichnis, die beim Erststart
# in das neue Datenverzeichnis kopiert werden ("kopiert bzw. erstellt").
# Reihenfolge egal - Duplikate (z.B. mehrere DB-Dateien) werden behandelt.
_DATA_GLOBS = (
    "alltagshelfer*.db",
    "ausgaben",
    "backups",
    "logs",
    ".alltagshelfer-state",
    ".alltagshelfer-state-*",
    ".alltagshelfer-active-profile",
)


def _platform_base(kind: str) -> Path:
    """Plattform-Basisordner; ``kind`` ist 'config' oder 'data'."""
    home = Path.home()
    if os.name == "nt":
        root = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        return Path(root) if root else home
    if sys.platform == "darwin":
        return home / "Library" / "Application Support"
    # Linux/Unix: XDG-Basisverzeichnisse
    if kind == "config":
        root = os.environ.get("XDG_CONFIG_HOME")
        return Path(root) if root else home / ".config"
    root = os.environ.get("XDG_DATA_HOME")
    return Path(root) if root else home / ".local" / "share"


def config_dir() -> Path:
    """Ordner fuer die Zeiger-Datei (ueberschreibbar via Env fuer Tests)."""
    override = os.environ.get(CONFIG_DIR_ENV)
    if override and override.strip():
        return Path(override).expanduser()
    return _platform_base("config") / APP_DIRNAME


def pointer_file() -> Path:
    """Pfad der Zeiger-Datei, die das gewaehlte Datenverzeichnis merkt."""
    return config_dir() / POINTER_FILENAME


def default_data_dir() -> Path:
    """Vernuenftiger Vorschlag fuer den Verzeichnis-Dialog beim Erststart."""
    return _platform_base("data") / APP_DIRNAME


def configured_data_dir() -> Optional[Path]:
    """Aufgeloestes Datenverzeichnis oder ``None`` beim Erststart.

    Env vor Zeiger-Datei. Ein leerer/ungueltiger Eintrag gilt als 'nicht
    gesetzt' (-> None), damit der Aufrufer das Verzeichnis erfragt.
    """
    env = os.environ.get(DATA_DIR_ENV)
    if env and env.strip():
        return Path(env).expanduser()
    try:
        data = json.loads(pointer_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    raw = data.get("data_dir") if isinstance(data, dict) else None
    if not raw or not str(raw).strip():
        return None
    return Path(str(raw)).expanduser()


def remember_data_dir(path: Path) -> Path:
    """Merkt das gewaehlte Verzeichnis dauerhaft in der Zeiger-Datei.

    Liefert den aufgeloesten Pfad, der gespeichert wurde.
    """
    resolved = Path(path).expanduser().resolve()
    cfg = config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    pointer_file().write_text(
        json.dumps({"data_dir": str(resolved)}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return resolved


def migrate_into(src: Path, dst: Path) -> list[str]:
    """Kopiert bekannte Datenartefakte aus ``src`` nach ``dst``.

    Nur was im Ziel noch nicht existiert wird kopiert; liefert die Namen
    der tatsaechlich kopierten Eintraege. 'Kopieren' (nicht Verschieben)
    ist bewusst gewaehlt: das Original bleibt als Sicherung erhalten, bis
    der Nutzer es selbst aufraeumt.
    """
    src_p = Path(src).expanduser().resolve()
    dst_p = Path(dst).expanduser().resolve()
    copied: list[str] = []
    if src_p == dst_p or not src_p.is_dir():
        return copied
    dst_p.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for pattern in _DATA_GLOBS:
        for item in sorted(src_p.glob(pattern)):
            if item.name in seen:
                continue
            seen.add(item.name)
            target = dst_p / item.name
            if target.exists():
                continue
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
            copied.append(item.name)
    return copied


def prepare_data_dir(path: Path,
                     migrate_from: Optional[Path] = None
                     ) -> tuple[Path, list[str]]:
    """Stellt das Datenverzeichnis bereit.

    Legt es bei Bedarf an, migriert optional vorhandene Daten aus
    ``migrate_from`` und liefert ``(aufgeloester_pfad, kopierte_namen)``.
    """
    resolved = Path(path).expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    if migrate_from is not None:
        copied = migrate_into(Path(migrate_from), resolved)
    return resolved, copied


def activate(path: Path) -> Path:
    """Wechselt das Arbeitsverzeichnis ins Datenverzeichnis.

    Danach landen alle CWD-relativen Pfade (DB, ``ausgaben/``, ``backups/``,
    Sync-State, Profil-Zeiger) dort. Liefert den aufgeloesten Pfad.
    """
    resolved = Path(path).expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    os.chdir(resolved)
    return resolved
