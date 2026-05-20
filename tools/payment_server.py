"""
CLI-Wrapper fuer den Anbieter, um den Webhook-Server zu starten.

Beispiel:

    export PRIV_HEX=...                 # Ed25519-Private-Key (geheim!)
    export PADDLE_SECRET=whsec_...
    export LEMON_SECRET=lssecret_...
    export SMTP_HOST=smtp.example.com
    export SMTP_USER=anbieter@example.com
    export SMTP_PASS=...

    python tools/payment_server.py \\
        --host 127.0.0.1 --port 7000 \\
        --paddle-mapping pri_ANNUAL=pro_annual:2,pri_FAMILY=pro_family:5 \\
        --lemon-mapping 1234=pro_monthly:2

Hinter einem Reverse-Proxy mit TLS betreiben (Caddy/Nginx). Wenn
direkt am Internet, dann --cert/--key fuer eingebautes TLS setzen.

Der Anbieter konfiguriert in Paddle / Lemon Squeezy:
  Webhook-URL: https://<deine-domain>/webhook/paddle  (bzw. /lemon_squeezy)
  Signing-Secret: das jeweilige PADDLE_SECRET / LEMON_SECRET
  Events: subscription.created, subscription.renewed, ...
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.licensing import Tier
from services.output import OutputService, SmtpConfig
from services.payment import PriceMapping
from services.payment_adapter_lemon import parse_event as lemon_parse
from services.payment_adapter_paddle import parse_event as paddle_parse
from services.payment_issuer import IssuerConfig
from services.payment_server import WebhookServerConfig, serve

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("payment-server")


def _parse_mapping(spec: str) -> PriceMapping:
    """'pri_ANNUAL=pro_annual:2,pri_FAMILY=pro_family:5' -> dict."""
    mapping: PriceMapping = {}
    if not spec:
        return mapping
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        key, _, value = chunk.partition("=")
        tier_raw, _, persons_raw = value.partition(":")
        try:
            mapping[key.strip()] = (Tier(tier_raw.strip()),
                                       int(persons_raw or "1"))
        except (ValueError, KeyError) as exc:
            raise SystemExit(f"Mapping kaputt '{chunk}': {exc}")
    return mapping


def _smtp_from_env() -> SmtpConfig | None:
    if not os.environ.get("SMTP_HOST"):
        return None
    return SmtpConfig(
        host=os.environ["SMTP_HOST"],
        port=int(os.environ.get("SMTP_PORT", "587")),
        username=os.environ.get("SMTP_USER", ""),
        password=os.environ.get("SMTP_PASS", ""),
        sender=os.environ.get("SMTP_SENDER", os.environ.get("SMTP_USER", "")),
        use_starttls=os.environ.get("SMTP_STARTTLS", "true").lower()
                      in ("1", "true", "yes"),
    )


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="payment-server",
                                 description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7000)
    p.add_argument("--paddle-mapping", default="",
                    help="Komma-separiert: pri_ID=tier:persons")
    p.add_argument("--lemon-mapping", default="",
                    help="Komma-separiert: variant_id=tier:persons")
    p.add_argument("--audit-log", default="logs/payment_audit.jsonl")
    p.add_argument("--cert", help="TLS-Zertifikat (PEM)")
    p.add_argument("--key", help="TLS-Private-Key (PEM)")
    args = p.parse_args(argv)

    priv = os.environ.get("PRIV_HEX", "")
    if not priv:
        print("ERROR: Umgebungsvariable PRIV_HEX fehlt "
               "(Ed25519-Private-Key des Anbieters).", file=sys.stderr)
        return 2

    paddle_cfg = None
    if os.environ.get("PADDLE_SECRET"):
        paddle_cfg = WebhookServerConfig(
            secret=os.environ["PADDLE_SECRET"],
            price_mapping=_parse_mapping(args.paddle_mapping),
            parser=paddle_parse,
        )
    lemon_cfg = None
    if os.environ.get("LEMON_SECRET"):
        lemon_cfg = WebhookServerConfig(
            secret=os.environ["LEMON_SECRET"],
            price_mapping=_parse_mapping(args.lemon_mapping),
            parser=lemon_parse,
        )
    if paddle_cfg is None and lemon_cfg is None:
        print("ERROR: Setze mindestens PADDLE_SECRET oder LEMON_SECRET.",
               file=sys.stderr)
        return 2

    smtp = _smtp_from_env()
    if smtp is None:
        log.warning("Kein SMTP konfiguriert - Tokens werden zwar signiert, "
                    "aber NICHT per Mail versendet. Audit-Log enthaelt sie.")
        send_mail = None
    else:
        # Output-Service nur fuer den Mailer-Teil instanziieren.
        out = OutputService(output_dir=Path("ausgaben"), smtp=smtp)
        send_mail = out.send_smtp

    issuer = IssuerConfig(
        private_key_hex=priv,
        audit_log_path=Path(args.audit_log),
        send_mail=send_mail,
    )

    log.info("Starte Payment-Webhook-Server auf %s:%s (paddle=%s, lemon=%s)",
             args.host, args.port,
             bool(paddle_cfg), bool(lemon_cfg))
    server = serve(args.host, args.port,
                    paddle=paddle_cfg, lemon=lemon_cfg, issuer=issuer,
                    certfile=args.cert, keyfile=args.key)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Stop")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":                              # pragma: no cover
    sys.exit(main(sys.argv[1:]))
