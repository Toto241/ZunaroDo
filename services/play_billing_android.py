"""
Android Play Billing Bruecke (pyjnius).

Treibt de.alltagshelfer.billing.PlayBillingBridge (BillingClient 6.x).
Auf Desktop/no-Android: is_available() == False, alle Aktionen melden
sauber 'nur auf Android'.

Ablauf eines Kaufs (siehe services/payment_provider.PlayBillingProvider):
  1. start_connection()           Verbindung zum Play-Dienst
  2. list_skus(...)               SKUs + Preise fuer die UI
  3. purchase(product_id)         Kauf-Dialog + Warten auf Purchase-Token
  4. -> Token geht an den Server (/verify/play), der die Lizenz signiert

Der Purchase-Token wird NICHT in der App verifiziert (das kann nur der
Server mit den Play-Developer-API-Credentials). Die App reicht ihn nur
weiter und wendet das zurueckkommende, signierte Lizenz-Token an.

!!! Bridge ist nur auf einem echten Geraet/Build verifizierbar. !!!
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Optional

# Standard-SKUs (muessen mit der Play Console + payment_adapter_play
# uebereinstimmen).
DEFAULT_SKUS = (
    "zunarodo_pro_monthly",
    "zunarodo_pro_yearly",
    "zunarodo_pro_family",
)

_BRIDGE_CLASS = "de.alltagshelfer.billing.PlayBillingBridge"


@dataclass(frozen=True)
class PlaySku:
    product_id: str
    title: str = ""
    price: str = ""


@dataclass
class PurchaseOutcome:
    """Ergebnis eines Kaufversuchs in der App."""

    ok: bool
    message: str
    purchase_token: str = ""
    product_id: str = ""


def _on_android() -> bool:
    try:
        from kivy.utils import platform as kivy_platform
        return kivy_platform == "android"
    except Exception:
        return False


def _bridge():
    """Liefert die autoclass-Bruecke oder None (Desktop / Fehler)."""
    if not _on_android():
        return None
    try:
        from jnius import autoclass  # type: ignore[import-untyped]

        return autoclass(_BRIDGE_CLASS)
    except Exception:
        return None


def is_available() -> bool:
    bridge = _bridge()
    if bridge is None:
        return False
    try:
        return bool(bridge.isBillingAvailable())
    except Exception:
        return False


def status_message() -> str:
    if not _on_android():
        return "Play Billing nur auf Android verfuegbar."
    bridge = _bridge()
    if bridge is None:
        return "Play Billing Bridge nicht geladen."
    try:
        return str(bridge.getStatusMessage())
    except Exception as exc:                              # noqa: BLE001
        return f"Play Billing Bridge Fehler: {exc}"


def start_connection(timeout: float = 8.0) -> bool:
    """Baut die Billing-Verbindung auf und wartet kurz darauf."""
    bridge = _bridge()
    if bridge is None:
        return False
    try:
        bridge.startConnection()
    except Exception:
        return False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if bool(bridge.isConnected()):
                return True
        except Exception:
            return False
        time.sleep(0.25)
    return False


def list_skus(product_ids: tuple[str, ...] = DEFAULT_SKUS,
              timeout: float = 6.0) -> list[PlaySku]:
    """Fragt SKUs + Preise ab (pollt, da queryProductDetails async ist)."""
    bridge = _bridge()
    if bridge is None:
        return []
    deadline = time.monotonic() + timeout
    while True:
        try:
            raw = bridge.queryProductsBlockingJson(list(product_ids))
            parsed = json.loads(str(raw) or "[]")
        except Exception:
            parsed = []
        if parsed:
            return [PlaySku(product_id=item.get("productId", ""),
                            title=item.get("title", ""),
                            price=item.get("price", ""))
                    for item in parsed]
        if time.monotonic() >= deadline:
            return []
        time.sleep(0.3)


def purchase(product_id: str, *, poll_timeout: float = 180.0) -> PurchaseOutcome:
    """
    Startet den Kauf-Dialog und wartet auf den Purchase-Token.

    MUSS aus einem Worker-Thread aufgerufen werden (blockiert pollend),
    nie aus dem Kivy-UI-Thread.
    """
    bridge = _bridge()
    if bridge is None:
        return PurchaseOutcome(False, status_message())

    # ProductDetails MUSS vor launchBillingFlow im Java-Cache liegen -
    # sonst findet die Bruecke kein Angebot und der Dialog oeffnet nie.
    if not list_skus((product_id,)):
        return PurchaseOutcome(
            False, "Produktdetails konnten nicht geladen werden.")

    try:
        bridge.clearLastPurchase()
        bridge.launchPurchase(product_id)
    except Exception as exc:                              # noqa: BLE001
        return PurchaseOutcome(False, f"Kauf-Start fehlgeschlagen: {exc}")

    deadline = time.monotonic() + poll_timeout
    while time.monotonic() < deadline:
        try:
            token = str(bridge.getLastPurchaseToken() or "")
            code = int(bridge.getLastResponseCode())
        except Exception:
            token, code = "", -1
        if token:
            bought_product = str(bridge.getLastProductId() or "") or product_id
            return PurchaseOutcome(True, "Kauf erfolgreich",
                                   purchase_token=token,
                                   product_id=bought_product)
        # Billing-Response-Codes: 0 == OK (Token folgt gleich), -1 == noch
        # keine Antwort. 1 == USER_CANCELED, alles andere = echter Fehler
        # (z.B. ITEM_ALREADY_OWNED, SERVICE_UNAVAILABLE). Dann nicht bis
        # zum Timeout warten, sondern sofort abbrechen.
        if code == 1:
            return PurchaseOutcome(False, "Kauf vom Nutzer abgebrochen.")
        if code not in (-1, 0):
            return PurchaseOutcome(
                False, f"Kauf fehlgeschlagen (Billing-Code {code}).")
        time.sleep(0.5)
    return PurchaseOutcome(False, "Zeitueberschreitung beim Kauf.")


def acknowledge(purchase_token: str) -> bool:
    """Bestaetigt den Kauf (Pflicht innerhalb 3 Tagen)."""
    bridge = _bridge()
    if bridge is None:
        return False
    try:
        return bool(bridge.acknowledge(purchase_token))
    except Exception:
        return False
