"""
Tests fuer tools/control_panel.py.

Wir testen das Tool *strukturell* (Aktions-Tabellen, Link-Liste,
Command-Runner-Logik), ohne das Fenster sichtbar zu machen.
Tkinter-DISPLAY-Anforderungen werden durch Headless-Init umgangen.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


REPO = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Aktions-Tabellen
# ---------------------------------------------------------------------------
def test_actions_tests_complete():
    from tools.control_panel import actions_tests
    items = actions_tests()
    labels = {a.label for a in items}
    # Mindestens 3 Aktionen: Status, Volle Suite, Dashboard
    assert len(items) >= 3
    assert any("Status" in l for l in labels)
    assert any("Test-Suite" in l for l in labels)
    assert any("Dashboard" in l for l in labels)


def test_actions_tests_call_python_modules():
    from tools.control_panel import actions_tests
    for a in actions_tests():
        assert a.command, f"Aktion {a.label} hat keinen Befehl"
        assert a.command[0] == sys.executable
        # Drittes Element ist das Modul nach -m
        if "-m" in a.command:
            mod_idx = a.command.index("-m") + 1
            assert a.command[mod_idx].startswith("tools."), (
                f"Aktion {a.label!r} ruft kein tools.* Modul auf")


def test_actions_build_lists_three_platforms_indirectly():
    from tools.control_panel import actions_build
    items = actions_build()
    labels = " | ".join(a.label for a in items)
    # Status + mindestens 2 Build-Aktionen
    assert "Status" in labels
    assert "PC" in labels
    assert "Android" in labels


def test_actions_build_uses_existing_scripts():
    from tools.control_panel import actions_build
    for a in actions_build():
        # Aktionen mit Skript-Aufruf -> Skript muss existieren
        for arg in a.command:
            if "scripts" in str(arg) and (arg.endswith(".bat")
                                            or arg.endswith(".sh")):
                assert Path(arg).is_file(), (
                    f"Aktion {a.label!r} verweist auf nicht-existierendes "
                    f"Skript {arg}")


def test_actions_playstore_complete():
    from tools.control_panel import actions_playstore
    items = actions_playstore()
    # Pflicht-Subcommands aus playstore_sync
    subcommands: set[str] = set()
    for a in items:
        if "tools.playstore_sync" in a.command:
            idx = a.command.index("tools.playstore_sync")
            if idx + 1 < len(a.command):
                subcommands.add(a.command[idx + 1])
    needed = {"init", "validate", "push", "pull", "diff", "export"}
    missing = needed - subcommands
    assert not missing, (
        f"Play-Store-Subcommands fehlen: {missing}. "
        f"Gefunden: {subcommands}")


def test_destructive_actions_have_confirm_prompt():
    """Init (--force) und Push muessen eine Bestaetigung verlangen."""
    from tools.control_panel import actions_playstore
    flagged = {a.label for a in actions_playstore() if a.confirm}
    assert any("Init" in l for l in flagged), (
        "Init ueberschreibt playstore.yml - braucht confirm")
    assert any("Push" in l and "dry" not in l.lower() for l in flagged), (
        "Echter Push braucht confirm")


def test_actions_release_checks_complete():
    from tools.control_panel import actions_release_checks
    items = actions_release_checks()
    labels = " | ".join(a.label for a in items)
    commands = [" ".join(a.command) for a in items]
    assert "Play-Store-Compliance" in labels
    assert "Data-Safety" in labels
    assert "Datenschutzerklärung" in labels
    assert "Android-Gerät" in labels
    for module in (
        "tools.playstore_check",
        "tools.data_safety",
        "tools.privacy_policy",
        "tools.legal_status",
        "tools.build_status",
        "tools.verify_android_device",
        "tools.release_open_items",
    ):
        assert any(module in cmd for cmd in commands), (
            f"Release-Check {module} fehlt")


def test_release_open_items_are_visible_to_control_panel():
    from tools.release_open_items import items
    release_items = items()
    assert release_items
    text = "\n".join(i.title + "\n" + i.why_manual for i in release_items)
    assert "Play Console" in text
    assert "Keystore" in text
    assert "Closed Testing" in text


# ---------------------------------------------------------------------------
# Doku-Links
# ---------------------------------------------------------------------------
def test_links_point_to_known_paths():
    from tools.control_panel import links
    items = links()
    assert items, "Keine Doku-Links definiert"
    # Mindestens index.html + Projekt-Ordner muessen drin sein
    targets = [str(l.target) for l in items]
    assert any("index.html" in t for t in targets)
    assert any("dashboard.html" in t for t in targets)


def test_release_item_references_are_repo_paths_or_https_urls():
    from tools.release_open_items import items
    for item in items():
        for ref in [*item.local_docs, *item.official_links]:
            if ref.is_url:
                assert ref.target.startswith("https://")
            else:
                rel = ref.target.split("#", 1)[0]
                assert (REPO / rel).exists(), (
                    f"{item.id}: Link {ref.target} existiert nicht")


def test_link_targets_are_known_repo_paths():
    from tools.control_panel import links
    for link in links():
        # Pfade gehoeren entweder zum Repo oder zum reports/-Ordner
        try:
            link.target.resolve().relative_to(REPO.resolve())
        except ValueError:
            pytest.fail(f"Link-Target {link.target} liegt ausserhalb des "
                         "Repos")


# ---------------------------------------------------------------------------
# Subprocess-Runner (ohne Tk)
# ---------------------------------------------------------------------------
def test_command_runner_streams_and_signals_done():
    from tools.control_panel import CommandRunner
    import threading
    import time

    lines: list[str] = []
    done_event = threading.Event()
    rcs: list[int] = []

    def on_line(s: str) -> None:
        lines.append(s)

    def on_done(rc: int) -> None:
        rcs.append(rc)
        done_event.set()

    runner = CommandRunner(on_line=on_line, on_done=on_done)
    ok = runner.start([sys.executable, "-c",
                        "print('hi'); print('bye')"])
    assert ok is True
    assert done_event.wait(timeout=10), "Befehl ist nicht zurueckgekehrt"
    assert rcs == [0]
    joined = "".join(lines)
    assert "hi" in joined and "bye" in joined


def test_command_runner_busy_flag():
    from tools.control_panel import CommandRunner
    import threading
    runner = CommandRunner(on_line=lambda _: None,
                            on_done=lambda _: None)
    assert runner.busy is False
    # Starte ein etwas laengeres Subprozess
    ok = runner.start([sys.executable, "-c",
                        "import time; time.sleep(0.3); print('done')"])
    assert ok is True
    assert runner.busy is True
    # Doppel-Start verweigern
    blocked = runner.start([sys.executable, "-c", "print('nope')"])
    assert blocked is False
    # warten
    import time
    for _ in range(100):
        if not runner.busy:
            break
        time.sleep(0.05)
    assert runner.busy is False


def test_command_runner_returns_nonzero_on_failure():
    from tools.control_panel import CommandRunner
    import threading
    done = threading.Event()
    rcs: list[int] = []
    runner = CommandRunner(on_line=lambda _: None,
                            on_done=lambda rc: (rcs.append(rc),
                                                  done.set()))
    runner.start([sys.executable, "-c", "import sys; sys.exit(7)"])
    assert done.wait(timeout=10)
    assert rcs == [7]


# ---------------------------------------------------------------------------
# Headless-Fenster-Init (nur wenn Display vorhanden)
# ---------------------------------------------------------------------------
def test_window_can_be_constructed_and_destroyed():
    """Auf Build-Agents ohne Display schlaegt CTk fehl - dann skip."""
    try:
        from tools.control_panel import ControlPanel
        app = ControlPanel()
    except Exception as exc:                              # noqa: BLE001
        msg = str(exc).lower()
        if "display" in msg or "no display name" in msg \
                or "tcl" in msg or "tkinter" in msg:
            pytest.skip(f"Kein Tkinter-Display verfuegbar: {exc}")
        raise
    try:
        app.update_idletasks()
        # Sektionen sind gebaut
        assert "Control Panel" in app.title()
        assert "release" in app._section_frames       # type: ignore[attr-defined]
        # Mindestens ein Button registriert
        assert len(app._busy_buttons) >= 18            # type: ignore[attr-defined]
    finally:
        app.destroy()


# ---------------------------------------------------------------------------
# start.bat: oeffnet direkt das Control Panel (alleinige GUI, kein Menue)
# ---------------------------------------------------------------------------
def test_start_bat_invokes_control_panel():
    text = (REPO / "start.bat").read_text(encoding="utf-8",
                                             errors="replace")
    assert "tools.control_panel" in text, (
        "start.bat sollte direkt das Control Panel oeffnen.")
    # Das Control Panel ist die alleinige grafische Oberflaeche - es darf
    # kein interaktives Konsolen-Menue mit Auswahl-Schleife geben.
    assert ":menu" not in text, (
        "start.bat enthaelt eine Konsolen-Menue-Schleife (:menu); das "
        "Control Panel soll der alleinige Einstieg sein.")
    assert "set /p choice" not in text, (
        "start.bat fragt im Konsolen-Menue nach einer Auswahl; das soll "
        "im Control Panel passieren, nicht in der Konsole.")


def test_start_bat_checks_customtkinter():
    text = (REPO / "start.bat").read_text(encoding="utf-8",
                                             errors="replace")
    assert "customtkinter" in text, (
        "start.bat sollte customtkinter pruefen / installieren")
