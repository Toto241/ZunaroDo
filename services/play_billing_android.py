"""
Android Play Billing Bruecke (pyjnius) — Phase 1 Stub.

Auf Desktop/no-Android: is_available() == False.
Sobald PlayBillingBridge in buildozer.spec eingebunden ist, hier
queryProducts/launchBillingFlow implementieren.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PlaySku:
    product_id: str
    title: str = ""
    price: str = ""


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

        bridge = autoclass("de.alltagshelfer.billing.PlayBillingBridge")
        return bool(bridge.isBillingAvailable())
    except Exception:
        return False


def status_message() -> str:
    if not _on_android():
        return "Play Billing nur auf Android verfuegbar."
    try:
        from jnius import autoclass  # type: ignore[import-untyped]

        bridge = autoclass("de.alltagshelfer.billing.PlayBillingBridge")
        return str(bridge.getStatusMessage())
    except Exception as exc:
        return f"Play Billing Bridge nicht geladen: {exc}"


def list_skus() -> list[PlaySku]:
    """Platzhalter bis BillingClient angebunden ist."""
    if not is_available():
        return []
    return []


def purchase(sku_id: str) -> tuple[bool, str]:
    if not is_available():
        return False, status_message()
    return False, "launchBillingFlow noch nicht implementiert."
