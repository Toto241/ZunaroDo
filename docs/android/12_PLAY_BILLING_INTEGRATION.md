# 12 — Google Play Billing (Integrations-Roadmap)

**Status:** Geplant (Blocker fuer Production-Abo auf Play)  
**Entscheidung:** [[SecBrain]](../../../SecBrain/brain/topics/zunarodo-play-billing-entscheidung.md) — Play-Flavor nur Play Billing; Paddle/Lemon fuer Desktop/Web.

## Phase 0 — Vorbereitung (erledigt / laufend)

- [x] Abo-Logik in `services/licensing.py`
- [x] Token-Aktivierung (Uebergang) in `services/activation_flow.py`
- [x] Payment-Provider-Interface: `services/payment_provider.py`
- [ ] `playstore.yml` → `in_app_purchases: true` (erst nach Phase 3)

## Phase 1 — Android-Bruecke (Kivy / Buildozer)

Python-for-android hat **kein** fertiges Play-Billing-Recipe. Optionen:

| Option | Aufwand | Hinweis |
|--------|---------|---------|
| A) Kleines Java-Modul + pyjnius | Hoch | Billing Library 6.x in `src/android/` |
| B) Flutter-Plugin-Insel | Sehr hoch | Nicht empfohlen |
| C) Nur Token bis Billing live | Niedrig | Nur Closed Test, nicht Production-Abo |

**Referenz:** MiniMaster `BillingClientWrapper.kt`, GitHub `android/play-billing-samples` (ClassyTaxi).

### Buildozer-Schritte (spaeter)

1. `android.gradle_dependencies` — `billing:6.x`
2. Java-Klasse `PlayBillingBridge.java` — `queryProducts`, `launchBillingFlow`
3. `services/play_billing_android.py` — pyjnius-Wrapper
4. Smoke-Test auf Geraet mit License-Tester-Konto

## Phase 2 — Server

- Purchase-Token-Verifikation (Play Developer API)
- Optional: RTDN Pub/Sub (wie MiniMaster `subscription.ts`)
- Mapping Play-SKU → `License` in `licensing.py`

## Phase 3 — App-UX

- `mobile/screens/license.py`: Button „Pro ueber Play Store“
- Play-Flavor: externen Token-Dialog ausblenden oder sekundaer
- Console: Subscriptions + Free Trial 14 Tage

## Phase 4 — Release

```powershell
python -m tools.playstore_check --strict
# playstore.yml in_app_purchases: true
```

## SKUs (Entwurf)

| SKU | Tier |
|-----|------|
| `zunarodo_pro_monthly` | Pro monatlich |
| `zunarodo_pro_yearly` | Pro jaehrlich |
| `zunarodo_pro_family` | Pro Familie |
