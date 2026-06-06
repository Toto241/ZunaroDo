"""Tests fuer play_billing_android.py (Desktop-Pfad)."""
from services import play_billing_android as pba


def test_not_available_on_desktop():
    assert pba.is_available() is False
    assert "Android" in pba.status_message()


def test_purchase_fails_when_unavailable():
    ok, msg = pba.purchase("zunarodo_pro_monthly")
    assert ok is False
    assert msg
