# 13 — Native-Integrationen: KI, DB-Verschluesselung, OCR

**Status:** Code vorhanden; Android-Seite NICHT auf einem echten Build
verifiziert (Buildozer laeuft nur unter WSL2/Linux, nicht Windows).
Desktop-Pfade sind durch Tests abgesichert.

Dieses Dokument beschreibt, wie die drei „optionalen" Funktionen aus der
README im Android-Build tatsaechlich landen. Wichtigste Erkenntnis: **Man
kann sie NICHT einfach in `requirements` aufnehmen** — das SDK-/Native-
Tooling der Pakete ist mit python-for-android unvereinbar. Jede Funktion
hat deshalb einen eigenen, baubaren Pfad.

---

## 1. KI-Assistent (Gemini) — REST statt SDK

| | |
|---|---|
| Problem | `google-generativeai` zieht `grpcio`+`protobuf` (C-Extensions) nach — unter p4a praktisch nicht baubar. |
| Loesung | [services/gemini_rest.py](../../services/gemini_rest.py) spricht die Gemini-REST-API ueber `requests` (schon in `requirements`). |
| Auswahl | [services/llm_factory.py](../../services/llm_factory.py): SDK auf Desktop (falls importierbar), sonst REST. Erzwingen per `ALLTAGSHELFER_FORCE_GEMINI_REST=1`. |
| Tests | [tests/test_gemini_rest.py](../../tests/test_gemini_rest.py) — Text-, Function-Call-, Fehler- und Token-Pfade (HTTP gemockt). |

Beide Clients erfuellen `services.llm.LLMClient`; der Assistent merkt
keinen Unterschied. Desktop-Verhalten bleibt unveraendert (nutzt weiter
das SDK, sofern installiert).

**Verifizieren (mit echtem Key):**
```powershell
$env:GOOGLE_API_KEY = "..."
$env:ALLTAGSHELFER_FORCE_GEMINI_REST = "1"
python main.py   # Assistent muss antworten, ohne google-generativeai
```

---

## 2. DB-Verschluesselung (SQLCipher)

| | |
|---|---|
| Python-Seite | **fertig** — [database.py](../../database.py) nutzt `sqlcipher3` + `PRAGMA key`, sobald ein Key vorliegt. |
| Key-Ableitung | [services/db_key.py](../../services/db_key.py): Env (Desktop) **oder** Android-Keystore via Bruecke. Liefert `None`, solange `sqlcipher3` fehlt → kein Startabbruch. |
| Keystore-Bruecke | [src/android/java/de/alltagshelfer/dbkey/DbKeyProvider.java](../../src/android/java/de/alltagshelfer/dbkey/DbKeyProvider.java) — EncryptedSharedPreferences + MasterKey (AES256_GCM). |
| p4a-Recipe | [recipes/sqlcipher3/__init__.py](../../recipes/sqlcipher3/__init__.py) — baut `sqlcipher3` gegen die OpenSSL-Recipe. |
| Gradle-Dep | `androidx.security:security-crypto` (in `buildozer.spec`). |

**Aktivieren:** in `buildozer.spec` `sqlcipher3` an `requirements`
anhaengen. `p4a.local_recipes = ./recipes` ist bereits gesetzt.

**Verifiziert (CI):** Der Robo-Workflow baut das Debug-APK inklusive
`sqlcipher3`-Recipe auf einem Linux-Runner (grüner Lauf 2026-06-10);
Host-Validierung: cipher_version 4.6.1, falscher Key abgewiesen. Offen
bleibt der Gerätecheck `Database.encryption_mode == "sqlcipher"`.

---

## 3. OCR fuer Kassenbons — ML Kit (On-Device)

| | |
|---|---|
| Problem | `pytesseract` braucht die native Tesseract-Engine, `easyocr` braucht PyTorch — beide unter p4a unrealistisch. |
| Loesung | Google ML Kit Text Recognition laeuft **lokal** auf dem Geraet (kein Cloud-Call → datenschutzkonform). |
| Bruecke | [src/android/java/de/alltagshelfer/ocr/MlKitOcrBridge.java](../../src/android/java/de/alltagshelfer/ocr/MlKitOcrBridge.java) + [services/ocr_android.py](../../services/ocr_android.py). |
| Einbindung | [services/ocr.py](../../services/ocr.py) `_select_engine()` bevorzugt `mlkit`, faellt sonst auf tesseract/easyocr zurueck. |
| Gradle-Dep | `com.google.mlkit:text-recognition` (in `buildozer.spec`). |

**! Verifizieren (Geraet):** Kassenbon scannen → `scan_receipt()` muss
`engine == "mlkit"` liefern. ML Kit laedt das Sprachmodell beim ersten
Aufruf nach.

---

## Zusammengefasste Build-Konfiguration (buildozer.spec)

```ini
requirements = python3,kivy==2.3.1,kivymd==1.2.0,certifi,requests,pyjnius,sqlcipher3
android.add_src = src/android/java
android.enable_androidx = True
android.gradle_dependencies = com.android.billingclient:billing:6.2.1, androidx.security:security-crypto:1.1.0-alpha06, com.google.mlkit:text-recognition:16.0.1
p4a.local_recipes = ./recipes
```

**Verifikationsstand:**
- [x] `buildozer android debug` baut mit `pyjnius` + AndroidX durch (CI, 2026-06-10)
- [x] `sqlcipher3`-Recipe baut (in `requirements` aktiv; CI + Host-Validierung)
- [ ] DB ist auf dem Geraet tatsaechlich verschluesselt (adb + `tools.verify_android_device`)
- [ ] ML-Kit-OCR liefert Text auf dem Geraet
- [ ] Gemini-REST antwortet im gebauten APK
