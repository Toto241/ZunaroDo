# Play Console & Keystore — Schritt-fuer-Schritt

Stand: 2026-06-16. Ergaenzt [`GO_LIVE_TODO.md`](GO_LIVE_TODO.md) §1.2–1.3 mit
ausfuehrbaren Befehlen. Die Schritte selbst erfordern Zugriff auf Google Play
Console und lokale Geheimnisse — im Repo liegen nur die Helfer.

---

## 1. Upload-Keystore erstellen

**Windows (PowerShell):**

```powershell
pwsh ./release/create_upload_keystore.ps1
```

**Linux / macOS / WSL / CI-Vorbereitung:**

```bash
chmod +x ./release/create_upload_keystore.sh
./release/create_upload_keystore.sh
```

Ausgabe: `release/keystore/alltagshelfer-upload.jks` (gitignored).

Passwoerter sofort im Passwort-Manager sichern. Verlust = ohne Play App Signing
kein weiterer Upload moeglich.

---

## 2. Lokaler Release-Build (optional)

Nach Keystore-Erstellung:

```bash
export P4A_RELEASE_KEYSTORE="$PWD/release/keystore/alltagshelfer-upload.jks"
export P4A_RELEASE_KEYSTORE_PASSWD="<keystore-passwort>"
export P4A_RELEASE_KEYALIAS="alltagshelfer-upload"
export P4A_RELEASE_KEYALIAS_PASSWD="<key-passwort>"
# buildozer android release  (siehe MOBILE.md)
```

---

## 3. GitHub Actions — vier Repo-Secrets

Unter **Settings → Secrets and variables → Actions** fuer den Release-Workflow
(`.github/workflows/android-release.yml`):

| Secret | Inhalt |
|--------|--------|
| `ANDROID_KEYSTORE_BASE64` | Base64 der `.jks`-Datei |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore-Passwort |
| `ANDROID_KEY_ALIAS` | `alltagshelfer-upload` |
| `ANDROID_KEY_ALIAS_PASSWORD` | Key-Passwort |

Base64 erzeugen:

```bash
base64 -w0 release/keystore/alltagshelfer-upload.jks
# macOS: base64 -i release/keystore/alltagshelfer-upload.jks
```

Release-AAB: Workflow **Android Release (AAB)** dispatchen → Artefakt `dist/*.aab`.

---

## 4. Play Console — App anlegen

1. [Play Developer Console](https://play.google.com/console) — Konto (25 USD) + Identitaetspruefung.
2. **Neue App:** Name **ZunaroDo**, Sprache **de-DE**, Kategorie **PRODUCTIVITY**, kostenlos.
3. Package: `de.alltagshelfer.alltagshelfer` (aus [`playstore.yml`](../playstore.yml) — nach Erst-Release unveraenderbar).
4. **Data Safety:** Antworten aus [`DATA_SAFETY_CONSOLE_ANSWERS.md`](DATA_SAFETY_CONSOLE_ANSWERS.md) und `playstore.yml` → `data_safety`.
5. **Datenschutz-URL:** `https://toto241.github.io/ZunaroDo/privacy/` (Pages-Workflow pruefen: HTTP 200).
6. **IARC** Content-Rating-Fragebogen ausfuellen.
7. **Store-Listing:** Texte/Bilder aus `playstore.yml` — Sync-Helfer:

   ```bash
   python -m tools.playstore_sync validate
   python -m tools.playstore_sync export   # Mock-Vorschau
   ```

8. **Screenshots:** `assets/store/phone-*.png` (regenerieren:

   ```bash
   python -m tools.capture_store_screenshots
   python -m tools.gen_assets --check
   ```

---

## 5. Pre-Submit-Checkliste

```bash
python -m tools.playstore_check --strict
python -m tools.data_safety --check
python -m tools.privacy_policy --list-placeholders
PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring python3 -m unittest discover tests
python -m tools.gen_assets --check
```

Alle muessen gruen sein, bevor ein AAB in die Console hochgeladen wird.

---

## 6. Referenzen

- [`GO_LIVE_TODO.md`](GO_LIVE_TODO.md) — Gesamt-Checkliste
- [`CLOSED_TEST_RUNBOOK.md`](CLOSED_TEST_RUNBOOK.md) — Closed Testing
- [`docs/android/07_CICD.md`](../docs/android/07_CICD.md) — CI/CD
- [`deploy-payment-server.md`](deploy-payment-server.md) — optional IAP
