"""
OCR-Dienst fuer Kassenbons (Modul B).

Bewusst optional: erfordert 'pytesseract' + Pillow + eine lokale
Tesseract-Installation. Wenn nichts davon vorhanden ist, gibt der Dienst
einen klar lesbaren Hinweis zurueck statt zu crashen.

Die Erkennung ist robust gehalten: sie zieht aus dem erkannten Text
Posten (Zeile mit Betrag am Ende) und eine Endsumme heraus.
"""
from __future__ import annotations

import re
from pathlib import Path


_PRICE_PATTERN = re.compile(r"(\d+[.,]\d{2})\s*$")
_SUM_HINTS = ("summe", "gesamt", "total", "zu zahlen", "betrag", "endbetrag")


def _try_import():
    """Versucht pytesseract + Pillow zu laden. None bei Fehler."""
    try:
        import pytesseract
        from PIL import Image
        return pytesseract, Image
    except Exception:
        return None


def scan_receipt(image_path: str) -> dict:
    """Liest einen Kassenbon als Bild ein und liefert Posten + Summe."""
    path = Path(image_path)
    if not path.exists():
        return {"error": f"Bild '{image_path}' nicht gefunden"}

    loaded = _try_import()
    if loaded is None:
        return {
            "error": "OCR-Bibliothek fehlt",
            "hinweis": ("Installiere 'pytesseract' und 'Pillow' sowie eine "
                         "Tesseract-Engine. Auf Windows z.B. das Installer-"
                         "Paket von github.com/UB-Mannheim/tesseract."),
        }
    pytesseract, Image = loaded
    try:
        text = pytesseract.image_to_string(Image.open(path), lang="deu")
    except Exception as exc:                            # pragma: no cover
        return {"error": f"OCR-Fehler: {exc}"}

    items: list[dict] = []
    total: float | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = _PRICE_PATTERN.search(line)
        if not match:
            continue
        price = float(match.group(1).replace(",", "."))
        label = line[:match.start()].strip(" -:\t")
        if not label:
            continue
        if any(hint in label.lower() for hint in _SUM_HINTS):
            total = price
        else:
            items.append({"label": label, "price": price})
    return {
        "status": "Kassenbon analysiert",
        "items": items,
        "total": total,
        "raw_text": text,
    }
