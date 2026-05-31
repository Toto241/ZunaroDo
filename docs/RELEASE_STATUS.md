# Go-Live-Status — ZunaroDo 1.0.0

> Momentaufnahme des Release-Stands, abgeleitet aus
> [docs/android/09_RELEASE_CHECKLIST.md](android/09_RELEASE_CHECKLIST.md).
> Trennt **im Repo erledigt / automatisiert verifiziert** von
> **operativ/manuell offen** (Play Console, echtes Gerät, externe Dienste).
> Stand: 2026-05-31.

## Zusammenfassung

- **Code/Repo: releasefertig.** Testsuite vollständig grün (577 Tests OK,
  9 bewusste Skips), `python -m tools.playstore_check --strict` → Exit 0,
  Version 1.0.0 konsistent über `buildozer.spec`, `pyproject.toml`,
  `playstore.yml`, `CHANGELOG.md`.
- **Verbleibend sind reine Betriebsschritte**, die außerhalb des Repos
  stattfinden: Play-Console-Upload/-Formulare, Signierung, Smoke auf echtem
  Gerät, Payment-Server-Deployment und Privacy-Policy-Hosting.

## Status je Checklisten-Abschnitt

Legende: ✅ erledigt/verifiziert · ⚙️ automatisiert geprüft · 🔧 operativ
(Mensch/extern) · ➖ nicht im Repo entscheidbar.

### A. Code & Build
- ✅ `versionName` = `1.0.0` (SemVer), `versionCode` = 2 (CI prüft Monotonie).
- ⚙️ `tools.playstore_check --strict` → Exit 0 (lokal verifiziert).
- ⚙️ Testsuite grün: `python3.12 -m unittest discover tests` → 577 OK.
- ⚙️ Demo-DBs vom Bundle ausgeschlossen (`source.exclude_exts = …,db,sqlite`).
- ✅ Keine Debug-`print(`-Reste im Bundle-Code; vorhandene `print()` liegen
  ausschließlich im CLI-/Sync-Server-/Notifier-Pfad (kein Mobile-Bundle).
- 🔧 CI-Pipelines `android-compliance` / `tests` / `security` final grün
  schalten (GitHub Actions, nicht lokal entscheidbar).

### B. Manifest & Permissions
- ✅ `android.api = 35`, `android.minapi = 24`.
- ⚙️ Permissions whitelisted: `INTERNET`, `POST_NOTIFICATIONS`.
- ✅ `android.allow_backup = False`.
- ➖ `exported`-Attribute / `usesCleartextTraffic` am **generierten**
  `AndroidManifest.xml` nach dem ersten Buildozer-Build prüfen.

### C. Signierung
- 🔧 Upload-Keystore + Backup, `apksigner verify`, Play App Signing,
  signierter Tag-Build — vollständig operativ.

### D. App-Inhalt
- ✅ `CHANGELOG.md` enthält 1.0.0-Eintrag (nutzerorientiert).
- ✅ **Release-Notes pro Locale** in `legal/release_notes/1.0.0/`
  (8 Vollsprachen, je ≤ 500 Zeichen); deckungsgleich im `production`-Track
  von `playstore.yml`.
- ✅ Legal-Dokumente vollständig ohne Platzhalter (`legal/`:
  AGB/IMPRESSUM/DATENSCHUTZ/WIDERRUF, de + en).
- ⚙️ Keine Lorem-ipsum-Platzhalter (Checker).
- 🔧 Privacy-Policy-URL (Play Console, HTTP 200) — Hosting via `pages.yml` +
  Repo-Variable `PRIVACY_POLICY_URL` setzen (siehe `docs/android/07_CICD.md`).

### E. Funktionaler Smoke (echtes Gerät)
- 🔧 Frischinstallation, Onboarding-Datenschutzdialog, 5 Bottom-Nav-Tabs,
  CRUD + Soft-Delete, „Alle Daten löschen", App-Killer-Test. Manuell.

### F. Lizenz- & Bezahlfluss
- ✅ Code vollständig: Trial/Tier-Lock, Pro-Aktivierung,
  Widerrufsverzicht-Dialog (`services/activation_flow.py`),
  Webhook-Token-Empfang (`services/license_events.py`), Revocation-Liste —
  durch Tests abgedeckt.
- 🔧 End-to-End mit echtem MoR-Webhook erst nach Payment-Server-Deployment
  (`release/deploy-payment-server.md`): Keypair erzeugen, Public-Key in
  `services/license_token.py` eintragen, Server betreiben.

### G. Sync-Server
- ✅ TLS via `python -m services.sync_server --self-signed`
  (`services/tls_certs.py`).
- 🔧 Production-Sync-URL eintragen + Zwei-Geräte-/Conflict-Replay-Test.

### H–J. Performance / Accessibility / Beobachtbarkeit
- 🔧 Cold-Start/Heap/APK-Größe, TalkBack/Schriftgröße/Kontrast/Rotation,
  Crash-Reporting-Opt-in & PII-Logcat-Check — alle am Gerät zu messen.

### K. Play Console
- ⚙️ Closed-Test-Gate erfüllt: Nachweis `release/closed-test-2026-05-30.md`,
  `evaluate_closed_test_gate` → `ready = true` (≥ 12 Tester / ≥ 14 Tage).
- ✅ Track-Konfiguration in `playstore.yml` (internal/closed/production).
- 🔧 Internal-Upload, Pre-Launch-Report, Data-Safety-Form
  (`tools/data_safety.py`), Content-Rating, Zielgruppe, Screenshots,
  Feature-Graphic, Staged-Rollout 10 % — Play-Console-Aktionen.

### L. Kommunikation
- 🔧 Newsletter/Status-Page, Support-Briefing, Public-CHANGELOG auf der
  Marketing-Site.

### M. Post-Release
- 🔧 Crash-/ANR-Rate, Reviews, Staged-Rollout 10 → 100 %, Retro in
  `docs/releases/v1.0.md`.

## Nächste konkrete Schritte (außerhalb des Repos)

1. Payment-Server deployen, Public-Key in `services/license_token.py`
   eintragen, Webhook-URL beim MoR setzen.
2. Privacy-Policy hosten und `PRIVACY_POLICY_URL` als Repo-Variable setzen.
3. AAB bauen, mit Upload-Key signieren, Internal-Track hochladen.
4. Manuellen Geräte-Smoke (Abschnitte E–J) durchführen und protokollieren.
5. Production-Draft auf 10 % Staged-Rollout freigeben.
