"""
Geraete-Langzeit-Identitaet fuer das Pairing-Konzept.

Jedes Geraet besitzt ein eigenes Ed25519-Schluesselpaar (RFC 8032).
Der private Schluessel verlaesst das Geraet nie - er liegt im
plattformeigenen Secure-Store (siehe services.pairing.secure_store).
Der oeffentliche Schluessel + ein abgeleiteter Fingerprint werden
unverschluesselt mit den gekoppelten Geraeten geteilt.

Konventionen, wie in PAIRING.md Kapitel 4 festgelegt:

  * Signaturen / Verifikation: Ed25519 (32-Byte-Private, 32-Byte-Public).
  * Fingerprint = die ersten 100 Bit von SHA-256(public_key_bytes),
    Base32-kodiert in fuenf Gruppen zu vier Zeichen, durch '-' getrennt.
    Beispiel: K7QH-3M2N-5T8X-PVR4-A9BC.
  * device_id = UUIDv4 als String. Reine Anzeige-/Routing-Information,
    keine sicherheitsrelevante Bedeutung.
  * device_name: vom Nutzer editierbar, defaultet auf den Hostnamen.

Was dieses Modul *nicht* tut: Speichern. Das Aufrufer-Modul holt sich
einen `SecureStore` und legt `private_key_bytes` dort ab.
"""
from __future__ import annotations

import base64
import hashlib
import socket
import uuid
from dataclasses import dataclass
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


FINGERPRINT_BITS = 100
"""Wie viele Bit des SHA-256-Hashes in den Fingerprint einfliessen.

100 Bit = 20 Base32-Zeichen = 5 Gruppen zu 4 Zeichen. Genug
Kollisionssicherheit fuer den Out-of-Band-Vergleich (2^-50 fuer den
Geburtstagsangriff), kurz genug zum Vorlesen am Telefon.
"""

_FINGERPRINT_GROUPS = 5
_FINGERPRINT_GROUP_LEN = 4


@dataclass(frozen=True)
class DeviceIdentity:
    """Oeffentliche Identitaet eines Geraets.

    Der private Schluessel ist hier bewusst *nicht* enthalten - er
    wird getrennt im Secure-Store gefuehrt. Diese Trennung haelt
    DeviceIdentity-Objekte gefahrlos serialisierbar und loggbar.
    """

    device_id: str
    device_name: str
    public_key: bytes  # 32-Byte Ed25519 Raw-Public-Key

    @property
    def fingerprint(self) -> str:
        return compute_fingerprint(self.public_key)


def generate_identity(device_name: Optional[str] = None) -> tuple[DeviceIdentity, bytes]:
    """Erzeugt ein neues Ed25519-Schluesselpaar und eine DeviceIdentity.

    Returns:
        (identity, private_key_bytes)

        Der Aufrufer ist verantwortlich, `private_key_bytes` *sofort*
        in einen `SecureStore` zu legen und die Referenz darauf in
        keiner Logdatei und keiner Klartextspeicherung zu hinterlassen.
    """
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    identity = DeviceIdentity(
        device_id=str(uuid.uuid4()),
        device_name=device_name or _default_device_name(),
        public_key=public_bytes,
    )
    return identity, private_bytes


def compute_fingerprint(public_key: bytes) -> str:
    """Berechnet den menschenlesbaren Fingerprint eines Public-Keys.

    Die ersten FINGERPRINT_BITS (=100) Bit von SHA-256(public_key)
    werden Base32-kodiert und in 5 Gruppen zu 4 Zeichen formatiert.

    Dieselbe Berechnung muss auf allen Plattformen identisch sein -
    Konformitaetstests in tests/test_pairing.py pruefen das.
    """
    if len(public_key) != 32:
        raise ValueError(
            f"Ed25519-Public-Key muss 32 Bytes lang sein, war {len(public_key)}"
        )
    digest = hashlib.sha256(public_key).digest()
    # 100 Bit / 5 Bit pro Base32-Zeichen = 20 Zeichen.
    # base64.b32encode arbeitet byteweise; 13 Bytes (=104 Bit) liefert
    # nach dem Strippen des Paddings genug Zeichen, von denen wir die
    # ersten 20 (=100 Bit) verwenden. Die uebrigen 4 Bit werfen wir weg.
    raw = digest[: (FINGERPRINT_BITS + 7) // 8]
    encoded = base64.b32encode(raw).decode("ascii").rstrip("=")
    encoded = encoded[: _FINGERPRINT_GROUPS * _FINGERPRINT_GROUP_LEN]
    groups = [
        encoded[i : i + _FINGERPRINT_GROUP_LEN]
        for i in range(0, len(encoded), _FINGERPRINT_GROUP_LEN)
    ]
    return "-".join(groups)


def sign(private_key_bytes: bytes, message: bytes) -> bytes:
    """Signiert `message` mit dem Ed25519-Private-Key."""
    key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    return key.sign(message)


def verify(public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
    """Prueft eine Ed25519-Signatur. Gibt True/False zurueck.

    Wirft *keine* Exception bei ungueltiger Signatur - das vermeidet,
    dass Aufrufer die Pruefung aus Versehen mit try/except ueberspringen.
    """
    try:
        key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        key.verify(signature, message)
        return True
    except (InvalidSignature, ValueError):
        return False


def _default_device_name() -> str:
    try:
        name = socket.gethostname().strip()
    except Exception:
        name = ""
    return name or "unbekannt"
