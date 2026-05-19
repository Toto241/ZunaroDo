"""
vCard-Export (RFC 6350, Version 3.0).

Schreibt soziale Kontakte als .vcf-Datei. Das Format ist von praktisch
allen Adressbuechern lesbar.

Wir exportieren bewusst nur die Felder, die wir auch fuehren:
  - FN (Display Name)
  - N (strukturierter Name)
  - NOTE (Notizen + Wunsch-Rhythmus + letztes Kontaktdatum)
  - CATEGORIES (Beziehung)

Telefon/E-Mail/Adresse fehlen in der App, daher auch im Export.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from models import SocialContact


def _escape(value: str) -> str:
    return (value.replace("\\", "\\\\")
                  .replace("\n", "\\n")
                  .replace(",", "\\,")
                  .replace(";", "\\;"))


def _unescape(value: str) -> str:
    out = (value.replace("\\\\", "\x00")
                 .replace("\\n", "\n")
                 .replace("\\,", ",")
                 .replace("\\;", ";")
                 .replace("\x00", "\\"))
    return out


def export_contacts(contacts: Iterable[SocialContact],
                     target: Path) -> int:
    """Schreibt vCard-Datei mit allen Kontakten. Liefert Anzahl."""
    target.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    count = 0
    for c in contacts:
        # Notiz zusammensetzen: vorhandene Notiz + Rhythmus + Last-Contact
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
            # N: Familienname;Vorname;... -> wir kennen nur einen Namen
            f"N:{_escape(c.name)};;;;",
            f"NOTE:{note}",
        ])
        if c.relation:
            lines.append(f"CATEGORIES:{_escape(c.relation)}")
        # UID damit ein erneuter Import vorhandene Kontakte aktualisiert
        lines.append(f"UID:alltagshelfer-social-{c.id or 'x'}")
        lines.append("END:VCARD")
        count += 1
    target.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return count


# ---------------------------------------------------------------------
#  Import
# ---------------------------------------------------------------------
def import_contacts(source: Path) -> list[SocialContact]:
    """
    Liest eine vCard-Datei und liefert SocialContact-Objekte.

    Bewusst nachsichtig: unbekannte Felder werden ignoriert, Eintraege
    ohne FN/N werden uebersprungen. Folding (Continuation mit Leading-
    Space) wird beruecksichtigt.
    """
    if not source.exists():
        raise FileNotFoundError(f"vCard-Datei '{source}' nicht gefunden")
    raw = source.read_text(encoding="utf-8")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Folding
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
                contacts.append(SocialContact(
                    name=name,
                    relation=current.get("relation", ""),
                    cadence_days=current.get("cadence", 30),
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
            # N: Familienname;Vorname;... - wir nutzen den ersten Teil
            first = _unescape(value).split(";")[0].strip()
            if first and "n" not in current:
                current["n"] = first
        elif key == "NOTE":
            current["notes"] = _unescape(value).strip()
            # Wenn die NOTE einen Rhythmus-Hinweis aus unserem Export
            # enthaelt, lesen wir den heraus.
            import re
            m = re.search(r"Rhythmus:\s*alle\s+(\d+)\s+Tage",
                           current["notes"])
            if m:
                try:
                    current["cadence"] = int(m.group(1))
                except ValueError:
                    pass
        elif key == "CATEGORIES":
            relation = _unescape(value).split(",", 1)[0].strip()
            current["relation"] = relation
    return contacts
