"""
Modul Geräte-Profile.

Macht die Multi-User-Profile (mehrere getrennte Datenbestände auf einem
Gerät) über Capabilities zugänglich - so können Assistent und jede UI sie
auflisten/anlegen/umschalten, ohne den Pointer manuell zu setzen. Die
eigentliche Logik liegt toolkit-frei in ``app_core.profiles``.

Capabilities tragen das ``system.``-Präfix und sind damit im Free-Tier
offen (kein Pro-Lock für die Datentrennung).
"""
from __future__ import annotations

from core.interface import Capability, ModuleInterface
from app_core.profiles import ProfilesManager


class ProfilesModule(ModuleInterface):

    def __init__(self, base_dir: str = ".") -> None:
        self._mgr = ProfilesManager(base_dir=base_dir)

    @property
    def module_id(self) -> str:
        return "profiles"

    @property
    def display_name(self) -> str:
        return "Geraete-Profile"

    def get_context_summary(self) -> str:
        return f"Aktives Profil: {self._mgr.active() or 'Standard'}"

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="system.profiles",
                description="Listet die Geraete-Profile (getrennte "
                            "Datenbestaende) auf und markiert das aktive.",
                parameters={},
                handler=self._cap_list,
            ),
            Capability(
                name="system.profile_create",
                description="Legt ein neues Profil an und macht es aktiv "
                            "(wirkt nach Neustart).",
                parameters={
                    "name": {"type": "string", "_required": True,
                             "description": "Profilname (A-Z a-z 0-9 _-)"},
                },
                handler=self._cap_create,
            ),
            Capability(
                name="system.profile_switch",
                description="Wechselt das aktive Profil (leer = Standard; "
                            "wirkt nach Neustart).",
                parameters={
                    "name": {"type": "string",
                             "description": "Zielprofil (leer = Standard)"},
                },
                handler=self._cap_switch,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_list(self) -> dict:
        return {"active": self._mgr.active(), "profiles": self._mgr.list()}

    def _cap_create(self, name: str) -> dict:
        return self._mgr.create(name)

    def _cap_switch(self, name: str = "") -> dict:
        return self._mgr.switch(name)
