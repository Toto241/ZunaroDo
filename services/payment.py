"""
Provider-neutrales Bezahl-Modell.

Idee:
  Webhook von Paddle / Lemon Squeezy / Stripe -> Adapter parsed das
  zu einem PaymentEvent -> services.payment_issuer signiert ein
  Lizenz-Token und versendet es per Mail an den Kunden.

Damit haengt die App-Logik nicht am konkreten Bezahldienstleister.
Wechsel von Paddle zu Lemon Squeezy = neuer Adapter, nichts anderes
muss angepasst werden.

Datenfluss:

    HTTPS POST /webhook/paddle
                    |
                    v
    services.payment_adapter_paddle.parse_event()
                    |
                    v
    PaymentEvent (provider-neutral)
                    |
                    v
    services.payment_issuer.handle_event()
        |              |              |
        v              v              v
    Token signieren  Mail an Kunde  Audit-Log
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from services.licensing import Platform, Tier


class EventKind(str, enum.Enum):
    """Was ist passiert beim Bezahldienstleister?"""

    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    ONE_TIME_PURCHASE = "one_time_purchase"
    REFUND = "refund"


# Mapping Provider-Preis-ID -> (Tier, Persons). Wird vom Anbieter
# beim Einrichten der Produkte/Preise in Paddle/Lemon Squeezy gepflegt.
# Beispiel:
#   PRICE_MAPPING = {
#       "pri_01H...": (Tier.PRO_MONTHLY, 2),
#       "pri_01J...": (Tier.PRO_ANNUAL, 2),
#       "pri_01K...": (Tier.PRO_FAMILY, 5),
#   }
# Wird ueber die config in services.payment_issuer befuellt.
PriceMapping = dict[str, tuple[Tier, int]]


@dataclass
class PaymentEvent:
    """Provider-neutrale Repraesentation eines Bezahl-Vorgangs."""

    kind: EventKind
    provider: str                    # "paddle" | "lemon_squeezy" | ...
    customer_email: str
    customer_id: str                  # Anbieter-eigene Kunden-ID
    tier: Tier
    persons: int
    expires_at: datetime              # wann das Abo/der Token ablaeuft
    platform: Platform = Platform.DESKTOP
    transaction_id: str = ""          # fuer Idempotenz - bereits verarbeitet?
    raw_payload: dict = field(default_factory=dict)  # fuer Audit/Debug


@dataclass
class WebhookContext:
    """Wird vom HTTP-Server an den Adapter uebergeben."""

    raw_body: bytes
    headers: dict[str, str]
    signing_secret: str
    price_mapping: PriceMapping


class WebhookError(Exception):
    """Webhook ist syntaktisch kaputt oder nicht autorisiert."""


class SignatureError(WebhookError):
    """HMAC-Signatur stimmt nicht - Webhook wird abgewiesen (401/403)."""


class UnknownPriceError(WebhookError):
    """Webhook referenziert eine Preis-ID, die nicht im Mapping steht.

    Tritt typischerweise auf, wenn der Anbieter ein neues Produkt
    anlegt und vergisst, das Mapping in der Config zu updaten -
    der Webhook wird stillschweigend verworfen (400), damit der
    Bezahldienstleister nicht ewig retried.
    """
