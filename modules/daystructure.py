"""
Modul Tagesstruktur & Energie.

Bewusst schlank: Energie-/Stimmungs-Tagebuch mit Skala 1-5 und einer
einfachen Empfehlung. Persistent in der DB (DayEntryRepository).
"""
from __future__ import annotations

from datetime import date

from core.interface import Capability, ModuleInterface
from database import DayEntryRepository
from models import DayEntry, Event


class DayStructureModule(ModuleInterface):
    """Steckbares Fachmodul mit persistenten Tageseintraegen."""

    def __init__(self, repo: DayEntryRepository):
        self.repo = repo

    @property
    def module_id(self) -> str:
        return "daystructure"

    @property
    def display_name(self) -> str:
        return "Tagesstruktur"

    def get_context_summary(self) -> str:
        recent = self.repo.list_recent(limit=7)
        if not recent:
            return "Noch keine Eintraege. Bewertung 1-5 ueber 'day.log_energy'."
        avg = sum(e.level for e in recent) / len(recent)
        return f"Energie-Schnitt der letzten {len(recent)} Tage: {avg:.1f}/5."

    def get_events(self, horizon_days: int = 90) -> list[Event]:
        today = date.today()
        if self.repo.has_entry_for(today):
            return []
        return [Event(
            title="Tagesreflexion: Energie eintragen",
            due_date=today,
            module_id=self.module_id,
            module_name=self.display_name,
            category="reflexion",
            detail="Kurz 1-5 bewerten via 'day.log_energy'.",
            days_remaining=0,
        )]

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="day.log_energy",
                description="Bewertet den heutigen Tag (1=ausgelaugt ... "
                            "5=top) und legt einen Eintrag an oder ersetzt "
                            "den heutigen.",
                parameters={
                    "level": {"type": "integer", "_required": True,
                              "description": "Skala 1-5"},
                    "note": {"type": "string", "description": "Kurzer Hinweis"},
                },
                handler=self._cap_log_energy,
            ),
            Capability(
                name="day.recent_entries",
                description="Listet die letzten Tageseintraege auf.",
                parameters={
                    "limit": {"type": "integer",
                               "description": "Maximal so viele (Standard: 30)"},
                },
                handler=self._cap_recent,
            ),
            Capability(
                name="day.recommendation",
                description="Liefert eine einfache Empfehlung auf Basis der "
                            "letzten Eintraege.",
                parameters={},
                handler=self._cap_recommendation,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_log_energy(self, level: int, note: str = "") -> dict:
        if not 1 <= level <= 5:
            return {"error": "level muss zwischen 1 und 5 liegen"}
        self.repo.upsert(DayEntry(day=date.today(), level=level, note=note))
        return {"status": "Eintrag gespeichert", "level": level}

    def _cap_recent(self, limit: int = 30) -> dict:
        entries = self.repo.list_recent(limit=limit)
        return {"count": len(entries),
                "entries": [{"day": e.day.isoformat(), "level": e.level,
                              "note": e.note} for e in entries]}

    def _cap_recommendation(self) -> dict:
        recent = self.repo.list_recent(limit=7)
        if not recent:
            return {"recommendation": ("Noch zu wenige Daten - trag ein paar "
                                        "Tage lang dein Energie-Level ein.")}
        avg = sum(e.level for e in recent) / len(recent)
        if avg < 2.5:
            tip = ("Niedrige Energie zuletzt - heute lieber kuerzere Bloecke, "
                   "frueh ins Bett, weniger Termine.")
        elif avg < 3.5:
            tip = ("Mittelmaessig - plane heute eine bewusste Pause am Nachmittag.")
        else:
            tip = ("Gute Energie - nutz' den Schwung fuer eine schwierige Aufgabe.")
        return {"average": round(avg, 1), "samples": len(recent),
                "recommendation": tip}
