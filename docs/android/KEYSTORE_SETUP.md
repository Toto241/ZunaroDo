# Upload-Keystore und signiertes AAB

## 1. Keystore erzeugen (einmalig)

```bash
./scripts/generate-upload-keystore.sh upload.keystore
```

Alias und Passwort notieren. **Keystore und Passwort verlieren = kein App-Update mehr möglich.**

## 2. GitHub Secrets setzen

Repository → Settings → Secrets and variables → Actions:

| Secret | Wert |
|--------|------|
| `ANDROID_KEYSTORE_BASE64` | `base64 -w0 upload.keystore` (Linux) |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore-Passwort |
| `ANDROID_KEY_ALIAS` | z. B. `zunarodo-upload` |
| `ANDROID_KEY_ALIAS_PASSWORD` | Alias-Passwort |

## 3. AAB bauen

Actions → **Android Release (AAB)** → Run workflow.

Das Artefakt `aab-*` enthält das signierte App Bundle für den Play-Store-Upload.

## 4. Play App Signing

In der Play Console beim ersten Upload **Play App Signing** aktivieren. Google signiert das an Nutzer ausgelieferte Bundle; der Upload-Key bleibt bei Ihnen.

## 5. Verifikation (lokal)

```bash
apksigner verify --verbose dist/*.aab
```
