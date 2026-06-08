# Native Java-Bruecken (pyjnius)

Java-Quellwurzel fuer die Android-Integrationen. In `buildozer.spec`
ueber `android.add_src = src/android/java` eingebunden; die Paketstruktur
(`de/alltagshelfer/...`) MUSS mit den `package`-Deklarationen
uebereinstimmen, damit Gradle kompiliert.

| Paket | Datei | Zweck | Python-Gegenstueck | Gradle-Dep |
|-------|-------|-------|--------------------|-----------|
| `de.alltagshelfer.billing` | `PlayBillingBridge.java` | Google Play Billing 6.x | `services/play_billing_android.py` | `com.android.billingclient:billing:6.2.1` |
| `de.alltagshelfer.dbkey` | `DbKeyProvider.java` | SQLCipher-Key im Keystore | `services/db_key.py` | `androidx.security:security-crypto` |
| `de.alltagshelfer.ocr` | `MlKitOcrBridge.java` | On-Device-OCR | `services/ocr_android.py` | `com.google.mlkit:text-recognition` |

## ⚠️ Verifikation ausstehend

Buildozer laeuft nur unter WSL2/Linux, nicht Windows — diese Bruecken
sind in der aktuellen Umgebung **nicht baubar/testbar**. Vor Release:

```bash
buildozer android debug      # baut die Bruecken
# danach auf Geraet:
#  - Play Billing: Kauf mit Lizenz-Tester-Konto
#  - SQLCipher:   Database.encryption_mode == "sqlcipher"
#  - ML Kit OCR:  scan_receipt() liefert engine == "mlkit"
```

Details: [docs/android/12_PLAY_BILLING_INTEGRATION.md](../../../docs/android/12_PLAY_BILLING_INTEGRATION.md)
und [docs/android/13_NATIVE_INTEGRATIONS.md](../../../docs/android/13_NATIVE_INTEGRATIONS.md).

Referenz Billing: GitHub `android/play-billing-samples` (ClassyTaxi).
