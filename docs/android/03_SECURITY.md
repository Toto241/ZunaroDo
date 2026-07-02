# 03 - Sicherheitsrichtlinie

## 1. Secrets-Management

### Hard-Rule

> **Keine Secrets im Repository. Niemals.**

Konkret verboten in Git:

- API-Keys (Gemini, Paddle, Lemon Squeezy, Affiliate-Partner)
- Signing-Key-Passwörter, Keystore-Dateien (`.jks`, `.keystore`)
- Sync-Server-Token, Webhook-Secrets
- TLS-Zertifikate mit privatem Key
- License-Signing-Private-Key (Ed25519) - aktuell in
  `tools/gen_license.py` - der **private** Key liegt nicht im Repo,
  der **public** schon (verifizierbar, ungefährlich).

### Erlaubt im Repo

- Public-Verifikations-Keys (Ed25519 Public)
- Beispiel-Configs mit Platzhaltern (`*.example`, klar markiert)
- Test-Fixtures, die nie produktiv genutzt werden

### Quellen für Secrets

| Quelle | Verwendung |
| ------ | ---------- |
| Env-Vars zur Laufzeit | Lokal: `.env` (gitignored), `direnv`. Server: CI-Secrets, Container-Secrets. |
| OS-Keychain | Desktop: `keyring` (bereits in `services/config.py` vorgesehen via `SECRET_KEYS`). |
| **Android Keystore** | Native: `EncryptedSharedPreferences` + `MasterKey`; Kivy: pyjnius-Brücke zu `android.security.keystore` für sensible Tokens. |
| **CI-Secrets** | GitHub Actions `secrets.*`, niemals `echo $SECRET` in Logs. |

### Auto-Scan

In `tools/playstore_check.py` und CI:

- `gitleaks` (oder `detect-secrets`) gegen jeden PR.
- Regex-Heuristik im Custom-Checker (s. dort) für übliche Patterns
  (`AIza[0-9A-Za-z\-_]{35}` für Google API Keys etc.).
- Pre-Commit-Hook (`.git/hooks/pre-commit` + `pre-commit`-Framework
  empfohlen) für lokale Frühwarnung.

## 2. Netzwerkkommunikation

### TLS-only

| Anforderung | Wo enforced |
| ----------- | ----------- |
| Kein `http://` außer `localhost` | `tools/playstore_check.py` Regex-Scan |
| `usesCleartextTraffic = false` (oder fehlt) im Manifest | Buildozer fügt es nicht standardmäßig hinzu - explizit prüfen |
| `network_security_config.xml` mit `cleartextTrafficPermitted="false"` | optional, redundante Defense-in-Depth |
| TLS 1.2 minimum | OkHttp default, in Python via `requests` + aktuelles `certifi` (im Buildozer-Recipe `certifi` enthalten) |

### Certificate Pinning (optional, vorbereitet)

Empfohlen für die Sync-Server-Kommunikation:

**Native:**

```kotlin
val pinner = CertificatePinner.Builder()
  .add("sync.alltagshelfer.de", "sha256/AAAA...")
  .add("sync.alltagshelfer.de", "sha256/BBBB...") // Backup-Pin
  .build()
OkHttpClient.Builder().certificatePinner(pinner).build()
```

**Python (`requests` + `httpx`):**

Pinning ist in `requests` nicht nativ. Workaround bei Bedarf: eigener
`HTTPAdapter`-Subclass, der nach Handshake den SPKI-SHA256 prüft.
Bewusst noch nicht implementiert — der Sync-Client verifiziert TLS über
das konfigurierte CA-Bundle (`services/sync.py`); Pinning würde bei
Native-Bedarf nachgerüstet.

### API-Kommunikation - Hardening

- **Auth-Header** in `Authorization: Bearer …` - nie in Query-Strings.
- Server gibt `Cache-Control: no-store` für sensitive Endpunkte.
- Idempotenz-Header (`Idempotency-Key`) für POSTs, die Geld bewegen
  (Webhook-Receiver - bereits relevant für Paddle/Lemon Squeezy).
- Replay-Schutz: Webhook-Signaturen prüfen (Paddle: HMAC-SHA256;
  Lemon Squeezy: X-Signature) - in [services/license_events.py](../../services/license_events.py)
  bzw. der Webhook-Handler bereits angelegt - **Test in CI** erweitern.

## 3. Lokale Speicherung

### Datenbank

- SQLite in App-Sandbox (`MDApp.user_data_dir`) - bereits umgesetzt.
- **SQLCipher-DB-Verschlüsselung: AKTIVIERT.** `sqlcipher3` steht in
  `buildozer.spec` `requirements`, lokale Recipe unter `recipes/sqlcipher3/`.
  - Passphrase aus Android Keystore ableiten (Native:
    `EncryptedSharedPreferences`; Kivy: `pyjnius` -> Keystore,
    `DbKeyProvider.java` + `services/db_key.py`).
  - Recipe-Build via CI verifiziert (Robo-Workflow, grüner Lauf
    2026-06-10; Host-Validierung cipher_version 4.6.1). **Noch offen:**
    auf Gerät prüfen, dass `Database.encryption_mode == "sqlcipher"` ist
    (`python -m tools.verify_android_device --skip-ocr`).

### Settings

| Daten | Speicherort | Verschlüsselt? |
| ----- | ----------- | -------------- |
| Theme, Sprache, UI-Defaults | `SettingsRepository` (DB) | nein |
| Sync-URL, Profil-Pfade | `SettingsRepository` (DB) | nein |
| API-Keys, Sync-Tokens, Lizenz-Token | **OS-Keychain** + Android Keystore, **NICHT** in DB | ja |
| Letzte Eingaben (Form-Drafts) | In-Memory only | n/a |

### Dateien

- Belege/Output: `user_data_dir/ausgaben/` - Sandbox, OS-verschlüsselt
  (FDE/FBE aktiv ab Android 6, default ab Android 10).
- Logs: rotierend, max. 5 MB, älteste Datei wird überschrieben.
- Backups: gleicher Sandbox; bei Export via SAF wählt der Nutzer das
  Ziel selbst.

## 4. Schutz vor Reverse Engineering

### Native (Kotlin)

- **R8 (Full Mode)** mit `proguard-android-optimize.txt`:
  - Code-Shrinking
  - Optimization (Inlining, Dead-Code)
  - Obfuscation (Klassen-/Methodennamen)
  - Resource-Shrinking (`isShrinkResources = true`)
- `proguard-rules.pro` hält Keep-Regeln für Reflection-Pfade
  (Kotlin Coroutines, Retrofit, Room).
- **DexGuard** / **iXGuard** sind optional - für ZunaroDo nicht
  zwingend, da kein hochwertiger IP-Schutz nötig.

### Python (Kivy)

- `python-for-android` bündelt `.pyc`-Files - lesbar nach Dekompilierung.
- Hardening-Optionen:
  - `--release` + `--optimize-python` (lässt Docstrings/Asserts weg).
  - **Bytecode-Verschleierung** (pyarmor) - **nicht empfohlen** wegen
    Buildozer-Inkompatibilität und CI-Komplexität.
  - **Native-Logik** für sensible Pfade (Lizenzprüfung, Krypto) als
    C-Extension oder über Java-Bridge auslagern, falls IP-Schutz
    relevant wird.
- Lizenz-Validierung läuft signiert (Ed25519) - der lokale Code kann
  reverse-engineert werden, aber **ohne Private Key kann niemand neue
  Lizenzen erzeugen**. Das ist das echte Schutzschild.

## 5. Komponenten-Exposition

Pflichtprüfung im automatisierten Checker:

| Komponente | Regel |
| ---------- | ----- |
| `Activity` | `exported="true"` nur, wenn explizit von außen aufrufbar (Deep Link). Sonst `false`. |
| `Service` | wie oben; `foregroundServiceType` korrekt gesetzt. |
| `Receiver` | mit Intent-Filter -> exported expliziert; ohne -> `false`. |
| `ContentProvider` | `exported="false"` default. Falls extern: Permission-geschützt. |
| `BroadcastReceiver` (dyn.) | bei `registerReceiver()` ab API 33 `RECEIVER_NOT_EXPORTED` setzen, sofern nicht system-broadcast |

Aktuell exponiert Kivy genau **eine** Activity (Launcher).
Keine ContentProvider, keine Services. Bei Erweiterung Regeln in
`AndroidManifest.tmpl.xml` (von p4a generiert) prüfen.

## 6. WebViews

Falls jemals eine WebView in der App landet:

- `setJavaScriptEnabled(true)` **nur** bei eigenem Content; bei externen
  URLs aus.
- `setAllowFileAccess(false)`
- `setAllowFileAccessFromFileURLs(false)`
- `setAllowUniversalAccessFromFileURLs(false)`
- `WebViewClient.shouldOverrideUrlLoading` mit **expliziter
  URL-Allowlist**, alles andere -> System-Browser-Intent.
- `addJavascriptInterface` **nur** mit `@JavascriptInterface`-annotierten
  Methoden, niemals Reflection-Brücken.

Aktuell **keine WebView** in der App. Hinzufügen erfordert PR-Review +
Update dieses Dokuments.

## 7. Krypto

- Algorithmen: **AES-GCM** für Symmetric, **Ed25519** für Signaturen
  (bereits in [services/license_token.py](../../services/license_token.py)).
- Niemals: `AES/ECB/*`, `DES`, `MD5` für Integrität, `SHA-1` für
  Sicherheit.
- Schlüssel-Rotation: License-Signing-Key wird in der Releasenotes-Doku
  geführt; Rotation alle 24 Monate oder bei Verdacht.
- Random: `secrets`-Modul (Python) bzw. `SecureRandom` (Java) - nie
  `random.Random()`.

## 8. Root- / Tamper-Detection (optional)

Vorbereitete Hooks (nicht aktiv, sondern bereit):

- **Root-Detection (Native):** Google Play Integrity API (kostenfrei,
  ersetzt SafetyNet) - liefert `deviceIntegrity`, `appIntegrity`.
- **Repackaging-Detection:** Signatur-Check beim App-Start
  (`PackageManager.GET_SIGNING_CERTIFICATES`).
- **Debugger-Detection:** `Debug.isDebuggerConnected()` in Release-
  Builds; bei `true` -> Telemetry + degradierte Funktion (keine
  Lizenz-Privilegien).

Aktivierung erfolgt erst, wenn ein Bedrohungsmodell es rechtfertigt
(z.B. Premium-Funktionen breit verbreitet sind).

## 9. Sichere Defaults pro Build-Typ

| Setting | Debug | Release |
| ------- | ----- | ------- |
| Logging-Level | DEBUG | INFO |
| StrictMode | ALL+penaltyLog | OFF |
| Crashlytics / Sentry | OFF | ON (anonymisiert) |
| Cleartext-Traffic | nur `localhost` | aus |
| Allowed Backup | egal | **false** |
| Debuggable | true | false |
| Demo-Daten-Seed | erlaubt | **verboten** |
| Entwicklermenü | sichtbar | **verborgen** (auch nicht via Easter-Egg!) |

## 10. Pen-Test- & Audit-Rhythmus

- **Quartal:** Dependency-CVE-Scan (CI automatisch).
- **Halbjahr:** Static-Code-Security-Scan (z.B. `semgrep` + `bandit`
  für Python, `mobsfscan` für Android).
- **Jährlich:** Externer Pen-Test, mindestens **dynamisch** auf der
  Sync-Server-API.
- **Bei jedem Major-Release:** komplette Permission-Matrix neu prüfen.

## 11. Vorfallreaktion

1. Erkennung via Crashlytics/Logs/User-Report.
2. **Innerhalb 24 h** Risikoeinschätzung + Patch-Plan.
3. Hotfix-Branch (siehe [07_CICD.md](07_CICD.md)).
4. Bei datenschutzrelevanten Vorfällen: **72 h Meldepflicht** an
   Aufsichtsbehörde (DSGVO Art. 33) + User-Information falls hohes
   Risiko (Art. 34).
5. Post-Mortem in `docs/incidents/YYYY-MM-DD-<slug>.md`.

## 12. Schnell-Referenz "Was tun, wenn ..."

| Situation | Reaktion |
| --------- | -------- |
| Secret versehentlich committed | Sofort rotieren (neuer Key), Repo-History reinigen (`git filter-repo`), Force-Push nach Absprache, Incident-Doc. |
| User meldet "App fragt nach X-Permission" | Permission-Matrix prüfen, ob das gewollt ist. Ungewollt -> Bug-Issue + nächster Release. |
| Crash mit "TrustAnchor not found" | Cert-Pinning hat ein Update verpasst. Backup-Pin sollte greifen; sonst Rollout-Halt + Hotfix. |
| `pip-audit` meldet CVSS 9.x | Release-Halt, sofortiger Dependency-Upgrade, Re-Run aller Tests. |
| Play Store rejected wegen "Permission Misuse" | Issue erstellen, Permission-Matrix anpassen, Re-Submit mit Begründung. |
