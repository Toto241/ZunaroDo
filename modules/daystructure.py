"""
Modul - Tagesstruktur & Energie (Scaffold).

Im urspruenglichen Konzept eines der Module, das aber nicht starr
Pomodoro-Timer sein soll, sondern Energie-Level und Gewohnheiten
lernen koennte. Dies hier ist ein bewusst schlankes Scaffold:

  - tagebuch_eintrag: kurzer Energie-/Stimmungseintrag mit Skala 1-5
  - tagestruktur:     liefert eine einfache Empfehlung auf Basis der
                      letzten Eintraege (Durchschnitt, Trend)
  - get_events:       liefert eine taegliche Erinnerung "Tagesreflexion"

So bleibt das Modul von Anfang an im System sichtbar, ohne unfertige
Versprechen. Spaeter koennen Wetter-/Schlaf-Quellen ergaenzt werden.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from core.interface import Capability, ModuleInterface
from models import Event


class DayStructureModule(ModuleInterface):
    """In-Memory-Scaffold ohne eigene DB-Tabelle (bewusst klein)."""

    def __init__(self) -> None:
        # Liste der Eintraege - bewusst nicht persistiert; das soll nicht
        # ausarten, solange das Modul nicht ausgereift ist.
        self._entries: list[tuple[date, int, str]] = []

    @property
    def module_id(self) -> str:
        return "daystructure"

    @property
    def display_name(self) -> str:
        return "Tagesstruktur (Vorschau)"

    def get_context_summary(self) -> str:
        if not self._entries:
            return "Noch keine Eintraege. Bewertung 1-5 ueber 'day.log_energy'."
        recent = self._entries[-7:]
        avg = sum(level for _, level, _ in recent) / len(recent)
        return f"Energie-Schnitt der letzten {len(recent)} Tage: {avg:.1f}/5."

    def get_events(self, horizon_days: int = 90) -> list[Event]:
        today = date.today()
        if any(d == today for d, _, _ in self._entries):
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
                            "5=top) und legt einen Eintrag an.",
                parameters={
                    "level": {"type": "integer", "_required": True,
                              "description": "Skala 1-5"},
                    "note": {"type": "string", "description": "Kurzer Hinweis"},
                },
                handler=self._cap_log_energy,
            ),
            Capability(
                name="day.recommendation",
                description="Liefert eine einfache Empfehlung auf Basis der "
                            "letzten Eintraege (Pausen, Tagesplanung).",
                parameters={},
                handler=self._cap_recommendation,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_log_energy(self, level: int, note: str = "") -> dict:
        if not 1 <= level <= 5:
            return {"error": "level muss zwischen 1 und 5 liegen"}
        # gleicher Tag - ersetzen
        self._entries = [e for e in self._entries if e[0] != date.today()]
        self._entries.append((date.today(), level, note))
        return {"status": "Eintrag gespeichert", "level": level}

    def _cap_recommendation(self) -> dict:
        if not self._entries:
            return {"recommendation": ("Noch zu wenige Daten - trag ein paar "
                                        "Tage lang dein Energie-Level ein.")}
        recent = self._entries[-7:]
        avg = sum(level for _, level, _ in recent) / len(recent)
        if avg < 2.5:
            tip = ("Niedrige Energie zuletzt - heute lieber kuerzere Bloecke, "
                   "frueh ins Bett, weniger Termine.")
        elif avg < 3.5:
            tip = ("Mittelmaessig - plane heute eine bewusste Pause am Nachmittag.")
        else:
            tip = ("Gute Energie - nutz' den Schwung fuer eine schwierige Aufgabe.")
        return {"average": round(avg, 1), "samples": len(recent),
                "recommendation": tip}
