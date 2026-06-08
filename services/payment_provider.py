"""
Zahlungsweg-Abstraktion: externer Token (Paddle/Lemon) vs. Google Play Billing.

Play-Store-Production-Ziel: PlayBillingProvider (Phase 1–3 in
docs/android/12_PLAY_BILLING_INTEGRATION.md).
Uebergang: ExternalTokenProvider fuer Desktop und Closed Test.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from services.licensing import License

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PurchaseResult:
    ok: bool
    message: str
    license: Optional[License] = None


class PaymentProvider(ABC):
    """Einheitliche Oberflaeche fuer Lizenz-Kauf/Aktivierung."""

    @abstractmethod
    def provider_id(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def activate_from_user_input(self, token: str, repo=None) -> PurchaseResult:
        ...


class ExternalTokenProvider(PaymentProvider):
    """Bestehender Weg: Nutzer fuegt Ed25519-Token ein."""

    def provider_id(self) -> str:
        return "external_token"

    def is_available(self) -> bool:
        return True

    def activate_from_user_input(self, token: str, repo=None) -> PurchaseResult:
        from services.license_ui import action_apply_token

        if repo is None:
            if not (token or "").strip():
                return PurchaseResult(False, "Kein Token eingegeben.")
            return PurchaseResult(
                False, "SettingsRepository erforderlich fuer Token-Aktivierung.")
        result = action_apply_token(repo, token)
        return PurchaseResult(result.success, result.message, result.license)


class PlayBillingProvider(PaymentProvider):
    """
    Google Play Billing — vollstaendiger Kauf-Flow.

    Der 'token'-Parameter von activate_from_user_input ist hier die zu
    kaufende Play-SKU (Produkt-ID), nicht ein Lizenz-Token. Ablauf:
      1. BillingClient verbinden + Kauf-Dialog (play_billing_android)
      2. Purchase-Token an den Server (/verify/play) schicken
      3. Server verifiziert mit der Play Developer API und liefert ein
         signiertes Ed25519-Lizenz-Token zurueck
      4. Dieses Token wird wie ein externer Token lokal angewandt
    """

    def __init__(self, verify_url: str = "",
                 default_sku: str = "zunarodo_pro_monthly"):
        self._verify_url = verify_url or os.environ.get(
            "ZUNARODO_PLAY_VERIFY_URL", "")
        self._default_sku = default_sku

    def provider_id(self) -> str:
        return "google_play_billing"

    def is_available(self) -> bool:
        from services.play_billing_android import is_available

        return is_available()

    def activate_from_user_input(self, token: str, repo=None) -> PurchaseResult:
        from services.play_billing_android import (acknowledge, purchase,
                                                   start_connection,
                                                   status_message)

        if not self.is_available():
            return PurchaseResult(False, status_message())

        product_id = (token or "").strip() or self._default_sku
        start_connection()
        outcome = purchase(product_id)
        if not outcome.ok:
            return PurchaseResult(False, outcome.message)

        license_token = self._verify_on_server(
            outcome.product_id, outcome.purchase_token)
        if not license_token:
            return PurchaseResult(
                False, "Kauf ok, aber Server-Verifikation fehlgeschlagen. "
                       "Bitte spaeter erneut versuchen.")

        # Kauf gegenueber Play bestaetigen (sonst Auto-Refund nach 3 Tagen).
        acknowledge(outcome.purchase_token)

        if repo is None:
            return PurchaseResult(True, "Lizenz erhalten.", None)
        from services.license_ui import action_apply_token
        result = action_apply_token(repo, license_token)
        return PurchaseResult(result.success, result.message, result.license)

    def _verify_on_server(self, product_id: str,
                          purchase_token: str) -> Optional[str]:
        """Schickt den Purchase-Token an den Server, liefert Lizenz-Token."""
        if not self._verify_url:
            log.error("ZUNARODO_PLAY_VERIFY_URL nicht gesetzt")
            return None
        try:
            import requests

            resp = requests.post(
                self._verify_url,
                json={"productId": product_id,
                      "purchaseToken": purchase_token},
                timeout=30)
            if resp.status_code >= 400:
                log.warning("Play-Verify-Server %s: %s",
                            resp.status_code, resp.text[:200])
                return None
            return resp.json().get("token")
        except Exception as exc:                          # noqa: BLE001
            log.exception("Play-Verify-Request fehlgeschlagen: %s", exc)
            return None


def default_provider() -> PaymentProvider:
    """Auf Android bevorzugt Play Billing, sonst externer Token."""
    try:
        from services.play_billing_android import is_available

        if is_available():
            return PlayBillingProvider()
    except Exception:                                     # noqa: BLE001
        pass
    return ExternalTokenProvider()
