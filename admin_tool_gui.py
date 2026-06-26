#!/usr/bin/env python3
"""
Graphical Admin Tool for ZunaroDo

This GUI wraps various scripts and checks into a user-friendly interface.
You can build Android artifacts, increment version numbers, run compliance
checks, verify assets, run unit tests, check the environment and secrets,
and perform additional maintenance tasks. All commands can be started by
clicking the corresponding button.

Requirements:
- Tkinter must be available (it usually is on standard Python installs).
- The script assumes it resides in the project root, next to
  buildozer.spec and playstore.yml.

Usage:
    python admin_tool_gui.py
"""
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_MANAGER = PROJECT_ROOT / "android_build_manager.py"


def run_command(cmd, log_callback, on_complete=None):
    """Run a command in a background thread and stream its output."""
    def _target():
        log_callback(f"\n[INFO] Running command: {' '.join(cmd)}\n")
        try:
            process = subprocess.Popen(
                cmd,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert process.stdout is not None
            for line in process.stdout:
                log_callback(line)
            code = process.wait()
            if code != 0:
                log_callback(f"[ERROR] Command exited with code {code}\n")
            else:
                log_callback("[INFO] Command completed successfully\n")
        except Exception as e:
            log_callback(f"[ERROR] {e}\n")
        finally:
            if on_complete:
                on_complete()
    threading.Thread(target=_target, daemon=True).start()


class AdminGUI:
    def __init__(self, root):
        self.root = root
        root.title("ZunaroDo Admin Tool")
        root.geometry("700x600")

        # Create frames
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        log_frame = tk.Frame(root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.NORMAL)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Build buttons
        self.add_button(btn_frame, "Build Debug", self.build_debug)
        self.add_button(btn_frame, "Build Release", self.build_release)
        self.add_button(btn_frame, "Increment Version", self.increment_version)
        self.add_button(btn_frame, "PlayStore Check", self.playstore_check)
        self.add_button(btn_frame, "Data Safety Check", self.data_safety_check)
        self.add_button(btn_frame, "Assets Check", self.assets_check)
        self.add_button(btn_frame, "Unit Tests", self.unit_tests)
        self.add_button(btn_frame, "List Placeholders", self.list_placeholders)
        self.add_button(btn_frame, "Env Check", self.env_check)
        self.add_button(btn_frame, "Secrets Check", self.secrets_check)
        self.add_button(btn_frame, "Static Analysis", self.static_analysis)
        self.add_button(btn_frame, "Backup DB", self.backup_db)
        self.add_button(btn_frame, "Restore DB", self.restore_db)
        self.add_button(btn_frame, "Trigger CI Release", self.ci_trigger_release)
        self.add_button(btn_frame, "Update Tool", self.update_tool)
        self.add_button(btn_frame, "Save Log", self.save_log)

    def add_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, width=14, command=command)
        btn.pack(side=tk.LEFT, padx=3, pady=2)

    def log(self, message):
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)

    def build_debug(self):
        cmd = ["python", str(BUILD_MANAGER), "--variant", "debug"]
        run_command(cmd, self.log)

    def build_release(self):
        cmd = ["python", str(BUILD_MANAGER), "--variant", "release"]
        run_command(cmd, self.log)

    def increment_version(self):
        cmd = ["python", str(BUILD_MANAGER), "--increment-version", "--variant", "debug"]
        run_command(cmd, self.log)

    def playstore_check(self):
        cmd = ["python", "-m", "tools.playstore_check", "--strict"]
        run_command(cmd, self.log)

    def data_safety_check(self):
        cmd = ["python", "-m", "tools.data_safety", "--check"]
        run_command(cmd, self.log)

    def assets_check(self):
        cmd = ["python", "-m", "tools.gen_assets", "--check"]
        run_command(cmd, self.log)

    def unit_tests(self):
        cmd = ["python", "-m", "unittest", "discover", "-s", "tests"]
        run_command(cmd, self.log)

    def list_placeholders(self):
        cmd = ["python", "-m", "tools.privacy_policy", "--list-placeholders"]
        run_command(cmd, self.log)

    def env_check(self):
        # Check buildozer
        buildozer_ok = subprocess.call(["bash", "-c", "command -v buildozer >/dev/null"], stdout=subprocess.DEVNULL) == 0
        java_ok = subprocess.call(["bash", "-c", "command -v java >/dev/null"], stdout=subprocess.DEVNULL) == 0
        self.log("\n[ENV CHECK]\n")
        self.log(f"Buildozer installiert: {'Ja' if buildozer_ok else 'Nein'}\n")
        self.log(f"Java installiert: {'Ja' if java_ok else 'Nein'}\n")
        # Additional tool checks can be added here

    def secrets_check(self):
        """Check that all required secrets and API keys are present in the environment.

        This includes the Android keystore variables for signing release builds as well as
        the keys required for server‑side KI functions. If a value is missing the user
        will be notified in the log. Keys that are optional (e.g. GEMINI_API_KEY) are
        still reported so that developers are aware of the current configuration.
        """
        required = [
            # Android keystore secrets
            "P4A_RELEASE_KEYSTORE",
            "P4A_RELEASE_KEYSTORE_PASSWD",
            "P4A_RELEASE_KEYALIAS",
            "P4A_RELEASE_KEYALIAS_PASSWD",
            # KI / LLM API keys
            "GEMINI_API_KEY",
            # "GOOGLE_API_KEY" is an alias retained for backwards compatibility. If both are
            # unset the KI‑Assistent läuft offline/regelbasiert.
            "GOOGLE_API_KEY",
        ]
        self.log("\n[SECRETS CHECK]\n")
        for var in required:
            val = os.environ.get(var)
            if val:
                self.log(f"{var}: gesetzt\n")
            else:
                # Note: Do not treat GEMINI_API_KEY/GOOGLE_API_KEY as fatal; offline mode is allowed
                self.log(f"{var}: FEHLT\n")

    def static_analysis(self):
        self.log("\n[STATIC ANALYSIS]\n")
        # Run pip-audit if available
        pip_audit = subprocess.call(["bash", "-c", "command -v pip-audit >/dev/null"], stdout=subprocess.DEVNULL) == 0
        if pip_audit:
            cmd = ["pip-audit"]
            self.log("Starte pip-audit...\n")
            run_command(cmd, self.log)
        else:
            self.log("pip-audit nicht installiert. Überspringe Sicherheits-Audit.\n")
        # Run gitleaks if available
        gitleaks = subprocess.call(["bash", "-c", "command -v gitleaks >/dev/null"], stdout=subprocess.DEVNULL) == 0
        if gitleaks:
            cmd = ["gitleaks", "protect", "--no-git"]
            self.log("Starte gitleaks...\n")
            run_command(cmd, self.log)
        else:
            self.log("gitleaks nicht installiert. Überspringe Secret-Scan.\n")

    def backup_db(self):
        # Ask user for DB file
        db_path = filedialog.askopenfilename(
            title="Datenbank auswählen",
            initialdir=str(PROJECT_ROOT),
            filetypes=[("SQLite/DB Dateien", "*.db *.sqlite *.sqlite3"), ("Alle Dateien", "*.*")],
        )
        if not db_path:
            return
        db_path = Path(db_path)
        # Ask user for backup directory
        backup_dir = filedialog.askdirectory(
            title="Backup-Verzeichnis auswählen",
            initialdir=str(PROJECT_ROOT),
        )
        if not backup_dir:
            return
        backup_dir = Path(backup_dir)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = backup_dir / f"{db_path.stem}-backup-{timestamp}{db_path.suffix}"
        try:
            backup_file.write_bytes(db_path.read_bytes())
            self.log(f"\n[BACKUP] Datenbank gesichert: {backup_file}\n")
        except Exception as e:
            self.log(f"\n[BACKUP] Fehler beim Sichern: {e}\n")

    def restore_db(self):
        """Restore a database from a backup file."""
        # Ask for backup file
        backup_file = filedialog.askopenfilename(
            title="Backup-Datei auswählen",
            initialdir=str(PROJECT_ROOT),
            filetypes=[("SQLite/DB Dateien", "*.db *.sqlite *.sqlite3"), ("Alle Dateien", "*.*")],
        )
        if not backup_file:
            return
        backup_file = Path(backup_file)
        # Ask for target DB location
        target_file = filedialog.askopenfilename(
            title="Zieldatenbank auswählen (wird überschrieben)",
            initialdir=str(PROJECT_ROOT),
            filetypes=[("SQLite/DB Dateien", "*.db *.sqlite *.sqlite3"), ("Alle Dateien", "*.*")],
        )
        if not target_file:
            return
        target_file = Path(target_file)
        try:
            target_file.write_bytes(backup_file.read_bytes())
            self.log(f"\n[RESTORE] Datenbank wiederhergestellt: {target_file}\n")
        except Exception as e:
            self.log(f"\n[RESTORE] Fehler beim Wiederherstellen: {e}\n")

    def ci_trigger_release(self):
        """Trigger GitHub Actions workflow for a release build."""
        # Run GitHub CLI workflow if gh is available
        gh_ok = subprocess.call(["bash", "-c", "command -v gh >/dev/null"], stdout=subprocess.DEVNULL) == 0
        if not gh_ok:
            self.log("\n[CI] GitHub CLI (gh) ist nicht installiert. Bitte installieren Sie es, um den Workflow auszulösen.\n")
            return
        # Determine repository from environment or fallback
        repo = os.environ.get("GITHUB_REPOSITORY", "Toto241/ZunaroDo")
        workflow_name = "Android Release (AAB)"
        cmd = ["gh", "workflow", "run", workflow_name, "-R", repo]
        self.log(f"\n[CI] Starte GitHub Workflow \"{workflow_name}\" für Repository {repo}...\n")
        run_command(cmd, self.log)

    def update_tool(self):
        """Update the local repository by pulling the latest changes."""
        # Check if git is installed
        git_ok = subprocess.call(["bash", "-c", "command -v git >/dev/null"], stdout=subprocess.DEVNULL) == 0
        if not git_ok:
            self.log("\n[UPDATE] Git ist nicht installiert. Bitte installieren Sie es, um Updates zu erhalten.\n")
            return
        cmd = ["git", "pull", "--ff-only"]
        self.log("\n[UPDATE] Prüfe auf Updates...\n")
        run_command(cmd, self.log)

    def save_log(self):
        """Save the current log to a text file."""
        file_path = filedialog.asksaveasfilename(
            title="Log speichern unter...",
            defaultextension=".txt",
            filetypes=[("Textdatei", "*.txt"), ("Alle Dateien", "*.*")],
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log_text.get("1.0", tk.END))
            self.log(f"\n[LOG] Log gespeichert unter: {file_path}\n")
        except Exception as e:
            self.log(f"\n[LOG] Fehler beim Speichern des Logs: {e}\n")


def main():
    root = tk.Tk()
    app = AdminGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
