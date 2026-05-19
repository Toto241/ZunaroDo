"""
iCalendar-Export (RFC 5545).

Schreibt Kalender-Eintraege als .ics-Datei, damit sie in jeden gaengigen
Kalender (Google, Apple, Outlook, Thunderbird) importiert werden koennen.

Bewusst handgeschrieben - kein externes 'icalendar'-Paket noetig.
Format-Vorsicht: keine Zeile darf laenger als 75 Oktette sein, lange
Texte werden umgebrochen. Sonderzeichen in TEXT-Feldern werden
escaped (Komma, Semikolon, Backslash, Zeilenumbruch).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

from models import CalendarEvent


_LINE_LIMIT = 75


def _escape(value: str) -> str:
    """Escaped Sonderzeichen fuer iCal-TEXT-Felder."""
    return (value.replace("\\", "\\\\")
                  .replace("\n", "\\n")
                  .replace(",", "\\,")
                  .replace(";", "\\;"))


def _fold(line: str) -> str:
    """Lange Zeilen folden: weitere Zeilen beginnen mit einem Space."""
    if len(line) <= _LINE_LIMIT:
        return line
    chunks = [line[:_LINE_LIMIT]]
    rest = line[_LINE_LIMIT:]
    while rest:
        chunks.append(" " + rest[:_LINE_LIMIT - 1])
        rest = rest[_LINE_LIMIT - 1:]
    return "\r\n".join(chunks)


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def export_events(events: Iterable[CalendarEvent], target: Path,
                   calendar_name: str = "Alltagshelfer") -> int:
    """
    Schreibt iCal-Datei mit allen Events. Liefert Anzahl Eintraege.

    Wiederkehrende Eintraege erhalten eine RRULE (DAILY mit INTERVAL).
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Alltagshelfer//Calendar Export//DE",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]
    stamp = _utc_stamp()
    count = 0
    for event in events:
        uid = f"alltagshelfer-{event.id or 'x'}-{event.due_date.isoformat()}"
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{stamp}")
        lines.append(f"DTSTART;VALUE=DATE:{_format_date(event.due_date)}")
        lines.append(f"SUMMARY:{_escape(event.title)}")
        if event.description:
            lines.append(f"DESCRIPTION:{_escape(event.description)}")
        if event.category:
            lines.append(f"CATEGORIES:{_escape(event.category)}")
        if event.recurrence_days and event.recurrence_days > 0:
            lines.append(
                f"RRULE:FREQ=DAILY;INTERVAL={int(event.recurrence_days)}")
        lines.append("END:VEVENT")
        count += 1
    lines.append("END:VCALENDAR")

    folded = [_fold(line) for line in lines]
    # iCal verlangt CRLF
    target.write_text("\r\n".join(folded) + "\r\n", encoding="utf-8")
    return count
