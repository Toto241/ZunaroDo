"""
Store-Listing-Lokalisierungen fuer den Play Store.

Erzeugt/prueft die `localizations` in playstore.yml: Titel, Kurz- und
Volltext-Beschreibung je Play-Locale. Die kuratierten Uebersetzungen
decken die Hauptsprachen ab (EN/FR/ES/IT/NL/PL/PT zusaetzlich zu DE);
weitere Locales lassen sich ergaenzen.

Der Validator setzt die Play-Laengenlimits hart durch - ein zu langer
Titel wird sonst erst beim Upload abgelehnt.

Aufruf:
    python -m tools.store_listing --check         # playstore.yml pruefen
    python -m tools.store_listing --generate      # gemergte localizations (YAML)
    python -m tools.store_listing --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAYSTORE_YML = REPO_ROOT / "playstore.yml"

#: Play-Console-Laengenlimits (Zeichen).
LIMITS = {"title": 30, "short_description": 80, "full_description": 4000}
REQUIRED_FIELDS = ("title", "short_description", "full_description")

#: Kuratierte Listing-Uebersetzungen je Play-Locale. DE/EN liegen bereits
#: in playstore.yml; diese werden beim Generieren nicht ueberschrieben.
CURATED: dict[str, dict[str, str]] = {
    "fr-FR": {
        "title": "Alltagshelfer",
        "short_description": "Contrats, rendez-vous, finances, famille - tout en local, sans cloud.",
        "full_description": (
            "Alltagshelfer est un assistant respectueux de la vie privee pour "
            "les contrats, les rendez-vous, les finances et l'organisation du "
            "foyer. Toutes les donnees restent en local sur l'appareil - sans "
            "suivi, sans publicite."),
    },
    "es-ES": {
        "title": "Alltagshelfer",
        "short_description": "Contratos, citas, finanzas, familia: todo local, sin nube obligatoria.",
        "full_description": (
            "Alltagshelfer es un asistente respetuoso con la privacidad para "
            "contratos, citas, finanzas y organizacion del hogar. Todos los "
            "datos permanecen localmente en el dispositivo: sin seguimiento, "
            "sin anuncios."),
    },
    "it-IT": {
        "title": "Alltagshelfer",
        "short_description": "Contratti, appuntamenti, finanze, famiglia - tutto in locale, no cloud.",
        "full_description": (
            "Alltagshelfer e un assistente rispettoso della privacy per "
            "contratti, appuntamenti, finanze e gestione della casa. Tutti i "
            "dati restano in locale sul dispositivo - senza tracciamento, "
            "senza pubblicita."),
    },
    "nl-NL": {
        "title": "Alltagshelfer",
        "short_description": "Contracten, afspraken, financien, gezin - lokaal, zonder cloud.",
        "full_description": (
            "Alltagshelfer is een privacyvriendelijke assistent voor "
            "contracten, afspraken, financien en huishoudplanning. Alle "
            "gegevens blijven lokaal op het apparaat - geen tracking, geen "
            "advertenties."),
    },
    "pl-PL": {
        "title": "Alltagshelfer",
        "short_description": "Umowy, terminy, finanse, rodzina - wszystko lokalnie, bez chmury.",
        "full_description": (
            "Alltagshelfer to przyjazny prywatnosci asystent do umow, "
            "terminow, finansow i organizacji domu. Wszystkie dane pozostaja "
            "lokalnie na urzadzeniu - bez sledzenia, bez reklam."),
    },
    "pt-PT": {
        "title": "Alltagshelfer",
        "short_description": "Contratos, compromissos, financas, familia - tudo local, sem nuvem.",
        "full_description": (
            "Alltagshelfer e um assistente que respeita a privacidade para "
            "contratos, compromissos, financas e organizacao da casa. Todos os "
            "dados permanecem localmente no dispositivo - sem rastreio, sem "
            "publicidade."),
    },
}


def validate_localizations(localizations: dict) -> list[tuple[str, str, str]]:
    """
    Prueft jede Locale auf Pflichtfelder + Play-Laengenlimits.
    Liefert (severity, path, message)-Tupel; severity in {error, warning}.
    """
    issues: list[tuple[str, str, str]] = []
    if not localizations:
        issues.append(("error", "localizations", "Keine Lokalisierung definiert."))
        return issues
    for loc, fields in localizations.items():
        fields = fields or {}
        for fld in REQUIRED_FIELDS:
            val = fields.get(fld)
            if not val:
                issues.append(("error", f"localizations.{loc}.{fld}",
                               "Pflichtfeld fehlt oder leer."))
                continue
            limit = LIMITS[fld]
            if len(val) > limit:
                issues.append((
                    "error", f"localizations.{loc}.{fld}",
                    f"{len(val)} Zeichen > Limit {limit}."))
    return issues


def generate_localizations(base: dict | None = None) -> dict:
    """
    Mergt die kuratierten Uebersetzungen in eine bestehende Basis
    (z.B. die DE/EN-Eintraege aus playstore.yml). Vorhandene Locales
    werden NICHT ueberschrieben.
    """
    out: dict[str, dict[str, str]] = dict(base or {})
    for loc, fields in CURATED.items():
        if loc not in out:
            out[loc] = dict(fields)
    return out


def _load_localizations() -> dict:
    if not PLAYSTORE_YML.is_file():
        return {}
    text = PLAYSTORE_YML.read_text(encoding="utf-8")
    try:
        import yaml
        data = yaml.safe_load(text) or {}
    except ImportError:                               # pragma: no cover
        data = json.loads(text)
    return data.get("localizations") or {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Store-Listing-Lokalisierungen erzeugen/pruefen.")
    parser.add_argument("--check", action="store_true",
                        help="playstore.yml-localizations pruefen (Exit 1 bei Fehler).")
    parser.add_argument("--generate", action="store_true",
                        help="DE/EN-Basis + kuratierte Sprachen ausgeben.")
    parser.add_argument("--json", action="store_true",
                        help="Ausgabe als JSON.")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")     # type: ignore[union-attr]
        except (AttributeError, ValueError):         # pragma: no cover
            pass

    if args.check:
        issues = validate_localizations(_load_localizations())
        errors = [i for i in issues if i[0] == "error"]
        for sev, path, msg in issues:
            stream = sys.stderr if sev == "error" else sys.stdout
            print(f"[{sev.upper()}] {path}: {msg}", file=stream)
        if not issues:
            print("OK: Alle Store-Listings erfuellen Pflichtfelder + Limits.")
        return 1 if errors else 0

    merged = generate_localizations(_load_localizations())
    if args.json:
        print(json.dumps({"localizations": merged}, indent=2, ensure_ascii=False))
    else:
        try:
            import yaml
            print(yaml.safe_dump({"localizations": merged}, sort_keys=False,
                                 allow_unicode=True, indent=2, width=92))
        except ImportError:                           # pragma: no cover
            print(json.dumps({"localizations": merged}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(main())
