"""
HKDF-SHA-256-Schluesselableitung (RFC 5869).

Duenner, gut testbarer Wrapper um cryptography.hazmat.primitives.kdf.hkdf.
Wir kapseln ihn, damit die Pairing-Module nicht direkt mit `hazmat`
arbeiten und Aufrufe einheitlich aussehen.

Konvention im Pairing-Stack:
  - `secret` ist das PAKE-Ergebnis (MS) oder ein anderes hochentropisches Geheimnis.
  - `salt` ist deterministisch und oeffentlich (z.B. sid, "sync-psk", ...).
  - `info` separiert Verwendungszwecke ("pair/v1", "sync-psk", ...).
"""
from __future__ import annotations

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def hkdf_sha256(secret: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    """Liefert `length` Bytes Schluesselmaterial.

    Default `length=32` passt zu ChaCha20-Poly1305-Schluesseln und
    Ed25519-Seed-Eingaben.
    """
    if length <= 0 or length > 255 * 32:  # HKDF-SHA-256 hard limit
        raise ValueError(f"Ungueltige Schluessellaenge {length}")
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    ).derive(secret)
