"""
pyjnius-Wrapper fuer die ML-Kit-OCR-Bruecke (Android).

Auf Desktop/no-Android: is_available() == False, recognize() == None.
Auf Android spricht es de.alltagshelfer.ocr.MlKitOcrBridge an (siehe
src/android/ocr/MlKitOcrBridge.java). Wird von services/ocr.py als
bevorzugte Engine genutzt, sobald sie verfuegbar ist.
"""
from __future__ import annotations

from typing import Optional


def _on_android() -> bool:
    try:
        from kivy.utils import platform as kivy_platform
        return kivy_platform == "android"
    except Exception:
        return False


def is_available() -> bool:
    if not _on_android():
        return False
    try:
        from jnius import autoclass  # type: ignore[import-untyped]

        bridge = autoclass("de.alltagshelfer.ocr.MlKitOcrBridge")
        return bool(bridge.isAvailable())
    except Exception:
        return False


def recognize(image_path: str) -> Optional[str]:
    """Liefert den erkannten Text oder None (nicht verfuegbar / Fehler)."""
    if not is_available():
        return None
    try:
        from jnius import autoclass  # type: ignore[import-untyped]

        bridge = autoclass("de.alltagshelfer.ocr.MlKitOcrBridge")
        text = bridge.recognize(image_path)
        return str(text) if text else None
    except Exception:
        return None
