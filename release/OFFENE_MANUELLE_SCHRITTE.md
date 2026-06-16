# Offene manuelle Release-Schritte

Diese Liste enthält Punkte, die das Repository vorbereiten und prüfen, aber nicht vollständig selbst erledigen kann. Sie wird aus `tools/release_open_items.py` generiert und ist dieselbe Quelle, die das Control Panel verwendet.

Legende: `[ ]` offen · `blocker` vor Production-Go zwingend · `optional` nur bei entsprechendem Launch-Umfang · `post_release` nach Rollout prüfen.

## [ ] SQLCipher, ML-Kit-OCR und App-Icon auf echtem Android-Gerät prüfen

- ID: `android-device-verification`
- Kategorie: `blocker`
- Status: `external_device_required`
- Warum nicht voll automatisierbar: Die Verschlüsselung im App-Sandbox-Pfad, ML-Kit-Kamera/OCR und Launcher-Darstellung hängen von einem realen Android-Gerät bzw. Emulator mit installierter App ab. Das Repo kann nur den Prüfbefehl bereitstellen, nicht das Gerät selbst.
- Lokale Doku: [Go-Live-TODO §1.1](release/GO_LIVE_TODO.md#11-android-build-erzeugen-basis-fuer-alles-weitere), [Android-Geräteprüfer](tools/verify_android_device.py), [Android-Release-Checkliste](docs/android/09_RELEASE_CHECKLIST.md#e-funktionaler-smoke-manuell-auf-echtem-gerat)
- Offizielle Links: [Android Debug Bridge (adb)](https://developer.android.com/tools/adb), [ML Kit Text Recognition](https://developers.google.com/ml-kit/vision/text-recognition/v2)

Nächste Schritte:

1. Debug- oder Release-Build installieren.
1. `python -m tools.verify_android_device` ausführen; für einen schnellen SQLCipher-Check zunächst `--skip-ocr` verwenden.
1. Für OCR einen Beleg in der App scannen und den Check ohne `--skip-ocr` wiederholen.
1. Launcher öffnen und prüfen, dass kein weißes Default-Icon angezeigt wird.

Prüf-/Hilfsbefehle:

- `python -m tools.verify_android_device --skip-ocr`
- `python -m tools.verify_android_device`

## [ ] Closed Testing mit mindestens 12 Testern über 14 Tage nachweisen

- ID: `closed-testing`
- Kategorie: `blocker`
- Status: `calendar_and_people_required`
- Warum nicht voll automatisierbar: Google verlangt bei neuen persönlichen Developer-Konten echte Tester, einen zusammenhängenden Zeitraum und Play-Console-Nachweise. Diese Signale können lokal nicht erzeugt oder simuliert werden.
- Lokale Doku: [Closed-Test-Runbook](release/CLOSED_TEST_RUNBOOK.md), [Evidenz-Vorlage](release/CLOSED_TEST_EVIDENCE_TEMPLATE.md), [Vorbereiteter Nachweis](release/closed-test-2026-05-30.md)
- Offizielle Links: [Closed testing requirements](https://support.google.com/googleplay/android-developer/answer/14151465), [Tracks einrichten](https://support.google.com/googleplay/android-developer/answer/9845334)

Nächste Schritte:

1. AAB in Internal/Closed Testing hochladen.
1. Testergruppe mit mindestens 12 aktiven Testern betreiben.
1. Mindestens 14 zusammenhängende Tage warten und Feedback/Crashes prüfen.
1. Nachweise in `release/closed-test-*.md` und `release/assets/` ablegen.

## [ ] Data-Safety- und Content-Rating/IARC-Formulare ausfüllen

- ID: `data-safety-iarc`
- Kategorie: `blocker`
- Status: `console_form_required`
- Warum nicht voll automatisierbar: Das Repo kann die Antworten generieren und gegen den Code prüfen, aber die Play-Console-Formulare müssen im Google-UI durch einen berechtigten Account bestätigt werden.
- Lokale Doku: [Data-Safety-Antworten](release/DATA_SAFETY_CONSOLE_ANSWERS.md), [Data-Safety-Tool](tools/data_safety.py), [Privacy-/Permissions-Doku](docs/android/04_PRIVACY_PERMISSIONS.md)
- Offizielle Links: [Play Data Safety](https://support.google.com/googleplay/android-developer/answer/10787469), [Content Ratings](https://support.google.com/googleplay/android-developer/answer/188189)

Nächste Schritte:

1. `python -m tools.data_safety --markdown` ausführen.
1. Antworten in der Play Console übertragen und mit `release/DATA_SAFETY_CONSOLE_ANSWERS.md` gegenprüfen.
1. IARC-/Content-Rating-Fragebogen ausfüllen und Ergebnis speichern.

Prüf-/Hilfsbefehle:

- `python -m tools.data_safety --check`
- `python -m tools.data_safety --markdown`

## [ ] iOS-Build auf macOS/Xcode verifizieren

- ID: `ios-build`
- Kategorie: `platform`
- Status: `macos_required`
- Warum nicht voll automatisierbar: Apple erlaubt iOS-Builds und Code-Signing nur mit macOS, Xcode und Apple-Developer-Zugang. Eine Linux/Windows-VM kann das Xcode-Projekt höchstens dokumentieren, nicht final bauen.
- Lokale Doku: [iOS-Build-Skript](scripts/build-ios.sh), [Mobile-Dokumentation](MOBILE.md), [Build-Status-Tool](tools/build_status.py)
- Offizielle Links: [Xcode](https://developer.apple.com/xcode/), [kivy-ios](https://github.com/kivy/kivy-ios)

Nächste Schritte:

1. Auf macOS `scripts/build-ios.sh` ausführen.
1. Xcode-Projekt öffnen, Bundle-ID und Signing-Team setzen.
1. Run auf Gerät/Simulator ausführen und IPA-Export separat prüfen.

Prüf-/Hilfsbefehle:

- `bash scripts/build-ios.sh`

## [ ] Optionalen Play-Billing-Kaufflow mit Lizenztester prüfen

- ID: `play-billing`
- Kategorie: `optional`
- Status: `conditional_if_iap_launches`
- Warum nicht voll automatisierbar: Echte Käufe, Lizenztester, Subscription-Produkte und Server-Verifikation laufen über Play Console, Google-Konten und einen deployten Payment-Server.
- Lokale Doku: [Payment-Dokumentation](PAYMENT.md), [Payment-Server-Deploy](release/deploy-payment-server.md), [Billing-Implementierung](services/play_billing_android.py)
- Offizielle Links: [Google Play Billing](https://developer.android.com/google/play/billing), [Subscriptions](https://developer.android.com/google/play/billing/subscriptions)

Nächste Schritte:

1. Nur nötig, wenn Pro/Abos bereits zum Launch verkauft werden.
1. Abo-IDs exakt wie in `services/play_billing_android.py` anlegen.
1. Payment-Server deployen und `/verify/play` mit Service-Account testen.
1. Echten Testkauf durchführen und signiertes Lizenz-Token prüfen.

## [ ] Play-Developer-Konto verifizieren und App in der Play Console anlegen

- ID: `play-console-app`
- Kategorie: `blocker`
- Status: `external_account_required`
- Warum nicht voll automatisierbar: Kontoerstellung, Identitätsprüfung, Zahlungsprofil und das finale Anlegen der App passieren ausschließlich in Googles Play Console und erfordern persönliche bzw. Organisationsdaten.
- Lokale Doku: [Play-Store-Anleitung](PLAYSTORE.md#5-play-console-einrichten), [Play-Console-Setup](release/PLAY_CONSOLE_SETUP.md), [Playstore-Konfiguration](playstore.yml)
- Offizielle Links: [Play Console Signup](https://play.google.com/console/signup), [App erstellen und einrichten](https://support.google.com/googleplay/android-developer/answer/9859152)

Nächste Schritte:

1. Developer Account anlegen bzw. verifizieren.
1. Neue App mit Name `ZunaroDo`, Standardsprache `de-DE`, Kategorie `PRODUCTIVITY` und Package `de.alltagshelfer.alltagshelfer` anlegen.
1. Support-, Marketing- und Datenschutz-URLs aus `playstore.yml` übertragen.

## [ ] Produktionsrollout überwachen und nach 48 Stunden bewerten

- ID: `production-monitoring`
- Kategorie: `post_release`
- Status: `live_traffic_required`
- Warum nicht voll automatisierbar: Crash-/ANR-Raten, Reviews und Support-Tickets entstehen erst durch echten Rollout mit echten Nutzern. Lokale Tests können nur die Schwellen und Checklisten vorbereiten.
- Lokale Doku: [Release-Checkliste M/Post-Release](docs/android/09_RELEASE_CHECKLIST.md#m-post-release), [Go-Live-TODO §3](release/GO_LIVE_TODO.md#3-finaler-pre-submit-check-vor-jedem-upload), [Playstore-Konfiguration Monitoring](playstore.yml)
- Offizielle Links: [Android Vitals](https://developer.android.com/topic/performance/vitals), [Play Console Vitals](https://play.google.com/console/about/vitals/)

Nächste Schritte:

1. Gestaffelten Rollout starten (z. B. 5 % → 20 % → 50 % → 100 %).
1. Android Vitals, Reviews und Support-Tickets in den ersten 48 h prüfen.
1. Bei P0/P1-Problemen Rollout pausieren und Incident-Doku anlegen.

## [ ] Signiertes Release-AAB bauen und als Play-Artefakt prüfen

- ID: `release-aab`
- Kategorie: `blocker`
- Status: `ci_or_build_host_required`
- Warum nicht voll automatisierbar: Google Play akzeptiert für neue Apps ein signiertes Android App Bundle. Der Build benötigt Linux/WSL2 oder CI sowie die nicht im Repo liegenden Keystore-Secrets.
- Lokale Doku: [Buildozer-Konfiguration](buildozer.spec), [Mobile-Build-Anleitung](MOBILE.md#build-schritt-fuer-schritt), [Release-Checkliste](docs/android/09_RELEASE_CHECKLIST.md#a-code--build)
- Offizielle Links: [Android App Bundles](https://developer.android.com/guide/app-bundle), [Buildozer](https://buildozer.readthedocs.io/)

Nächste Schritte:

1. Release-Workflow `Android Release (AAB)` dispatchen oder unter Linux/WSL2 `buildozer android release` ausführen.
1. Artefakt `dist/*.aab` herunterladen und Version/Signatur prüfen.
1. Bei jedem Upload `android.numeric_version` und `playstore.yml identity.version_code` gemeinsam erhöhen.

Prüf-/Hilfsbefehle:

- `python -m tools.playstore_check --strict`
- `buildozer android release`

## [ ] Upload-Keystore erzeugen, sichern und Secrets setzen

- ID: `upload-keystore`
- Kategorie: `blocker`
- Status: `secret_material_required`
- Warum nicht voll automatisierbar: Der Upload-Key ist geheimes, langlebiges Signiermaterial. Er darf nicht im Repository erzeugt oder gespeichert werden und muss in einem Passwort-Manager sowie als CI-Secret außerhalb des Codes gesichert werden.
- Lokale Doku: [Play-Console-Setup](release/PLAY_CONSOLE_SETUP.md), [Windows-Keystore-Helfer](release/create_upload_keystore.ps1), [Linux/macOS-Keystore-Helfer](release/create_upload_keystore.sh)
- Offizielle Links: [Play App Signing](https://support.google.com/googleplay/android-developer/answer/9842756), [App signieren](https://developer.android.com/studio/publish/app-signing)

Nächste Schritte:

1. `release/create_upload_keystore.ps1` oder `release/create_upload_keystore.sh` lokal ausführen.
1. Keystore-Datei und Passwörter sicher außerhalb des Repos sichern.
1. CI-Secrets `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_ALIAS_PASSWORD` setzen.
1. Vor dem ersten Production-Upload Play App Signing aktivieren.
