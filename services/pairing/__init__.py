"""
Sichere Geraetekopplung - Krypto- und Speicher-Fundament.

Dieses Subpackage implementiert Schritt fuer Schritt das in
PAIRING.md beschriebene Konzept. Aktueller Stand:

  - identity      Geraete-Langzeit-Identitaet (Ed25519), Fingerprint,
                  Sign/Verify.
  - secure_store  Abstraktion fuer plattformeigene Schluesselablage
                  (Windows DPAPI, macOS Keychain, Linux SecretService
                  via 'keyring'; In-Memory-Variante fuer Tests).

Noch nicht enthalten (folgt in eigenen PRs):

  - handshake     SPAKE2-PAKE + Ed25519-Transcript-Signatur.
  - qr / usb / sms  Die drei Pairing-Wege.
  - transport     TLS-1.3-PSK-Integration in services/sync_server.py.
  - mobile bridges  Android-Keystore und iOS-Keychain-Adapter.
"""
from services.pairing.identity import (
    DeviceIdentity,
    FINGERPRINT_BITS,
    compute_fingerprint,
    generate_identity,
    sign,
    verify,
)
from services.pairing.secure_store import (
    InMemorySecureStore,
    KeyringSecureStore,
    SecureStore,
    SecureStoreError,
    default_secure_store,
)

__all__ = [
    "DeviceIdentity",
    "FINGERPRINT_BITS",
    "compute_fingerprint",
    "generate_identity",
    "sign",
    "verify",
    "InMemorySecureStore",
    "KeyringSecureStore",
    "SecureStore",
    "SecureStoreError",
    "default_secure_store",
]
