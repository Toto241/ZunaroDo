"""
Coverage-Report fuer mehrsprachige Rechtstexte.

Zeigt, fuer welche Rechtstexte (Impressum/Datenschutz/AGB/Widerruf) es in
welcher Sprache eine eigene, gepruefte Fassung gibt. Die Mechanik selbst
liegt in services/legal.py.

Aufruf:
    python -m tools.legal_status            # Tabelle
    python -m tools.legal_status --json
"""
from __future__ import annotations

import argparse
import json
import sys

from services.legal import DEFAULT_LANGUAGE, coverage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sprach-Coverage der Rechtstexte anzeigen.")
    parser.add_argument("--json", action="store_true",
                        help="Ausgabe als JSON.")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")     # type: ignore[union-attr]
        except (AttributeError, ValueError):         # pragma: no cover
            pass

    cov = coverage()
    if args.json:
        sys.stdout.write(json.dumps(cov, indent=2, ensure_ascii=False) + "\n")
        return 0

    lines = ["Rechtstexte - Sprach-Coverage", "=" * 50]
    for doc, langs in cov.items():
        if not langs:
            status = "fehlt!"
        else:
            translated = [l for l in langs if l != DEFAULT_LANGUAGE]
            extra = (f" + {', '.join(translated)}" if translated
                     else " (nur Deutsch - Uebersetzungen ausstehend)")
            status = f"de{extra}"
        lines.append(f"  {doc:<12} {status}")
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(main())
