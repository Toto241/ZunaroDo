# Payment-Produktion — Checkliste

Repo-seitig vorbereitet; Live-Betrieb erfordert MoR-Konto und Server.

## Im Repository (erledigt)

- [x] Ed25519-Public-Key in `services/license_token.py` (`DEFAULT_PUBLIC_KEY_HEX`)
- [x] `tools/payment_server.py` (Paddle + Lemon Webhooks)
- [x] `release/payment-server.env.example`
- [x] `release/deploy-payment-server.md`
- [x] `docker-compose.payment.yml`

## Vor Go-live (Betreiber)

1. `python tools/gen_license.py keygen` — Private Key **nur** auf dem Server
2. `release/payment-server.env` aus Example anlegen (`PRIV_HEX`, Webhook-Secrets)
3. Paddle/Lemon: Webhook → `https://<domain>/webhook/paddle` bzw. `/webhook/lemon`
4. Price-IDs in `--paddle-mapping` / Lemon-Variant-IDs abgleichen
5. Checkout-URLs in App-Settings (`checkout.url_*`) oder Umgebung setzen
6. Smoke: Testkauf → Token per E-Mail → Aktivierung in GUI / Mobile → Lizenz

Details: [PAYMENT.md](../PAYMENT.md).
