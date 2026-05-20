"""
Tests fuer das Pairing-Fundament (services/pairing/).

Pruefen:
  * Identity: Schluesselpaar-Erzeugung, Sign/Verify-Roundtrip,
    deterministischer und plattformunabhaengiger Fingerprint,
    Fehlerverhalten bei falschen Eingaben.
  * SecureStore: In-Memory-Backend roundtrippt; KeyringSecureStore
    wird nur ausgefuehrt, wenn das keyring-Backend lokal verfuegbar
    ist (sonst geskippt - CI ohne D-Bus oder ohne keyring-PyPI).
"""
from __future__ import annotations

import os
import re
import unittest

from services.pairing import (
    DeviceIdentity,
    FINGERPRINT_BITS,
    InMemorySecureStore,
    KeyringSecureStore,
    SecureStore,
    SecureStoreError,
    compute_fingerprint,
    default_secure_store,
    generate_identity,
    sign,
    verify,
)


FINGERPRINT_RE = re.compile(r"^[A-Z2-7]{4}(-[A-Z2-7]{4}){4}$")
"""Format: 5 Gruppen Base32-Alphabet (RFC 4648) zu 4 Zeichen, durch '-' getrennt."""


class TestIdentity(unittest.TestCase):

    def test_generate_identity_returns_valid_pair(self) -> None:
        identity, priv = generate_identity()
        self.assertIsInstance(identity, DeviceIdentity)
        self.assertEqual(len(identity.public_key), 32)
        self.assertEqual(len(priv), 32)
        # device_id ist eine UUIDv4 als String
        self.assertRegex(
            identity.device_id,
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        )
        self.assertTrue(identity.device_name)

    def test_generate_identity_accepts_custom_name(self) -> None:
        identity, _ = generate_identity(device_name="Mein PC")
        self.assertEqual(identity.device_name, "Mein PC")

    def test_two_identities_are_distinct(self) -> None:
        a, pa = generate_identity()
        b, pb = generate_identity()
        self.assertNotEqual(a.device_id, b.device_id)
        self.assertNotEqual(a.public_key, b.public_key)
        self.assertNotEqual(pa, pb)

    def test_sign_verify_roundtrip(self) -> None:
        identity, priv = generate_identity()
        msg = b"hallo welt"
        sig = sign(priv, msg)
        self.assertEqual(len(sig), 64)  # Ed25519-Signaturen sind 64 Byte
        self.assertTrue(verify(identity.public_key, msg, sig))

    def test_verify_rejects_tampered_message(self) -> None:
        identity, priv = generate_identity()
        sig = sign(priv, b"original")
        self.assertFalse(verify(identity.public_key, b"original ", sig))
        self.assertFalse(verify(identity.public_key, b"manipuliert", sig))

    def test_verify_rejects_wrong_public_key(self) -> None:
        _, priv = generate_identity()
        other, _ = generate_identity()
        sig = sign(priv, b"x")
        self.assertFalse(verify(other.public_key, b"x", sig))

    def test_verify_returns_false_for_garbage_signature(self) -> None:
        identity, _ = generate_identity()
        self.assertFalse(verify(identity.public_key, b"x", b"\x00" * 64))
        self.assertFalse(verify(identity.public_key, b"x", b"zu kurz"))


class TestFingerprint(unittest.TestCase):

    def test_fingerprint_format(self) -> None:
        identity, _ = generate_identity()
        fp = identity.fingerprint
        self.assertEqual(len(fp), 5 * 4 + 4)  # 20 Zeichen + 4 Trennstriche
        self.assertRegex(fp, FINGERPRINT_RE)

    def test_fingerprint_is_deterministic(self) -> None:
        pk = b"\x01" * 32
        self.assertEqual(compute_fingerprint(pk), compute_fingerprint(pk))

    def test_fingerprint_differs_for_different_keys(self) -> None:
        a = compute_fingerprint(b"\x01" * 32)
        b = compute_fingerprint(b"\x02" * 32)
        self.assertNotEqual(a, b)

    def test_fingerprint_known_vector(self) -> None:
        # Plattformunabhaengiger Konformitaetstest. SHA-256 ist
        # eindeutig, Base32 (RFC 4648) ebenso - der Wert hier muss
        # auf Windows / Linux / macOS / Android / iOS identisch sein.
        # Aenderungen an FINGERPRINT_BITS oder der Encoding-Strategie
        # brechen diesen Test bewusst.
        all_zero = b"\x00" * 32
        # SHA-256(0x00 * 32) beginnt mit Bytes
        #   66 68 7a ad f8 62 bd 77 6c 8f c1 8b 8e 9f 8e 20...
        # Base32(rfc4648) der ersten 13 Bytes = "MZUHVLPYMK6XO7DPYGFY", ohne Pad.
        # Davon nehmen wir die ersten 20 Zeichen und gruppieren sie.
        fp = compute_fingerprint(all_zero)
        # Schwacher Vertrag: Format passt + Wert ist nicht trivial.
        self.assertRegex(fp, FINGERPRINT_RE)
        # Harter Vertrag: exakter Wert. Wenn dieser bricht, ist das
        # ein Protokollbruch - alle gekoppelten Geraete muessen neu
        # gekoppelt werden.
        self.assertEqual(fp, _expected_fingerprint_for_zero_key())

    def test_fingerprint_rejects_wrong_length(self) -> None:
        with self.assertRaises(ValueError):
            compute_fingerprint(b"")
        with self.assertRaises(ValueError):
            compute_fingerprint(b"\x00" * 31)
        with self.assertRaises(ValueError):
            compute_fingerprint(b"\x00" * 33)

    def test_fingerprint_bits_constant_matches_format(self) -> None:
        # Wenn jemand FINGERPRINT_BITS auf einen Wert setzt, der nicht
        # 5*4*5 = 100 ist, dann ist das Anzeigeformat (5 Gruppen zu 4)
        # nicht mehr stimmig.
        self.assertEqual(FINGERPRINT_BITS, 100)


def _expected_fingerprint_for_zero_key() -> str:
    """Berechnet den erwarteten Fingerprint fuer den Nullvektor - in
    eigener, expliziter Form. So ist der Test gegen sich selbst
    redundant, aber nicht zirkulaer: die Erwartung wird hier mit der
    Standard-Bibliothek nachgebaut.
    """
    import base64
    import hashlib

    digest = hashlib.sha256(b"\x00" * 32).digest()
    encoded = base64.b32encode(digest[:13]).decode("ascii").rstrip("=")[:20]
    return "-".join(encoded[i : i + 4] for i in range(0, 20, 4))


class TestInMemorySecureStore(unittest.TestCase):

    def setUp(self) -> None:
        self.store: SecureStore = InMemorySecureStore()

    def test_set_and_get_roundtrip(self) -> None:
        self.store.set("k1", b"hallo")
        self.assertEqual(self.store.get("k1"), b"hallo")

    def test_get_missing_returns_none(self) -> None:
        self.assertIsNone(self.store.get("nicht-da"))

    def test_overwrite_replaces_value(self) -> None:
        self.store.set("k", b"alt")
        self.store.set("k", b"neu")
        self.assertEqual(self.store.get("k"), b"neu")

    def test_delete_makes_key_disappear(self) -> None:
        self.store.set("k", b"x")
        self.store.delete("k")
        self.assertIsNone(self.store.get("k"))

    def test_delete_missing_is_silent(self) -> None:
        self.store.delete("never-existed")  # darf nicht werfen

    def test_list_keys_filters_by_prefix(self) -> None:
        self.store.set("peer.A", b"1")
        self.store.set("peer.B", b"2")
        self.store.set("identity", b"3")
        self.assertEqual(self.store.list_keys(""), ["identity", "peer.A", "peer.B"])
        self.assertEqual(self.store.list_keys("peer."), ["peer.A", "peer.B"])

    def test_rejects_non_bytes(self) -> None:
        with self.assertRaises(TypeError):
            self.store.set("k", "string-ist-falsch")  # type: ignore[arg-type]

    def test_protocol_runtime_check(self) -> None:
        self.assertIsInstance(self.store, SecureStore)


def _keyring_works() -> bool:
    """Prueft, ob das Standard-Keyring-Backend einen Roundtrip schafft.

    GitHub-Hosted-Linux hat keinen D-Bus - dort scheitert das
    'null'/'fail'-Backend bereits beim set_password. Wir wollen die
    Tests dann ueberspringen, statt sie rot zu faerben.
    """
    try:
        import keyring  # noqa
    except ImportError:
        return False
    try:
        store = KeyringSecureStore(service="alltagshelfer.pairing.testprobe")
        store.set("__probe__", b"x")
        ok = store.get("__probe__") == b"x"
        store.delete("__probe__")
        # Manifest mitaufraeumen
        try:
            import keyring as _kr
            _kr.delete_password(
                "alltagshelfer.pairing.testprobe", "__manifest__"
            )
        except Exception:
            pass
        return ok
    except Exception:
        return False


@unittest.skipUnless(
    _keyring_works(),
    "Kein funktionsfaehiges keyring-Backend (GitHub-CI, kein D-Bus, "
    "keyring nicht installiert).",
)
class TestKeyringSecureStore(unittest.TestCase):

    SERVICE = "alltagshelfer.pairing.test"

    def setUp(self) -> None:
        self.store = KeyringSecureStore(service=self.SERVICE)
        # Test-Isolation: vorhandene Reste loeschen
        for k in list(self.store.list_keys()):
            self.store.delete(k)

    def tearDown(self) -> None:
        for k in list(self.store.list_keys()):
            self.store.delete(k)
        # Manifest mit-aufraeumen
        try:
            import keyring
            keyring.delete_password(self.SERVICE, "__manifest__")
        except Exception:
            pass

    def test_roundtrip(self) -> None:
        payload = bytes(range(32))
        self.store.set("identity", payload)
        self.assertEqual(self.store.get("identity"), payload)

    def test_list_keys_returns_set_keys(self) -> None:
        self.store.set("peer.A", b"x")
        self.store.set("peer.B", b"y")
        self.assertEqual(self.store.list_keys("peer."), ["peer.A", "peer.B"])

    def test_delete_removes_from_list(self) -> None:
        self.store.set("tmp", b"x")
        self.assertIn("tmp", self.store.list_keys())
        self.store.delete("tmp")
        self.assertNotIn("tmp", self.store.list_keys())

    def test_manifest_key_is_reserved(self) -> None:
        with self.assertRaises(ValueError):
            self.store.set("__manifest__", b"x")


class TestDefaultSecureStore(unittest.TestCase):

    def test_env_override_to_memory(self) -> None:
        old = os.environ.get("ALLTAGSHELFER_PAIRING_BACKEND")
        os.environ["ALLTAGSHELFER_PAIRING_BACKEND"] = "memory"
        try:
            store = default_secure_store()
            self.assertIsInstance(store, InMemorySecureStore)
        finally:
            if old is None:
                del os.environ["ALLTAGSHELFER_PAIRING_BACKEND"]
            else:
                os.environ["ALLTAGSHELFER_PAIRING_BACKEND"] = old

    def test_returns_some_secure_store(self) -> None:
        # Mindestens das In-Memory-Fallback ist immer verfuegbar.
        store = default_secure_store()
        self.assertIsInstance(store, SecureStore)


if __name__ == "__main__":
    unittest.main()
