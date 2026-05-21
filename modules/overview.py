"""
Modul Tages-/Wochenuebersicht.

Buendelt die anstehenden Fristen ALLER aktiven Module (ueber den
ModuleContext) und gruppiert sie nach Kalendertag. Standardmaessig deckt
die Uebersicht die kommenden sieben Tage ab (Wochenuebersicht).

Bewusst datums- statt zeitbasiert: ein System-/Zeitzonensprung verschiebt
nur den Tagesschnitt, fuehrt aber zu keiner Doppelzaehlung.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from core.interface import (Capability, ModuleContext, ModuleInterface)

_WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
                "Freitag", "Samstag", "Sonntag"]


class OverviewModule(ModuleInterface):
    """Aggregiert Fristen aller Module zu einer Tages-/Wochenuebersicht."""

    def __init__(self) -> None:
        self._ctx: Optional[ModuleContext] = None

    @property
    def module_id(self) -> str:
        return "overview"

    @property
    def display_name(self) -> str:
        return "Tages- & Wochenuebersicht"

    def on_register(self, context: ModuleContext) -> None:
        self._ctx = context

    def get_context_summary(self) -> str:
        return "Tages-/Wochenuebersicht ueber 'system.agenda'."

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="system.agenda",
                description="Gruppiert die anstehenden Fristen aller Module "
                            "nach Kalendertag. Standard: kommende 7 Tage "
                            "(Wochenuebersicht). Ueberfaellige Eintraege "
                            "kommen separat zurueck.",
                parameters={
                    "horizon_days": {"type": "integer",
                                     "description": "Anzahl Tage ab heute "
                                                    "(Standard: 7)"},
                },
                handler=self._cap_agenda,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_agenda(self, horizon_days: int = 7) -> dict:
        try:
            horizon_days = int(horizon_days)
        except (TypeError, ValueError):
            return {"error": "horizon_days muss eine ganze Zahl sein"}
        if horizon_days < 1:
            return {"error": "horizon_days muss mindestens 1 sein"}

        events = self._ctx.collect_events(horizon_days) if self._ctx else []
        today = date.today()

        days: list[dict] = []
        index: dict[date, dict] = {}
        for offset in range(horizon_days):
            d = today + timedelta(days=offset)
            entry = {"date": d.isoformat(),
                     "weekday": _WEEKDAYS_DE[d.weekday()],
                     "count": 0, "events": []}
            days.append(entry)
            index[d] = entry

        overdue: list[dict] = []
        for ev in events:
            delta = (ev.due_date - today).days
            payload = ev.to_dict()
            if delta < 0:
                overdue.append(payload)
            elif delta < horizon_days:
                bucket = index[ev.due_date]
                bucket["events"].append(payload)
                bucket["count"] += 1
            # delta >= horizon_days: ausserhalb des Fensters -> ignorieren

        for bucket in days:
            bucket["events"].sort(key=lambda e: (e.get("due_date") or "",
                                                 e.get("title") or ""))
        overdue.sort(key=lambda e: (e.get("due_date") or "",
                                    e.get("title") or ""))

        return {
            "horizon_days": horizon_days,
            "from": today.isoformat(),
            "to": (today + timedelta(days=horizon_days - 1)).isoformat(),
            "overdue": overdue,
            "overdue_count": len(overdue),
            "days": days,
            "total": sum(b["count"] for b in days) + len(overdue),
        }
