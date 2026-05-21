"""
Privacy-Policy-Hosting + Verfuegbarkeitspruefung.

Play Store verlangt eine oeffentlich erreichbare Datenschutzerklaerung.
Dieses Tool rendert legal/DATENSCHUTZ.md zu einer self-contained HTML-
Seite (ohne GUI-Abhaengigkeit, GitHub-Pages-tauglich) und prueft lokal,
ob die Policy veroeffentlichungsreif ist:

  * existiert die Quelle?
  * sind noch Vorlagen-Platzhalter ([ANBIETER] ...) offen?
  * ist in playstore.yml eine echte privacy_policy_url hinterlegt
    (kein example.org-Platzhalter)?

Die Netz-Erreichbarkeit prueft zusaetzlich der CI-Job
'privacy-policy-reachable' per HEAD-Request (siehe android-compliance.yml).

Aufruf:
    python -m tools.privacy_policy --build [--out site/privacy/index.html]
    python -m tools.privacy_policy --check        # Exit 1 bei Fehler
    python -m tools.privacy_policy --list-placeholders
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from tools.md_to_html import DOC_CSS, markdown_to_html

REPO_ROOT = Path(__file__).resolve().parent.parent
POLICY_MD = REPO_ROOT / "legal" / "DATENSCHUTZ.md"
DEFAULT_OUT = REPO_ROOT / "site" / "privacy" / "index.html"
PLAYSTORE_YML = REPO_ROOT / "playstore.yml"

#: Eckige-Klammer-Platzhalter der Vorlage: beginnen mit Grossbuchstabe,
#: gefolgt von Grossbuchstaben/Trennern. `(?!\()` schliesst Markdown-
#: Links [text](url) aus.
_PLACEHOLDER = re.compile(r"\[[A-ZÄÖÜ][A-ZÄÖÜ0-9 ._/-]*\](?!\()")

#: Minimal-Theme, damit DOC_CSS (nutzt CSS-Variablen) self-contained ist
#: - keine Abhaengigkeit zu tools/dashboard.py (das GUI-Libs zieht).
_MINIMAL_CSS = """
:root{
  --surface:#ffffff; --surface-muted:#f5f6f8; --text:#1a1d21;
  --text-muted:#5b636c; --border:#e2e5e9; --primary:#2563eb;
  --shadow:0 1px 3px rgba(0,0,0,.08);
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
body{margin:0;background:#eef0f3;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}
main{padding:24px;}
"""


def find_placeholders(text: str) -> list[str]:
    """Liefert die noch offenen Vorlagen-Platzhalter (unique, sortiert)."""
    return sorted({m.group(0) for m in _PLACEHOLDER.finditer(text)})


def build_html(md_text: str, title: str = "Datenschutzerklaerung") -> str:
    """Rendert die Policy als self-contained HTML-Seite."""
    body = markdown_to_html(md_text)
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="index,follow">
  <title>{html.escape(title)}</title>
  <style>{_MINIMAL_CSS}{DOC_CSS}</style>
</head>
<body>
  <main><article class="doc">
{body}
  </article></main>
</body>
</html>"""


def _privacy_url() -> str:
    if not PLAYSTORE_YML.is_file():
        return ""
    text = PLAYSTORE_YML.read_text(encoding="utf-8")
    try:
        import yaml
        data = yaml.safe_load(text) or {}
    except ImportError:                               # pragma: no cover
        import json
        data = json.loads(text)
    return ((data.get("contact") or {}).get("privacy_policy_url") or "")


def check(repo_root: Path = REPO_ROOT) -> list[tuple[str, str]]:
    """
    Prueft die Veroeffentlichungsreife. Liefert (severity, message)-Tupel,
    severity in {error, warning}.
    """
    issues: list[tuple[str, str]] = []
    md = repo_root / "legal" / "DATENSCHUTZ.md"
    if not md.is_file():
        issues.append(("error", "legal/DATENSCHUTZ.md fehlt."))
        return issues
    placeholders = find_placeholders(md.read_text(encoding="utf-8"))
    if placeholders:
        issues.append((
            "warning",
            f"{len(placeholders)} offene Vorlagen-Platzhalter "
            f"(z.B. {', '.join(placeholders[:3])}) - vor Veroeffentlichung "
            "ausfuellen."))
    url = _privacy_url()
    if not url:
        issues.append(("warning", "Keine privacy_policy_url in playstore.yml."))
    elif "example.org" in url or "example.com" in url:
        issues.append((
            "warning",
            f"privacy_policy_url ist ein Platzhalter ({url})."))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Privacy-Policy rendern + Veroeffentlichungsreife pruefen.")
    parser.add_argument("--build", action="store_true",
                        help="HTML-Seite aus legal/DATENSCHUTZ.md erzeugen.")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help=f"Ziel-Datei (Default: {DEFAULT_OUT}).")
    parser.add_argument("--check", action="store_true",
                        help="Veroeffentlichungsreife pruefen (Exit 1 bei Fehler).")
    parser.add_argument("--list-placeholders", action="store_true",
                        help="Offene Platzhalter auflisten.")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")     # type: ignore[union-attr]
        except (AttributeError, ValueError):         # pragma: no cover
            pass

    if not POLICY_MD.is_file():
        print("FEHLER: legal/DATENSCHUTZ.md fehlt.", file=sys.stderr)
        return 2
    md_text = POLICY_MD.read_text(encoding="utf-8")

    if args.list_placeholders:
        for p in find_placeholders(md_text):
            print(p)
        return 0

    if args.build:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_html(md_text), encoding="utf-8")
        print(f"Gerendert: {out}")
        # Hinweis, falls noch Platzhalter offen sind.
        ph = find_placeholders(md_text)
        if ph:
            print(f"Hinweis: {len(ph)} Platzhalter noch offen "
                  "(nicht veroeffentlichungsreif).")
        return 0

    if args.check:
        issues = check()
        errors = [i for i in issues if i[0] == "error"]
        for sev, msg in issues:
            stream = sys.stderr if sev == "error" else sys.stdout
            print(f"[{sev.upper()}] {msg}", file=stream)
        if not issues:
            print("OK: Privacy-Policy veroeffentlichungsreif.")
        return 1 if errors else 0

    parser.print_help()
    return 0


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(main())
