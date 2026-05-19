"""
Leichtes i18n-Scaffolding fuer den Alltagshelfer.

Bewusst minimal: ein in JSON gepflegter Key-Value-Speicher pro Sprache.
'de' ist die Default-Sprache und enthaelt den Grossteil der Strings;
'en' liefert eine pragmatische Englisch-Fassung fuer die wichtigsten
Labels. Unbekannte Schluessel fallen auf den Key zurueck (damit ein
fehlender Eintrag im Code sichtbar bleibt, aber nichts crasht).

Verwendung:
    i18n = I18n("de")
    label = i18n.t("tab.dashboard")

Spracheinstellung wird ueber 'i18n.language' aus den App-Settings
gesteuert. Default: "de".
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


# Verzeichnis liegt neben dem services/-Paket
_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


class I18n:
    """Sehr schlanker Uebersetzungs-Lookup."""

    DEFAULT_LANGUAGE = "de"
    SUPPORTED_LANGUAGES = ("de", "en")

    def __init__(self, language: str = "de"):
        self.language = language if language in self.SUPPORTED_LANGUAGES \
            else self.DEFAULT_LANGUAGE
        self._strings = self._load(self.language)
        # Fallback: Defaultsprache fuer Schluessel, die in der gewaehlten
        # Sprache fehlen.
        self._fallback = (self._load(self.DEFAULT_LANGUAGE)
                           if self.language != self.DEFAULT_LANGUAGE
                           else {})

    def t(self, key: str, default: Optional[str] = None) -> str:
        """Liefert die Uebersetzung. Reihenfolge: lang -> default -> key."""
        if key in self._strings:
            return self._strings[key]
        if key in self._fallback:
            return self._fallback[key]
        return default if default is not None else key

    @staticmethod
    def _load(language: str) -> dict[str, str]:
        path = _LOCALES_DIR / f"{language}.json"
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {k: str(v) for k, v in data.items() if isinstance(k, str)}
