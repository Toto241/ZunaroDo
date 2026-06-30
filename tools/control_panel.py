"""
Zunarodo Control Panel - grafisches Steuerwerk fuer Tests, Builds,
Play-Store-Sync und Dokumentation.

Ergaenzt das Konsolen-Menue in start.bat: ein eigenes Fenster im
Windows-11-Look (Fluent / Mica) mit strukturierten Sektionen, Buttons
fuer jede Aktion und einem Live-Log unten, das die Ausgabe der
jeweiligen Befehle streamt.

Sektionen:

  1. Tests & Cockpit
       - Status anzeigen, gesamte Suite laufen lassen, Dashboard
         neu rendern, Cockpit im Browser oeffnen
  2. Build
       - Plattform-Status, PC-Build (PyInstaller),
         Android-Build (WSL2 + Buildozer), iOS-Build (Info)
  3. Play-Store-Sync
       - init / validate / push --dry-run / push / pull / diff / export
  4. Release-Check & offene Punkte
       - lokale Compliance-/Data-Safety-/Privacy-Checks
       - manuelle Restpunkte mit Doku- und offiziellen Links
  5. Dokumentation
       - Direkter Sprung zu TESTING.html / UI_CONCEPT.html /
         PLAYSTORE.html / index.html und in den Projekt-Ordner

Aufruf:

    python -m tools.control_panel

Das Fenster bleibt offen, bis du es schliesst. Lange Befehle
(z.B. die volle Test-Suite, PyInstaller, Buildozer) laufen in einem
Hintergrund-Thread, sodass das UI bedienbar bleibt.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from core.tooltip import attach_tooltip
from tools.release_open_items import (OpenItem, Reference, automated_checks,
                                      items as release_open_items)

# CustomTkinter ist eine Pflicht-Abhaengigkeit der Hauptanwendung.
# Wenn es trotzdem fehlt (z.B. in einer Slim-CI), liefern wir eine
# klare Fehlermeldung statt einen ImportError-Stacktrace.
try:
    import customtkinter as ctk
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception as exc:                                # noqa: BLE001
    print("FEHLER: customtkinter fehlt. Installiere es mit:")
    print("        pip install customtkinter")
    print(f"        ({exc})")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_JSON = REPO_ROOT / "tests" / "concept" / "reports" / "protocol.json"
INDEX_HTML = REPO_ROOT / "index.html"
DASHBOARD_HTML = REPO_ROOT / "tests" / "concept" / "reports" / "dashboard.html"
DOCS_DIR = REPO_ROOT / "tests" / "concept" / "reports"


# ---------------------------------------------------------------------------
# Windows-11-Look (Fluent / Mica)
#
# Farben sind als (Light, Dark)-Tupel modelliert, damit das Panel sowohl im
# hellen als auch im dunklen System-Modus wie Windows 11 wirkt. Werte sind an
# die Fluent-Palette angelehnt (Mica-Hintergrund, #005FB8 Akzent, weiche
# Kanten). Schriftfamilie wird zur Laufzeit auf "Segoe UI Variable" / "Segoe
# UI" gesetzt, mit Fallback auf eine vorhandene System-Schrift.
# ---------------------------------------------------------------------------
WIN11 = {
    "window_bg":    ("#F3F3F3", "#202020"),   # Mica
    "card_bg":      ("#FBFBFB", "#2D2D2D"),   # Layer / Card
    "card_border":  ("#E5E5E5", "#3A3A3A"),
    "accent":       ("#005FB8", "#0078D4"),   # Akzent-Button
    "accent_hover": ("#1A6FC0", "#1A86D9"),
    "subtle_hover": ("#ECECEC", "#383838"),   # Hover fuer transparente Knoepfe
    "nav_active":   ("#E8E8E8", "#383838"),    # aktiver Sidebar-Eintrag
    "text":         ("#1A1A1A", "#FFFFFF"),
    "text_muted":   ("#5A5A5A", "#9A9A9A"),
    "log_bg":       ("#FFFFFF", "#1B1B1B"),
    "ok":           ("#1b873b", "#3fb950"),
    "warn":         ("#b54708", "#e08a3c"),
    "err":          ("#b42318", "#f85149"),
}
# Kandidaten in Reihenfolge der Bevorzugung (Windows 11 -> generisch).
_FONT_CANDIDATES = ("Segoe UI Variable Text", "Segoe UI", "Segoe UI Emoji")


# ---------------------------------------------------------------------------
# Aktions-Modell
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Action:
    label: str                          # Knopf-Beschriftung
    command: list[str]                  # subprocess-Argumente
    description: str = ""               # sichtbares Label + Hover-Tooltip
    confirm: Optional[str] = None       # wenn gesetzt -> Bestaetigungsdialog
    needs_wsl: bool = False             # nur sinnvoll, wenn 'wsl' verfuegbar


@dataclass(frozen=True)
class LinkAction:
    label: str
    target: Path
    description: str = ""


def _console_python() -> str:
    """Liefert einen Konsolen-Python fuer Subprozesse.

    Das Panel selbst kann via ``pythonw.exe`` gestartet werden. Fuer Tools,
    die stdout/stderr streamen (pytest, Play-Store-Checks, Build-Status),
    ist ``python.exe`` unter Windows robuster und macht Fehlermeldungen im
    Live-Log sichtbar.
    """
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        console = exe.with_name("python.exe")
        if console.is_file():
            return str(console)
    return sys.executable


# Die Aktions-Tabellen sind als Funktionen modelliert (kein
# Top-Level-Konstrukt), damit Pfade dynamisch sind und Tests sie
# inspizieren koennen.
def actions_tests() -> list[Action]:
    py = _console_python()
    return [
        Action("Status", [py, "-m", "tools.build_status", "--no-emoji"],
                "Build-Voraussetzungen und letzte Artefakte anzeigen."),
        Action("Volle Test-Suite + Dashboard",
                [py, "-m", "tools.test_protocol", "--all"],
                "Komplette Pyteste-Suite (~3 min), aktualisiert das "
                "Protokoll."),
        Action("Dashboard / index.html neu rendern",
                [py, "-m", "tools.dashboard"],
                "Schnell (~3 s) - keine Tests, nur neue HTML."),
    ]


# Info-Text fuer den iOS-Knopf auf Nicht-macOS-Systemen (als python -c).
_IOS_INFO_SNIPPET = (
    "print('iOS-Build ist nur auf macOS moeglich (Xcode + kivy-ios).');"
    "print('Wege:  Mac -> scripts/build-ios.sh   |   "
    "Cloud -> GitHub Actions / CI.');"
    "print('Details: MOBILE.md')"
)


def actions_build() -> list[Action]:
    py = _console_python()
    is_windows = os.name == "nt"
    builds = [
        Action("Build-Status anzeigen",
                [py, "-m", "tools.build_status", "--no-emoji"],
                "Listet pro Plattform Tool, Befehl, letztes Artefakt."),
    ]
    if is_windows:
        builds.extend([
            Action("PC bauen (PyInstaller)",
                    ["cmd", "/c", str(REPO_ROOT / "scripts" /
                                       "build-desktop.bat")],
                    "Erzeugt dist/ZunaroDo/ZunaroDo.exe."),
            Action("Android bauen (WSL2 + Buildozer)",
                    ["cmd", "/c", str(REPO_ROOT / "scripts" /
                                       "build-android.bat")],
                    "Ruft WSL2 auf, Buildozer baut .apk in bin/.",
                    needs_wsl=True),
        ])
    else:
        builds.extend([
            Action("PC bauen (PyInstaller)",
                    ["bash", str(REPO_ROOT / "scripts" /
                                  "build-desktop.sh")],
                    "Erzeugt dist/ZunaroDo/."),
            Action("Android bauen (Buildozer)",
                    ["bash", str(REPO_ROOT / "scripts" /
                                  "build-android.sh")],
                    "Erfordert Linux/macOS + JDK 17."),
        ])

    # iOS: nur auf macOS lokal baubar. Auf anderen Plattformen ein
    # Info-Befehl, damit alle drei Apps in der Build-Sektion sichtbar sind.
    if sys.platform == "darwin":
        builds.append(
            Action("iOS bauen (kivy-ios)",
                    ["bash", str(REPO_ROOT / "scripts" / "build-ios.sh")],
                    "Erfordert macOS + Xcode + kivy-ios."))
    else:
        builds.append(
            Action("iOS (nur macOS)",
                    [py, "-c", _IOS_INFO_SNIPPET],
                    "Hinweis: iOS-Build nur auf macOS (Xcode + kivy-ios)."))
    return builds


def actions_playstore() -> list[Action]:
    py = _console_python()
    return [
        Action("Init  (YAML aus Repo erzeugen, --force)",
                [py, "-m", "tools.playstore_sync", "init", "--force"],
                "Erzeugt/Ueberschreibt playstore.yml aus buildozer.spec.",
                confirm="playstore.yml wird ueberschrieben - fortfahren?"),
        Action("Validate",
                [py, "-m", "tools.playstore_sync", "validate"],
                "Prueft playstore.yml gegen Schema + Play-Limits."),
        Action("Push  --dry-run",
                [py, "-m", "tools.playstore_sync", "push", "--dry-run"],
                "Zeigt, was gepusht wuerde, schreibt nichts."),
        Action("Push  (Mock / Real je nach Credentials)",
                [py, "-m", "tools.playstore_sync", "push"],
                "Schiebt YAML in Play Console (oder Mock-Datei).",
                confirm="Push schreibt in die Play Console "
                          "(falls Credentials gesetzt sind). Fortfahren?"),
        Action("Pull --merge",
                [py, "-m", "tools.playstore_sync", "pull", "--merge"],
                "Liest Console-Stand in playstore.yml (merged)."),
        Action("Diff",
                [py, "-m", "tools.playstore_sync", "diff"],
                "Zeigt YAML vs. Play Console."),
        Action("Export Snapshot",
                [py, "-m", "tools.playstore_sync", "export"],
                "Schreibt Markdown-Snapshot nach release/."),
    ]


def actions_config() -> list[Action]:
    """Einfache Konfiguration (App/Laufzeit-Ebene): gefuehrte .env-Erzeugung
    und Status, plus die nicht-interaktiven PowerShell-Setups.

    Bewusst NICHT verdrahtet: release/create_upload_keystore.ps1 - keytool
    fragt interaktiv per stdin nach Passwoertern und wuerde den Capture-Runner
    blockieren. Dieser Schritt bleibt manuell (siehe Release-Sektion).
    """
    py = _console_python()
    actions = [
        Action(".env initialisieren  (aus .env.example)",
                [py, "-m", "tools.env_setup", "--init"],
                "Kopiert .env.example -> .env (ueberschreibt nie eine "
                "bestehende). Danach die [SECRET]-Werte eintragen; ZunaroDo "
                "laeuft auch ganz ohne .env offline."),
        Action(".env-Status pruefen",
                [py, "-m", "tools.env_setup", "--check"],
                "Zeigt, welche Umgebungsvariablen/Secrets gesetzt sind - "
                "Werte werden maskiert (nur gesetzt/leer + Quelle)."),
    ]
    if os.name == "nt":
        scripts = REPO_ROOT / "scripts"
        ps = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
              "-File"]
        actions.extend([
            Action("Play-Console-Paket erzeugen  (PowerShell)",
                    [*ps, str(scripts / "setup-play-console.ps1")],
                    "Erzeugt Data-Safety-Antworten + Checkliste lokal in "
                    "release/. Nicht-interaktiv, schreibt nichts extern."),
            Action("GitHub Pages einrichten & Privacy deployen  (PowerShell)",
                    [*ps, str(scripts / "setup-github-pages.ps1")],
                    "Aktiviert GitHub Pages und deployt die Datenschutz-Seite "
                    "via 'gh'. Voraussetzung: 'gh' installiert und eingeloggt.",
                    confirm="Aktiviert GitHub Pages und deployt die "
                            "Privacy-Policy in das echte Repo (via gh). "
                            "Fortfahren?"),
        ])
    return actions


def actions_release_checks() -> list[Action]:
    py = _console_python()
    actions: list[Action] = []
    for check in automated_checks():
        desc = check.description
        if check.requires:
            desc = f"{desc} Voraussetzung: {', '.join(check.requires)}."
        actions.append(Action(check.label, check.command(py), desc))
    return actions


def links() -> list[LinkAction]:
    return [
        LinkAction("Cockpit oeffnen  (index.html)",
                    INDEX_HTML,
                    "Einstiegspunkt mit Build-Center + Status."),
        LinkAction("Test-Dashboard  (HTML)",
                    DASHBOARD_HTML,
                    "Volle Testlauf-Resultate."),
        LinkAction("TESTING (Konzept, HTML)",
                    DOCS_DIR / "TESTING.html",
                    "Test- und Compliance-Konzept (Teil I + II)."),
        LinkAction("UI_CONCEPT (HTML)",
                    DOCS_DIR / "UI_CONCEPT.html",
                    "Admin-Panel-Architektur."),
        LinkAction("PLAYSTORE (HTML)",
                    DOCS_DIR / "PLAYSTORE.html",
                    "Schritt-fuer-Schritt Play-Console-Anleitung."),
        LinkAction("Audit-Protokoll  (HTML)",
                    DOCS_DIR / "protocol.html",
                    "Letzter Pytest-Audit-Bericht."),
        LinkAction("Konfiguration & Onboarding  (README.md)",
                    REPO_ROOT / "README.md",
                    "Setup, Erststart und alle Konfig-Optionen erklaert."),
        LinkAction("Umgebungsvariablen  (.env.example)",
                    REPO_ROOT / ".env.example",
                    "Alle Env-Vars (Gemini/DB-Key/IMAP/SMTP/Sync) mit Kommentaren."),
        LinkAction("Sicherheit & Secrets  (SECURITY.md)",
                    REPO_ROOT / "SECURITY.md",
                    "Secret-Handling, Verschluesselung und .env-Hinweise."),
        LinkAction("Projekt-Ordner",
                    REPO_ROOT,
                    "Im Datei-Manager oeffnen."),
        LinkAction("Reports-Ordner",
                    DOCS_DIR,
                    "Alle generierten Dashboards + Reports."),
    ]


# ---------------------------------------------------------------------------
# Subprocess-Runner mit Live-Stream in eine Queue
# ---------------------------------------------------------------------------
class CommandRunner:
    """Fuehrt ein Subprozess aus und schiebt jede Zeile in eine Queue.

    Das eigentliche UI poll't die Queue ueber `after()` und schreibt
    sie in das Log-Widget. So bleibt das UI reaktiv, auch wenn der
    Befehl 3 Minuten laeuft.
    """

    def __init__(self, on_line: Callable[[str], None],
                 on_done: Callable[[int], None]):
        self.on_line = on_line
        self.on_done = on_done
        self.proc: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def busy(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self, command: list[str], cwd: Path = REPO_ROOT,
               env_extra: Optional[dict] = None) -> bool:
        if self.busy:
            return False
        env = dict(os.environ)
        # UTF-8 fuer Subprozesse, damit Umlaute im Live-Log sauber sind.
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        if env_extra:
            env.update(env_extra)
        try:
            self.proc = subprocess.Popen(
                command, cwd=str(cwd), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                bufsize=1, text=True, encoding="utf-8", errors="replace",
            )
        except Exception as exc:                          # noqa: BLE001
            self.on_line(f"[FEHLER] Befehl kann nicht gestartet werden: "
                          f"{exc}\n")
            self.on_done(127)
            return False
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        if self.busy and self.proc is not None:
            try:
                self.proc.terminate()
            except Exception:                             # noqa: BLE001
                pass

    def _pump(self) -> None:
        assert self.proc is not None
        assert self.proc.stdout is not None
        try:
            for line in self.proc.stdout:
                self.on_line(line)
        except Exception as exc:                          # noqa: BLE001
            self.on_line(f"[FEHLER beim Lesen] {exc}\n")
        rc = self.proc.wait()
        self.on_done(rc)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
class ControlPanel(ctk.CTk):
    """Hauptfenster - Sidebar-Navigation + Inhaltsbereich + Live-Log.

    Die vier Sektionen (Tests, Build, Play-Store, Dokumentation) werden
    EINMAL aufgebaut und ueber die Sidebar nur ein-/ausgeblendet - so sind
    alle Aktionsknoepfe von Anfang an vorhanden (busy-Sperre + Tests).
    """

    LOG_LIMIT = 4000      # max. Zeilen im Log (FIFO)

    # (key, Sidebar-Titel, Aktions-Factory)
    _SECTIONS = [
        ("tests", "Tests & Cockpit", actions_tests),
        ("config", "Konfiguration", actions_config),
        ("build", "Build · Android / iOS / PC", actions_build),
        ("playstore", "Play-Store-Sync", actions_playstore),
        ("release", "Release-Check & offene Punkte", actions_release_checks),
    ]

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        self._font_family = self._pick_font_family()
        self.title("ZunaroDo  -  Control Panel")
        self.geometry("1180x820")
        self.minsize(960, 660)
        # Mica-aehnlicher Fensterhintergrund (statt CTk-Standardgrau).
        self.configure(fg_color=WIN11["window_bg"])

        self._log_queue: "queue.Queue[str]" = queue.Queue()
        self._exit_queue: "queue.Queue[int]" = queue.Queue()
        self._runner = CommandRunner(
            on_line=self._log_queue.put,
            on_done=self._exit_queue.put)
        self._busy_buttons: list[ctk.CTkButton] = []     # Aktions-Knoepfe
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._section_frames: dict[str, ctk.CTkFrame] = {}
        self._current_section = ""
        self._current_action_label = ""
        self._after_ids: set[str] = set()

        self._build_ui()
        self._select_section("tests")
        self._refresh_status()
        # ueber after() kontinuierlich die Queues pumpen
        self._safe_after(100, self._drain_queues)

    # ---- after()-Verwaltung (sauberes Canceln beim Schliessen) ---------
    def _safe_after(self, ms: int, fn: Callable[[], None]) -> str:
        ident = self.after(ms, fn)
        self._after_ids.add(ident)
        return ident

    def _on_close(self) -> None:
        for ident in list(self._after_ids):
            try:
                self.after_cancel(ident)
            except Exception:                             # noqa: BLE001
                pass
        self._after_ids.clear()
        self._runner.stop()
        self.destroy()

    # ---- Look & Feel ---------------------------------------------------
    def _pick_font_family(self) -> str:
        """Waehlt die beste verfuegbare Windows-11-Schrift.

        Faellt auf eine vorhandene System-Schrift zurueck, falls keine der
        Segoe-Varianten installiert ist (z.B. auf Linux/macOS).
        """
        try:
            import tkinter.font as tkfont
            available = set(tkfont.families())
        except Exception:                                 # noqa: BLE001
            return "Segoe UI"
        for fam in _FONT_CANDIDATES:
            if fam in available:
                return fam
        return "Segoe UI"

    def _font(self, size: int = 13, weight: str = "normal") -> "ctk.CTkFont":
        return ctk.CTkFont(family=self._font_family, size=size, weight=weight)

    # ---- Aufbau --------------------------------------------------------
    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        # Fenster-Lebenszyklus + Tastatur-Shortcuts
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda _e: self._stop_current())
        self.bind("<Control-l>", lambda _e: self._clear_log())

    def _build_sidebar(self) -> None:
        side = ctk.CTkFrame(self, width=232, corner_radius=0,
                            fg_color=WIN11["card_bg"])
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)
        side.grid_rowconfigure(20, weight=1)            # Spacer nach unten

        ctk.CTkLabel(side, text="ZunaroDo", text_color=WIN11["text"],
                      font=self._font(20, "bold")
                      ).grid(row=0, column=0, sticky="w", padx=18,
                             pady=(18, 0))
        ctk.CTkLabel(side, text="Control Panel", text_color=WIN11["text_muted"],
                      font=self._font(12)
                      ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))

        nav = [(k, t) for k, t, _ in self._SECTIONS]
        nav.append(("docs", "Dokumentation"))
        for i, (key, title) in enumerate(nav):
            btn = ctk.CTkButton(
                side, text=title, anchor="w", height=38, corner_radius=6,
                font=self._font(13), fg_color="transparent",
                text_color=WIN11["text"], hover_color=WIN11["subtle_hover"],
                command=lambda k=key: self._select_section(k))
            btn.grid(row=2 + i, column=0, sticky="ew", padx=10, pady=2)
            self._nav_buttons[key] = btn

        ctk.CTkLabel(side, text="Darstellung", text_color=WIN11["text_muted"],
                      font=self._font(11)
                      ).grid(row=21, column=0, sticky="w", padx=18, pady=(8, 0))
        self.mode_switch = ctk.CTkSegmentedButton(
            side, values=["System", "Hell", "Dunkel"],
            command=self._on_mode_change, font=self._font(12))
        self.mode_switch.set("System")
        self.mode_switch.grid(row=22, column=0, sticky="ew", padx=10,
                              pady=(2, 16))

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=3)             # Inhalt groesser
        main.grid_rowconfigure(2, weight=2)             # Log darunter

        # Topbar: Sektionstitel + Status
        top = ctk.CTkFrame(main, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))
        top.grid_columnconfigure(0, weight=1)
        self.section_title = ctk.CTkLabel(
            top, text="", text_color=WIN11["text"],
            font=self._font(20, "bold"))
        self.section_title.grid(row=0, column=0, sticky="w")
        self.status_label = ctk.CTkLabel(
            top, text="Status: -", text_color=WIN11["text_muted"],
            font=self._font(13))
        self.status_label.grid(row=0, column=1, sticky="e")

        # Inhalt: alle Sektionen vorab bauen, nur aktive sichtbar
        self.content_host = ctk.CTkFrame(main, fg_color="transparent")
        self.content_host.grid(row=1, column=0, sticky="nsew", padx=20, pady=6)
        self.content_host.grid_columnconfigure(0, weight=1)
        self.content_host.grid_rowconfigure(0, weight=1)
        for key, _title, factory in self._SECTIONS:
            if key == "release":
                self._section_frames[key] = self._build_release_section()
            else:
                self._section_frames[key] = self._build_action_section(factory())
        self._section_frames["docs"] = self._build_links_section(links())

        self._build_log(main, row=2)

    def _build_action_section(self, actions: list[Action]) -> "ctk.CTkFrame":
        frame = ctk.CTkScrollableFrame(self.content_host, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_remove()
        frame.grid_columnconfigure(0, weight=1)
        for i, action in enumerate(actions):
            self._action_card(frame, action).grid(
                row=i, column=0, sticky="ew", pady=5)
        return frame

    def _build_links_section(self, items: list[LinkAction]) -> "ctk.CTkFrame":
        frame = ctk.CTkScrollableFrame(self.content_host, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_remove()
        frame.grid_columnconfigure(0, weight=1)
        for i, link in enumerate(items):
            self._link_card(frame, link).grid(
                row=i, column=0, sticky="ew", pady=5)
        return frame

    def _build_release_section(self) -> "ctk.CTkFrame":
        frame = ctk.CTkScrollableFrame(self.content_host, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_remove()
        frame.grid_columnconfigure(0, weight=1)

        intro = self._card_shell(frame)
        intro.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(
            intro, text="Automatisierbare Checks",
            text_color=WIN11["text"], font=self._font(15, "bold"),
            anchor="w").grid(row=0, column=0, sticky="w", padx=14,
                              pady=(12, 2))
        ctk.CTkLabel(
            intro,
            text=("Diese Prüfungen laufen lokal im Live-Log. Sie ersetzen "
                  "nicht die darunter gelisteten externen Schritte in "
                  "Play Console, auf echtem Gerät oder auf macOS/Xcode."),
            text_color=WIN11["text_muted"], font=self._font(12),
            anchor="w", justify="left", wraplength=780
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

        row = 1
        self._manual_summary_card(frame).grid(row=row, column=0,
                                              sticky="ew", pady=(0, 8))
        row += 1
        for action in actions_release_checks():
            self._action_card(frame, action).grid(row=row, column=0,
                                                   sticky="ew", pady=5)
            row += 1

        manual_head = self._card_shell(frame)
        manual_head.grid(row=row, column=0, sticky="ew", pady=(12, 8))
        row += 1
        ctk.CTkLabel(
            manual_head, text="Offene Punkte, die externe Schritte brauchen",
            text_color=WIN11["text"], font=self._font(15, "bold"),
            anchor="w").grid(row=0, column=0, sticky="w", padx=14,
                              pady=(12, 2))
        ctk.CTkLabel(
            manual_head,
            text=("Jede Karte erklärt, warum der Punkt nicht vollständig "
                  "automatisiert werden kann, was als Nächstes zu tun ist "
                  "und welche lokalen/offiziellen Links helfen."),
            text_color=WIN11["text_muted"], font=self._font(12),
            anchor="w", justify="left", wraplength=780
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

        for item in release_open_items():
            self._manual_item_card(frame, item).grid(row=row, column=0,
                                                     sticky="ew", pady=5)
            row += 1
        return frame

    def _manual_summary_card(self, parent) -> "ctk.CTkFrame":
        items = release_open_items()
        blockers = [i for i in items if i.category == "blocker"]
        card = self._card_shell(parent)
        card.grid_columnconfigure(0, weight=1)
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        info.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            info, text=(f"{len(blockers)} Blocker · {len(items)} offene "
                        "manuelle Release-Punkte"),
            text_color=WIN11["text"], font=self._font(14, "bold"),
            anchor="w").grid(row=0, column=0, sticky="w")
        summary = "\n".join(f"• {item.title}" for item in blockers[:4])
        if len(blockers) > 4:
            summary += f"\n• … {len(blockers) - 4} weitere Blocker"
        ctk.CTkLabel(
            info, text=summary, text_color=WIN11["text_muted"],
            font=self._font(12), anchor="w", justify="left",
            wraplength=760).grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ctk.CTkButton(
            card, text="Doku oeffnen", width=140, corner_radius=6,
            font=self._font(13), fg_color="transparent", border_width=1,
            border_color=WIN11["card_border"], text_color=WIN11["text"],
            hover_color=WIN11["subtle_hover"],
            command=lambda: self._open_path_or_url(
                REPO_ROOT / "release" / "OFFENE_MANUELLE_SCHRITTE.md",
                "Offene manuelle Release-Schritte")
        ).grid(row=0, column=1, padx=(8, 14), pady=12)
        return card

    def _card_shell(self, parent) -> "ctk.CTkFrame":
        card = ctk.CTkFrame(
            parent, corner_radius=8, fg_color=WIN11["card_bg"],
            border_width=1, border_color=WIN11["card_border"])
        card.grid_columnconfigure(0, weight=1)
        return card

    def _action_card(self, parent, action: Action) -> "ctk.CTkFrame":
        card = self._card_shell(parent)
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        info.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(info, text=action.label, text_color=WIN11["text"],
                      font=self._font(14, "bold"), anchor="w", justify="left"
                      ).grid(row=0, column=0, sticky="w")
        if action.description:
            ctk.CTkLabel(info, text=action.description,
                          text_color=WIN11["text_muted"], font=self._font(12),
                          anchor="w", justify="left", wraplength=620
                          ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        label = "Bestaetigen ..." if action.confirm else "Ausfuehren"
        btn = ctk.CTkButton(
            card, text=label, width=140, corner_radius=6,
            font=self._font(13), fg_color=WIN11["accent"],
            hover_color=WIN11["accent_hover"], text_color="#FFFFFF",
            command=lambda a=action: self._run_action(a))
        btn.grid(row=0, column=1, padx=(8, 14), pady=12)
        attach_tooltip(btn, action.description)
        self._busy_buttons.append(btn)
        return card

    def _link_card(self, parent, link: LinkAction) -> "ctk.CTkFrame":
        card = self._card_shell(parent)
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        info.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(info, text=link.label, text_color=WIN11["text"],
                      font=self._font(14, "bold"), anchor="w", justify="left"
                      ).grid(row=0, column=0, sticky="w")
        if link.description:
            ctk.CTkLabel(info, text=link.description,
                          text_color=WIN11["text_muted"], font=self._font(12),
                          anchor="w", justify="left", wraplength=620
                          ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        open_btn = ctk.CTkButton(
            card, text="Oeffnen", width=140, corner_radius=6,
            font=self._font(13), fg_color="transparent", border_width=1,
            border_color=WIN11["card_border"], text_color=WIN11["text"],
            hover_color=WIN11["subtle_hover"],
            command=lambda l=link: self._open_link(l))
        open_btn.grid(row=0, column=1, padx=(8, 14), pady=12)
        tip = link.description
        if str(link.target) not in tip:
            tip = f"{tip}\n{link.target}" if tip else str(link.target)
        attach_tooltip(open_btn, tip)
        return card

    def _manual_item_card(self, parent, item: OpenItem) -> "ctk.CTkFrame":
        card = self._card_shell(parent)
        card.grid_columnconfigure(0, weight=1)
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        info.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew")
        title_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            title_row, text=item.title, text_color=WIN11["text"],
            font=self._font(14, "bold"), anchor="w", justify="left",
            wraplength=760).grid(row=0, column=0, sticky="w")
        badge = f"{item.category} · {item.status}"
        ctk.CTkLabel(
            title_row, text=badge, text_color=WIN11["warn"],
            font=self._font(11, "bold")).grid(row=0, column=1, sticky="e",
                                               padx=(8, 0))

        ctk.CTkLabel(
            info, text=f"Warum manuell: {item.why_manual}",
            text_color=WIN11["text_muted"], font=self._font(12),
            anchor="w", justify="left", wraplength=840
        ).grid(row=1, column=0, sticky="ew", pady=(6, 0))

        steps = "\n".join(f"• {step}" for step in item.what_to_do)
        ctk.CTkLabel(
            info, text=steps, text_color=WIN11["text"],
            font=self._font(12), anchor="w", justify="left",
            wraplength=840
        ).grid(row=2, column=0, sticky="ew", pady=(8, 0))

        if item.related_commands:
            commands = "\n".join(f"$ {cmd}" for cmd in item.related_commands)
            ctk.CTkLabel(
                info, text=commands, text_color=WIN11["text_muted"],
                font=ctk.CTkFont(family="Cascadia Mono", size=11),
                anchor="w", justify="left", wraplength=840
            ).grid(row=3, column=0, sticky="ew", pady=(8, 0))

        refs = ctk.CTkFrame(info, fg_color="transparent")
        refs.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        col = 0
        for ref in [*item.local_docs, *item.official_links]:
            truncated = len(ref.label) > 26
            btn_text = ref.label[:26] + ("…" if truncated else "")
            ref_btn = ctk.CTkButton(
                refs, text=btn_text, height=28, corner_radius=6,
                font=self._font(11), fg_color="transparent", border_width=1,
                border_color=WIN11["card_border"], text_color=WIN11["text"],
                hover_color=WIN11["subtle_hover"],
                command=lambda r=ref: self._open_reference(r))
            ref_btn.grid(row=0, column=col, padx=(0, 6), pady=2)
            # Vollen Label + Ziel zeigen - der Knopf-Text ist auf 26 Zeichen
            # gekuerzt, der Tooltip macht das Ziel wieder lesbar.
            attach_tooltip(ref_btn, f"{ref.label}\n{ref.target}")
            col += 1
        return card

    def _build_log(self, master, row: int) -> None:
        log_frame = ctk.CTkFrame(
            master, corner_radius=8, fg_color=WIN11["card_bg"],
            border_width=1, border_color=WIN11["card_border"])
        log_frame.grid(row=row, column=0, sticky="nsew", padx=20, pady=(6, 10))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(log_frame, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        head.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(head, text="Live-Log", text_color=WIN11["text"],
                      font=self._font(14, "bold")
                      ).grid(row=0, column=0, sticky="w")
        self.action_label = ctk.CTkLabel(
            head, text="bereit", text_color=WIN11["text_muted"],
            font=self._font(12))
        self.action_label.grid(row=0, column=1, sticky="w", padx=(10, 8))
        self.exit_badge = ctk.CTkLabel(head, text="", font=self._font(12,
                                       "bold"))
        self.exit_badge.grid(row=0, column=2, padx=(0, 8))
        for col, (txt, cmd) in enumerate((
                ("Kopieren", self._copy_log),
                ("Log loeschen", self._clear_log))):
            ctk.CTkButton(
                head, text=txt, width=110, corner_radius=6,
                font=self._font(13), fg_color="transparent", border_width=1,
                border_color=WIN11["card_border"], text_color=WIN11["text"],
                hover_color=WIN11["subtle_hover"], command=cmd
            ).grid(row=0, column=3 + col, padx=3)
        self.stop_button = ctk.CTkButton(
            head, text="Stoppen", width=110, state="disabled",
            corner_radius=6, font=self._font(13), fg_color="transparent",
            border_width=1, border_color=WIN11["card_border"],
            text_color=WIN11["text"], hover_color=WIN11["subtle_hover"],
            command=self._stop_current)
        self.stop_button.grid(row=0, column=5, padx=3)

        self.log_text = ctk.CTkTextbox(
            log_frame, wrap="word", activate_scrollbars=True,
            corner_radius=6, fg_color=WIN11["log_bg"],
            text_color=WIN11["text"], border_width=0,
            font=ctk.CTkFont(family="Cascadia Mono", size=12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12,
                            pady=(0, 12))
        self.log_text.configure(state="disabled")

    # ---- Navigation ----------------------------------------------------
    def _select_section(self, key: str) -> None:
        if key not in self._section_frames:
            return
        for k, frame in self._section_frames.items():
            if k == key:
                frame.grid()
            else:
                frame.grid_remove()
        for k, btn in self._nav_buttons.items():
            active = (k == key)
            btn.configure(
                fg_color=WIN11["nav_active"] if active else "transparent",
                text_color=WIN11["accent"] if active else WIN11["text"])
        titles = {
            "tests": "Tests & Cockpit",
            "config": "Konfiguration · .env & Setup",
            "build": "Build · Android / iOS / PC",
            "playstore": "Play-Store-Sync",
            "release": "Release-Check & offene Punkte",
            "docs": "Dokumentation & Schnellzugriff",
        }
        self.section_title.configure(text=titles.get(key, key))
        self._current_section = key

    def _on_mode_change(self, value: str) -> None:
        ctk.set_appearance_mode(
            {"System": "system", "Hell": "light", "Dunkel": "dark"}
            .get(value, "system"))

    # ---- Aktionen ------------------------------------------------------
    def _run_action(self, action: Action) -> None:
        if self._runner.busy:
            messagebox.showwarning(
                "Bereits laufend",
                "Es laeuft schon ein Befehl. Bitte abwarten "
                "oder 'Stoppen' druecken.")
            return
        if action.confirm:
            if not messagebox.askyesno("Bestaetigung", action.confirm):
                return
        if action.needs_wsl and os.name == "nt":
            # WSL pruefen, sonst Hinweis statt zu starten
            import shutil
            if shutil.which("wsl") is None:
                messagebox.showerror(
                    "WSL2 fehlt",
                    "'wsl' wurde nicht gefunden. Installiere WSL2 + "
                    "Ubuntu 22.04 zuerst (siehe MOBILE.md).")
                return
        self.exit_badge.configure(text="")
        self._append_log(f"\n$ {' '.join(self._quote_args(action.command))}\n")
        self._set_busy(True, action.label)
        ok = self._runner.start(action.command)
        if not ok:
            self._set_busy(False, "")

    def _quote_args(self, cmd: list[str]) -> list[str]:
        # Nur fuer die Anzeige - keine Shell-Escapes ausfuehren
        return [a if " " not in a else f'"{a}"' for a in cmd]

    def _stop_current(self) -> None:
        self._runner.stop()
        self._append_log("[Abbruch angefordert]\n")

    def _set_busy(self, busy: bool, label: str) -> None:
        state = "disabled" if busy else "normal"
        for b in self._busy_buttons:
            try:
                b.configure(state=state)
            except Exception:                             # noqa: BLE001
                pass
        self.stop_button.configure(state="normal" if busy else "disabled")
        self.action_label.configure(
            text=f"laeuft: {label}" if busy else "bereit",
            text_color=WIN11["warn"] if busy else WIN11["text_muted"])
        self._current_action_label = label

    def _copy_log(self) -> None:
        try:
            text = self.log_text.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:                                 # noqa: BLE001
            pass

    # ---- Log -----------------------------------------------------------
    def _append_log(self, text: str) -> None:
        if not text:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        # FIFO-Trim
        n_lines = int(self.log_text.index("end-1c").split(".")[0])
        if n_lines > self.LOG_LIMIT:
            self.log_text.delete("1.0",
                                  f"{n_lines - self.LOG_LIMIT}.0")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _drain_queues(self) -> None:
        # alle wartenden Zeilen vom Runner an das Textfeld weiterreichen
        try:
            while True:
                self._append_log(self._log_queue.get_nowait())
        except queue.Empty:
            pass
        try:
            while True:
                rc = self._exit_queue.get_nowait()
                self._on_command_done(rc)
        except queue.Empty:
            pass
        self._safe_after(100, self._drain_queues)

    def _on_command_done(self, rc: int) -> None:
        self._append_log(f"[fertig - Exit-Code {rc}]\n")
        self.exit_badge.configure(
            text="OK" if rc == 0 else f"Exit {rc}",
            text_color=WIN11["ok"] if rc == 0 else WIN11["err"])
        self._set_busy(False, "")
        # Wenn die Tests gelaufen sind, Status oben neu lesen
        self._refresh_status()

    # ---- Status oben rechts -------------------------------------------
    def _refresh_status(self) -> None:
        text = "Status: -"
        color = WIN11["text_muted"]
        if PROTOCOL_JSON.is_file():
            try:
                data = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))
                decision = (data.get("decision") or "?").upper()
                totals = data.get("totals", {}) or {}
                passed = totals.get("passed", 0)
                count = totals.get("count", 0)
                text = (f"Status: {decision}  -  "
                        f"{passed}/{count} Tests")
                color = {
                    "GO":    ("#1b873b", "#3fb950"),
                    "HOLD":  ("#b54708", "#e08a3c"),
                    "NO-GO": ("#b42318", "#f85149"),
                }.get(decision, WIN11["text_muted"])
            except Exception:                             # noqa: BLE001
                text = "Status: (protocol.json defekt)"
        self.status_label.configure(text=text, text_color=color)

    # ---- Schnellaktionen ----------------------------------------------
    def _open_link(self, link: LinkAction) -> None:
        self._open_path_or_url(link.target, link.target.name)

    def _open_reference(self, ref: Reference) -> None:
        if ref.is_url:
            self._open_path_or_url(ref.target, ref.label)
            return
        local = ref.target.split("#", 1)[0]
        self._open_path_or_url(REPO_ROOT / local, ref.label)

    def _open_path_or_url(self, target, label: str = "") -> None:
        if isinstance(target, str) and target.startswith(("https://", "http://")):
            try:
                webbrowser.open(target)
            except Exception as exc:                    # noqa: BLE001
                messagebox.showerror("Oeffnen fehlgeschlagen", str(exc))
            return
        target = Path(target)
        if not target.exists():
            messagebox.showinfo(
                "Nicht gefunden",
                f"{label or target.name} existiert noch nicht.\n\n"
                "Tipp: 'Volle Test-Suite' erzeugt die Doku-HTMLs und "
                "das Dashboard.")
            return
        try:
            if target.is_dir():
                # Datei-Manager oeffnen (plattformabhaengig)
                if os.name == "nt":
                    os.startfile(target)                  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(target)])
                else:
                    subprocess.Popen(["xdg-open", str(target)])
            else:
                webbrowser.open(target.as_uri())
        except Exception as exc:                          # noqa: BLE001
            messagebox.showerror("Oeffnen fehlgeschlagen", str(exc))


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    app = ControlPanel()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
