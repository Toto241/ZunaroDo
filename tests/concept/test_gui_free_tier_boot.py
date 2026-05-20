"""
Live-Boot-Test: AlltagshelferGUI startet im FREE-Tier ohne Crash.

Hintergrund: zweimal hat die Auslieferung wegen genau dieses Falls
gecrasht (AttributeError fuer 'expense_list' und 'chat'). Der
statische Scanner in test_gui_widget_guards.py findet die Quelle des
Bugs - dieser Live-Test verifiziert, dass die App im FREE-Tier
tatsaechlich bootet (mit gesperrten Pro-Tabs).

Wir starten dazu einen **frischen Subprozess**: bootstrap() ruft
diverse Module auf, die Modul-Level-State setzen (License-Cache,
Scheduler-Singletons, Tk-Defaults). Wuerden wir die GUI in-process
hochziehen, koennten nachfolgende Tests im selben pytest-Lauf
diesen State sehen. Subprozess = saubere Isolation.

Wird automatisch uebersprungen, wenn kein Tkinter-Display oder
kein customtkinter verfuegbar ist.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest


pytestmark = [pytest.mark.concept, pytest.mark.release_gate, pytest.mark.slow]


REPO = Path(__file__).resolve().parents[2]


def _has_display() -> bool:
    if os.name == "nt":
        return True
    return bool(os.environ.get("DISPLAY"))


def _has_customtkinter() -> bool:
    try:
        import customtkinter      # noqa: F401
        return True
    except Exception:              # noqa: BLE001
        return False


_BOOT_TEMPLATE = textwrap.dedent("""
    import os, sys, tempfile, traceback
    REPO = %(repo)r
    LICENSE_TIER = %(tier)r

    tmp = tempfile.mkdtemp(prefix='zd-boot-')
    os.chdir(tmp)
    if os.name == 'nt':
        os.environ['USERPROFILE'] = tmp
        os.environ['APPDATA'] = tmp
    else:
        os.environ['HOME'] = tmp
    os.environ['ALLTAGSHELFER_PROFILE'] = 'smoke'
    sys.path.insert(0, REPO)

    from services.licensing import License, Tier
    import services.licensing as lic_mod

    if LICENSE_TIER == 'FREE':
        lic_mod.load_license = lambda _repo: License(
            tier=Tier.FREE, persons=1)

    try:
        import customtkinter as ctk
        ctk.set_appearance_mode('system')
        ctk.set_default_color_theme('blue')

        import gui as g
        (db, registry, assistant, config, settings,
         module_states, synced, profile, auto_backup) = g.bootstrap()
        try:
            app = g.AlltagshelferGUI(
                registry, assistant, config, settings,
                module_states, synced, profile, auto_backup=auto_backup)
            app.update_idletasks()
            app.update()
            title = app.title()
            app.destroy()
            print('BOOT_OK title=' + repr(title) + ' tier=' + LICENSE_TIER)
            sys.exit(0)
        finally:
            db.close()
    except SystemExit:
        raise
    except BaseException:
        traceback.print_exc()
        sys.exit(2)
""")


def _run_boot_subprocess(license_tier: str) -> subprocess.CompletedProcess:
    """Startet einen frischen Python-Prozess, der bootstrap() +
    AlltagshelferGUI(...) ausfuehrt und nach einem Render-Tick beendet."""
    inner = _BOOT_TEMPLATE % {"repo": REPO.as_posix(), "tier": license_tier}
    return subprocess.run(
        [sys.executable, "-c", inner],
        capture_output=True, text=True, timeout=60,
        cwd=str(REPO))


@pytest.fixture(autouse=True)
def _skip_without_display_or_ctk():
    if not _has_customtkinter():
        pytest.skip("customtkinter nicht verfuegbar")
    if not _has_display():
        pytest.skip("kein Tkinter-Display ($DISPLAY) verfuegbar")


def test_gui_boots_in_free_tier_without_crash():
    """Bug-Reproduktion: im FREE-Tier sind viele Tabs gesperrt, die
    Refresh-Methoden duerfen nicht auf nicht-existierende Widgets
    zugreifen."""
    result = _run_boot_subprocess("FREE")
    if result.returncode != 0:
        pytest.fail(
            f"GUI-Boot im FREE-Tier hat Exit-Code {result.returncode}:\n"
            f"---- stdout ----\n{result.stdout}\n"
            f"---- stderr ----\n{result.stderr}")
    assert "BOOT_OK" in result.stdout


def test_gui_boots_with_default_license_too():
    """Default-Lizenz (frisch installiert, kein Token) - GUI muss
    ebenfalls hochfahren."""
    result = _run_boot_subprocess("DEFAULT")
    if result.returncode != 0:
        pytest.fail(
            f"GUI-Boot mit Default-Lizenz hat Exit-Code "
            f"{result.returncode}:\n"
            f"---- stdout ----\n{result.stdout}\n"
            f"---- stderr ----\n{result.stderr}")
    assert "BOOT_OK" in result.stdout
