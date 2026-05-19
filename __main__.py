"""
Erlaubt `python -m alltagshelfer` als CLI-Einstieg.

Subcommands:
  (kein)        startet die Konsolen-Demo (main.py)
  --diagnose    druckt einen Statusbericht (Verfuegbarkeit der Backends,
                 Module, OCR-Engines, Umgebungsvariablen)
  --gui         startet die GUI
  --sync-server [--port N] startet den HTTP-Sync-Server
"""
from __future__ import annotations

import sys


def main() -> int:
    args = sys.argv[1:]
    if not args:
        from main import main as run_demo
        run_demo()
        return 0
    if args[0] == "--diagnose":
        from diagnose import print_diagnosis
        return print_diagnosis()
    if args[0] == "--gui":
        from gui import main as run_gui
        run_gui()
        return 0
    if args[0] == "--sync-server":
        # restliche Args durchreichen
        sys.argv = ["alltagshelfer-sync-server"] + args[1:]
        from services.sync_server import main as run_server
        run_server()
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
