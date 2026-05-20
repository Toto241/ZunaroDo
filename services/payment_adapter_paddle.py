"""
Paddle-Billing-Webhook-Adapter.

Signatur:
  Header 'Paddle-Signature: ts=<unix>;h1=<hex_hmac>'
  HMAC-SHA256(secret, f"{ts}:{raw_body}")

Wir akzeptieren Webhooks nur, wenn:
  - ts liegt innerhalb von +/- TOLERANCE_SECONDS um die aktuelle Zeit
    (verhindert Replay-Attacken)
  - HMAC ueber 'ts:body' mit dem Anbieter-Webhook-Secret stimmt

Referenz: https://developer.paddle.com/webhooks/signature-verification
"""
from __future__ import annotations

import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Optional

from services.licensing import Platform, Tier
from services.payment import (EventKind, PaymentEvent, SignatureError,
                                UnknownPriceError, WebhookContext,
                                WebhookError)


TOLERANCE_SECONDS = 5 * 60
PROVIDER_NAME = "paddle"


# Paddle-Event-Type -> EventKind. Nicht jedes Paddle-Event interessiert uns;
# unbekannte werden vom Parser ignoriert (None zurueckgegeben).
_EVENT_TYPE_MAP: dict[str, EventKind] = {
    "subscription.created": EventKind.SUBSCRIPTION_CREATED,
    "subscription.activated": EventKind.SUBSCRIPTION_CREATED,
    "subscription.renewed": EventKind.SUBSCRIPTION_RENEWED,
    "subscription.canceled": EventKind.SUBSCRIPTION_CANCELED,
    "transaction.completed": EventKind.ONE_TIME_PURCHASE,
    "adjustment.created": EventKind.REFUND,
}


def verify_signature(raw_body: bytes,
                      paddle_signature_header: str,
                      secret: str,
                      *,
                      now: Optional[float] = None) -> None:
    """Wirft SignatureError, wenn Header oder HMAC nicht passen."""
    if not paddle_signature_header:
        raise SignatureError("Header 'Paddle-Signature' fehlt")
    if not secret:
        raise SignatureError("Kein Webhook-Secret konfiguriert")
    parts = dict(p.split("=", 1) for p in paddle_signature_header.split(";")
                  if "=" in p)
    ts_raw = parts.get("ts")
    sig_hex = parts.get("h1")
    if not ts_raw or not sig_hex:
        raise SignatureError("Paddle-Signature unvollstaendig (ts/h1 fehlt)")
    try:
        ts = int(ts_raw)
    except ValueError:
        raise SignatureError("Paddle-Signature ts ist keine Zahl")
    current = now if now is not None else time.time()
    if abs(current - ts) > TOLERANCE_SECONDS:
        raise SignatureError(
            f"Paddle-Signature ts liegt ausserhalb der Toleranz "
            f"({abs(current - ts):.0f}s > {TOLERANCE_SECONDS}s)")

    message = f"{ts}:".encode("utf-8") + raw_body
    expected = hmac.new(secret.encode("utf-8"), message,
                         sha256).hexdigest()
    if not hmac.compare_digest(expected, sig_hex):
        raise SignatureError("Paddle-Signature HMAC stimmt nicht")


def parse_event(ctx: WebhookContext) -> Optional[PaymentEvent]:
    """Parsed einen Paddle-Webhook in ein PaymentEvent oder None."""
    verify_signature(
        ctx.raw_body,
        ctx.headers.get("Paddle-Signature", ""),
        ctx.signing_secret,
    )
    try:
        payload = json.loads(ctx.raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebhookError(f"Body ist kein gueltiges JSON: {exc}")

    event_type = payload.get("event_type", "")
    kind = _EVENT_TYPE_MAP.get(event_type)
    if kind is None:
        return None  # uninteressantes Event - 200 OK ohne Action

    data = payload.get("data", {}) or {}
    # Paddle Billing-Struktur: items[].price.id, customer.email
    items = data.get("items") or []
    if not items:
        raise WebhookError("Paddle-Webhook ohne items[]")
    price_id = (items[0].get("price") or {}).get("id", "")
    if not price_id or price_id not in ctx.price_mapping:
        raise UnknownPriceError(
            f"Preis-ID '{price_id}' nicht im Mapping - "
            "Anbieter muss Mapping in config ergaenzen")
    tier, persons = ctx.price_mapping[price_id]

    customer = data.get("customer") or {}
    email = customer.get("email", "") or data.get("customer_email", "")
    customer_id = customer.get("id", "") or data.get("customer_id", "")
    if not email:
        raise WebhookError("Paddle-Webhook ohne customer.email")

    # Ablaufdatum: bevorzugt aus 'next_billed_at', sonst aus 'current_billing_period.ends_at',
    # sonst eine sinnvolle Default-Frist je nach Tier.
    expires_iso = (data.get("next_billed_at")
                    or (data.get("current_billing_period") or {}).get("ends_at"))
    expires_at = _parse_iso(expires_iso) or _default_expiry(tier)

    return PaymentEvent(
        kind=kind,
        provider=PROVIDER_NAME,
        customer_email=email,
        customer_id=customer_id,
        tier=tier,
        persons=persons,
        expires_at=expires_at,
        platform=Platform.DESKTOP,
        transaction_id=str(data.get("id") or payload.get("event_id") or ""),
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
