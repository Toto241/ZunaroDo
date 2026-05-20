"""
Lemon-Squeezy-Webhook-Adapter.

Signatur:
  Header 'X-Signature: <hex_hmac>'
  HMAC-SHA256(secret, raw_body)

Anders als Paddle ohne Timestamp - dafuer kein Replay-Schutz, was
Lemon Squeezy bewusst so designt hat. Wir fangen Replays
ueber 'transaction_id' im Issuer ab (idempotente Token-Ausstellung).

Referenz: https://docs.lemonsqueezy.com/help/webhooks#signing-requests
"""
from __future__ import annotations

import hmac
import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Optional

from services.licensing import Platform, Tier
from services.payment import (EventKind, PaymentEvent, SignatureError,
                                UnknownPriceError, WebhookContext,
                                WebhookError)


PROVIDER_NAME = "lemon_squeezy"


_EVENT_TYPE_MAP: dict[str, EventKind] = {
    "subscription_created": EventKind.SUBSCRIPTION_CREATED,
    "subscription_resumed": EventKind.SUBSCRIPTION_CREATED,
    "subscription_payment_success": EventKind.SUBSCRIPTION_RENEWED,
    "subscription_cancelled": EventKind.SUBSCRIPTION_CANCELED,
    "order_created": EventKind.ONE_TIME_PURCHASE,
    "order_refunded": EventKind.REFUND,
}


def verify_signature(raw_body: bytes,
                      signature_header: str,
                      secret: str) -> None:
    """Wirft SignatureError, wenn der HMAC nicht passt."""
    if not signature_header:
        raise SignatureError("Header 'X-Signature' fehlt")
    if not secret:
        raise SignatureError("Kein Webhook-Secret konfiguriert")
    expected = hmac.new(secret.encode("utf-8"), raw_body,
                         sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header.strip()):
        raise SignatureError("X-Signature HMAC stimmt nicht")


def parse_event(ctx: WebhookContext) -> Optional[PaymentEvent]:
    """Parsed einen Lemon-Squeezy-Webhook in ein PaymentEvent oder None."""
    verify_signature(
        ctx.raw_body,
        ctx.headers.get("X-Signature", ""),
        ctx.signing_secret,
    )
    try:
        payload = json.loads(ctx.raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebhookError(f"Body ist kein gueltiges JSON: {exc}")

    meta = payload.get("meta", {}) or {}
    event_name = meta.get("event_name", "")
    kind = _EVENT_TYPE_MAP.get(event_name)
    if kind is None:
        return None

    data = payload.get("data", {}) or {}
    attrs = data.get("attributes", {}) or {}

    # Lemon-Squeezy nutzt 'variant_id' (Number) als Preis-Identifikator.
    variant_id = str(attrs.get("variant_id") or "")
    if not variant_id or variant_id not in ctx.price_mapping:
        raise UnknownPriceError(
            f"variant_id '{variant_id}' nicht im Mapping - "
            "Anbieter muss Mapping in config ergaenzen")
    tier, persons = ctx.price_mapping[variant_id]

    email = attrs.get("user_email", "")
    customer_id = str(attrs.get("customer_id") or "")
    if not email:
        raise WebhookError("Lemon-Squeezy-Webhook ohne user_email")

    expires_at = (_parse_iso(attrs.get("renews_at"))
                   or _parse_iso(attrs.get("ends_at"))
                   or _default_expiry(tier))

    return PaymentEvent(
        kind=kind,
        provider=PROVIDER_NAME,
        customer_email=email,
        customer_id=customer_id,
        tier=tier,
        persons=persons,
        expires_at=expires_at,
        platform=Platform.DESKTOP,
        transaction_id=str(data.get("id") or ""),
        raw_payload=payload,
    )


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _default_expiry(tier: Tier) -> datetime:
    now = datetime.now(timezone.utc)
    if tier == Tier.PRO_ANNUAL:
        return now + timedelta(days=365)
    return now + timedelta(days=30)
