"""
Geräte-Profile: mehrere getrennte Datenbestände (je eigene DB + State)
auf einem Gerät, mit umschaltbarem aktiven Profil.

Das aktive Profil wird in einer kleinen Pointer-Datei persistiert, damit
ein UI-Umschalter über Neustarts hinweg wirkt - unabhängig von der
Umgebungsvariable ``ALLTAGSHELFER_PROFILE`` (die für CLI/CI Vorrang behält).

Die eigentliche DB/State-Trennung liefert ``services.profile``
(``db_path``/``state_dir``); dieser Manager ergänzt nur Auflisten, Anlegen
und persistentes Umschalten - alles toolkit-frei und vollautomatisch
testbar.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from services.profile import list_profiles, sanitize_profile

#: Anzeige-Label des Default-Profils (leerer Profilname).
DEFAULT_LABEL = "Standard"
_STATE_PREFIX = ".alltagshelfer-state"


class ProfilesManager:
    """Auflisten / Anlegen / Umschalten von Geräte-Profilen."""

    def __init__(self, base_dir: str | Path = ".",
                 pointer_path: Optional[str | Path] = None) -> None:
        self.base_dir = Path(base_dir)
        self.pointer_path = (Path(pointer_path) if pointer_path
                             else self.base_dir / ".alltagshelfer-active-profile")

    # ---- Lesen --------------------------------------------------------
    def active(self) -> str:
        """Aktiver Profilname ('' = Standard). Env hat Vorrang, dann
        Pointer-Datei, sonst Standard."""
        env = os.environ.get("ALLTAGSHELFER_PROFILE")
        if env is not None:
            return sanitize_profile(env)
        if self.pointer_path.is_file():
            try:
                data = json.loads(self.pointer_path.read_text(encoding="utf-8"))
                return sanitize_profile(data.get("active", ""))
            except (json.JSONDecodeError, OSError, AttributeError):
                return ""
        return ""

    def list(self) -> list[dict]:
        """Alle bekannten Profile inkl. Default, markiert das aktive."""
        names = set(list_profiles(str(self.base_dir)))
        names.add("")                       # Default ist immer wählbar
        names.add(self.active())            # aktives stets sichtbar
        active = self.active()
        ordered = sorted(names, key=lambda n: (n != "", n.lower()))
        return [{"name": n, "label": self._label(n), "active": n == active}
                for n in ordered]

    @staticmethod
    def _label(name: str) -> str:
        return DEFAULT_LABEL if name == "" else name

    # ---- Schreiben ----------------------------------------------------
    def create(self, name: str) -> dict:
        """Legt ein neues Profil an (eigenes State-Verzeichnis) und macht es
        aktiv. Die DB entsteht beim nächsten Start. Ungültig -> Fehler."""
        clean = sanitize_profile(name)
        if not clean:
            return {"error": "Ungueltiger Profilname (nur A-Z, a-z, 0-9, _-)"}
        self._state_dir_for(clean).mkdir(parents=True, exist_ok=True)
        self._write_active(clean)
        return {"status": "angelegt", "active": clean,
                "restart_required": True}

    def switch(self, name: str) -> dict:
        """Wechselt das aktive Profil ('' = Standard). Wirkt nach Neustart."""
        clean = sanitize_profile(name)       # '' bleibt '' (Default)
        self._write_active(clean)
        return {"status": "gewechselt", "active": clean,
                "restart_required": True}

    # ---- intern -------------------------------------------------------
    def _state_dir_for(self, name: str) -> Path:
        suffix = _STATE_PREFIX if not name else f"{_STATE_PREFIX}-{name}"
        return self.base_dir / suffix

    def _write_active(self, name: str) -> None:
        self.pointer_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.pointer_path.with_name(self.pointer_path.name + ".tmp")
        tmp.write_text(json.dumps({"active": name}), encoding="utf-8")
        tmp.replace(self.pointer_path)
