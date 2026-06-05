"""
Zahlungsweg-Abstraktion: externer Token (Paddle/Lemon) vs. Google Play Billing.

Play-Store-Production-Ziel: PlayBillingProvider (Phase 1–3 in
docs/android/12_PLAY_BILLING_INTEGRATION.md).
Uebergang: ExternalTokenProvider fuer Desktop und Closed Test.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from services.licensing import License


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
    """Stub bis Java/pyjnius-Bruecke implementiert ist."""

    def provider_id(self) -> str:
        return "google_play_billing"

    def is_available(self) -> bool:
        return False

    def activate_from_user_input(self, token: str, repo=None) -> PurchaseResult:
        return PurchaseResult(
            False,
            "Google Play Billing ist noch nicht integriert. "
            "Siehe docs/android/12_PLAY_BILLING_INTEGRATION.md.",
        )


def default_provider() -> PaymentProvider:
    """Play-Flavor kann spaeter PlayBillingProvider bevorzugen."""
    return ExternalTokenProvider()
