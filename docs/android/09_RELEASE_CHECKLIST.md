# 09 - Release-Checkliste

> Pflicht-Liste, abzuhaken vor JEDEM Push in den Play-Store-Production-
> Track. Diese Liste ist der harte Cut zwischen "Beta-Stand" und
> "User-tauglich".

Verantwortlicher: **Release-Owner** (rotierend, in `CODEOWNERS` markiert).

## A. Code & Build

- [ ] Branch ist `release/vX.Y` oder Tag-Commit auf `main`.
- [ ] `versionName` in `buildozer.spec` ist SemVer und neu.
- [ ] `versionCode` ist strikt größer als letzter Production-Code
      (CI verifiziert).
- [ ] `python -m tools.playstore_check --strict` → exit 0 lokal.
- [ ] CI-Pipeline `android-compliance` → grün.
- [ ] CI-Pipeline `tests` → grün.
- [ ] CI-Pipeline `security` → grün.
- [ ] Coverage Δ >= -2 % gegenüber main.
- [ ] Keine `print(` / `Log.d(` / Debug-only-Funktionen im Release-Code
      (Checker prüft).
- [ ] Demo-Datenbanken (`*.db`, `*.sqlite`) sind via
      `source.exclude_exts` aus dem Bundle ausgeschlossen.

## B. Manifest & Permissions

- [ ] `android.api = 35` (oder höher) gesetzt.
- [ ] `android.minapi = 24` (mindestens).
- [ ] Permissions in `buildozer.spec` decken sich mit der Matrix in
      [04_PRIVACY_PERMISSIONS.md](04_PRIVACY_PERMISSIONS.md).
- [ ] Keine Permission ohne Begründung im Repo.
- [ ] Generiertes `AndroidManifest.xml` enthält keine
      `usesCleartextTraffic="true"`.
- [ ] `allowBackup` ist deaktiviert oder ein expliziter `BackupAgent`
      wurde implementiert.
- [ ] Alle `Activity`/`Service`/`Receiver`-Komponenten haben explizites
      `android:exported`-Attribut.

## C. Signierung

- [ ] Upload-Keystore vorhanden und mit gesichertem Backup.
- [ ] `apksigner verify` bestätigt v1 + v2 + v3 + v4 Signatur (je nach
      Mindest-API).
- [ ] Play App Signing aktiv (Play Console).
- [ ] Tag-Build wird mit Upload-Key signiert (CI-Schritt grün).

## D. App-Inhalt

- [ ] `CHANGELOG.md` enthält Eintrag für neue Version (User-orientiert,
      keine internen Tickets).
- [ ] Release-Notes (max. 500 Zeichen pro Locale) in `legal/release_notes/`
      oder Play-Console-Form.
- [ ] Privacy Policy URL (in Play Console hinterlegt) liefert HTTP 200.
      Hosting via `pages.yml`; Setup + Repo-Variable `PRIVACY_POLICY_URL`
      siehe [07_CICD.md → Privacy-Policy-Hosting](07_CICD.md).
- [ ] AGB- und Impressum-Links in der App führen zu den aktuellen
      `legal/`-Dokumenten.
- [ ] Keine "lorem ipsum"-Platzhalter im Settings-/About-Bildschirm.

## E. Funktionaler Smoke (manuell, auf echtem Gerät)

- [ ] Frische Installation: App öffnet sich, kein Crash.
- [ ] Onboarding-Datenschutz-Dialog erscheint, Akzeptieren wird
      persistiert.
- [ ] Bottom-Nav: alle 5 Tabs öffnen sich.
- [ ] Erste Eingabe (Vertrag / Ausgabe / Termin) anlegen → in Liste
      sichtbar.
- [ ] Eintrag löschen → verschwindet → Soft-Delete-Liste zeigt ihn.
- [ ] Settings → "Datenschutz" öffnet das Dokument.
- [ ] Settings → "Alle Daten löschen" entfernt DB-File + Sandbox-
      Verzeichnisse (separates Testgerät!).
- [ ] App-Killer-Test: App per Wischen schließen, neu öffnen → Daten
      noch da.

## F. Lizenz- & Bezahlfluss

- [ ] Trial-Modus aktiv (Erstinstallation).
- [ ] Pro-Aktivierung mit Test-Token funktioniert.
- [ ] Widerrufsverzicht-Dialog erscheint vor Aktivierung
      (siehe [services/activation_flow.py](../../services/activation_flow.py)).
- [ ] Webhook-Empfang (Paddle/Lemon Squeezy) liefert Token korrekt
      (siehe [services/license_events.py](../../services/license_events.py)).
- [ ] Lizenz-Revocation-Liste lokal aktualisierbar.
- [ ] Tier-Lock greift bei abgelaufener Lizenz (Pro-Funktion → Lock-
      Dialog).

## G. Sync-Server

- [ ] Sync-Endpoint-URL in `settings` ist Production-URL, nicht
      Staging.
- [ ] TLS-Zertifikat des Sync-Servers gültig (HSTS, kein Mixed Content).
- [ ] Sync mit zweitem Demo-Gerät: Änderung von Gerät A erscheint auf
      Gerät B innerhalb < 60 s.
- [ ] Conflict-Replay-Test: parallele Änderung → last-writer-wins
      konsistent.

## H. Performance

- [ ] Cold-Start auf Pixel 6 (oder vergleichbar) < 2 s.
- [ ] Listen-Scroll glatt (subjektiv), keine Hänger.
- [ ] APK/AAB-Größe < 40 MB Download.
- [ ] Idle-Heap < 80 MB.

## I. Accessibility

- [ ] TalkBack-Walkthrough für Bottom-Nav + FAB.
- [ ] System-Schriftgröße XL: kein Clipping.
- [ ] Dark-Mode: lesbare Kontraste.
- [ ] Rotation Portrait ↔ Landscape: kein Daten-Verlust, kein Crash.

## J. Beobachtbarkeit

- [ ] Crash-Reporting opt-in funktioniert (sobald aktiv).
- [ ] Sync-Logs landen in Sandbox, nicht auf SD-Card.
- [ ] Keine PII in Logcat (`adb logcat | grep alltagshelfer` prüft
      manuell).

## K. Play Console

- [ ] Internal-Testing-Track-Upload erfolgreich.
- [ ] Pre-Launch-Report ohne Crashes / Sicherheitsproblemen.
- [ ] Closed Testing **≥ 14 zusammenhängende Tage** mit **≥ 12 aktiven
      Testern** gelaufen (Pflicht für neue Personal-Developer-Accounts).
      Werte sind in `playstore.yml` (`tracks.closed.min_testers`/`min_days`)
      hinterlegt.
- [ ] Nachweis abgelegt unter `release/closed-test-JJJJ-MM.md` (Vorlage:
      `release/CLOSED_TEST_EVIDENCE_TEMPLATE.md`). Erst dann liefert das
      Release-Gate `evaluate_closed_test_gate` → `ready = true`
      (`python -m tools.playstore_check` zeigt unter `[closed_test]` den
      Nachweis).
- [ ] Data-Safety-Form aktualisiert, falls Datenfluss geändert.
- [ ] Content-Rating-Fragebogen aktuell.
- [ ] Zielgruppe gesetzt (>= 13 Jahre, "Mixed audiences").
- [ ] Screenshots aktuell (kein Skeleton, keine Lorem-ipsum-Inhalte).
- [ ] Feature-Graphic + Icon aktuell.
- [ ] Staged-Rollout auf 10 % startbereit.

## L. Kommunikation

- [ ] User-Communication (Newsletter / Status-Page) für neue Features
      vorbereitet.
- [ ] Internes Support-Team über Änderungen briefen
      (FAQ-Diff angefügt).
- [ ] Public CHANGELOG auf der Marketing-Site live.

## M. Post-Release

Innerhalb 48 h nach Rollout:

- [ ] Crash-Rate < 1,09 % bestätigt.
- [ ] ANR-Rate < 0,47 % bestätigt.
- [ ] Negative Reviews durchsehen, P0 erkannt → ggf. Rollout-Halt.
- [ ] Support-Tickets-Spike beobachten.

Innerhalb 7 Tage:

- [ ] Staged-Rollout auf 100 % oder gestoppt mit Begründung in
      `docs/incidents/`.
- [ ] Retro: was lief gut, was nicht. Eintrag in `docs/releases/<vX.Y>.md`.
