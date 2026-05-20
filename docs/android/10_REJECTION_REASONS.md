# 10 - Typische Play-Store-Ablehnungsgründe & Gegenmaßnahmen

Diese Liste fasst die in der Praxis häufigsten Reject-Gründe für Apps
des Produktivitäts-/Lifestyle-Segments zusammen und ordnet jeweils
konkrete Maßnahmen zu, die wir bereits ergriffen haben oder ergreifen
müssen. Status-Spalte: ✅ erfüllt, ⚠️ Action nötig, 🟦 nicht relevant
für aktuellen Funktionsumfang.

## 1. API-Level & Outdated-Apps

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "App nutzt eine veraltete Version der Android-API." | `android.api = 35` setzen, jährlich auf das vom Play Store geforderte Min-Target nachziehen. | ⚠️ aktuell 33 → in [buildozer.spec](../../buildozer.spec) anheben |
| "Update der App, das das Target-API-Level senkt, ist nicht erlaubt." | CI verifiziert `versionCode` und `targetSdk` monoton. | ✅ (Checker-Regel) |
| Min-SDK zu niedrig, Kompatibilität nicht prüfbar | `android.minapi = 24`, CI-Build auf API-24-Emulator als Smoke. | ⚠️ Smoke ergänzen |

## 2. Permissions

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "Unbegründete Berechtigung X." | Permission-Matrix [04_PRIVACY_PERMISSIONS.md](04_PRIVACY_PERMISSIONS.md), Whitelist im Checker. | ✅ |
| "SMS/Call-Log/Contacts ohne Permissions Declaration Form." | Wir verwenden keine dieser Permissions. | 🟦 |
| "AccessibilityService außerhalb Zweckbestimmung." | Kein eigener AccessibilityService. | 🟦 |
| "All Files Access (MANAGE_EXTERNAL_STORAGE) ohne Anerkennung." | Wir nutzen Scoped Storage; Permission nie deklariert. | ✅ |
| "Background-Location ohne klaren Nutzen." | Kein Standort, niemals deklariert. | 🟦 |
| "QUERY_ALL_PACKAGES ohne Begründung." | Nicht deklariert; Lint-Regel im Checker. | ✅ |

## 3. Foreground Services & Background Work

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "Foreground Service ohne erlaubten Typ." | Bei Bedarf nur `dataSync`. Doku in [02_PLAYSTORE_COMPLIANCE.md](02_PLAYSTORE_COMPLIANCE.md#4-hintergrundprozesse--foreground-services). | ⚠️ vorsorglich dokumentiert |
| "App ignoriert Battery Optimization Restrictions." | Kein `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`. | ✅ |
| "Exact alarm ohne Begründung." | `SCHEDULE_EXACT_ALARM` nicht im Manifest. | ✅ |
| "Hintergrund-Standortprüfungen ohne Disclosure." | Kein Standort. | 🟦 |

## 4. Sicherheit & Krypto

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "Klartext-HTTP-Traffic erlaubt." | `usesCleartextTraffic` default-false; Checker prüft. | ✅ |
| "Unsicherer TrustManager / Hostname-Verifier." | Niemals selbst implementiert; Checker-Smell-Regex. | ✅ |
| "Insecure cryptographic primitives (DES, ECB)." | Wir nutzen AES-GCM, Ed25519. | ✅ |
| "Hardcoded API Keys gefunden." | Secret-Scan in CI (`gitleaks`). | ⚠️ in CI ergänzen |
| "Debuggable Release-Build." | Buildozer setzt das im `release`-Mode aus; Checker verifiziert. | ✅ |
| "App enthält Backdoors / verdächtige Native-Libs." | Wir prüfen alle `requirements` per CVE-Scan + manuelles Review. | ✅ |

## 5. Privacy & Daten

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "Fehlende Privacy Policy URL." | URL in Play Console hinterlegt, Inhalt aus [legal/DATENSCHUTZ.md](../../legal/DATENSCHUTZ.md). | ✅ (Doku da; URL beim Listing setzen) |
| "Privacy Policy nicht erreichbar." | Im Release-Checker HEAD-Request gegen die hinterlegte URL. | ⚠️ Checker erweitern |
| "Data Safety Form passt nicht zum tatsächlichen Datenfluss." | Form-Vorlage in [04_PRIVACY_PERMISSIONS.md](04_PRIVACY_PERMISSIONS.md#4-data-safety-form-play-console---antworten). | ⚠️ vor jedem Release abgleichen |
| "App sammelt Daten ohne Disclosure (z.B. Advertising ID)." | Wir erheben keine. | ✅ |
| "Kinder unter 13 ohne COPPA/Families-Konformität anvisiert." | Zielgruppe >= 13, im Listing gesetzt. | ✅ |
| "App löscht keine Nutzerdaten auf Anfrage." | Löschfunktion **muss** vor Release implementiert sein. | ⚠️ in Settings ergänzen |

## 6. Inhalt & UX

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "Screenshots oder Beschreibung sind irreführend." | Screenshots sind reale UI-Stände, kein Photoshop. | ✅ |
| "Schwach funktionierende oder unvollständige App." | DoD inkl. manueller Smoke; Pre-Launch-Report. | ✅ |
| "Crashes bei Erstinstallation." | Release-Smoke (5-Punkte-Liste). | ✅ |
| "Default-Sample-Daten (Lorem ipsum) sichtbar." | Checker scannt nach `lorem ipsum`, `TODO`, `FIXME` in Strings. | ⚠️ Regel ergänzt |
| "App fordert Bewertungen aggressiv ein." | Wir nutzen Play In-App-Review API max. einmal pro 90 Tage. | ✅ (sobald implementiert) |
| "Versteckte Funktionalität (Easter-Egg-Pro-Features)." | Pro-Funktionen sind sichtbar, Lock-Dialog informiert. | ✅ |
| "App erfordert Login, ohne Funktion zu zeigen." | App ist lokal nutzbar; Login optional. | ✅ |

## 7. Billing & Geld

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "Digitale Inhalte über Drittanbieter-Zahlung." | Wir verkaufen Lizenz **außerhalb** der App (Browser-Redirect zu Paddle/Lemon Squeezy). Klare Trennung im UI. | ✅ |
| "Hidden Fees / Subscription unklar." | Pricing-Seite zeigt alle Tier-Preise + Laufzeiten transparent. | ✅ |
| "Auto-Renewal-Disclosure fehlt." | Vor Aktivierung wird Widerrufsverzicht eingeholt, Renewal-Bedingungen in AGB. | ✅ |
| "Kostenpflichtige Funktionen ohne Hinweis aktivieren." | Trial endet mit klarem Dialog; keine versteckten Käufe. | ✅ |

## 8. Drittanbieter-SDKs

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "SDK XYZ ist als verbotene Spyware bekannt." | SDK-Inventar [04_PRIVACY_PERMISSIONS.md#5-sdk-inventar](04_PRIVACY_PERMISSIONS.md#5-sdk-inventar), aktuell nur Mainstream-Libs. | ✅ |
| "SDK sammelt Daten ohne Disclosure." | Jede neue Dep durchläuft PR-Review + SDK-Inventar-Update. | ✅ |
| "Werbung ohne Family-Friendly-Filter in Kinder-Kategorie." | Keine Werbung. | 🟦 |

## 9. Quality / Crashes

| Reject | Maßnahme | Status |
| ------ | -------- | ------ |
| "Crashes/ANRs über Android-Vitals-Schwelle." | Schwellen in [05_PERFORMANCE.md](05_PERFORMANCE.md#1-performance-budget). Staged-Rollout-Beobachtung. | ✅ |
| "App startet nicht in Pre-Launch-Tests." | Buildozer-Release lokal verifizieren + Internal-Track-Crash-Free. | ✅ |
| "App enthält Debug-Symbole / `.apk` ohne Signatur." | Tag-Build muss signiert sein, Checker. | ✅ |

## 10. Spezifische Kivy/Buildozer-Fallen

| Problem | Maßnahme |
| ------- | -------- |
| `python-for-android` baut alte SQLite-Version mit | aktuelle `p4a`-Version pinnen, im `buildozer.spec` `p4a.branch = master` regelmäßig refreshen |
| Kivy bringt Default-Icons mit, die als Apple-/Lizenzproblematisch flagged werden | eigenes Icon liefern, `icon.filename` setzen |
| App-Bundle-Support in Buildozer noch experimentell | `buildozer android release --aab` testen; falls instabil, alternativer Weg über `bundletool` mit zerlegtem APK |
| App startet auf API-35 nicht wegen Edge-to-Edge | Manifest-Theme prüfen, `WindowCompat.setDecorFitsSystemWindows(false)` Pendant in Kivy auf `Window.softinput_mode = "below_target"` |
| `INTERNET`-Permission ist deklariert, aber Sync nicht erreichbar -> Reviewer sieht "App reagiert nicht" | Default: Sync **aus** beim ersten Start, klare Anleitung wie aktivieren |

## 11. Sonderfälle / Bonusfehler

- **"Misleading impersonation"** - App heißt wie eine bestehende
  bekannte App. Maßnahme: Name "Alltagshelfer" + Markencheck vor
  Release.
- **"Missing target audience selection"** - Pflicht-Feld in der Play
  Console, oft vergessen. Checker erinnert via Release-Liste Punkt K.
- **"AAB exceeds 200 MB"** - bei uns nicht relevant (<50 MB), aber
  Asset-Größe trotzdem im Checker beobachtet.
- **"Trademark/Copyright violation in screenshots"** - Screenshots
  ohne fremde Marken, Avatare aus eigenem Asset-Pool.
- **"Misleading App Store Listing"** - Listing-Text muss
  Funktionalität beschreiben, kein "magic AI"-Hype.

## 12. Wiederholtafel-Reject

Falls Google den Re-Submit nochmal ablehnt:

1. Vollständigen Ablehnungstext archivieren (`docs/play_rejections/`).
2. Verstoß genau zuordnen (welche Policy-Sektion).
3. Konkreten Code-/Doku-Change als PR.
4. Antwortschreiben an Play Review mit "what we changed and why".
5. Bei wiederholtem unbegründetem Reject: Play Console -> Appeal-Flow.

## 13. Vermeidungs-Routinen (verstetigt)

- Vor jedem Release: Liste in [09_RELEASE_CHECKLIST.md](09_RELEASE_CHECKLIST.md)
  durcharbeiten.
- Vor jedem PR: Compliance-Checker grün.
- Wöchentlich: Play Console -> "Policy Status" -> Warnungen scannen.
- Monatlich: Diese Liste auf Aktualität prüfen (Google ändert ständig).
- Quartalsweise: Re-Lesen der **Play Developer Program Policies**
  (https://play.google.com/about/developer-content-policy/) und der
  **Families Policy**, **Health Apps Policy**, **Spam Policy**.
