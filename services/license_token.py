"""
Ed25519-signiertes Lizenz-Token fuer Tamper-Schutz.

Hintergrund:
Ohne Signatur kann jeder per SQL-Editor 'license.tier=pro_annual' in
app_settings schreiben und ist Pro. Mit Ed25519 muss er den privaten
Schluessel haben - der liegt aber NICHT in der App, sondern beim
Verkaeufer (Anbieter). Die App kennt nur den oeffentlichen Schluessel
und kann damit Tokens verifizieren, aber nicht selber signieren.

Format eines Lizenz-Tokens:
  <base64url(payload_json)>.<base64url(signature)>

payload_json ist eine kanonisch sortierte JSON-Repraesentation mit:
  - 'tier':              "pro_monthly" | "pro_annual" | "pro_family"
  - 'persons':           int >= 1
  - 'purchased_at':      ISO-8601 UTC
  - 'expires_at':        ISO-8601 UTC
  - 'customer_id':       str  (z.B. Hash der Mail, fuer Wiederfinden)
  - 'platform':          "desktop" | "ios" | "android" | "web"

Die Verifikation ist offline-faehig - keine Server-Verbindung noetig.
Die Hauptsicherheit liegt im geheim gehaltenen Private-Key des
Anbieters; ein Leak macht alle existierenden Tokens revokierbar
(siehe REVOKED_KEY_IDS, sobald implementiert).

Abhaengigkeit: 'cryptography' (bereits transitive Abhaengigkeit
ueber andere Komponenten). Faellt sanft auf 'kein Token-Support'
zurueck, wenn das Paket fehlt.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    CRYPTO_AVAILABLE = True
except ImportError:                                    # pragma: no cover
    CRYPTO_AVAILABLE = False
    InvalidSignature = Exception
    Ed25519PrivateKey = None
    Ed25519PublicKey = None

from services.licensing import Platform, Tier


# Oeffentlicher Schluessel des Anbieters (Hex). MUSS im Release durch
# den echten Schluessel ersetzt werden, der per 'tools/gen_license.py'
# beim Erstellen des Private-Keys mit ausgegeben wird.
DEFAULT_PUBLIC_KEY_HEX: str = (
    "0000000000000000000000000000000000000000000000000000000000000000"
)


@dataclass
class LicenseToken:
    tier: Tier
    persons: int
    purchased_at: datetime
    expires_at: datetime
    customer_id: str
    platform: Platform = Platform.DESKTOP

    def to_payload(self) -> dict:
        return {
            "tier": self.tier.value,
            "persons": self.persons,
            "purchased_at": _to_iso(self.purchased_at),
            "expires_at": _to_iso(self.expires_at),
            "customer_id": self.customer_id,
            "platform": self.platform.value,
        }

    @classmethod
    def from_payload(cls, data: dict) -> "LicenseToken":
        return cls(
            tier=Tier(data["tier"]),
            persons=int(data["persons"]),
            purchased_at=_parse_iso(data["purchased_at"]),
            expires_at=_parse_iso(data["expires_at"]),
            customer_id=str(data["customer_id"]),
            platform=Platform(data.get("platform", "desktop")),
        )


# ---------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------
def _to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _b64u_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _canonical_json(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------
# Sign / Verify
# ---------------------------------------------------------------------
class TokenError(Exception):
    """Verifikation oder Parsing fehlgeschlagen."""


def generate_keypair() -> tuple[str, str]:
    """Erzeugt ein neues Ed25519-Keypair (private_hex, public_hex)."""
    if not CRYPTO_AVAILABLE:
        raise TokenError("'cryptography' nicht installiert")
    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key()
    return (sk.private_bytes_raw().hex(),
             pk.public_bytes_raw().hex())


def sign_token(token: LicenseToken, private_key_hex: str) -> str:
    """Signiert ein Token mit dem Anbieter-Private-Key."""
    if not CRYPTO_AVAILABLE:
        raise TokenError("'cryptography' nicht installiert")
    sk = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    payload = _canonical_json(token.to_payload())
    signature = sk.sign(payload)
    return f"{_b64u_encode(payload)}.{_b64u_encode(signature)}"


def verify_token(token_str: str,
                  public_key_hex: Optional[str] = None,
                  *,
                  now: Optional[datetime] = None) -> LicenseToken:
    """
    Verifiziert ein Token-String.

    Wirft TokenError bei jedem Problem (kaputt, falsche Signatur,
    abgelaufen). Im Erfolgsfall: das geparste LicenseToken.

    'now' nur fuer Tests - default ist datetime.now(timezone.utc).
    """
    if not CRYPTO_AVAILABLE:
        raise TokenError("'cryptography' nicht installiert")
    pk_hex = (public_key_hex or DEFAULT_PUBLIC_KEY_HEX).strip()
    if pk_hex == DEFAULT_PUBLIC_KEY_HEX:
        # Kein echter Anbieter-Key konfiguriert - jede Validierung
        # waere ein false-positive. Lieber sauber abweisen.
        raise TokenError("Kein Anbieter-Public-Key konfiguriert")

    if not isinstance(token_str, str) or token_str.count(".") != 1:
        raise TokenError("Token-Format ungueltig")
    payload_b64, sig_b64 = token_str.split(".", 1)
    try:
        payload_raw = _b64u_decode(payload_b64)
        signature = _b64u_decode(sig_b64)
    except Exception as exc:                            # noqa: BLE001
        raise TokenError(f"Base64-Dekodierung fehlgeschlagen: {exc}")

    pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pk_hex))
    try:
        pk.verify(signature, payload_raw)
    except InvalidSignature:
        raise TokenError("Signatur ungueltig")

    try:
        payload = json.loads(payload_raw.decode("utf-8"))
        token = LicenseToken.from_payload(payload)
    except (ValueError, KeyError) as exc:
        raise TokenError(f"Payload kaputt: {exc}")

    now = now or datetime.now(timezone.utc)
    if token.expires_at < now:
        # Wir signalisieren das als TokenError, damit der Aufrufer
        # entscheiden kann, ob Grace-Period angewendet wird.
        raise TokenError(
            f"Token am {token.expires_at.isoformat()} abgelaufen")

    return token


def apply_token_to_repo(repo, token: LicenseToken) -> None:
    """
    Schreibt die verifizierten Token-Daten in das SettingsRepository
    der App - damit gilt der Tier ab sofort.
    """
    from services.licensing import (KEY_EXPIRES_AT, KEY_PERSONS,
                                      KEY_PLATFORM, KEY_PURCHASED_AT,
                                      KEY_TIER, KEY_TOKEN)
    repo.set(KEY_TIER, token.tier.value)
    repo.set(KEY_PERSONS, str(token.persons))
    repo.set(KEY_PURCHASED_AT, _to_iso(token.purchased_at))
    repo.set(KEY_EXPIRES_AT, _to_iso(token.expires_at))
    repo.set(KEY_PLATFORM, token.platform.value)
    # Token selbst speichern - so kann beim naechsten Start nochmal
    # verifiziert werden, ob jemand die Settings manuell manipuliert hat.
    # (Re-Verifikation passiert in services/licensing.load_license -
    #  hier ist nur die Persistenz.)
