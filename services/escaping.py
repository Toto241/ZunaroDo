"""
Gemeinsame Escape-/Unescape-Hilfen fuer iCalendar und vCard.

Beide Formate teilen das gleiche Standard-Escaping (\\\\, \\,, \\;, \\n).
Die Logik lag bisher in services/ical.py und services/vcard.py
identisch zweimal - hier zentralisiert (Fix F5).
"""
from __future__ import annotations

import re


def escape_text(value) -> str:
    """Escaped Sonderzeichen fuer iCal- und vCard-TEXT-Felder."""
    if value is None:
        return ""
    return (str(value).replace("\\", "\\\\")
                       .replace("\n", "\\n")
                       .replace(",", "\\,")
                       .replace(";", "\\;"))


_UNESCAPE_RE = re.compile(r"\\([\\,;nN])")
_UNESCAPE_MAP = {"\\": "\\", ",": ",", ";": ";", "n": "\n", "N": "\n"}


def unescape_text(value: str) -> str:
    """Macht escape_text rueckgaengig - regex-basiert, kein NUL-Placeholder."""
    return _UNESCAPE_RE.sub(
        lambda m: _UNESCAPE_MAP.get(m.group(1), m.group(0)), value)
