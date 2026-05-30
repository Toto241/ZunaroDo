"""
Generator fuer die lokalisierten Capability-Beschreibungen.

Die Capability-Beschreibungen werden im Code (modules/*.py) deutsch
definiert. Dieses Werkzeug schreibt sie unter dem Key ``cap.<name>.desc``
in die Locale-Dateien, damit sie ueber ``Capability.localized_description``
in der jeweiligen Sprache ausgegeben werden koennen.

  * Die deutsche Fassung (``de.json``) wird zur Laufzeit aus der Registry
    gezogen - sie ist damit per Definition deckungsgleich mit dem Code.
  * Uebersetzungen liegen in TRANSLATIONS (Sprachcode -> {cap_name: text}).
  * Sprachen, fuer die (noch) keine Uebersetzung vorliegt, werden NICHT
    angefasst (kein Schluessel angelegt) - die Laufzeit faellt dann ueber
    den i18n-Fallback sauber auf Deutsch/Englisch bzw. den Code-Text zurueck.

Aufruf:

    python -m tools.gen_cap_descriptions          # schreibt die Locale-Dateien
    python -m tools.gen_cap_descriptions --check   # nur pruefen (Exit 1 bei Drift)

Idempotent: mehrfaches Ausfuehren erzeugt dieselbe Ausgabe. Bestehende
Nicht-cap.*-Keys bleiben unveraendert; die cap.*-Keys werden am Ende der
Datei in stabiler (Capability-Namen-)Reihenfolge gefuehrt.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = REPO_ROOT / "locales"
KEY_PREFIX = "cap."
KEY_SUFFIX = ".desc"


def german_descriptions() -> dict[str, str]:
    """Zieht {capability_name: deutsche Beschreibung} aus der Registry."""
    # Import erst hier, damit --help auch ohne vollstaendige Umgebung geht.
    from tests.test_smoke import _build_system  # type: ignore

    db, reg, _assistant, path = _build_system()
    try:
        return {c.name: c.description for c in reg.all_capabilities(
            include_disabled=True)}
    finally:
        db.close()
        try:
            os.unlink(path)
        except OSError:
            pass


# Uebersetzungstabellen: Sprachcode -> {capability_name: Beschreibung}.
# Deutsch fehlt bewusst (kommt aus dem Code). Pflege erfolgt hier zentral.
from tools._cap_translations import TRANSLATIONS  # noqa: E402


def _key(cap_name: str) -> str:
    return f"{KEY_PREFIX}{cap_name}{KEY_SUFFIX}"


def _load(code: str) -> dict[str, str]:
    path = LOCALES_DIR / f"{code}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _strip_cap_keys(data: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in data.items()
            if not (k.startswith(KEY_PREFIX) and k.endswith(KEY_SUFFIX))}


def build_locale(code: str, german: dict[str, str]) -> dict[str, str]:
    """Erzeugt den Soll-Inhalt einer Locale-Datei inkl. cap.*-Keys."""
    data = _strip_cap_keys(_load(code))
    if code == "de":
        table = german
    else:
        table = TRANSLATIONS.get(code, {})
    # cap.*-Keys in stabiler Reihenfolge (sortiert nach Capability-Name)
    for cap_name in sorted(german):
        text = table.get(cap_name)
        if text:
            data[_key(cap_name)] = text
    return data


def _dump(data: dict[str, str]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def write_all(check: bool = False) -> int:
    german = german_descriptions()
    # Alle Sprachen, fuer die eine Datei existiert, plus de.
    codes = sorted({p.stem for p in LOCALES_DIR.glob("*.json")})
    drift = []
    for code in codes:
        target = build_locale(code, german)
        rendered = _dump(target)
        path = LOCALES_DIR / f"{code}.json"
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if rendered == current:
            continue
        drift.append(code)
        if not check:
            tmp = tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=LOCALES_DIR, delete=False)
            tmp.write(rendered)
            tmp.close()
            os.replace(tmp.name, path)
    if check and drift:
        print("Locale-Dateien nicht aktuell (gen_cap_descriptions): "
              + ", ".join(drift), file=sys.stderr)
        return 1
    if not check:
        translated = sum(1 for c in codes if c != "de" and TRANSLATIONS.get(c))
        print(f"Geschrieben: {len(codes)} Locale-Dateien, "
              f"{len(german)} Capabilities, "
              f"{translated + 1} Sprachen mit cap.*-Texten.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Nur pruefen, nichts schreiben (Exit 1 bei Drift).")
    args = parser.parse_args(argv)
    return write_all(check=args.check)


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())
