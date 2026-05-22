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
  4. Dokumentation
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
    "text":         ("#1A1A1A", "#FFFFFF"),
    "text_muted":   ("#5A5A5A", "#9A9A9A"),
    "log_bg":       ("#FFFFFF", "#1B1B1B"),
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
    description: str = ""               # Tooltip / Status-Bar-Text
    confirm: Optional[str] = None       # wenn gesetzt -> Bestaetigungsdialog
    needs_wsl: bool = False             # nur sinnvoll, wenn 'wsl' verfuegbar


@dataclass(frozen=True)
class LinkAction:
    label: str
    target: Path
    description: str = ""


# Die Aktions-Tabellen sind als Funktionen modelliert (kein
# Top-Level-Konstrukt), damit Pfade dynamisch sind und Tests sie
# inspizieren koennen.
def actions_tests() -> list[Action]:
    py = sys.executable
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
    py = sys.executable
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
                    "Erzeugt dist/Alltagshelfer/Alltagshelfer.exe."),
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
                    "Erzeugt dist/Alltagshelfer/."),
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
    py = sys.executable
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
    """Hauptfenster - 4 Sektionen + Live-Log."""

    LOG_LIMIT = 4000      # max. Zeilen im Log (FIFO)

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        self._font_family = self._pick_font_family()
        self.title("Zunarodo  -  Control Panel")
        self.geometry("1120x780")
        self.minsize(900, 640)
        # Mica-aehnlicher Fensterhintergrund (statt CTk-Standardgrau).
        self.configure(fg_color=WIN11["window_bg"])

        self._log_queue: "queue.Queue[str]" = queue.Queue()
        self._exit_queue: "queue.Queue[int]" = queue.Queue()
        self._runner = CommandRunner(
            on_line=self._log_queue.put,
            on_done=self._exit_queue.put)
        self._busy_buttons: list[ctk.CTkButton] = []
        self._current_action_label = ""

        self._build_ui()
        self._refresh_status()
        # ueber after() kontinuierlich die Queues pumpen
        self.after(100, self._drain_queues)

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
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header, text="Zunarodo  ·  Control Panel",
            text_color=WIN11["text"],
            font=self._font(size=20, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        self.status_label = ctk.CTkLabel(
            header, text="Status: -", text_color=WIN11["text_muted"],
            font=self._font(size=13))
        self.status_label.grid(row=0, column=2, sticky="e")

        # Sektionen
        self._build_section(
            row=1, title="Tests & Cockpit",
            actions=actions_tests(),
            extra=[self._subtle_button(self, "Cockpit oeffnen",
                                       self._open_index)])
        self._build_section(
            row=2, title="Build  -  Android / iOS / PC",
            actions=actions_build())
        self._build_section(
            row=3, title="Play-Store-Sync",
            actions=actions_playstore())
        self._build_link_section(
            row=4, title="Dokumentation & Schnellzugriff",
            items=links())

        # Live-Log
        log_frame = ctk.CTkFrame(
            self, corner_radius=8, fg_color=WIN11["card_bg"],
            border_width=1, border_color=WIN11["card_border"])
        log_frame.grid(row=5, column=0, sticky="nsew", padx=20, pady=6)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        log_head = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_head.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        log_head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_head, text="Live-Log", text_color=WIN11["text"],
                      font=self._font(size=14, weight="bold")
                      ).grid(row=0, column=0, sticky="w")
        self.action_label = ctk.CTkLabel(log_head, text="bereit",
                                           text_color=WIN11["text_muted"],
                                           font=self._font(size=12))
        self.action_label.grid(row=0, column=1, padx=(8, 8))
        ctk.CTkButton(log_head, text="Log loeschen", width=120,
                       corner_radius=6, font=self._font(size=13),
                       fg_color="transparent", border_width=1,
                       border_color=WIN11["card_border"],
                       text_color=WIN11["text"],
                       hover_color=WIN11["subtle_hover"],
                       command=self._clear_log
                       ).grid(row=0, column=2, padx=3)
        self.stop_button = ctk.CTkButton(
            log_head, text="Stoppen", width=120, state="disabled",
            corner_radius=6, font=self._font(size=13),
            fg_color="transparent", border_width=1,
            border_color=WIN11["card_border"], text_color=WIN11["text"],
            hover_color=WIN11["subtle_hover"],
            command=self._stop_current)
        self.stop_button.grid(row=0, column=3, padx=3)

        self.log_text = ctk.CTkTextbox(
            log_frame, wrap="word", activate_scrollbars=True,
            corner_radius=6, fg_color=WIN11["log_bg"],
            text_color=WIN11["text"], border_width=0,
            font=ctk.CTkFont(family="Cascadia Mono", size=12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12,
                            pady=(0, 12))
        self.log_text.configure(state="disabled")

        # Statuszeile unten
        footer = ctk.CTkLabel(
            self, text=f"Projekt: {REPO_ROOT}",
            text_color=WIN11["text_muted"], font=self._font(size=11))
        footer.grid(row=6, column=0, sticky="w", padx=20, pady=(0, 10))

    def _card(self, row: int, title: str) -> "ctk.CTkFrame":
        """Erzeugt eine Windows-11-Card (abgerundet, Layer-Farbe, Titel)."""
        frame = ctk.CTkFrame(
            self, corner_radius=8, fg_color=WIN11["card_bg"],
            border_width=1, border_color=WIN11["card_border"])
        frame.grid(row=row, column=0, sticky="ew", padx=20, pady=6)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=title, text_color=WIN11["text"],
                      font=self._font(size=15, weight="bold")
                      ).grid(row=0, column=0, sticky="w", padx=14,
                             pady=(12, 4))
        return frame

    def _accent_button(self, master, text, command) -> "ctk.CTkButton":
        return ctk.CTkButton(
            master, text=text, command=command, width=240,
            corner_radius=6, font=self._font(size=13),
            fg_color=WIN11["accent"], hover_color=WIN11["accent_hover"],
            text_color="#FFFFFF")

    def _subtle_button(self, master, text, command) -> "ctk.CTkButton":
        return ctk.CTkButton(
            master, text=text, command=command, width=240,
            corner_radius=6, font=self._font(size=13),
            fg_color="transparent", border_width=1,
            border_color=WIN11["card_border"], text_color=WIN11["text"],
            hover_color=WIN11["subtle_hover"])

    def _build_section(self, row: int, title: str,
                        actions: list[Action],
                        extra: Optional[list[ctk.CTkButton]] = None) -> None:
        frame = self._card(row, title)
        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 12))
        col = 0
        for action in actions:
            btn = self._accent_button(
                btn_row, action.label,
                command=lambda a=action: self._run_action(a))
            btn.grid(row=col // 4, column=col % 4, padx=4, pady=4,
                      sticky="ew")
            self._busy_buttons.append(btn)
            col += 1
        for c in range(4):
            btn_row.grid_columnconfigure(c, weight=1)
        if extra:
            for w in extra:
                w.master = btn_row
                w.grid(row=(col // 4), column=(col % 4), padx=4, pady=4,
                        sticky="ew")
                col += 1

    def _build_link_section(self, row: int, title: str,
                             items: list[LinkAction]) -> None:
        frame = self._card(row, title)
        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 12))
        for idx, link in enumerate(items):
            btn = self._subtle_button(
                btn_row, link.label,
                command=lambda l=link: self._open_link(l))
            btn.grid(row=idx // 4, column=idx % 4, padx=4, pady=4,
                      sticky="ew")
        for c in range(4):
            btn_row.grid_columnconfigure(c, weight=1)

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
            text_color=(("#b54708", "#e08a3c") if busy
                        else WIN11["text_muted"]))
        self._current_action_label = label

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
        self.after(100, self._drain_queues)

    def _on_command_done(self, rc: int) -> None:
        self._append_log(f"[fertig - Exit-Code {rc}]\n")
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
    def _open_index(self) -> None:
        if INDEX_HTML.is_file():
            webbrowser.open(INDEX_HTML.as_uri())
        else:
            messagebox.showinfo(
                "Noch keine index.html",
                "Bitte zuerst 'Volle Test-Suite' oder 'Dashboard neu rendern' "
                "ausfuehren.")

    def _open_link(self, link: LinkAction) -> None:
        target = link.target
        if not target.exists():
            messagebox.showinfo(
                "Nicht gefunden",
                f"{target.name} existiert noch nicht.\n\n"
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
