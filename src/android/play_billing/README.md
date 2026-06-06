# Play Billing Bridge (Phase 1)

Java-Modul fuer Google Play Billing Library. Noch **nicht** in `buildozer.spec`
eingebunden — erst nach Review von `docs/android/12_PLAY_BILLING_INTEGRATION.md`.

## Dateien

- `PlayBillingBridge.java` — Stub; spaeter BillingClient 6.x
- Python: `services/play_billing_android.py`

## Buildozer (spaeter)

```ini
# buildozer.spec [app] — Beispiel, noch nicht aktiv:
# android.add_src = src/android/play_billing
# android.gradle_dependencies = com.android.billingclient:billing:7.1.1
```

## Referenz

MiniMaster `BillingClientWrapper.kt`, GitHub `android/play-billing-samples` (ClassyTaxi).
