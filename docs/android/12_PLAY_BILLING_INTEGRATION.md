# 12 — Google Play Billing (Integration)

**Status:** Code vollstaendig; **Geraete-/Server-Verifikation ausstehend**
(Buildozer nur unter WSL2/Linux; Play-Developer-API braucht Service-Account).  
**Entscheidung:** Play-Flavor nur Play Billing; Paddle/Lemon fuer Desktop/Web.

**Architektur-Kern:** Play Billing nutzt die bestehende Ed25519-Lizenz-
Token-Maschinerie wieder. Die App holt einen `purchaseToken` vom
BillingClient, schickt ihn an den Server (`/verify/play`); der Server
verifiziert ihn mit der Play Developer API und gibt ein **signiertes
Lizenz-Token** zurueck, das die App lokal anwendet (`apply_token_to_repo`).
So bleibt die Offline-Verifikation + der Tamper-Schutz unveraendert.

## Phase 0 — Vorbereitung ✅

- [x] Abo-Logik in `services/licensing.py`
- [x] Token-Aktivierung in `services/activation_flow.py`
- [x] Payment-Provider-Interface: `services/payment_provider.py`
- [ ] `playstore.yml` → `in_app_purchases: true` (erst NACH Geraete-Test)

## Phase 1 — Android-Bruecke ✅ (unverifiziert)

- [x] `src/android/java/de/alltagshelfer/billing/PlayBillingBridge.java`
      — BillingClient 6.x: connect, queryProductDetails, launchBillingFlow,
      PurchasesUpdatedListener, acknowledge
- [x] `services/play_billing_android.py` — pyjnius-Wrapper (connect,
      list_skus, purchase mit Token-Polling, acknowledge)
- [x] `buildozer.spec`: `android.gradle_dependencies` mit
      `com.android.billingclient:billing:6.2.1`, `android.add_src`, `pyjnius`
- [ ] **Smoke-Test auf Geraet mit License-Tester-Konto** ← offen

## Phase 2 — Server ✅ (unverifiziert)

- [x] `services/payment_adapter_play.py` — Purchase-Token → PaymentEvent;
      Google-API-Call als injizierbarer `verifier` (testbar)
- [x] `POST /verify/play` in `services/payment_server.py` — gibt das
      signierte Token an die App zurueck (KEINE Mail wie bei Webhooks)
- [x] Mapping Play-SKU → Tier in `payment_adapter_play.DEFAULT_PLAY_SKU_MAPPING`
- [ ] **Echter Service-Account + `purchases.subscriptionsv2.get`** ← offen
- [ ] Optional: RTDN Pub/Sub fuer Renewals/Cancellations

## Phase 3 — App-UX ✅

- [x] `mobile/screens/license.py`: Button „Pro ueber Play Store“
      (nur sichtbar, wenn Billing verfuegbar; Kauf laeuft im Worker-Thread)
- [ ] Console: Subscriptions + Free Trial 14 Tage anlegen

## Phase 4 — Release (offen)

```powershell
python -m tools.playstore_check --strict
# NACH erfolgreichem Geraete-Test: playstore.yml in_app_purchases: true
```

## Offene Verifikation (nur WSL2/Linux + Geraet + Server)

- [ ] `buildozer android debug` baut die Billing-Bruecke
- [ ] Kauf mit Lizenz-Tester-Konto liefert einen `purchaseToken`
- [ ] Server (`/verify/play`) verifiziert ihn mit echtem Service-Account
- [ ] App wendet das zurueckkommende Lizenz-Token an → Tier wird Pro
- [ ] `playstore.yml` `in_app_purchases: true` setzen + Re-Submit

## SKUs (Entwurf)

| SKU | Tier |
|-----|------|
| `zunarodo_pro_monthly` | Pro monatlich |
| `zunarodo_pro_yearly` | Pro jaehrlich |
| `zunarodo_pro_family` | Pro Familie |
