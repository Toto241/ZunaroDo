"""
Build-Status fuer Android / iOS / PC.

Ein reines Lese-Modul: es startet nichts, sondern liest aus dem
Repository, was schon gebaut wurde, und liefert eine kanonische
Beschreibung pro Plattform zurueck.

Daten je Plattform:

  * platform     - "android" | "ios" | "desktop"
  * label        - Anzeige-Name fuer das Dashboard
  * icon         - Emoji-Icon
  * available    - True, wenn der Build auf dieser Maschine moeglich ist
  * tool         - z.B. "buildozer" / "kivy-ios" / "pyinstaller"
  * command      - sichtbarer Build-Befehl (kopier-tauglich)
  * script_path  - Pfad zu scripts/build-<plat>.{bat,sh}, falls vorhanden
  * artifact     - Dict mit { exists, path, size, mtime, version } des
                   zuletzt gebauten Artefakts (None wenn keines)
  * prereqs      - Liste der Vorbedingungen ("WSL2", "Xcode" ...)
  * notes        - Freitext (Doku-Hinweis)

Auf diese Beschreibung greift `tools/dashboard.py` zu, um die Build-
Center-Karten zu rendern. Aufruf aus der Shell:

    python -m tools.build_status            # kompakte Tabelle
    python -m tools.build_status --json     # maschinenlesbar
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ---------------------------------------------------------------------------
# Modell
# ---------------------------------------------------------------------------
@dataclass
class ArtifactInfo:
    path: str
    exists: bool
    size_bytes: int = 0
    mtime_iso: str = ""
    version_guess: str = ""


@dataclass
class BuildStatus:
    platform: str
    label: str
    icon: str
    tool: str
    command: str
    available: bool
    prereqs: list[str] = field(default_factory=list)
    script_path: Optional[str] = None
    artifact: Optional[ArtifactInfo] = None
    notes: str = ""


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------
def _which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _read_spec(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.split("#", 1)[0].strip()
    return out


def _newest_artifact(directory: Path, patterns: tuple[str, ...]) -> Optional[Path]:
    if not directory.is_dir():
        return None
    candidates: list[Path] = []
    for pat in patterns:
        candidates.extend(directory.rglob(pat))
    candidates = [p for p in candidates if p.is_file()]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _artifact_info(path: Optional[Path]) -> Optional[ArtifactInfo]:
    if path is None:
        return None
    st = path.stat()
    mtime = dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).isoformat(
        timespec="seconds")
    # Versions-Heuristik aus Dateiname (z.B. alltagshelfer-0.9.0-arm64-...)
    name = path.name
    m = re.search(r"-([0-9]+(?:\.[0-9]+){1,2})-", name)
    version = m.group(1) if m else ""
    return ArtifactInfo(
        path=str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT)
              else str(path),
        exists=True, size_bytes=st.st_size,
        mtime_iso=mtime, version_guess=version)


# ---------------------------------------------------------------------------
# Plattform-Status
# ---------------------------------------------------------------------------
def _android_status() -> BuildStatus:
    spec = _read_spec(REPO_ROOT / "buildozer.spec")
    pkg = spec.get("package.name", "alltagshelfer")
    version = spec.get("version", "0.0.0")
    # Buildozer schreibt nach bin/ oder dist/ - beide pruefen
    artifact_path = _newest_artifact(
        DIST_DIR, ("*.apk", "*.aab")
    ) or _newest_artifact(REPO_ROOT / "bin", ("*.apk", "*.aab"))
    artifact = _artifact_info(artifact_path)

    on_linux_or_mac = platform.system() in ("Linux", "Darwin")
    on_wsl = "microsoft" in platform.release().lower() if on_linux_or_mac \
        else False
    has_buildozer = _which("buildozer")
    available = (on_linux_or_mac and has_buildozer) or on_wsl

    script = SCRIPTS_DIR / ("build-android.bat" if os.name == "nt"
                              else "build-android.sh")
    return BuildStatus(
        platform="android",
        label="Android",
        icon="🤖",
        tool="Buildozer / python-for-android",
        command="buildozer android debug",
        available=available,
        prereqs=[
            "Linux oder macOS (Windows: WSL2 + Ubuntu 22.04)",
            "Java 17 (openjdk-17-jdk)",
            "Android SDK + NDK (laedt Buildozer automatisch)",
            "Python 3.10+",
            "pip install buildozer cython==0.29.36",
        ],
        script_path=str(script.relative_to(REPO_ROOT).as_posix())
            if script.is_file() else None,
        artifact=artifact,
        notes=(f"Erzeugt `{pkg}-{version}-arm64-v8a-debug.apk` unter "
               "`dist/` (bzw. `bin/`). Buildozer laedt beim ersten Lauf "
               "ca. 1 GB SDK/NDK herunter."),
    )


def _ios_status() -> BuildStatus:
    # iOS ist in diesem Repo noch nicht aufgesetzt. Wir liefern eine
    # vorbereitete Scaffolding-Beschreibung.
    artifact_path = _newest_artifact(DIST_DIR, ("*.ipa", "*.app"))
    artifact = _artifact_info(artifact_path)
    on_mac = platform.system() == "Darwin"
    has_xcode = on_mac and _which("xcodebuild")
    has_toolchain = on_mac and _which("toolchain")
    available = on_mac and has_xcode and has_toolchain

    script = SCRIPTS_DIR / "build-ios.sh"
    return BuildStatus(
        platform="ios",
        label="iOS",
        icon="🍎",
        tool="kivy-ios + Xcode",
        command="toolchain create ZunaroDo .. && open ZunaroDo-ios/",
        available=available,
        prereqs=[
            "macOS mit Xcode 15+",
            "pip install kivy-ios",
            "toolchain build python3 kivy openssl",
            "Apple-Developer-Account fuer Code-Signing (Release)",
        ],
        script_path=str(script.relative_to(REPO_ROOT).as_posix())
            if script.is_file() else None,
        artifact=artifact,
        notes=("iOS-Port erfordert macOS - kivy-ios baut die Python-/Kivy-"
               "Runtime fuer ARM64 und erzeugt ein Xcode-Projekt. Aktuell "
               "im Repo noch nicht aufgesetzt."),
    )


def _desktop_status() -> BuildStatus:
    spec = REPO_ROOT / "alltagshelfer.spec"
    artifact_dir = DIST_DIR / "ZunaroDo"
    artifact_path: Optional[Path] = None
    if artifact_dir.is_dir():
        artifact_path = _newest_artifact(
            artifact_dir, ("ZunaroDo.exe", "ZunaroDo", "*.dmg"))
    if artifact_path is None:
        artifact_path = _newest_artifact(DIST_DIR,
                                          ("ZunaroDo.exe",
                                           "ZunaroDo", "*.dmg",
                                           "*.AppImage"))
    artifact = _artifact_info(artifact_path)
    has_pyinstaller = _which("pyinstaller") or _has_module("PyInstaller")
    available = spec.is_file() and has_pyinstaller

    script = SCRIPTS_DIR / ("build-desktop.bat" if os.name == "nt"
                              else "build-desktop.sh")
    return BuildStatus(
        platform="desktop",
        label="PC (Desktop)",
        icon="🖥️",
        tool="PyInstaller",
        command="pyinstaller --noconfirm alltagshelfer.spec",
        available=available,
        prereqs=[
            "Python 3.10+",
            "pip install pyinstaller",
            "Tk + customtkinter (kommt mit der App)",
        ],
        script_path=str(script.relative_to(REPO_ROOT).as_posix())
            if script.is_file() else None,
        artifact=artifact,
        notes=(f"Erzeugt ein Single-Folder-Bundle in "
               f"`dist/ZunaroDo/`. Spec-Datei: "
               f"`alltagshelfer.spec`. Plattform-Build: "
               f"jeweils auf der Zielplattform ausfuehren "
               f"(Windows/macOS/Linux). PyInstaller verfuegbar: "
               f"{'ja' if has_pyinstaller else 'nein'}."),
    )


def _has_module(name: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def gather() -> list[BuildStatus]:
    return [_android_status(), _ios_status(), _desktop_status()]


def to_dict(items: list[BuildStatus]) -> list[dict]:
    out: list[dict] = []
    for s in items:
        d = asdict(s)
        if d.get("artifact") is None:
            d["artifact"] = None
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true",
                        help="JSON-Ausgabe (maschinenlesbar)")
    parser.add_argument("--no-emoji", action="store_true",
                        help="Emojis aus der Ausgabe entfernen (Windows-CP)")
    args = parser.parse_args(argv)
    # Windows-CP1252-Stdout kann Emojis nicht; UTF-8 erzwingen oder
    # Emojis weglassen.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass
    items = gather()
    if args.no_emoji:
        for s in items:
            s.icon = ""
    if args.json:
        print(json.dumps(to_dict(items), indent=2, ensure_ascii=False))
        return 0
    for s in items:
        print(f"=== {s.icon} {s.label}  ({'bereit' if s.available else 'nicht verfuegbar'}) ===")
        print(f"  Tool:    {s.tool}")
        print(f"  Befehl:  {s.command}")
        if s.script_path:
            print(f"  Skript:  {s.script_path}")
        if s.artifact:
            print(f"  Letztes Artefakt:")
            print(f"    Pfad:     {s.artifact.path}")
            print(f"    Groesse:  {s.artifact.size_bytes:,} Bytes")
            print(f"    Datum:    {s.artifact.mtime_iso}")
            if s.artifact.version_guess:
                print(f"    Version:  {s.artifact.version_guess}")
        else:
            print(f"  Letztes Artefakt: (keines gefunden)")
        print(f"  Voraussetzungen:")
        for p in s.prereqs:
            print(f"    - {p}")
        print(f"  Hinweise: {s.notes}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
