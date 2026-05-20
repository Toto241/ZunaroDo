"""
Sichere Geraetekopplung - Krypto- und Speicher-Fundament.

Dieses Subpackage implementiert Schritt fuer Schritt das in
PAIRING.md beschriebene Konzept. Aktueller Stand:

  - identity      Geraete-Langzeit-Identitaet (Ed25519), Fingerprint,
                  Sign/Verify.
  - secure_store  Abstraktion fuer plattformeigene Schluesselablage
                  (Windows DPAPI, macOS Keychain, Linux SecretService
                  via 'keyring'; In-Memory-Variante fuer Tests).
  - kdf           HKDF-SHA-256-Wrapper.
  - transcript    Kanonische Serialisierung des Pairing-Transcripts.
  - session       PairingSession - State-Machine fuer den eigentlichen
                  Handshake (SPAKE2-PAKE + Ed25519-Transcript-Signatur).

Noch nicht enthalten (folgt in eigenen PRs):

  - qr / usb / sms  Die drei Pairing-Wege als Anwendungs-Schicht.
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
from services.pairing.kdf import hkdf_sha256
from services.pairing.secure_store import (
    InMemorySecureStore,
    KeyringSecureStore,
    SecureStore,
    SecureStoreError,
    default_secure_store,
)
from services.pairing.session import (
    PairingError,
    PairingMethod,
    PairingResult,
    PairingRole,
    PairingSession,
    run_pairing_in_memory,
)
from services.pairing.transcript import (
    TRANSCRIPT_VERSION,
    make_transcript,
    transcript_hash,
)

__all__ = [
    # identity
    "DeviceIdentity",
    "FINGERPRINT_BITS",
    "compute_fingerprint",
    "generate_identity",
    "sign",
    "verify",
    # secure_store
    "InMemorySecureStore",
    "KeyringSecureStore",
    "SecureStore",
    "SecureStoreError",
    "default_secure_store",
    # kdf
    "hkdf_sha256",
    # transcript
    "TRANSCRIPT_VERSION",
    "make_transcript",
    "transcript_hash",
    # session
    "PairingError",
    "PairingMethod",
    "PairingResult",
    "PairingRole",
    "PairingSession",
    "run_pairing_in_memory",
]

