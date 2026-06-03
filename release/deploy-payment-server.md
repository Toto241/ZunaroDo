# Payment-Server (Produktion)

Kurzanleitung zum Betrieb von `tools/payment_server.py` mit Paddle oder Lemon Squeezy.

## Voraussetzungen

1. Ed25519-Keypair: `python tools/gen_license.py keygen`
2. **Public-Key** in `services/license_token.py` → `DEFAULT_PUBLIC_KEY_HEX`
3. **Private-Key** nur auf dem Server als `PRIV_HEX` (siehe `payment-server.env.example`)

## Start (Beispiel)

```bash
set -a && source release/payment-server.env && set +a
python tools/payment_server.py \
  --host 0.0.0.0 --port 7000 \
  --paddle-mapping pri_ANNUAL=pro_annual:2,pri_FAMILY=pro_family:5,pri_MONTHLY=pro_monthly:2
```

Webhook-URL beim MoR: `https://<ihre-domain>/webhook/paddle` (oder `/webhook/lemon`).

Details: [PAYMENT.md](../PAYMENT.md).
