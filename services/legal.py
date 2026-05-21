"""
Lokalisierte Rechtstexte mit Deutsch-Fallback.

Rechtstexte (Impressum, Datenschutz, AGB, Widerruf) sind rechtsverbindlich
und duerfen NICHT maschinell uebersetzt werden - jede Sprachfassung muss
anwaltlich geprueft werden (siehe legal/README.md). Dieses Modul liefert
nur die *Mechanik*: Es loest fuer eine gewuenschte Sprache die beste
verfuegbare Fassung auf und faellt sonst auf die deutsche Originalfassung
zurueck.

Ablage-Konvention:
    legal/<DOC>.md            -> deutsche Originalfassung (verbindlich)
    legal/<lang>/<DOC>.md     -> gepruefte Uebersetzung (optional)

`<DOC>` ist einer aus LEGAL_DOCS (Grossschreibung). `<lang>` ist ein
ISO-639-1-Code wie 'fr'.

Verwendung:
    text, lang = resolve_legal("DATENSCHUTZ", "fr")  # ('...', 'de' falls fehlt)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

_LEGAL_DIR = Path(__file__).resolve().parent.parent / "legal"

DEFAULT_LANGUAGE = "de"

#: Die vier Pflicht-/Standard-Dokumente (Dateiname ohne .md).
LEGAL_DOCS = ("IMPRESSUM", "DATENSCHUTZ", "AGB", "WIDERRUF")


def _base_path(doc: str) -> Path:
    return _LEGAL_DIR / f"{doc.upper()}.md"


def _translated_path(doc: str, language: str) -> Path:
    return _LEGAL_DIR / language / f"{doc.upper()}.md"


def legal_path(doc: str, language: str = DEFAULT_LANGUAGE) -> Optional[Path]:
    """
    Pfad zur besten verfuegbaren Fassung von `doc` fuer `language`.

    Reihenfolge: legal/<lang>/<DOC>.md -> legal/<DOC>.md (Deutsch).
    None, wenn nicht einmal die deutsche Originalfassung existiert.
    """
    if language and language != DEFAULT_LANGUAGE:
        cand = _translated_path(doc, language)
        if cand.is_file():
            return cand
    base = _base_path(doc)
    return base if base.is_file() else None


def resolve_legal(doc: str, language: str = DEFAULT_LANGUAGE
                  ) -> Optional[tuple[str, str]]:
    """
    Liefert (Text, effektive_Sprache) oder None, wenn das Dokument fehlt.
    Faellt eine Uebersetzung, wird die deutsche Fassung mit 'de' geliefert.
    """
    if language and language != DEFAULT_LANGUAGE:
        cand = _translated_path(doc, language)
        if cand.is_file():
            return cand.read_text(encoding="utf-8"), language
    base = _base_path(doc)
    if base.is_file():
        return base.read_text(encoding="utf-8"), DEFAULT_LANGUAGE
    return None


def available_translations(doc: str) -> list[str]:
    """
    Sprachen mit einer *eigenen* (uebersetzten) Fassung von `doc`.
    Die Default-Sprache ist immer dabei, wenn die Originaldatei existiert.
    """
    langs: list[str] = []
    if _base_path(doc).is_file():
        langs.append(DEFAULT_LANGUAGE)
    if _LEGAL_DIR.is_dir():
        for child in sorted(_LEGAL_DIR.iterdir()):
            if child.is_dir() and (child / f"{doc.upper()}.md").is_file():
                langs.append(child.name)
    return langs


def coverage() -> dict[str, list[str]]:
    """{DOC: [Sprachen mit eigener Fassung]} ueber alle LEGAL_DOCS.

    Den menschenlesbaren Report liefert `python -m tools.legal_status`.
    """
    return {doc: available_translations(doc) for doc in LEGAL_DOCS}
