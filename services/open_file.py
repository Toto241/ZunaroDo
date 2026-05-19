"""
Plattformneutrales Oeffnen einer Datei mit dem System-Standardprogramm.

Wird von der GUI z.B. fuer 'PDF nach Erstellung anzeigen' verwendet.
Bewusst nichts Magisches: kein Browser, kein Webdienst, sondern das,
was das Betriebssystem ohnehin tut, wenn der Nutzer doppelklickt.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Union


PathLike = Union[str, Path]


def open_with_default_app(path: PathLike) -> bool:
    """Oeffnet eine Datei mit dem OS-Standardprogramm.

    Rueckgabe: True bei erfolgreichem Startaufruf, False sonst.
    Wirft *keine* Exception - die Aufrufer bauen meist eine Toast-
    Nachricht aus dem False-Fall.
    """
    p = Path(path)
    if not p.exists():
        return False
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(p))                          # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(
                ["open", str(p)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                ["xdg-open", str(p)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return True
    except (OSError, FileNotFoundError):
        return False
