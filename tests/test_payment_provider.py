"""Tests fuer payment_provider.py."""
from services.payment_provider import (ExternalTokenProvider, PlayBillingProvider,
                                       default_provider)


def test_default_provider_is_external():
    assert default_provider().provider_id() == "external_token"


def test_play_billing_not_available_yet():
    p = PlayBillingProvider()
    assert p.is_available() is False
    r = p.activate_from_user_input("")
    assert r.ok is False
    assert "nicht integriert" in r.message


def test_external_token_rejects_empty():
    r = ExternalTokenProvider().activate_from_user_input("", repo=None)
    assert r.ok is False
    assert "Kein Token" in r.message
