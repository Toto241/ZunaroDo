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


# ---------------------------------------------------------------------
#  Import
# ---------------------------------------------------------------------
def _unescape(value: str) -> str:
    """Kehrt das _escape aus dem Export-Pfad um."""
    # Reihenfolge wichtig: erst \\ -> placeholder, dann andere, dann zurueck
    out = (value.replace("\\\\", "\x00")
                .replace("\\n", "\n")
                .replace("\\,", ",")
                .replace("\\;", ";")
                .replace("\x00", "\\"))
    return out


def _unfold(raw: str) -> list[str]:
    """RFC-5545-Line-Unfolding: Zeilen, die mit Whitespace beginnen, an die
    vorherige anhaengen."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    result: list[str] = []
    for line in raw.split("\n"):
        if line.startswith((" ", "\t")) and result:
            result[-1] += line[1:]
        else:
            result.append(line)
    return result


def _parse_date(value: str) -> date | None:
    """Akzeptiert sowohl 'YYYYMMDD' (DATE) als auch 'YYYYMMDDTHHMMSSZ' (DATE-TIME)."""
    value = value.strip()
    if not value:
        return None
    base = value.split("T", 1)[0]
    if len(base) != 8 or not base.isdigit():
        return None
    try:
        return date(int(base[:4]), int(base[4:6]), int(base[6:8]))
    except ValueError:
        return None


def _parse_rrule(value: str) -> int | None:
    """Extrahiert recurrence_days aus RRULE. Akzeptiert FREQ=DAILY/WEEKLY/
    MONTHLY/YEARLY mit optionalem INTERVAL."""
    parts = {}
    for piece in value.split(";"):
        if "=" in piece:
            k, v = piece.split("=", 1)
            parts[k.strip().upper()] = v.strip()
    freq = parts.get("FREQ", "").upper()
    try:
        interval = int(parts.get("INTERVAL", "1"))
    except ValueError:
        interval = 1
    if interval <= 0:
        return None
    if freq == "DAILY":
        return interval
    if freq == "WEEKLY":
        return interval * 7
    if freq == "MONTHLY":
        return interval * 30        # naehe-rungsweise (kein echter Kalender)
    if freq == "YEARLY":
        return interval * 365
    return None


def import_events(source: Path) -> list[CalendarEvent]:
    """
    Liest eine iCal-Datei und liefert CalendarEvent-Objekte.

    Bewusst nachsichtig: unbekannte Felder werden ignoriert, Bloecke
    ohne SUMMARY oder DTSTART uebersprungen. Zeilen-Folding und das
    Standard-Escaping (\\n, \\,, \\;, \\\\) werden korrekt aufgeloest.
    """
    if not source.exists():
        raise FileNotFoundError(f"iCal-Datei '{source}' nicht gefunden")
    raw = source.read_text(encoding="utf-8")
    lines = _unfold(raw)

    events: list[CalendarEvent] = []
    in_event = False
    current: dict = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.upper() == "BEGIN:VEVENT":
            in_event = True
            current = {}
            continue
        if line.upper() == "END:VEVENT":
            in_event = False
            title = current.get("summary")
            due = current.get("dtstart")
            if title and due:
                events.append(CalendarEvent(
                    title=title,
                    due_date=due,
                    category=current.get("category") or "termin",
                    description=current.get("description") or "",
                    recurrence_days=current.get("rrule"),
                ))
            current = {}
            continue
        if not in_event:
            continue
        # Property-Zeilen: KEY[;PARAMS]:VALUE
        if ":" not in line:
            continue
        head, _, value = line.partition(":")
        key = head.split(";", 1)[0].upper()
        if key == "SUMMARY":
            current["summary"] = _unescape(value).strip()
        elif key == "DTSTART":
            current["dtstart"] = _parse_date(value)
        elif key == "DESCRIPTION":
            current["description"] = _unescape(value)
        elif key == "CATEGORIES":
            # Erste Kategorie reicht, wir trennen nicht weiter
            cat = _unescape(value).split(",", 1)[0].strip().lower()
            current["category"] = cat if cat else "termin"
        elif key == "RRULE":
            current["rrule"] = _parse_rrule(value)
    return events
