"""
Selbstsignierte TLS-Zertifikate für den eingebetteten Sync-Server.

Der Sync-Server (services/sync_server.py) kann mit ``certfile``/``keyfile``
TLS sprechen - ihm fehlte aber ein Weg, ein Zertifikat zu erzeugen. Diese
Helfer schließen das: ein selbstsigniertes Cert+Key-Paar (RSA-2048, mit
SubjectAltName für Hostname/localhost/127.0.0.1), passend für ein lokales
Heimnetz-Setup (der Client pinnt das Cert).

`cryptography` wird bewusst **lazy** importiert, damit der Modul-Import auf
Systemen ohne funktionierendes cryptography-Backend nicht scheitert.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional


def generate_self_signed_cert(
        cert_path: str | Path,
        key_path: str | Path,
        *,
        common_name: str = "localhost",
        sans: Optional[Iterable[str]] = None,
        days_valid: int = 825,
        overwrite: bool = False) -> tuple[Path, Path]:
    """Schreibt ein selbstsigniertes Zertifikat (PEM) + privaten Schlüssel
    (PEM, unverschlüsselt) an die angegebenen Pfade und liefert sie zurück.

    `sans` ergänzt zusätzliche SubjectAltNames (DNS-Namen oder IPs); der
    `common_name`, ``localhost`` und ``127.0.0.1`` sind immer enthalten.
    Existierende Dateien werden nur mit ``overwrite=True`` ersetzt.
    """
    import ipaddress
    from datetime import datetime, timedelta, timezone

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    cert_path = Path(cert_path)
    key_path = Path(key_path)
    if not overwrite and cert_path.exists() and key_path.exists():
        return cert_path, key_path

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # SAN-Liste aufbauen: CN + localhost + 127.0.0.1 + Extras, dedupliziert.
    names = [common_name, "localhost", "127.0.0.1"]
    names += list(sans or [])
    san_entries: list = []
    seen: set[str] = set()
    for raw in names:
        n = str(raw).strip()
        if not n or n in seen:
            continue
        seen.add(n)
        try:
            san_entries.append(x509.IPAddress(ipaddress.ip_address(n)))
        except ValueError:
            san_entries.append(x509.DNSName(n))

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Alltagshelfer"),
    ])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=days_valid))
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None),
                       critical=True)
        .sign(key, hashes.SHA256())
    )

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()))
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    try:                                   # Schlüssel restriktiv (POSIX)
        key_path.chmod(0o600)
    except OSError:                        # pragma: no cover - z.B. Windows
        pass
    return cert_path, key_path
