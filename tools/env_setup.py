"""
ZunaroDo - .env Setup-Helfer (einfache Konfiguration, Ebene App/Laufzeit).

Schliesst die Luecke aus dem Konfig-Audit (docs/KONFIG_AUDIT.md): Es gab bisher
keinen gefuehrten Weg, eine ``.env`` aus ``.env.example`` zu erzeugen, und keinen
Status-Ueberblick, welche Umgebungsvariablen/Secrets gesetzt sind.

Bewusst ohne Fremd-Abhaengigkeit (kein python-dotenv): nur stdlib, damit das
Tool ueberall laeuft, wo das Control Panel laeuft.

Aufruf::

    python -m tools.env_setup --init     # .env aus Vorlage erzeugen (nie ueberschreiben)
    python -m tools.env_setup --check     # Status aller dokumentierten Variablen (Default)
    python -m tools.env_setup --path      # absoluten Pfad der .env ausgeben

Sicherheit: Werte werden NIE ausgegeben - nur ``gesetzt``/``leer`` pro Variable.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Mapping, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = REPO_ROOT / ".env.example"
ENV_FILE = REPO_ROOT / ".env"

# Variablenzeile: NAME=...  (NAME in GROSS_SCHREIBUNG_MIT_UNDERSCORES)
_VAR_RE = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")
# Inline-Kommentar nur, wenn ihm Whitespace vorausgeht (dotenv-Konvention):
# "wert  # kommentar" -> "wert", aber "ab#cd" (z.B. in einem Passwort) bleibt.
_INLINE_COMMENT_RE = re.compile(r"\s#")


def parse_example(text: str) -> list[tuple[str, bool]]:
    """Liefert ``(NAME, is_secret)`` je in ``.env.example`` dokumentierter Var.

    ``is_secret`` ist True, wenn die Zeile den Marker ``[SECRET]`` enthaelt.
    Kommentar- und Leerzeilen werden ignoriert.
    """
    out: list[tuple[str, bool]] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _VAR_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        out.append((name, "[SECRET]" in raw))
    return out


def parse_env_values(text: str) -> dict[str, str]:
    """Liest ``NAME=VALUE``-Paare aus einer ``.env`` (Kommentare entfernt).

    Inline-Kommentare (Whitespace + ``#``) werden abgeschnitten, damit eine
    aus ``.env.example`` kopierte, noch leere Variable wie
    ``KEY=        # [SECRET] ...`` korrekt als *leer* erkannt wird.
    """
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _VAR_RE.match(line)
        if not m:
            continue
        value = m.group(2)
        cut = _INLINE_COMMENT_RE.search(value)
        if cut:
            value = value[: cut.start()]
        values[m.group(1)] = value.strip()
    return values


def init_env(example: Path = ENV_EXAMPLE,
             target: Path = ENV_FILE) -> tuple[int, str]:
    """Kopiert ``example`` nach ``target`` - ueberschreibt NIE eine bestehende.

    Rueckgabe: ``(exit_code, message)``. Eine bereits vorhandene ``.env`` ist
    kein Fehler (idempotent, Exit 0); eine fehlende Vorlage schon (Exit 1).
    """
    if not example.exists():
        return 1, f"FEHLER: Vorlage fehlt: {example}"
    if target.exists():
        return 0, (f"{target.name} existiert bereits - nichts geaendert. "
                   f"({target})")
    shutil.copyfile(example, target)
    return 0, (f"Erstellt: {target}\n"
               "Naechster Schritt: die mit [SECRET] markierten Werte eintragen "
               "(z.B. ALLTAGSHELFER_DB_KEY, GOOGLE_API_KEY, ALLTAGSHELFER_SMTP_PASS). "
               "Leere Variablen bleiben einfach inaktiv - ZunaroDo laeuft auch "
               "ohne sie offline.")


def check_env(example: Path = ENV_EXAMPLE,
              target: Path = ENV_FILE,
              environ: Optional[Mapping[str, str]] = None) -> tuple[int, list[str]]:
    """Erzeugt einen Status-Bericht: welche dokumentierten Variablen gesetzt
    sind (aus der Prozess-Umgebung oder aus ``.env``), Secrets maskiert.

    Werte werden bewusst nie ausgegeben - nur ``gesetzt``/``leer`` + Quelle.
    """
    import os
    env = os.environ if environ is None else environ
    if not example.exists():
        return 1, [f"FEHLER: Vorlage fehlt: {example}"]
    variables = parse_example(example.read_text(encoding="utf-8"))
    file_vals = (parse_env_values(target.read_text(encoding="utf-8"))
                 if target.exists() else {})

    lines: list[str] = []
    set_count = 0
    for name, is_secret in variables:
        env_val = (env.get(name) or "").strip()
        file_val = file_vals.get(name, "")
        is_set = bool(env_val or file_val)
        if is_set:
            set_count += 1
        source = "Umgebung" if env_val else (".env" if file_val else "-")
        tag = " [SECRET]" if is_secret else ""
        state = "gesetzt" if is_set else "leer"
        lines.append(f"  [{state:^7}] {name}{tag}   (Quelle: {source})")

    exists = target.exists()
    header = [
        f".env-Pfad: {target}"
        + (" (vorhanden)" if exists else " (fehlt - 'Init' erzeugt sie)"),
        f"{set_count}/{len(variables)} dokumentierte Variablen gesetzt.",
        "",
    ]
    return 0, header + lines


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.env_setup",
        description="Erzeugt/prueft die .env fuer ZunaroDo (einfache Konfiguration).")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--init", action="store_true",
                       help="Erzeugt .env aus .env.example (ueberschreibt nie).")
    group.add_argument("--check", action="store_true",
                       help="Zeigt den Status der Umgebungsvariablen (Default).")
    group.add_argument("--path", action="store_true",
                       help="Gibt den absoluten Pfad der .env aus.")
    args = parser.parse_args(argv)

    if args.path:
        print(ENV_FILE)
        return 0

    if args.init:
        code, message = init_env()
        print(message)
        return code

    # Default: --check
    code, lines = check_env()
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
