"""
vCard-Export und -Import (RFC 6350, Version 3.0).

Schreibt soziale Kontakte als .vcf-Datei. Format ist von praktisch
allen Adressbuechern lesbar.

Wir exportieren bewusst nur die Felder, die wir auch fuehren:
  - FN (Display Name)
  - N (strukturierter Name)
  - NOTE (Notizen + Wunsch-Rhythmus + letztes Kontaktdatum)
  - CATEGORIES (Beziehung)

Import: cadence_days wird auf >=1 geclampt, um Endlos-„heute-faellig"-
Loops zu vermeiden.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from models import SocialContact


def _escape(value) -> str:
    if value is None:
        return ""
    return (str(value).replace("\\", "\\\\")
                       .replace("\n", "\\n")
                       .replace(",", "\\,")
                       .replace(";", "\\;"))


# Regex-basiertes Unescape - keine NUL-Byte-Placeholder noetig
_UNESCAPE_RE = re.compile(r"\\([\\,;nN])")
_UNESCAPE_MAP = {"\\": "\\", ",": ",", ";": ";", "n": "\n", "N": "\n"}


def _unescape(value: str) -> str:
    return _UNESCAPE_RE.sub(
        lambda m: _UNESCAPE_MAP.get(m.group(1), m.group(0)), value)


def _atomic_write_text(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)


def export_contacts(contacts: Iterable[SocialContact],
                     target: Path) -> int:
    """Schreibt vCard-Datei mit allen Kontakten. Liefert Anzahl."""
    lines: list[str] = []
    count = 0
    for c in contacts:
        notes_parts: list[str] = []
        if c.notes:
            notes_parts.append(c.notes)
        notes_parts.append(f"Rhythmus: alle {c.cadence_days} Tage")
        if c.last_contacted:
            notes_parts.append(
                f"Zuletzt kontaktiert: {c.last_contacted.isoformat()}")
        note = _escape(" | ".join(notes_parts))

        lines.extend([
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{_escape(c.name)}",
            f"N:{_escape(c.name)};;;;",
            f"NOTE:{note}",
        ])
        if c.relation:
            lines.append(f"CATEGORIES:{_escape(c.relation)}")
        lines.append(f"UID:alltagshelfer-social-{c.id or 'x'}")
        lines.append("END:VCARD")
        count += 1
    _atomic_write_text(target, "\r\n".join(lines) + "\r\n")
    return count


# ---------------------------------------------------------------------
#  Import
# ---------------------------------------------------------------------
_RHYTHM_RE = re.compile(r"Rhythmus:\s*alle\s+(\d+)\s+Tage", re.IGNORECASE)


def import_contacts(source: Path) -> list[SocialContact]:
    """Liest eine vCard-Datei und liefert SocialContact-Objekte."""
    if not source.exists():
        raise FileNotFoundError(f"vCard-Datei '{source}' nicht gefunden")
    raw = source.read_text(encoding="utf-8")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    unfolded: list[str] = []
    for line in raw.split("\n"):
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)

    contacts: list[SocialContact] = []
    in_card = False
    current: dict = {}
    for line in unfolded:
        line = line.strip()
        if not line:
            continue
        if line.upper() == "BEGIN:VCARD":
            in_card = True
            current = {}
            continue
        if line.upper() == "END:VCARD":
            in_card = False
            name = current.get("fn") or current.get("n")
            if name:
                # Rhythmus immer mindestens 1 - sonst Endlos-Spam.
                cadence = max(1, current.get("cadence", 30))
                contacts.append(SocialContact(
                    name=name,
                    relation=current.get("relation", ""),
                    cadence_days=cadence,
                    notes=current.get("notes", ""),
                ))
            current = {}
            continue
        if not in_card:
            continue
        if ":" not in line:
            continue
        head, _, value = line.partition(":")
        key = head.split(";", 1)[0].upper()
        if key == "FN":
            current["fn"] = _unescape(value).strip()
        elif key == "N":
            first = _unescape(value).split(";")[0].strip()
            if first and "n" not in current:
                current["n"] = first
        elif key == "NOTE":
            current["notes"] = _unescape(value).strip()
            m = _RHYTHM_RE.search(current["notes"])
            if m:
                try:
                    current["cadence"] = int(m.group(1))
                except ValueError:
                    pass
        elif key == "CATEGORIES":
            relation = _unescape(value).split(",", 1)[0].strip()
            current["relation"] = relation
    return contacts
