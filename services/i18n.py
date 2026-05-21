"""
Leichtes i18n-Scaffolding fuer den Alltagshelfer.

Bewusst minimal: ein in JSON gepflegter Key-Value-Speicher pro Sprache.
'de' ist die Default-Sprache und enthaelt den vollstaendigen Satz an
Strings. Weitere Sprachen liefern eine Teil- oder Vollmenge; fehlende
oder leere Schluessel fallen auf die Default-Sprache zurueck (und zuletzt
auf den Key selbst, damit ein im Code vergessener Eintrag sichtbar
bleibt, aber nichts crasht).

Unterstuetzt werden die 24 EU-Amtssprachen. Welche davon wie weit
uebersetzt sind, zeigt `python -m tools.i18n_sync --coverage`.

Verwendung:
    i18n = I18n("de")
    label = i18n.t("tab.dashboard")

Sprachwahl:
    - Die App liest 'i18n.language' aus den Settings (siehe
      services/config.py). Default ist "de".
    - Steht dort der Sonderwert "auto", wird die Geraetesprache via
      `detect_device_language()` ermittelt und - falls unterstuetzt -
      verwendet (sonst Default).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional


# Verzeichnis liegt neben dem services/-Paket
_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"

#: Sonderwert in den Settings: "erkenne die Geraetesprache".
AUTO = "auto"

#: Die 24 EU-Amtssprachen mit ihrem nativen Anzeigenamen. Reihenfolge:
#: Default (de) zuerst, dann alphabetisch nach Code - so ist der
#: Sprachumschalter stabil sortiert und 'Deutsch' steht oben.
EU_LANGUAGES: dict[str, str] = {
    "de": "Deutsch",
    "bg": "Български",
    "cs": "Čeština",
    "da": "Dansk",
    "el": "Ελληνικά",
    "en": "English",
    "es": "Español",
    "et": "Eesti",
    "fi": "Suomi",
    "fr": "Français",
    "ga": "Gaeilge",
    "hr": "Hrvatski",
    "hu": "Magyar",
    "it": "Italiano",
    "lt": "Lietuvių",
    "lv": "Latviešu",
    "mt": "Malti",
    "nl": "Nederlands",
    "pl": "Polski",
    "pt": "Português",
    "ro": "Română",
    "sk": "Slovenčina",
    "sl": "Slovenščina",
    "sv": "Svenska",
}


def normalize_language(raw: str | None) -> str | None:
    """
    Reduziert einen beliebigen Locale-String auf den 2-Buchstaben-Code.

    Akzeptiert Formen wie 'de', 'de_DE', 'de-DE', 'de_DE.UTF-8',
    'C', '' und liefert den ISO-639-1-Code in Kleinbuchstaben oder
    None, wenn nichts Brauchbares drinsteht.
    """
    if not raw:
        return None
    # Trenner vereinheitlichen und Encoding-Suffix abschneiden.
    token = raw.strip().replace("-", "_").split(".")[0].split("@")[0]
    if not token:
        return None
    primary = token.split("_")[0].lower()
    # 'C' / 'POSIX' sind keine echten Sprachen.
    if primary in ("c", "posix") or len(primary) != 2:
        return None
    return primary


def _detect_android_language() -> Optional[str]:
    """Geraetesprache auf Android via java.util.Locale (pyjnius)."""
    try:
        from jnius import autoclass  # type: ignore
    except Exception:
        return None
    try:
        Locale = autoclass("java.util.Locale")
        return normalize_language(Locale.getDefault().getLanguage())
    except Exception:                                # pragma: no cover
        return None


def _detect_desktop_language() -> Optional[str]:
    """Geraetesprache auf Desktop: Env-Vars zuerst, dann stdlib `locale`."""
    # Reihenfolge wie bei GNU gettext: LANGUAGE kann eine Liste sein.
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var)
        if val:
            # LANGUAGE darf 'de:en:fr' sein - erstes Element zaehlt.
            first = val.split(":")[0]
            code = normalize_language(first)
            if code:
                return code
    try:
        import locale
        # getlocale ist seit 3.11 die nicht-deprecated Variante.
        loc = locale.getlocale()[0] or locale.getdefaultlocale()[0]  # type: ignore[attr-defined]
        return normalize_language(loc)
    except Exception:                                # pragma: no cover
        return None


def detect_device_language() -> Optional[str]:
    """
    Ermittelt die Sprache des Geraets/OS.

    Android wird zuerst versucht (pyjnius), dann der Desktop-Pfad
    (Umgebungsvariablen + stdlib `locale`). Liefert einen
    2-Buchstaben-Code oder None, wenn nichts erkennbar ist. Der
    Rueckgabewert ist *nicht* notwendig eine unterstuetzte Sprache -
    dafuer ist `resolve_language()` zustaendig.
    """
    return _detect_android_language() or _detect_desktop_language()


def resolve_language(
    preferred: str | None,
    *,
    supported: "tuple[str, ...] | frozenset[str] | None" = None,
    default: str = "de",
) -> str:
    """
    Bestimmt die effektiv zu nutzende Sprache.

    - `preferred == "auto"` (case-insensitive): Geraetesprache erkennen.
    - sonst wird `preferred` normalisiert.
    Faellt der ermittelte Code nicht in `supported`, wird `default`
    zurueckgegeben. So bekommt der Aufrufer garantiert eine unterstuetzte
    Sprache.
    """
    sup = frozenset(supported) if supported is not None else frozenset(EU_LANGUAGES)
    if preferred is not None and preferred.strip().lower() == AUTO:
        code = detect_device_language()
    else:
        code = normalize_language(preferred)
    if code and code in sup:
        return code
    return default


class I18n:
    """Sehr schlanker Ueenrsetzungs-Lookup mit EU-Sprachunterstuetzung."""

    DEFAULT_LANGUAGE = "en"
    #: Alle Sprachen, fuer die ein Locale-File existieren *darf*.
    SUPPORTED_LANGUAGES = tuple(EU_LANGUAGES.keys())

    def __init__(self, language: str = "de"):
        # 'auto' und unbekannte Codes werden hier sauber aufgeloest.
        self.language = resolve_language(
            language,
            supported=self.SUPPORTED_LANGUAGES,
            default=self.DEFAULT_LANGUAGE,
        )
        self._strings = self._load(self.language)
        # Fallback: Defaultsprache fuer Schluessel, die in der gewaehlten
        # Sprache fehlen.
        self._fallback = (self._load(self.DEFAULT_LANGUAGE)
                           if self.language != self.DEFAULT_LANGUAGE
                           else {})

    def t(self, key: str, default: Optional[str] = None) -> str:
        """Liefert die Uebersetzung. Reihenfolge: lang -> default-lang -> arg -> key.

        Leere Strings gelten als 'nicht uebersetzt' und loesen denselben
        Fallback aus wie ein fehlender Key.
        """
        if key in self._strings and self._strings[key]:
            return self._strings[key]
        if key in self._fallback and self._fallback[key]:
            return self._fallback[key]
        return default if default is not None else key

    @classmethod
    def available_languages(cls) -> list[tuple[str, str]]:
        """
        Sprachen, fuer die tatsaechlich ein Locale-File existiert, als
        (code, nativer_name)-Liste in der Reihenfolge von EU_LANGUAGES.

        Eignet sich direkt als Datenquelle fuer einen Sprachumschalter.
        Die Default-Sprache ist immer dabei (sie liefert alle Keys).
        """
        out: list[tuple[str, str]] = []
        for code, name in EU_LANGUAGES.items():
            if code == cls.DEFAULT_LANGUAGE or (_LOCALES_DIR / f"{code}.json").exists():
                out.append((code, name))
        return out

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
