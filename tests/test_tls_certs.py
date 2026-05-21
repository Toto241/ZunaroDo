"""
Tests für die TLS-Zertifikatserstellung (services.tls_certs).

Läuft nur, wenn ein funktionierendes ``cryptography``-Backend vorhanden
ist (auf CI gegeben). Wo nicht (z.B. fehlendes/kaputtes pyo3-Backend),
wird sauber übersprungen - ``BaseException`` fängt auch eine
``PanicException`` beim Import ab.
"""
from __future__ import annotations

import os
import ssl
import tempfile
import unittest
from pathlib import Path

try:
    from cryptography import x509  # noqa: F401
    from services.tls_certs import generate_self_signed_cert
    _HAS_CRYPTO = True
except BaseException:                                # noqa: BLE001
    _HAS_CRYPTO = False


@unittest.skipUnless(_HAS_CRYPTO, "cryptography-Backend nicht verfuegbar")
class TestSelfSignedCert(unittest.TestCase):

    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="ah_tls_"))
        self.cert = self.dir / "cert.pem"
        self.key = self.dir / "key.pem"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_generates_valid_cert_and_key(self) -> None:
        cert, key = generate_self_signed_cert(
            self.cert, self.key, common_name="example.lan")
        self.assertTrue(cert.exists() and key.exists())
        from cryptography import x509
        loaded = x509.load_pem_x509_certificate(cert.read_bytes())
        cn = loaded.subject.get_attributes_for_oid(
            x509.NameOID.COMMON_NAME)[0].value
        self.assertEqual(cn, "example.lan")
        # SANs enthalten CN + localhost + 127.0.0.1
        san = loaded.extensions.get_extension_for_class(
            x509.SubjectAlternativeName).value
        dns = set(san.get_values_for_type(x509.DNSName))
        self.assertIn("example.lan", dns)
        self.assertIn("localhost", dns)

    def test_loads_into_ssl_context(self) -> None:
        generate_self_signed_cert(self.cert, self.key)
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=str(self.cert), keyfile=str(self.key))

    def test_does_not_overwrite_without_flag(self) -> None:
        generate_self_signed_cert(self.cert, self.key)
        first = self.cert.read_bytes()
        generate_self_signed_cert(self.cert, self.key)        # no overwrite
        self.assertEqual(self.cert.read_bytes(), first)
        generate_self_signed_cert(self.cert, self.key, overwrite=True)
        self.assertNotEqual(self.cert.read_bytes(), first)    # neu erzeugt

    def test_key_permissions_restrictive_on_posix(self) -> None:
        if os.name != "posix":
            self.skipTest("nur POSIX")
        generate_self_signed_cert(self.cert, self.key)
        self.assertEqual(self.key.stat().st_mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
