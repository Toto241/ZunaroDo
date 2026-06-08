# 02 - Play-Store-Compliance-Checkliste

Pflicht-Checks vor jedem Release. Jeder Punkt ist im automatisierten
Checker ([tools/playstore_check.py](../../tools/playstore_check.py)) als
Regel hinterlegt, sofern es technisch prüfbar ist (`A` = automatisiert,
`M` = manuell).

## 1. API-Level

| Anforderung | Wert | Wo gesetzt | Status |
| ----------- | ---- | ---------- | ------ |
| `targetSdkVersion` | **>=35** (Android 15) - Pflicht für neue Apps und App-Updates ab August 2025 | `buildozer.spec: android.api` | A |
| `compileSdkVersion` | =35 | implizit via `android.api` | A |
| `minSdkVersion` | =24 (Android 7.0) - deckt >=98 % aktiver Geräte | `buildozer.spec: android.minapi` | A |
| `targetSdk` bewusst gesetzt | nicht implizit per Default | Manifest-Lint | A |

**Konkrete Aktion (aktuell `android.api = 33`):**

```ini
# buildozer.spec
android.api = 35
android.minapi = 24
android.ndk_api = 24
```

Bei Anhebung auf API 35 zwingend testen:

- Foreground-Services-Restrictions (Android 14+, jetzt strenger in 15)
- Photo Picker statt READ_MEDIA_IMAGES, wo immer möglich
- `BroadcastReceiver` `RECEIVER_EXPORTED` / `RECEIVER_NOT_EXPORTED` explizit
- Predictive-Back-Gesture (`android:enableOnBackInvokedCallback="true"`)
- Edge-to-Edge-Layout (Android 15 default)

## 2. Manifest

| Check | Erläuterung | Modus |
| ----- | ----------- | ----- |
| Kein `android:debuggable="true"` im Release | Wird durch `buildozer android release` deaktiviert - im automatischen Check verifizieren | A |
| Kein `android:allowBackup="true"` für sensible Apps; statt dessen explizite `BackupAgent` oder `false` | ZunaroDo hält PII -> `allowBackup="false"` empfohlen | A |
| `android:exported` an JEDER Activity/Service/Receiver mit Intent-Filter **explizit** gesetzt | Pflicht ab API 31 | A |
| `usesCleartextTraffic` = `false` oder fehlt | siehe [03_SECURITY](03_SECURITY.md) | A |
| `android:networkSecurityConfig` referenziert | optional, aber empfohlen | A |
| `applicationId` stabil und nicht versehentlich mit Suffix in Production | Schutz vor falscher Veröffentlichung | A |
| `versionCode` monoton steigend, in CI verifiziert | Play Store lehnt sinkende Codes ab | A |
| `versionName` SemVer-konform | `MAJOR.MINOR.PATCH` | A |

## 3. Berechtigungen - Minimal-Prinzip

Vorgabe: **nur deklarieren, was tatsächlich genutzt wird**. Begründung
für jede Permission in [04_PRIVACY_PERMISSIONS.md](04_PRIVACY_PERMISSIONS.md).

| Permission | Status aktuell | Soll | Begründung |
| ---------- | -------------- | ---- | ---------- |
| `INTERNET` | deklariert | bleibt | Sync-Server, optional Gemini-Client |
| `ACCESS_NETWORK_STATE` | nicht deklariert | nur wenn benötigt | Connectivity-Check vor Sync |
| `POST_NOTIFICATIONS` | nicht deklariert | wenn Termin-Erinnerungen geplant | Android 13+ Pflicht |
| `READ_MEDIA_IMAGES` | nicht deklariert | **NICHT** hinzufügen | OCR/Beleg-Import nutzt Photo-Picker (keine Permission nötig) |
| `READ_EXTERNAL_STORAGE` | nicht deklariert | **verboten** auf API >= 33 | durch Scoped Storage ersetzt |
| `WRITE_EXTERNAL_STORAGE` | nicht deklariert | **verboten** | nutze App-Sandbox |
| `FOREGROUND_SERVICE` + `FOREGROUND_SERVICE_DATA_SYNC` | nicht deklariert | nur falls Hintergrund-Sync nötig | siehe Foreground-Service-Regeln unten |
| `RECEIVE_BOOT_COMPLETED` | nicht deklariert | nur wenn AlarmManager nach Reboot weiterlaufen muss | sparsam einsetzen |
| `SCHEDULE_EXACT_ALARM` | nicht deklariert | vermeiden, `USE_EXACT_ALARM` nur für Wecker/Kalender mit User-Anlass | Play Store prüft Notwendigkeit |
| `QUERY_ALL_PACKAGES` | nicht deklariert | **verboten** | sehr restriktiv von Google geprüft |

**Whitelist** der erlaubten Permissions wird in
[tools/playstore_check.py](../../tools/playstore_check.py) als `ALLOWED_PERMISSIONS`
hinterlegt. Jede Erweiterung erfordert PR-Review + Update der Permission-
Matrix in `04_PRIVACY_PERMISSIONS.md`.

## 4. Hintergrundprozesse & Foreground-Services

Play-Store-Vorgaben (verschärft ab Android 14):

- Jeder `Service` mit `foregroundServiceType` muss zur Laufzeit den
  korrekten Typ als zweiten Parameter an `startForeground()` übergeben.
- **Erlaubt für ZunaroDo (falls genutzt):** `dataSync`
  (Sync-Worker), `mediaPlayback` (nicht relevant), `health` (nicht
  relevant).
- **Nicht erlaubt:** `specialUse` ohne Sondergenehmigung.
- Dauer-Foreground-Services > 6 h: nur mit Begründung in der Play
  Console.

Standardweg in dieser App: **WorkManager** für periodischen Sync; nur
falls eine harte SLA-Anforderung besteht, wird ein Foreground-Service
verwendet.

## 5. Battery-Optimierung

- **Kein** `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` außer mit
  Sondergenehmigung. Play Store entfernt Apps, die das missbrauchen.
- WorkManager mit `setRequiresBatteryNotLow()` und `setRequiresCharging()`
  setzen, wo sinnvoll.
- Periodische Worker >= 15 Minuten Intervall (Android-Mindestwert).
- Kein dauerhaftes Wakelock.

## 6. Scoped Storage

- DB / Output / Logs / Backups landen **ausschließlich** in
  `Context.filesDir` (Native) bzw. `MDApp.user_data_dir` (Kivy).
- Geteilte Inhalte (Belege, PDFs) via **Storage Access Framework**
  (`ACTION_OPEN_DOCUMENT`, `ACTION_CREATE_DOCUMENT`) - **nie**
  hardgecodete `/sdcard/`-Pfade.
- Photo-Picker für Bilder; kein Crawl über `MediaStore` ohne klaren
  Use-Case.

**Aktueller Code:** [mobile/app.py:107](../../mobile/app.py#L107) speichert
`ausgaben/` im `user_data_dir` - korrekt. Beibehalten.

## 7. Datenschutz-Anforderungen (Pflicht für Play-Listing)

- **Privacy Policy URL** in der Play-Console hinterlegt; Inhalt in
  [legal/DATENSCHUTZ.md](../../legal/DATENSCHUTZ.md). MUSS:
  - Verantwortliche Stelle nennen
  - Datenkategorien benennen
  - Zwecke und Rechtsgrundlage je Kategorie
  - Drittempfänger (Google Gemini, Paddle, Lemon Squeezy) auflisten
  - Speicherdauer/Löschkonzept
  - Rechte (Auskunft, Löschung, Widerspruch)
  - Kontakt für Datenschutzanfragen
- **In-App-Verlinkung:** Datenschutz und AGB sind vom Settings-Screen
  aus mit zwei Taps erreichbar.
- **Data Safety Form** in Play Console: in
  [04_PRIVACY_PERMISSIONS.md](04_PRIVACY_PERMISSIONS.md) wird die
  Vorlage mit allen Antworten geführt.

## 8. Inhalt & Content Rating

- IARC-Fragebogen ausfüllen (Play Console). Erwartet: PEGI 3 / ESRB
  Everyone - die App enthält keine sensiblen Inhalte.
- Zielgruppe: **nicht primär für Kinder** -> "Mixed audiences" mit
  Altersgrenze >= 13.

## 9. Verbotene / problematische APIs (Heuristik)

Der Checker scannt das Repo auf folgende Smell-Patterns:

| Pattern | Begründung |
| ------- | ---------- |
| `WebView.setJavaScriptEnabled(true)` ohne `WebViewClient` mit URL-Allowlist | XSS-Risiko |
| `MODE_WORLD_READABLE` / `MODE_WORLD_WRITEABLE` | seit Android 4 deprecated |
| `setAllowFileAccessFromFileURLs(true)` | Lokale Datei-Exfiltration |
| `Cipher.getInstance("DES")` / `"AES/ECB/*"` | unsichere Krypto |
| `TrustManager` mit leerem `checkServerTrusted` | TLS-Bypass - direkter Reject |
| `Runtime.exec("su")` / `Runtime.exec("sh")` | Root-Versuche / unsichere Shell-Aufrufe |
| Verwendung von `Android Advertising ID` ohne Disclosure | DSGVO + Play Policy |

Im Python-Teil zusätzlich:

- `eval(`, `exec(` mit nicht-konstantem Argument
- `subprocess.*(shell=True)` ohne harten Whitelist-Check
- `requests` mit `verify=False`

## 10. Veraltete Bibliotheken

- Pin-Liste in `requirements.txt` + `dependabot` / Renovate aktiv.
- Quartalsweiser Scan via `pip-audit` (Python) bzw.
  `dependency-check`-Gradle-Plugin (Native).
- CVE-Hits mit CVSS >= 7 blocken den Release.

## 11. App-Bundle (AAB) statt APK

Für die Play-Console-Veröffentlichung **immer** AAB bauen:

- Native: `bundleRelease`.
- Kivy: `buildozer android release` erzeugt aktuell APK. Für AAB:
  `buildozer -v android release --aab` (Buildozer >= 1.5) oder manuell
  via `bundletool` aus APK-Splits umpacken. Migration auf AAB ist
  Pflicht-Item Sprint 1.

## 12. Play App Signing

- **Upload Key**: nur lokal beim Release-Owner, in einem Passwort-Manager.
- **App Signing Key**: bei Google (Play App Signing).
- Backup des Upload-Keys + `keystore.properties` in einem unabhängigen
  Tresor (z.B. Bitwarden Org-Vault), siehe
  [09_RELEASE_CHECKLIST.md](09_RELEASE_CHECKLIST.md).

## 13. Pflicht-Texte / Pflicht-Felder im Play Listing

| Feld | Quelle |
| ---- | ------ |
| App-Name | `ZunaroDo` |
| Kurzbeschreibung (<=80 Z.) | Marketing-Snippet, Pflicht in DE+EN |
| Lange Beschreibung (<=4000 Z.) | DE+EN |
| Screenshots | Phone + 7"-Tablet + 10"-Tablet, je 2-8 Stück |
| Feature Graphic | 1024x500, ohne Text-Lücken |
| App Icon | 512x512 PNG, transparent only wo nötig |
| Kategorie | `Productivity` |
| Email-Kontakt | Pflicht, geht an Support-Adresse |
| Website | Pflicht, verlinkt auf Landing |
| Privacy Policy URL | siehe oben |

## 14. Ads, Käufe, Abos

- **In-App-Käufe** (Pro-Lizenz) laufen aktuell über Paddle / Lemon
  Squeezy außerhalb der App. Sobald **digitale Inhalte in der App
  freigeschaltet** werden, MUSS Google Play Billing verwendet werden
  (sonst Reject "Payments Policy").
- "External offers" gemäß DMA sind ab 2024 in der EU erlaubt, aber
  Disclosure-pflichtig. Wir bleiben aktuell **außerhalb der App** für
  Vertragsabschluss - klare Trennung dokumentieren.
- Keine Werbung in der App -> kein Ad-SDK -> keine Ad-spezifische
  Compliance.

## 15. App-Defense-Center & Pre-Launch-Reports

- Pre-Launch-Report (Play Console -> Testing -> Pre-launch reports)
  bei jedem Internal-Track-Upload aktivieren.
- Crashes/ANRs aus dem Bericht in das Issue-Tracking spiegeln.
- Android Vitals-Schwellen einhalten:
  - **User-perceived ANR-Rate** < 0,47 %
  - **User-perceived Crash-Rate** < 1,09 %

## 16. Versionsverwaltung & Track-Strategie

Tracks (Reihenfolge der Promotion):

1. **Internal Testing** - Devs + QA, max. 100 Tester.
2. **Closed Testing (Alpha)** - 20-50 Power-User, mindestens 14 Tage,
   ab August 2024 Pflicht für neue Personal-Developer-Accounts.
3. **Open Testing (Beta)** - optional, public sign-up.
4. **Production** - Staged Rollout (10 % -> 25 % -> 50 % -> 100 %),
   automatischer Halt bei Crash-Rate-Anstieg.

## 17. Sonderkategorien

Wenn jemals eine dieser Funktionen hinzukommt, gelten verschärfte
Regeln (eigene Sub-Doku anlegen):

- **Health** / Medizinische Daten -> Sensitive-Data-Policy
- **Standort** im Hintergrund -> Hintergrund-Standort-Permission-Review
- **SMS/Call-Log** -> Permission-Declaration-Form Pflicht
- **AccessibilityService** -> nur, wenn primärer App-Zweck es
  rechtfertigt; sonst Reject

Aktuell **keine** dieser Kategorien aktiv -> nichts zu tun.

## 18. Selbst-Audit pro Release

Vor jedem Production-Push **muss** Folgendes grün sein:

- [ ] `python -m tools.playstore_check --strict` exit 0
- [ ] CI-Workflow `android-compliance` grün
- [ ] Crash-/ANR-Rate aus Vorversion unter Schwelle
- [ ] Privacy-Policy URL erreichbar (HTTP 200)
- [ ] AAB signiert mit Upload-Key
- [ ] `versionCode` > letzter Production-Code
- [ ] Release-Notes in `CHANGELOG.md` ergänzt
