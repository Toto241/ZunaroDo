"""
OCR-Dienst fuer Kassenbons (Modul B).

Versuche in dieser Reihenfolge - alle LOKAL, keine Cloud:
  0. ML Kit (nur Android)             - On-Device-OCR ueber pyjnius-Bruecke
  1. pytesseract (+ Tesseract-Engine) - sehr robust fuer Quittungen
  2. easyocr                          - alternative reine Python-Bibliothek
  3. ohne OCR                         - klarer Hinweis statt Crash

Cloud-OCR-Anbieter (Google Vision, AWS Textract, Azure Computer Vision)
sind BEWUSST nicht eingebaut: die App ist datenschutzfreundlich angelegt,
und Belege koennen sehr persoenliche Informationen enthalten (Apotheke,
Kontoauszug u. a.).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional


_PRICE_PATTERN = re.compile(r"(\d+[.,]\d{2})\s*$")
_SUM_HINTS = ("summe", "gesamt", "total", "zu zahlen", "betrag", "endbetrag")


# -----------------------------------------------------------------
#  Engine-Auswahl
# -----------------------------------------------------------------
def _try_mlkit():
    """ML-Kit-OCR (Android). Auf Desktop nicht verfuegbar -> None."""
    try:
        from services import ocr_android

        if not ocr_android.is_available():
            return None

        def run(path: Path) -> str:
            text = ocr_android.recognize(str(path))
            if text is None:
                raise RuntimeError("ML Kit lieferte keinen Text")
            return text
        return run
    except Exception:
        return None


def _try_tesseract():
    try:
        import pytesseract                                   # type: ignore[import-not-found]
        from PIL import Image                                # type: ignore[import-not-found]

        def run(path: Path) -> str:
            return pytesseract.image_to_string(Image.open(path), lang="deu")
        return run
    except Exception:
        return None


def _try_easyocr():
    try:
        import easyocr                                       # type: ignore[import-not-found]
        reader = easyocr.Reader(["de"], gpu=False)

        def run(path: Path) -> str:
            return "\n".join(reader.readtext(str(path), detail=0))
        return run
    except Exception:
        return None


def _select_engine() -> Optional[tuple[str, Any]]:
    """Liefert (Name, Aufruf) der ersten verfuegbaren OCR-Engine."""
    engine = _try_mlkit()
    if engine is not None:
        return "mlkit", engine
    engine = _try_tesseract()
    if engine is not None:
        return "tesseract", engine
    engine = _try_easyocr()
    if engine is not None:
        return "easyocr", engine
    return None


# -----------------------------------------------------------------
#  Public-API
# -----------------------------------------------------------------
def scan_receipt(image_path: str) -> dict:
    """Liest einen Kassenbon und liefert Posten + Summe + Roh-Text."""
    path = Path(image_path)
    if not path.exists():
        return {"error": f"Bild '{image_path}' nicht gefunden"}

    selected = _select_engine()
    if selected is None:
        return {
            "error": "OCR-Engine fehlt",
            "hinweis": ("Installiere entweder 'pytesseract' + Tesseract-Engine "
                         "ODER 'easyocr'. Cloud-OCR wird aus Datenschutzgruenden "
                         "bewusst nicht angeboten."),
        }
    engine_name, runner = selected
    try:
        text = runner(path)
    except Exception as exc:                                # pragma: no cover
        return {"error": f"OCR-Fehler ({engine_name}): {exc}"}

    items: list[dict] = []
    total: Optional[float] = None
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
        "engine": engine_name,
        "items": items,
        "total": total,
        "raw_text": text,
    }


def available_engines() -> list[str]:
    """Liefert eine Liste der hier verfuegbaren OCR-Engines (zur Diagnose)."""
    out: list[str] = []
    if _try_mlkit() is not None:
        out.append("mlkit")
    if _try_tesseract() is not None:
        out.append("tesseract")
    if _try_easyocr() is not None:
        out.append("easyocr")
    return out
