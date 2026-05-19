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
