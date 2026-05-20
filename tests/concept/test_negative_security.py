"""
Negativtests Block D - Sicherheits-/Manipulationsangriffe und Block E -
API-/Backend-Negativtests (TESTING.md Abschnitt 11.3 D + E).

Wir testen:

  N-D-04 / N-E-04   Manipulierter Token / Request-Body -> Verifikation
                    schlaegt fehl, kein Free-Pass
  N-E-01            Ungueltiger Token-String
  N-E-02            Abgelaufener Token -> TokenExpired
  N-E-03            Token ohne konfigurierten Public-Key -> Abweisung
  N-D-06            Path-Traversal in Import-Pfaden -> Validator blockt
  N-D-10            Escape-Roundtrip: keine Code-Injection in Export
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.escaping import escape_text, unescape_text
from services.io_validation import validate_import_path
from services.license_token import (LicenseToken, Platform, Tier, TokenError,
                                     TokenExpired, generate_keypair,
                                     sign_token, verify_token)


pytestmark = [pytest.mark.concept, pytest.mark.security]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def _make_token(*, expired: bool = False) -> tuple[str, str, LicenseToken]:
    priv, pub = generate_keypair()
    now = datetime.now(timezone.utc)
    if expired:
        purchased = now - timedelta(days=400)
        expires = now - timedelta(days=10)
    else:
        purchased = now
        expires = now + timedelta(days=365)
    tok = LicenseToken(
        tier=Tier.PRO_MONTHLY, persons=2,
        purchased_at=purchased, expires_at=expires,
        customer_id="cust-test", platform=Platform.DESKTOP)
    signed = sign_token(tok, priv)
    return signed, pub, tok


# ---------------------------------------------------------------------------
# N-D-04 / N-E-04: Manipulierter Token
# ---------------------------------------------------------------------------
def test_ND04_tampered_payload_is_rejected():
    signed, pub, _ = _make_token()
    # Wir flippen ein Byte im Payload-Teil (Format: payload.signature)
    head, _, sig = signed.partition(".")
    assert head and sig
    mutated_head = head[:-1] + ("A" if head[-1] != "A" else "B")
    bad = f"{mutated_head}.{sig}"
    with pytest.raises(TokenError):
        verify_token(bad, public_key_hex=pub)


def test_ND04_tampered_signature_is_rejected():
    signed, pub, _ = _make_token()
    head, _, sig = signed.partition(".")
    bad = f"{head}.{('A' if sig[0] != 'A' else 'B') + sig[1:]}"
    with pytest.raises(TokenError):
        verify_token(bad, public_key_hex=pub)


def test_ND04_swapped_signing_key_is_rejected():
    """Ein mit Schluessel A signiertes Token darf nicht mit Schluessel B
    erfolgreich verifiziert werden."""
    signed_a, _pub_a, _ = _make_token()
    _, pub_b = generate_keypair()
    with pytest.raises(TokenError):
        verify_token(signed_a, public_key_hex=pub_b)


# ---------------------------------------------------------------------------
# N-E-01 / N-E-02: ungueltige / abgelaufene Tokens
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad", [
    "", ".", "no-dot-here", "...", "x.y.z.too.many.dots",
    "AAAA.BBBB",                          # Base64-aehnlich, aber sinnlos
    "{}.signature",
])
def test_NE01_invalid_token_strings(bad):
    _, pub = generate_keypair()
    with pytest.raises(TokenError):
        verify_token(bad, public_key_hex=pub)


def test_NE02_expired_token_raises_token_expired():
    signed, pub, _ = _make_token(expired=True)
    with pytest.raises(TokenExpired):
        verify_token(signed, public_key_hex=pub)


def test_NE02_expired_token_still_provides_payload():
    """TokenExpired traegt das Token mit, damit die App die Grace-Period
    auswerten kann - ohne Free-Pass."""
    signed, pub, tok = _make_token(expired=True)
    try:
        verify_token(signed, public_key_hex=pub)
    except TokenExpired as exc:
        assert exc.token is not None
        assert exc.token.customer_id == tok.customer_id
    else:
        pytest.fail("TokenExpired wurde nicht ausgeloest")


# ---------------------------------------------------------------------------
# N-E-03: ohne konfigurierten Public-Key
# ---------------------------------------------------------------------------
def test_NE03_empty_pubkey_is_rejected():
    signed, _, _ = _make_token()
    with pytest.raises(TokenError):
        verify_token(signed, public_key_hex="")


def test_NE03_garbage_pubkey_is_rejected():
    """Ein syntaktisch ungueltiger Public-Key darf NIE als 'valid'
    durchgehen. Der Aufrufer (license_gate) faengt sowohl TokenError
    als auch ValueError, deshalb akzeptieren wir beides."""
    signed, _, _ = _make_token()
    with pytest.raises((TokenError, ValueError)):
        verify_token(signed, public_key_hex="not-a-hex")


# ---------------------------------------------------------------------------
# N-D-06: Path-Traversal-Angriffe gegen Import
# ---------------------------------------------------------------------------
def test_ND06_path_traversal_is_blocked():
    with tempfile.TemporaryDirectory() as base:
        legit = Path(base) / "ok.ics"
        legit.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n", encoding="utf-8")

        # Validator MUSS Symlinks, '..'-Sequenzen und falsche Extensions
        # ablehnen. Wir testen mehrere Klassen.
        bad_inputs = [
            str(Path(base) / ".." / "ok.ics"),
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            str(legit) + "\x00.ics",      # NUL-Bytes
            str(legit.with_suffix(".exe")),
        ]
        for raw in bad_inputs:
            with pytest.raises(Exception):
                validate_import_path(raw, allowed_extensions=(".ics", ".vcf"))


def test_ND06_legit_path_accepted():
    with tempfile.TemporaryDirectory() as base:
        legit = Path(base) / "ok.ics"
        legit.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n", encoding="utf-8")
        result = validate_import_path(
            str(legit), allowed_extensions=(".ics", ".vcf"))
        assert Path(result).is_file()


# ---------------------------------------------------------------------------
# N-D-10 / Code-Injection-aehnliche Eingaben im Export
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("payload", [
    "Anna\nBEGIN:VCALENDAR\nMaliciousField:1\nEND:VCALENDAR",
    "title;",
    "title,with,commas",
    "title with \\ backslash",
    "​ zero-width space",
])
def test_ND10_escape_roundtrip_is_safe(payload: str):
    """Egal welche Sonderzeichen / Zeilenumbrueche wir reinwerfen -
    escape + unescape muss die Original-Eingabe wiederherstellen
    UND der escaped String darf KEINE rohen Steuerzeichen enthalten,
    die einen iCal/vCard-Parser verwirren wuerden."""
    escaped = escape_text(payload)
    assert "\n" not in escaped, "Roh-Newlines sind im Export verboten"
    assert ";" not in escaped.replace("\\;", ""), (
        "Roh-Semikolons (nicht escaped) sind im Export verboten")
    assert "," not in escaped.replace("\\,", ""), (
        "Roh-Kommas (nicht escaped) sind im Export verboten")
    assert unescape_text(escaped) == payload


# ---------------------------------------------------------------------------
# Bonus: Token-ID wird automatisch befuellt (Replay-Schutz)
# ---------------------------------------------------------------------------
def test_token_id_auto_populated_for_revocation():
    priv, _pub = generate_keypair()
    tok = LicenseToken(
        tier=Tier.PRO_MONTHLY, persons=2,
        purchased_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        customer_id="cust-x")
    sign_token(tok, priv)
    assert tok.token_id, "Token-ID muss automatisch gesetzt sein (Revocation)"
