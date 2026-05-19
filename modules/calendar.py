"""
Modul C - Termine & Kalender.

Sammelt alle allgemeinen Termine: Behoerdentermine, Garantien, TUEV,
Steuerfristen, sonstige Erinnerungen, Geburtstage (wiederkehrend).

Jeder Termin kann optional einer Person zugeordnet werden (Querschnitts-
Dimension via family.members). Wiederkehrende Termine werden ueber
recurrence_days umgesetzt: '365' fuer jaehrlich, '30' fuer monatlich.

Zwei Spezialfaelle, die das Modul von sich aus liefert:
  - die deutschen Standard-Steuerfristen des laufenden Jahres
  - Geburtstage der erfassten Haushaltsmitglieder
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from core.interface import Capability, ModuleContext, ModuleInterface
from database import CalendarRepository
from models import CalendarEvent, Event


# Wiederkehrende deutsche Standard-Steuerfristen (Monat, Tag, Titel)
_STEUERFRISTEN: list[tuple[int, int, str]] = [
    (5, 31, "Einkommensteuererklaerung (ohne Steuerberater)"),
    (7, 31, "Einkommensteuererklaerung (mit Steuerberater, Vorjahr)"),
    (1, 10, "Umsatzsteuer-Voranmeldung Q4 (falls relevant)"),
    (4, 10, "Umsatzsteuer-Voranmeldung Q1 (falls relevant)"),
    (7, 10, "Umsatzsteuer-Voranmeldung Q2 (falls relevant)"),
    (10, 10, "Umsatzsteuer-Voranmeldung Q3 (falls relevant)"),
]


class CalendarModule(ModuleInterface):
    """Modul C als steckbares Fachmodul."""

    def __init__(self, repo: CalendarRepository):
        self.repo = repo
        self._ctx: ModuleContext | None = None

    @property
    def module_id(self) -> str:
        return "calendar"

    @property
    def display_name(self) -> str:
        return "Termine & Kalender"

    def on_register(self, context: ModuleContext) -> None:
        self._ctx = context

    def get_context_summary(self) -> str:
        upcoming = self.repo.list_upcoming(horizon_days=30)
        bday_count = sum(1 for _ in self._birthday_events(30))
        if not upcoming and not bday_count:
            return "Keine Termine in den naechsten 30 Tagen."
        return (f"{len(upcoming) + bday_count} Termin(e) in den naechsten "
                f"30 Tagen (davon {bday_count} Geburtstag(e)).")

    def get_events(self, horizon_days: int = 90) -> list[Event]:
        today = date.today()
        result: list[Event] = []

        # 1) explizite Kalender-Eintraege
        for cal_ev in self.repo.list_upcoming(horizon_days):
            days = (cal_ev.due_date - today).days
            detail = cal_ev.description
            if cal_ev.person_name:
                detail = (f"Betrifft: {cal_ev.person_name}. " + detail).strip()
            result.append(Event(
                title=f"{self._category_label(cal_ev.category)}: {cal_ev.title}",
                due_date=cal_ev.due_date,
                module_id=self.module_id,
                module_name=self.display_name,
                category=cal_ev.category,
                detail=detail,
                days_remaining=days,
            ))

        # 2) Geburtstage der Haushaltsmitglieder
        result.extend(self._birthday_events(horizon_days))

        # 3) gesetzliche Standard-Steuerfristen
        result.extend(self._steuerfristen(horizon_days))

        return result

    # ---- Faehigkeiten --------------------------------------------------
    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="calendar.add_event",
                description="Legt einen Termin an (einmalig oder wiederkehrend).",
                parameters={
                    "title": {"type": "string", "_required": True,
                              "description": "Bezeichnung des Termins"},
                    "due_date": {"type": "string", "_required": True,
                                 "description": "Datum ISO (YYYY-MM-DD)"},
                    "category": {"type": "string",
                                 "description": "termin, garantie, tuev, "
                                                "steuer, geburtstag, sonstiges"},
                    "description": {"type": "string", "description": "Details"},
                    "recurrence_days": {"type": "integer",
                                        "description": "Wiederholung in Tagen "
                                                       "(z.B. 365 = jaehrlich)"},
                    "person_id": {"type": "integer",
                                  "description": "Optional: betroffene Person "
                                                 "(siehe family.members)"},
                },
                handler=self._cap_add_event,
            ),
            Capability(
                name="calendar.list_events",
                description="Listet alle erfassten Termine auf.",
                parameters={},
                handler=self._cap_list,
            ),
            Capability(
                name="calendar.upcoming",
                description="Liefert anstehende Termine innerhalb eines Horizonts.",
                parameters={
                    "horizon_days": {"type": "integer",
                                     "description": "Bis wie viele Tage in der "
                                                    "Zukunft (Standard: 90)"},
                },
                handler=self._cap_upcoming,
            ),
            Capability(
                name="calendar.export_ical",
                description="Exportiert alle Termine als iCalendar-Datei "
                            "(.ics), die in jeden gaengigen Kalender "
                            "importiert werden kann.",
                parameters={
                    "path": {"type": "string", "_required": True,
                             "description": "Zielpfad (sollte auf .ics enden)"},
                },
                handler=self._cap_export_ical,
            ),
            Capability(
                name="calendar.delete_event",
                description="Entfernt einen Termin.",
                parameters={
                    "event_id": {"type": "integer", "_required": True,
                                 "description": "ID des Termins"},
                },
                handler=self._cap_delete,
                destructive=True,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    # Erlaubte Kategorien - dient der Vollstaendigkeitspruefung. Beliebige
    # Strings werden zwar akzeptiert, aber das LLM/die GUI sollen die
    # bekannten Kategorien bevorzugen, damit Filter und Labels passen.
    _KNOWN_CATEGORIES: set[str] = {
        "termin", "garantie", "tuev", "steuer", "geburtstag", "sonstiges"}

    def _cap_add_event(self, title: str, due_date: str,
                       category: str = "termin",
                       description: str = "",
                       recurrence_days: int | None = None,
                       person_id: int | None = None) -> dict:
        if not title or not title.strip():
            return {"error": "Titel darf nicht leer sein"}
        # 'recurrence_days' muss entweder fehlen (einmaliger Termin) oder
        # positiv sein - 0 oder negative Werte sind unzulaessig, weil sie
        # die Wiederholungs-Schleife endlos machen wuerden.
        if recurrence_days is not None and recurrence_days <= 0:
            return {"error": "recurrence_days muss positiv sein "
                              "(oder leer lassen fuer einmalig)"}
        # Unbekannte Kategorien werden auf 'sonstiges' normalisiert -
        # so bleibt die UI-Anzeige konsistent.
        if category not in self._KNOWN_CATEGORIES:
            category = "sonstiges"
        try:
            parsed = date.fromisoformat(due_date)
        except (TypeError, ValueError):
            return {"error": f"Ungueltiges Datum '{due_date}', "
                              "erwartet YYYY-MM-DD"}
        ev = CalendarEvent(
            title=title,
            due_date=parsed,
            category=category,
            description=description,
            recurrence_days=recurrence_days,
            person_id=person_id if person_id else None,
        )
        saved = self.repo.add(ev)
        return {"status": "angelegt", "event": saved.to_dict()}

    def _cap_list(self) -> dict:
        events = self.repo.list_all()
        return {"count": len(events),
                "events": [e.to_dict() for e in events]}

    def _cap_upcoming(self, horizon_days: int = 90) -> dict:
        events = self.repo.list_upcoming(horizon_days)
        return {"horizon_days": horizon_days, "count": len(events),
                "events": [e.to_dict() for e in events]}

    def _cap_delete(self, event_id: int) -> dict:
        self.repo.delete(event_id)
        return {"status": "geloescht", "event_id": event_id}

    def _cap_export_ical(self, path: str) -> dict:
        from services.ical import export_events
        target = Path(path)
        count = export_events(self.repo.list_all(), target)
        return {"status": "exportiert", "count": count, "path": str(target)}

    # ---- Spezialquellen ------------------------------------------------
    def _birthday_events(self, horizon_days: int) -> Iterable[Event]:
        """Geburtstage der Haushaltsmitglieder (via Modul D)."""
        if self._ctx is None or not self._ctx.has_capability("family.members"):
            return []
        members = self._ctx.call("family.members").get("members", [])
        today = date.today()
        result: list[Event] = []
        for m in members:
            iso = m.get("birthday")
            if not iso:
                continue
            try:
                bday = date.fromisoformat(iso)
            except ValueError:
                continue
            this_year = bday.replace(year=today.year)
            if this_year < today:
                this_year = bday.replace(year=today.year + 1)
            days = (this_year - today).days
            if days > horizon_days:
                continue
            result.append(Event(
                title=f"Geburtstag: {m['name']}",
                due_date=this_year,
                module_id=self.module_id,
                module_name=self.display_name,
                category="geburtstag",
                detail=f"Nicht vergessen, {m['name']} zu gratulieren.",
                days_remaining=days,
            ))
        return result

    def _steuerfristen(self, horizon_days: int) -> Iterable[Event]:
        today = date.today()
        result: list[Event] = []
        for month, day, title in _STEUERFRISTEN:
            for year_shift in (0, 1):
                try:
                    d = date(today.year + year_shift, month, day)
                except ValueError:
                    continue
                if d < today:
                    continue
                days = (d - today).days
                if days <= horizon_days:
                    result.append(Event(
                        title=f"Steuerfrist: {title}",
                        due_date=d,
                        module_id=self.module_id,
                        module_name=self.display_name,
                        category="steuer",
                        detail="Gesetzliche Frist - rechtzeitig vorbereiten.",
                        days_remaining=days,
                    ))
                    break       # nur das naechste Auftreten
        return result

    @staticmethod
    def _category_label(category: str) -> str:
        return {
            "termin": "Termin",
            "garantie": "Garantie laeuft aus",
            "tuev": "TUEV faellig",
            "steuer": "Steuerfrist",
            "geburtstag": "Geburtstag",
            "sonstiges": "Erinnerung",
        }.get(category, "Termin")
