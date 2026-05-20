"""
CLI-Werkzeug fuer den Anbieter, um Lizenz-Tokens auszustellen.

Beispiel:

    # Einmalig: neues Keypair erzeugen (Private-Key SICHER aufbewahren!)
    python tools/gen_license.py keygen

    # Token fuer einen Kunden signieren
    python tools/gen_license.py sign \\
        --private-key 1a2b3c... \\
        --tier pro_annual \\
        --persons 4 \\
        --customer-id kunde@example.com \\
        --days 365

Die Ausgabe ist der Token-String, der dem Kunden zugesendet wird
(z.B. per Mail nach erfolgreicher Zahlung). Der Kunde fuegt ihn im
Einstellungen-Tab unter 'Lizenz aktivieren' ein.

Der Anbieter-Public-Key wird in services/license_token.py unter
DEFAULT_PUBLIC_KEY_HEX hinterlegt - bei jedem Release ueberschreiben,
damit Tokens verifizierbar sind.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Repo-Wurzel in sys.path bringen, damit das Tool aus tools/ heraus
# importieren kann.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.license_token import (LicenseToken, generate_keypair,
                                      sign_token)
from services.licensing import Platform, Tier


def cmd_keygen(args: argparse.Namespace) -> int:
    private_hex, public_hex = generate_keypair()
    print("Privater Schluessel (NIE veroeffentlichen):")
    print(f"  {private_hex}")
    print()
    print("Oeffentlicher Schluessel (in services/license_token.py hinterlegen):")
    print(f"  DEFAULT_PUBLIC_KEY_HEX = \"{public_hex}\"")
    return 0


def cmd_sign(args: argparse.Namespace) -> int:
    now = datetime.now(timezone.utc)
    token = LicenseToken(
        tier=Tier(args.tier),
        persons=args.persons,
        purchased_at=now,
        expires_at=now + timedelta(days=args.days),
        customer_id=args.customer_id,
        platform=Platform(args.platform),
    )
    print(sign_token(token, args.private_key))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="gen_license")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("keygen", help="Neues Ed25519-Keypair erzeugen")

    s = sub.add_parser("sign", help="Token signieren")
    s.add_argument("--private-key", required=True,
                    help="Privater Hex-Schluessel des Anbieters")
    s.add_argument("--tier", choices=[t.value for t in Tier
                                        if t.value.startswith("pro_")],
                    required=True)
    s.add_argument("--persons", type=int, required=True)
    s.add_argument("--customer-id", required=True,
                    help="Beliebige Kunden-Referenz (z.B. Mail-Hash)")
    s.add_argument("--days", type=int, default=365,
                    help="Gueltigkeitsdauer in Tagen (Default: 365)")
    s.add_argument("--platform",
                    choices=[p.value for p in Platform],
                    default="desktop")

    args = parser.parse_args(argv)
    if args.cmd == "keygen":
        return cmd_keygen(args)
    if args.cmd == "sign":
        return cmd_sign(args)
    parser.print_help()
    return 1


if __name__ == "__main__":                              # pragma: no cover
    sys.exit(main(sys.argv[1:]))
