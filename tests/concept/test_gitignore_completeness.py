"""
Tests fuer die Vollstaendigkeit der .gitignore.

Hintergrund: zweimal hat ein versehentlicher `git add dist/` oder
`git add build/` riesige Build-Artefakte ins Repo gezogen. Diese
Tests verhindern das dauerhaft:

  1. .gitignore enthaelt alle Pflicht-Pattern fuer die Build-Pipelines
     (PyInstaller, Buildozer, Kivy-iOS, Xcode).
  2. `git check-ignore` bestaetigt, dass typische Build-Artefakte
     tatsaechlich ignoriert wuerden (verifiziert die Regel-Wirksamkeit,
     nicht nur die Existenz).
  3. Keine Build-Binaries sind aktuell im Repo getrackt
     (.exe, .dll, .apk, .aab, .ipa, .pyd, .so, .dylib).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


REPO = Path(__file__).resolve().parents[2]
GITIGNORE = REPO / ".gitignore"


# Pflicht-Pattern: was MUSS in .gitignore stehen
REQUIRED_PATTERNS = [
    # Desktop-Build
    "build/", "dist/",
    "*.exe", "*.dll", "*.pyd", "*.so", "*.dylib",
    # Android-Build (Buildozer)
    ".buildozer/", "bin/",
    "*.apk", "*.aab", "*.keystore",
    # iOS-Build
    "*.ipa", "xcuserdata/", "DerivedData/",
    # Lokal generierte Test-/App-Daten
    "*.db", "*.sqlite", "ausgaben/", "logs/", "backups/",
    # Play-Store-Sync-Mock
    "playstore.local.json",
    # Python-Standard
    "__pycache__/", "*.pyc", ".venv/", ".pytest_cache/",
    ".mypy_cache/", ".coverage", "htmlcov/",
    # IDE
    ".vscode/", ".idea/",
    # OS
    ".DS_Store", "Thumbs.db",
]


def _gitignore_text() -> str:
    return GITIGNORE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Pflicht-Pattern in .gitignore
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("pattern", REQUIRED_PATTERNS)
def test_gitignore_contains_pattern(pattern):
    text = _gitignore_text()
    assert pattern in text, (
        f".gitignore enthaelt das Pflicht-Pattern {pattern!r} nicht. "
        "Build-Artefakte wuerden im Repo landen.")


def test_gitignore_not_empty():
    text = _gitignore_text()
    assert len(text) > 200, ".gitignore ist verdaechtig kurz."


def test_gitignore_has_pyinstaller_section_comment():
    """Wer die Datei pflegt, soll auf einen Blick sehen, welcher
    Block welche Pipeline schuetzt."""
    text = _gitignore_text()
    assert "PyInstaller" in text or "Desktop-Build" in text
    assert "Buildozer" in text or "Android-Build" in text


# ---------------------------------------------------------------------------
# 2) `git check-ignore` bestaetigt Wirksamkeit
# ---------------------------------------------------------------------------
def _check_ignored(path: str) -> bool:
    """True, wenn git den Pfad als ignored ansieht.

    Wir benutzen --no-index, damit der Test auch funktioniert, wenn
    der Pfad nicht existiert.
    """
    proc = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", path],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    # Exit-Code 0 = ignored, 1 = not ignored, 128 = git-Fehler
    return proc.returncode == 0


SAMPLE_PATHS_THAT_MUST_BE_IGNORED = [
    # Desktop-Build (PyInstaller)
    "build/foo.txt",
    "build/anything/at/any/depth.py",
    "dist/ZunaroDo/ZunaroDo.exe",
    "dist/ZunaroDo/_internal/python311.dll",
    "dist/ZunaroDo/_internal/_tcl_data/tcl8.6/init.tcl",
    "dist/ZunaroDo/_internal/cryptography/hazmat/_oid.cpython-311.dll",
    "dist/something.dmg",
    "ZunaroDo.exe",
    "release.deb",
    "release.AppImage",
    # Android-Build
    ".buildozer/android/platform/build.cfg",
    "bin/alltagshelfer-0.9.0-arm64-v8a-debug.apk",
    "release.aab",
    "release.keystore",
    "release.jks",
    # iOS-Build
    "release.ipa",
    "ZunaroDo-ios/xcuserdata/torst.xcuserdatad/UserInterfaceState.xcuserstate",
    "ZunaroDo-ios/Pods/Manifest.lock",
    "DerivedData/Build/Products/Debug.app/Foo",
    # Lokale Daten
    "alltagshelfer.db",
    "test.sqlite",
    "ausgaben/2026-05.pdf",
    "logs/app.log",
    "backups/2026-05.tar.gz",
    # Mock-Backend
    "playstore.local.json",
    # Python
    "tools/__pycache__/dashboard.cpython-311.pyc",
    ".pytest_cache/v/cache/lastfailed",
    ".coverage",
    "htmlcov/index.html",
    # OS-Cruft
    ".DS_Store",
    "Thumbs.db",
]


@pytest.mark.parametrize("path", SAMPLE_PATHS_THAT_MUST_BE_IGNORED)
def test_path_is_ignored_by_git(path: str):
    """Die Wirksamkeit der Pattern wird mit git selbst geprueft -
    nicht nur die Existenz im Datei-Text."""
    assert _check_ignored(path), (
        f"git wuerde den Pfad {path!r} NICHT ignorieren. "
        "Build-Artefakte koennten ins Repo gelangen.")


# ---------------------------------------------------------------------------
# 3) Keine Build-Binaries sind aktuell getrackt
# ---------------------------------------------------------------------------
def _tracked_files() -> set[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return set()
    return set(proc.stdout.splitlines())


@pytest.mark.parametrize("suffix", [
    ".exe", ".dll", ".dylib", ".so", ".pyd",
    ".apk", ".aab", ".ipa",
    ".keystore", ".jks",
    ".dmg", ".AppImage", ".deb", ".rpm", ".msi",
])
def test_no_build_binary_is_tracked(suffix: str):
    tracked = _tracked_files()
    if not tracked:
        pytest.skip("Kein Git-Repo bzw. 'git ls-files' liefert nichts")
    offenders = [f for f in tracked if f.endswith(suffix)]
    assert not offenders, (
        f"Build-Binary-Dateien {suffix} sind im Repo getrackt: "
        f"{offenders[:3]}. Bitte mit "
        f"`git rm --cached <pfad>` aus dem Index entfernen.")


def test_no_dist_or_build_folder_tracked():
    """Kein einziger Eintrag unter dist/ oder build/ darf getrackt sein."""
    tracked = _tracked_files()
    if not tracked:
        pytest.skip("Kein Git-Repo bzw. 'git ls-files' liefert nichts")
    bad = [f for f in tracked
           if f.startswith("dist/") or f.startswith("build/")
           or f.startswith(".buildozer/") or f.startswith("bin/")]
    assert not bad, (
        f"Folgende Build-Output-Pfade sind getrackt: {bad[:5]}")


def test_playstore_local_json_not_tracked():
    """Mock-State des Play-Store-Sync-Tools darf nicht im Repo sein."""
    tracked = _tracked_files()
    if not tracked:
        pytest.skip("Kein Git-Repo")
    assert "playstore.local.json" not in tracked, (
        "playstore.local.json ist getrackt - das ist ein lokaler "
        "Mock-State, der nicht ins Repo gehoert. Mit "
        "`git rm --cached playstore.local.json` aus dem Index "
        "entfernen.")
