"""Tests fuer den Google-Play-Billing-Adapter (Server-Seite).

Der Google-API-Call wird durch einen Fake-Verifier ersetzt - es geht um
das Mapping Purchase -> PaymentEvent -> signiertes Lizenz-Token, nicht um
echte Play-Developer-API-Aufrufe.
"""
from __future__ import annotations

import json
import tempfile
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.licensing import Platform, Tier
from services.payment import UnknownPriceError, WebhookError
from services.payment_adapter_play import (DEFAULT_PLAY_SKU_MAPPING,
                                           PlayVerification,
                                           parse_play_purchase)

PKG = "de.alltagshelfer.alltagshelfer"


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    """Stdlib-HTTP-POST (kein 'requests' noetig - laeuft auch in CI)."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, (json.loads(body) if body else {})


def _ok_verifier(expiry=None, order_id="GPA.1234"):
    exp = expiry or datetime.now(timezone.utc) + timedelta(days=30)

    def verify(package_name, product_id, purchase_token):
        assert package_name == PKG
        # Play meldet dieselbe Produkt-ID zurueck -> Check besteht.
        return PlayVerification(valid=True, expiry_at=exp, order_id=order_id,
                                external_account_id="ext-42",
                                product_id=product_id,
                                raw={"subscriptionState": "ACTIVE"})
    return verify


def test_valid_purchase_maps_to_event():
    event = parse_play_purchase(
        {"productId": "zunarodo_pro_yearly", "purchaseToken": "tok-abc"},
        package_name=PKG,
        sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
        verifier=_ok_verifier(),
    )
    assert event is not None
    assert event.tier == Tier.PRO_ANNUAL
    assert event.persons == 2
    assert event.platform == Platform.ANDROID
    assert event.provider == "google_play"
    assert event.transaction_id == "GPA.1234"
    assert event.customer_id == "ext-42"


def test_product_id_mismatch_rejected():
    # Gueltiger Token, aber Play meldet eine ANDERE Produkt-ID als die vom
    # Client behauptete SKU -> kein Token (Anti-Tier-Escalation).
    def mismatch_verifier(pkg, pid, tok):
        return PlayVerification(valid=True, product_id="zunarodo_pro_monthly",
                                order_id="GPA.9")

    event = parse_play_purchase(
        {"productId": "zunarodo_pro_family", "purchaseToken": "tok"},
        package_name=PKG,
        sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
        verifier=mismatch_verifier,
    )
    assert event is None


def test_invalid_token_returns_none():
    def bad_verifier(pkg, pid, tok):
        return PlayVerification(valid=False)

    event = parse_play_purchase(
        {"productId": "zunarodo_pro_monthly", "purchaseToken": "tok"},
        package_name=PKG,
        sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
        verifier=bad_verifier,
    )
    assert event is None


def test_unknown_sku_raises():
    with pytest.raises(UnknownPriceError):
        parse_play_purchase(
            {"productId": "not_a_real_sku", "purchaseToken": "tok"},
            package_name=PKG,
            sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
            verifier=_ok_verifier(),
        )


def test_missing_fields_raises():
    with pytest.raises(WebhookError):
        parse_play_purchase(
            {"productId": "zunarodo_pro_monthly"},   # purchaseToken fehlt
            package_name=PKG,
            sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
            verifier=_ok_verifier(),
        )


def test_server_verify_play_returns_signed_token():
    """End-to-End ueber den HTTP-Handler: Kauf -> verifiziertes Lizenz-Token.

    Nutzt den echten Issuer (Ed25519) + Fake-Verifier und prueft, dass das
    zurueckkommende Token mit dem Anbieter-Pubkey verifizierbar ist.
    """
    from services.license_token import (CRYPTO_AVAILABLE, generate_keypair,
                                        verify_token)
    if not CRYPTO_AVAILABLE:
        pytest.skip("cryptography nicht verfuegbar")
    from services.payment_issuer import IssuerConfig
    from services.payment_server import PlayVerifyConfig, serve

    priv, pub = generate_keypair()
    log_path = Path(tempfile.mkdtemp(prefix="zd_play_")) / "audit.jsonl"
    issuer = IssuerConfig(private_key_hex=priv, audit_log_path=log_path,
                          send_mail=None)   # KEINE Mail im Play-Flow
    play_cfg = PlayVerifyConfig(
        package_name=PKG,
        sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
        verifier=_ok_verifier(),
        issuer=issuer,
    )
    # Server auf einem freien Port starten.
    server = serve("127.0.0.1", 0, paddle=None, lemon=None,
                   issuer=issuer, play=play_cfg)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        host, port = server.server_address
        status, body = _post_json(
            f"http://{host}:{port}/verify/play",
            {"productId": "zunarodo_pro_family", "purchaseToken": "tok-xyz"})
        assert status == 201, body
        token_str = body["token"]
        assert token_str
        # Das zurueckkommende Token ist ein gueltiges, signiertes Pro-Token.
        verified = verify_token(token_str, pub)
        assert verified.tier == Tier.PRO_FAMILY
        assert verified.platform == Platform.ANDROID
    finally:
        server.shutdown()
        server.server_close()


def test_server_verify_play_rejects_invalid_purchase():
    from services.license_token import CRYPTO_AVAILABLE, generate_keypair
    if not CRYPTO_AVAILABLE:
        pytest.skip("cryptography nicht verfuegbar")
    from services.payment_issuer import IssuerConfig
    from services.payment_server import PlayVerifyConfig, serve

    priv, _pub = generate_keypair()
    log_path = Path(tempfile.mkdtemp(prefix="zd_play_")) / "audit.jsonl"
    issuer = IssuerConfig(private_key_hex=priv, audit_log_path=log_path,
                          send_mail=None)

    def bad_verifier(pkg, pid, tok):
        return PlayVerification(valid=False)

    play_cfg = PlayVerifyConfig(package_name=PKG,
                                sku_mapping=DEFAULT_PLAY_SKU_MAPPING,
                                verifier=bad_verifier, issuer=issuer)
    server = serve("127.0.0.1", 0, paddle=None, lemon=None,
                   issuer=issuer, play=play_cfg)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        host, port = server.server_address
        status, _body = _post_json(
            f"http://{host}:{port}/verify/play",
            {"productId": "zunarodo_pro_monthly", "purchaseToken": "fake"})
        assert status == 402
    finally:
        server.shutdown()
        server.server_close()
