"""Tests fuer play_billing_android.py (Desktop-Pfad)."""
from services import play_billing_android as pba


def test_not_available_on_desktop():
    assert pba.is_available() is False
    assert "Android" in pba.status_message()


def test_purchase_fails_when_unavailable():
    outcome = pba.purchase("zunarodo_pro_monthly")
    assert outcome.ok is False
    assert outcome.message
    assert outcome.purchase_token == ""


def test_list_skus_empty_on_desktop():
    assert pba.list_skus() == []


def test_start_connection_false_on_desktop():
    assert pba.start_connection(timeout=0.1) is False
