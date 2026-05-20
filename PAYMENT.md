# Payment-Flow - Operations-Doku fuer den Anbieter

Dieses Dokument beschreibt, wie der **Anbieter** der App die Bezahlung
einrichtet. End-User brauchen das nicht zu lesen.

## Empfohlene Architektur

```
                          +-------------------+
                          |   Paddle / Lemon  |
                          |   (Merchant of    |
                          |    Record)        |
                          +---------+---------+
                                    | Webhook (HTTPS)
                                    v
+--------------+   Mail-Token  +----+--------------------+
|              | <-------------+ tools/payment_server.py  |
|  End-User    |               | (eigener Server)         |
|  (Desktop/   |               +--------------------------+
|   Mobile)    |
|              |               +--------------------------+
|              | --------------> services.activation_flow |
|              |  Token paste  |  in der App (lokal)      |
+--------------+               +--------------------------+
```

**Merchant of Record (MoR)** ist hier der Schluessel: Paddle/Lemon Squeezy
uebernehmen EU-Umsatzsteuer (OSS), Rechnungsstellung, Refund-Abwicklung
und das 14-Tage-Widerrufsrecht. Du als Anbieter brauchst kein Stripe-
Konto, keine OSS-Registrierung, kein eigenes Inkasso.

## Setup-Schritte

### 1. Einmal: Ed25519-Keypair erzeugen

```bash
python tools/gen_license.py keygen
```

Der private Schluessel landet **nur** auf dem Anbieter-Server (in der
Env-Var `PRIV_HEX`). Der oeffentliche Schluessel wird in den App-Release
einkompiliert (`services/license_token.py:DEFAULT_PUBLIC_KEY_HEX`).

**Verlierst du den Private-Key**: alle existierenden Tokens bleiben gueltig
bis Ablauf, aber du kannst keine neuen mehr signieren. Neuen Key
generieren, alle aktiven Abos manuell re-issuen.

**Wird der Private-Key kompromittiert**: ein Angreifer kann sich selbst
gueltige Tokens erstellen. Du musst dann (a) neuen Key generieren,
(b) App-Release mit neuem Public-Key herausbringen, (c) alle Bestands-
kunden neue Tokens schicken. Aufwand entsprechend - **also gut aufpassen**.

### 2. Paddle einrichten

1. Paddle-Account anlegen, Produkte/Preise erstellen.
2. Produkt-Konfiguration: drei Pro-Preise (monthly, annual, family).
3. Notiere die Price-IDs (Format `pri_01H...`).
4. Webhook-URL hinterlegen: `https://<deine-domain>/webhook/paddle`
5. Webhook-Secret notieren (Header `Paddle-Signature` wird damit signiert).
6. Events abonnieren:
   - `subscription.created`
   - `subscription.activated`
   - `subscription.renewed`
   - `subscription.canceled`
   - `transaction.completed` (fuer One-Time-Purchases falls geplant)

### 3. Webhook-Server starten

```bash
export PRIV_HEX="<dein-private-hex-key>"
export PADDLE_SECRET="whsec_..."
export SMTP_HOST=smtp.example.com
export SMTP_USER=anbieter@example.com
export SMTP_PASS=...

python tools/payment_server.py \
    --host 127.0.0.1 --port 7000 \
    --paddle-mapping pri_ANNUAL=pro_annual:2,pri_FAMILY=pro_family:5,pri_MONTHLY=pro_monthly:2
```

Hinter einem Reverse-Proxy mit TLS betreiben (Caddy/Nginx). Wenn direkt
am Internet, dann `--cert/--key` setzen.

**Caddy-Beispiel:**

```caddy
payments.deine-domain.de {
    reverse_proxy 127.0.0.1:7000
}
```

### 4. Lemon Squeezy als Alternative oder Zweit-Provider

Lemon Squeezy hat sich besonders fuer kleine Anbieter etabliert:
30-Sekunden-Onboarding, transparente Gebuehren (5 % + 50 ct pro Tx).
Identischer Workflow wie Paddle, nur andere Secret-Env-Var und
URL-Pfad:

```bash
export LEMON_SECRET="..."
python tools/payment_server.py \
    --lemon-mapping 12345=pro_annual:2,12346=pro_family:5
```

Webhook-URL in Lemon Squeezy: `https://<deine-domain>/webhook/lemon_squeezy`

### 5. Checkout-URLs in den End-User-Apps verteilen

In den `app_settings`-Tabellen der ausgelieferten App-Versionen
hinterlegt der Nutzer (oder das Onboarding) die Checkout-URLs:

| Setting-Key | Inhalt |
| --- | --- |
| `checkout.url_monthly` | https://checkout.paddle.com/... |
| `checkout.url_annual` | https://checkout.paddle.com/... |
| `checkout.url_family` | https://checkout.paddle.com/... |

Sobald gesetzt, erscheinen im Settings-Tab Buttons „Pro monatlich
kaufen" usw., die den Browser auf die Hosted-Checkout-Seite oeffnen.

## End-to-End-Flow

1. Nutzer klickt im Settings-Tab auf „Pro jaehrlich kaufen".
2. Browser oeffnet die Paddle-Checkout-Seite.
3. Nutzer bezahlt - Paddle schickt Webhook an deinen Server.
4. `payment_server.py` verifiziert HMAC, parsed das Event, ruft
   `payment_issuer.handle_event()` auf.
5. Issuer signiert ein Ed25519-Token, sendet es per Mail an den Kunden,
   schreibt einen Audit-Log-Eintrag.
6. Kunde kopiert den Token aus der Mail, fuegt ihn im Settings-Tab ein.
7. App verifiziert mit dem eingebauten Public-Key, persistiert ihn,
   schaltet alle Pro-Funktionen frei.

## Idempotenz und Retries

Bezahldienstleister retryen Webhooks teilweise stundenlang. Der Issuer
verwendet die `transaction_id` als Idempotency-Key und ueberspringt
bereits verarbeitete Events stillschweigend (200 OK an den Provider).
Du wirst also nicht doppelte Tokens an denselben Kunden schicken,
selbst wenn Paddle dasselbe Event 10x sendet.

## Was du NICHT brauchst

- Kein eigenes Stripe-Konto (es sei denn du willst keine MoR)
- Keine OSS/MOSS-Registrierung (uebernimmt Paddle/Lemon)
- Keine Rechnungs-Software (uebernimmt Paddle/Lemon)
- Keine eigene PCI-Compliance (Karten kommen nie auf deinen Server)
- Keine SQL-Datenbank fuer Abos (Audit-Log als JSONL reicht voellig -
  Source-of-Truth bleibt Paddle/Lemon)

## Refunds, Streit, Stornos

- Paddle-Dashboard: Refund-Button. Webhook `adjustment.created` wird
  geschickt, Issuer notiert das im Audit-Log (kein neuer Token).
- Wenn der Kunde reklamiert, dass sein Token nicht ankam: im Audit-Log
  nach customer_email suchen, Token nochmal manuell mailen
  (`python tools/gen_license.py sign --customer-id ...`).

## Monitoring

- `tail -f logs/payment_audit.jsonl` - Live-Verfolgung
- Provider-Dashboard fuer MRR, Churn, Refund-Quote
- Health-Endpoint: `curl https://<deine-domain>/health` -> `{"ok": true}`
