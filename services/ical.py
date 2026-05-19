"""
iCalendar-Export und -Import (RFC 5545).

Bewusst handgeschrieben - kein externes 'icalendar'-Paket noetig.

Format-Vorsicht:
  - Keine Zeile darf 75 OKTETTE ueberschreiten (RFC 5545 zaehlt Bytes,
    nicht Code-Points). Multi-Byte-UTF-8-Sequenzen werden an
    Code-Point-Grenzen geteilt.
  - Sonderzeichen werden escaped (\\,, \\;, \\\\, \\n). Beim Unescape
    machen wir das in einem einzigen Regex-Pass, damit ein echtes
    NUL-Byte im Inhalt keinen Schaden anrichten kann.
  - DTSTART mit Uhrzeit + Z-Suffix wird in lokale Zeit konvertiert,
    damit das resultierende Date dem tatsaechlichen lokalen Datum
    entspricht.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

from models import CalendarEvent


_LINE_BYTE_LIMIT = 75


def _escape(value) -> str:
    """Escaped Sonderzeichen fuer iCal-TEXT-Felder. None wird zu ''."""
    if value is None:
        return ""
    return (str(value).replace("\\", "\\\\")
                       .replace("\n", "\\n")
                       .replace(",", "\\,")
                       .replace(";", "\\;"))


# Regex fuer Unescape: ein Backslash gefolgt von Schluesselzeichen
_UNESCAPE_RE = re.compile(r"\\([\\,;nN])")
_UNESCAPE_MAP = {"\\": "\\", ",": ",", ";": ";", "n": "\n", "N": "\n"}


def _unescape(value: str) -> str:
    """
    Macht das _escape rueckgaengig - in einem einzigen Pass per Regex.
    So tritt das frueher genutzte NUL-Byte-Placeholder-Verfahren nicht
    in Konflikt mit echten NUL-Bytes im Input.
    """
    return _UNESCAPE_RE.sub(
        lambda m: _UNESCAPE_MAP.get(m.group(1), m.group(0)), value)


def _fold(line: str) -> str:
    """
    RFC-5545-Line-Folding: keine Zeile laenger als 75 BYTES (UTF-8).
    Continuation-Lines beginnen mit einem Space.

    Wichtig: an Code-Point-Grenzen splitten, sonst zerschneiden wir
    Multi-Byte-Sequenzen. Wir laufen byte-weise rueckwaerts vom Limit
    weg, bis wir auf einem Anfangs-Byte landen (Bit-Muster 0xxxxxxx
    oder 11xxxxxx).
    """
    encoded = line.encode("utf-8")
    if len(encoded) <= _LINE_BYTE_LIMIT:
        return line
    chunks: list[str] = []
    remaining = encoded
    first = True
    while remaining:
        budget = _LINE_BYTE_LIMIT if first else _LINE_BYTE_LIMIT - 1
        if len(remaining) <= budget:
            chunks.append(remaining.decode("utf-8", errors="replace"))
            break
        # An Code-Point-Grenze splitten: budget rueckwaerts, bis ein
        # Anfangs-Byte erreicht ist (Continuation: 10xxxxxx).
        cut = budget
        while cut > 0 and (remaining[cut] & 0xC0) == 0x80:
            cut -= 1
        if cut == 0:
            cut = budget                            # Notbremse
        chunks.append(remaining[:cut].decode("utf-8", errors="replace"))
        remaining = remaining[cut:]
        first = False
    return "\r\n ".join(chunks)


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _format_rrule(days: int) -> str:
    """
    Liefert eine moeglichst aussagekraeftige RRULE.

    Beim Roundtrip Daily-Daily wirkt FREQ=DAILY;INTERVAL=7 identisch
    zu WEEKLY;INTERVAL=1 - aber andere Tools (Google Calendar) zeigen
    den Termin als 'jede Woche' statt 'alle 7 Tage'. Wir bevorzugen
    daher die hoechst-passende FREQ.
    """
    if days <= 0:
        return ""
    if days % 365 == 0:
        return f"RRULE:FREQ=YEARLY;INTERVAL={days // 365}"
    if days % 30 == 0:
        return f"RRULE:FREQ=MONTHLY;INTERVAL={days // 30}"
    if days % 7 == 0:
        return f"RRULE:FREQ=WEEKLY;INTERVAL={days // 7}"
    return f"RRULE:FREQ=DAILY;INTERVAL={days}"


def _atomic_write_text(target: Path, content: str) -> None:
    """Schreibt 'content' atomar: erst temp, dann replace."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)


def export_events(events: Iterable[CalendarEvent], target: Path,
                   calendar_name: str = "Alltagshelfer") -> int:
    """
    Schreibt iCal-Datei mit allen Events. Liefert Anzahl Eintraege.
    Atomar: ein Crash mittendrin laesst eine bereits vorhandene Datei
    unveraendert.
    """
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
            rrule = _format_rrule(event.recurrence_days)
            if rrule:
                lines.append(rrule)
        lines.append("END:VEVENT")
        count += 1
    lines.append("END:VCALENDAR")

    folded = [_fold(line) for line in lines]
    _atomic_write_text(target, "\r\n".join(folded) + "\r\n")
    return count


# ---------------------------------------------------------------------
#  Import
# ---------------------------------------------------------------------
def _unfold(raw: str) -> list[str]:
    """Continuation-Lines an die vorherige anhaengen."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    result: list[str] = []
    for line in raw.split("\n"):
        if line.startswith((" ", "\t")) and result:
            result[-1] += line[1:]
        else:
            result.append(line)
    return result


def _parse_dtstart(value: str) -> date | None:
    """
    Akzeptiert sowohl 'YYYYMMDD' (DATE) als auch 'YYYYMMDDTHHMMSS' /
    'YYYYMMDDTHHMMSSZ' (DATE-TIME). Bei UTC-Suffix wird in lokale Zeit
    konvertiert, damit das Datum dem tatsaechlichen lokalen Datum
    entspricht (M2).
    """
    value = value.strip()
    if not value:
        return None
    if "T" not in value:
        # Reines Datum
        return _parse_date_only(value)
    date_part, time_part = value.split("T", 1)
    base = _parse_date_only(date_part)
    if base is None:
        return None
    is_utc = time_part.endswith("Z")
    clean_time = time_part.rstrip("Z")
    if len(clean_time) < 6 or not clean_time[:6].isdigit():
        return base
    hh = int(clean_time[0:2])
    mm = int(clean_time[2:4])
    ss = int(clean_time[4:6])
    try:
        if is_utc:
            dt = datetime(base.year, base.month, base.day, hh, mm, ss,
                            tzinfo=timezone.utc)
            return dt.astimezone().date()         # lokale Zeitzone
        # Floating: einfach das Datum
        return base
    except ValueError:
        return base


def _parse_date_only(value: str) -> date | None:
    value = value.strip()
    if len(value) != 8 or not value.isdigit():
        return None
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except ValueError:
        return None


def _parse_rrule(value: str) -> int | None:
    """Liefert recurrence_days oder None bei ungueltigem Eintrag."""
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
        return interval * 30
    if freq == "YEARLY":
        return interval * 365
    return None


def import_events(source: Path) -> list[CalendarEvent]:
    """Liest eine iCal-Datei und liefert CalendarEvent-Objekte."""
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
                    title=title, due_date=due,
                    category=current.get("category") or "termin",
                    description=current.get("description") or "",
                    recurrence_days=current.get("rrule"),
                ))
            current = {}
            continue
        if not in_event:
            continue
        if ":" not in line:
            continue
        head, _, value = line.partition(":")
        key = head.split(";", 1)[0].upper()
        if key == "SUMMARY":
            current["summary"] = _unescape(value).strip()
        elif key == "DTSTART":
            current["dtstart"] = _parse_dtstart(value)
        elif key == "DESCRIPTION":
            current["description"] = _unescape(value)
        elif key == "CATEGORIES":
            cat = _unescape(value).split(",", 1)[0].strip().lower()
            current["category"] = cat if cat else "termin"
        elif key == "RRULE":
            current["rrule"] = _parse_rrule(value)
    return events
