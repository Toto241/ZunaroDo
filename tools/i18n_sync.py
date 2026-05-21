"""
i18n-Wartungswerkzeug fuer Alltagshelfer/ZunaroDo.

Haelt die Locale-Dateien unter locales/ konsistent zur Default-Sprache
(de.json) und gibt einen Ueberblick, wie weit die einzelnen EU-Sprachen
uebersetzt sind.

Aufruf:

    python -m tools.i18n_sync --check       # CI: Parität + Pflicht-Keys
    python -m tools.i18n_sync --coverage    # Tabelle: Abdeckung je Sprache
    python -m tools.i18n_sync --scaffold    # fehlende Locale-Dateien anlegen
    python -m tools.i18n_sync --json        # maschinenlesbar

Regeln, die `--check` hart durchsetzt (Exit 1 bei Verstoss):
  * keine Sprache enthaelt Keys, die de.json nicht kennt (Tippfehler-Schutz)
  * jede vorhandene Locale-Datei deckt mindestens den CORE_KEYS-Satz ab
    (Navigation + Buttons), damit der Sprachumschalter nie auf Deutsch
    durchfaellt fuer die sichtbarsten Elemente
  * de.json selbst ist vollstaendig (alle CORE_KEYS vorhanden)

Der Checker ist bewusst ohne Drittabhaengigkeiten - er laeuft in der CI
ohne Setup.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.i18n import EU_LANGUAGES

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = REPO_ROOT / "locales"
DEFAULT_LANG = "de"

#: Schluessel, die *jede* Locale-Datei zwingend enthalten muss. Das ist
#: der sichtbarste Teil der UI (Navigation + universelle Buttons): Hier
#: faellt eine Luecke sofort auf, also lassen wir keinen Fallback zu.
#: Vollstaendige Sprachen (FR/ES/IT/NL/PL/PT) gehen darueber hinaus.
CORE_KEYS: tuple[str, ...] = (
    "app.title",
    # Bottom-Navigation / Tabs
    "tab.dashboard", "tab.contracts", "tab.family", "tab.finance",
    "tab.calendar", "tab.social", "tab.inbox", "tab.search",
    "tab.settings", "tab.statistics", "tab.data",
    # Universelle Buttons
    "common.save", "common.cancel", "common.delete", "common.confirm",
    "common.close", "common.edit", "common.add", "common.send",
    "common.refresh",
    # Settings-Einstieg (Sprachumschalter lebt hier)
    "settings.title", "settings.save",
)


def _load(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:                # pragma: no cover
        raise SystemExit(f"FEHLER: {path.name} ist kein gueltiges JSON: {exc}")
    return {str(k): str(v) for k, v in data.items()}


def load_default() -> dict[str, str]:
    return _load(LOCALES_DIR / f"{DEFAULT_LANG}.json")


def locale_path(code: str) -> Path:
    return LOCALES_DIR / f"{code}.json"


def existing_locales() -> list[str]:
    """Sprachcodes, fuer die eine Locale-Datei existiert (inkl. Default)."""
    return [c for c in EU_LANGUAGES if locale_path(c).exists()]


# ---------------------------------------------------------------------------
# Auswertung
# ---------------------------------------------------------------------------

def analyze() -> dict:
    """Sammelt Parität-, Coverage- und Core-Key-Status fuer alle Sprachen."""
    default = load_default()
    default_keys = set(default)
    core = set(CORE_KEYS)

    languages: dict[str, dict] = {}
    for code in EU_LANGUAGES:
        path = locale_path(code)
        if not path.exists():
            languages[code] = {
                "exists": False,
                "translated": 0,
                "total": len(default_keys),
                "coverage": 0.0,
                "extra_keys": [],
                "missing_core": sorted(core),
            }
            continue
        strings = _load(path)
        keys = set(strings)
        extra = sorted(keys - default_keys)
        # 'uebersetzt' = vorhandener Key (Default-Sprache zaehlt komplett).
        translated = len(keys & default_keys) if code != DEFAULT_LANG else len(default_keys)
        missing_core = sorted(core - keys) if code != DEFAULT_LANG else []
        languages[code] = {
            "exists": True,
            "translated": translated,
            "total": len(default_keys),
            "coverage": round(translated / len(default_keys) * 100, 1) if default_keys else 100.0,
            "extra_keys": extra,
            "missing_core": missing_core,
        }
    return {
        "default_lang": DEFAULT_LANG,
        "default_key_count": len(default_keys),
        "missing_core_in_default": sorted(core - default_keys),
        "languages": languages,
    }


def check(report: dict) -> list[str]:
    """Liefert die Liste der Regelverstoesse (leer = alles ok)."""
    errors: list[str] = []
    if report["missing_core_in_default"]:
        errors.append(
            f"de.json fehlen CORE_KEYS: {report['missing_core_in_default']}")
    for code, info in report["languages"].items():
        if not info["exists"]:
            continue
        if info["extra_keys"]:
            errors.append(
                f"{code}.json hat Keys, die de.json nicht kennt: "
                f"{info['extra_keys']}")
        if info["missing_core"]:
            errors.append(
                f"{code}.json fehlen Pflicht-CORE_KEYS: {info['missing_core']}")
    return errors


def scaffold() -> list[str]:
    """
    Legt fuer jede EU-Sprache ohne Datei ein leeres `{}`-Locale an.
    Leere Dateien fallen via I18n komplett auf Deutsch zurueck - das ist
    der bewusst gewuenschte Startzustand vor der ersten Uebersetzung.
    Liefert die Liste der neu angelegten Codes.
    """
    created: list[str] = []
    for code in EU_LANGUAGES:
        if code == DEFAULT_LANG:
            continue
        path = locale_path(code)
        if path.exists():
            continue
        path.write_text("{}\n", encoding="utf-8")
        created.append(code)
    return created


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

def format_coverage(report: dict) -> str:
    lines = [
        f"Locale-Coverage (Basis: {DEFAULT_LANG}.json, "
        f"{report['default_key_count']} Keys)",
        "=" * 60,
        f"{'Sprache':<24}{'Datei':<7}{'Keys':>8}{'Abdeckung':>12}",
        "-" * 60,
    ]
    for code, name in EU_LANGUAGES.items():
        info = report["languages"][code]
        has = "ja" if info["exists"] else "-"
        cov = f"{info['coverage']:.1f}%"
        label = f"{code} {name}"
        lines.append(
            f"{label:<24}{has:<7}"
            f"{info['translated']:>4}/{info['total']:<3}{cov:>12}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="i18n-Wartung: Parität, Coverage, Scaffolding.")
    parser.add_argument("--check", action="store_true",
                        help="Parität + Pflicht-Keys pruefen (Exit 1 bei Verstoss).")
    parser.add_argument("--coverage", action="store_true",
                        help="Abdeckungstabelle je Sprache ausgeben.")
    parser.add_argument("--scaffold", action="store_true",
                        help="Fehlende Locale-Dateien als leeres {} anlegen.")
    parser.add_argument("--json", action="store_true",
                        help="Report maschinenlesbar als JSON.")
    args = parser.parse_args(argv)

    # Native Sprachnamen (Kyrillisch, Griechisch ...) brauchen UTF-8.
    # Auf Windows-Konsolen ist der Default oft cp1252 -> reconfigure.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")     # type: ignore[union-attr]
        except (AttributeError, ValueError):         # pragma: no cover
            pass

    if args.scaffold:
        created = scaffold()
        print(f"Angelegt: {created}" if created else "Nichts anzulegen.")

    report = analyze()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        # Im JSON-Modus signalisiert der Exit-Code trotzdem den Check.
        return 1 if (args.check and check(report)) else 0

    if args.coverage or not (args.check or args.scaffold):
        print(format_coverage(report))

    if args.check:
        errors = check(report)
        if errors:
            print("\nFEHLER:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print("\nOK: Parität + CORE_KEYS erfuellt.")
    return 0


if __name__ == "__main__":                             # pragma: no cover
    raise SystemExit(main())
