"""
Path-Validierung fuer Datei-Imports.

Wird von iCal/vCard-Import (und potentiell weiteren Import-Pfaden)
genutzt, damit eine Capability nicht beliebige Dateipfade liest.

Schutzschichten:
  1. Resolve: Pfad wird kanonisch aufgeloest (verhindert '..'-Spielchen
     und Symlinks)
  2. Symlink-Pruefung: Symlinks werden explizit abgelehnt
  3. Existenz + Datei (keine Verzeichnisse)
  4. Erlaubte Extensions
  5. Max-Groesse: limitiert die Speichermenge, die ein Import in den
     Hauptthread ziehen kann (N4)
"""
from __future__ import annotations

from pathlib import Path


# 10 MB ist mehr als genug fuer typische .ics/.vcf-Exports
DEFAULT_MAX_IMPORT_BYTES = 10 * 1024 * 1024


def validate_import_path(path: str,
                          allowed_extensions: set[str],
                          max_bytes: int = DEFAULT_MAX_IMPORT_BYTES) -> Path:
    """
    Validiert einen Import-Pfad. Wirft ValueError bei Verstoessen.

    Liefert einen aufgeloesten, sicheren Path. Aufrufer kann den
    Inhalt anschliessend ohne weitere Pfadpruefung lesen.
    """
    if not path:
        raise ValueError("Pfad ist leer")
    p = Path(path).expanduser()
    try:
        resolved = p.resolve(strict=False)
    except OSError as exc:
        raise ValueError(f"Pfad konnte nicht aufgeloest werden: {exc}") from exc

    # Symlinks ablehnen, weil sie eine indirekte Pfad-Aufloesung sind
    if p.exists() and p.is_symlink():
        raise ValueError(f"Symlinks sind nicht erlaubt: '{path}'")

    if not resolved.exists():
        raise FileNotFoundError(f"Datei '{path}' nicht gefunden")

    if not resolved.is_file():
        raise ValueError(f"'{path}' ist keine regulaere Datei")

    suffix = resolved.suffix.lower()
    allowed_lower = {s.lower() for s in allowed_extensions}
    if suffix not in allowed_lower:
        raise ValueError(
            f"Dateityp '{suffix}' nicht erlaubt; erlaubt: "
            f"{sorted(allowed_lower)}")

    size = resolved.stat().st_size
    if size > max_bytes:
        raise ValueError(
            f"Datei zu gross ({size} Bytes); Limit: {max_bytes} Bytes")

    return resolved
