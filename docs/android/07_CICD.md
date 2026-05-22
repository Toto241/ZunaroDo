# 07 - CI/CD-Konzept

## 1. Überblick

```text
            ┌─────────────┐
            │  feature/*  │  ── push ──► CI: lint + unit + compliance
            └──────┬──────┘
                   │ PR open
                   ▼
            ┌─────────────┐
            │     PR      │  ── checks ─► CI: lint + unit + integration + compliance + apk-smoke
            └──────┬──────┘
                   │ merge (Squash)
                   ▼
            ┌─────────────┐
            │    main     │  ── on push ─► CI: full suite + bundle + macrobench
            └──────┬──────┘
                   │ release branch / tag v*
                   ▼
            ┌─────────────┐
            │  release    │  ── tag push ─► Release: AAB sign + upload internal track
            └──────┬──────┘
                   │ promote (manuell oder Staged Rollout)
                   ▼
            ┌─────────────┐
            │ production  │  ── Play Console ─► Staged Rollout 10/25/50/100 %
            └─────────────┘
```

## 2. Branching-Strategie

- **`main`** - immer release-fähig, geschützt (Reviews + grüne CI Pflicht).
- **`feature/<ticket>-<slug>`** - kurzlebig, < 5 Tage.
- **`release/<vX.Y>`** - vom main abgezweigt, bekommt nur Bugfixes
  während Release-Phase.
- **`hotfix/<vX.Y.Z>`** - vom Production-Tag abgezweigt, geht zurück
  in `main` und `release/*`.
- Keine Long-Lived-Branches außer `release/*`.

Schutz-Regeln für `main`:
- Signed Commits empfohlen.
- Reviews >= 1, Code-Owner-Review wenn `docs/android/*` berührt.
- Status-Checks pflichtig: `lint`, `tests`, `compliance`.
- Linear History (Squash-Merge bevorzugt).

## 3. Versions-Strategie

| Datei | Quelle der Wahrheit | Update durch |
| ----- | ------------------- | ------------ |
| `buildozer.spec: version` | manuell, SemVer | Release-Owner |
| Native `versionName` (Gradle) | manuell, SemVer | Release-Owner |
| Native `versionCode` | automatisch via CI = `YYYYMMDDNN` | CI-Pipeline |
| Python-Package-Version (`pyproject.toml`) | bleibt synchron mit `buildozer.spec: version` | Pre-commit-Hook (optional) |

`versionCode` MUSS streng monoton steigen. CI verifiziert das gegen
den letzten `release/*`-Tag.

## 4. GitHub Actions - Workflow-Inventar

Aktuell: `.github/workflows/ci.yml` (Python-Tests).

Hinzu kommen:

| Workflow | Trigger | Zweck |
| -------- | ------- | ----- |
| `ci.yml` | push/PR | Python-Tests (bereits da) |
| `android-compliance.yml` | push/PR | Play-Store-Compliance-Checker, Manifest-/Permission-/Secret-Scans (neu) |
| `android-build.yml` | PR + push main | Debug-APK-Build mit Buildozer in Ubuntu-Container |
| `android-release.yml` | tag `v*` | Signierter AAB-Build, Upload internal track |
| `security.yml` | scheduled (wöchentlich) | `pip-audit`, `gitleaks`, `mobsfscan` |

Konkrete Implementierung von `android-compliance.yml` ist Bestandteil
dieses PRs - siehe [`.github/workflows/android-compliance.yml`](../../.github/workflows/android-compliance.yml).

## 5. Build-Pipeline-Anatomie (Buildozer / Ubuntu)

Schlüsselfragmente, die in `android-build.yml` landen:

```yaml
- name: System dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y python3-pip openjdk-17-jdk \
        autoconf libtool pkg-config zlib1g-dev libncurses-dev \
        libtinfo5 cmake unzip libffi-dev libssl-dev

- name: Cache Buildozer + Android SDK
  uses: actions/cache@v4
  with:
    path: |
      ~/.buildozer
      ~/.android
      ~/.gradle/caches
    key: buildozer-${{ runner.os }}-${{ hashFiles('buildozer.spec', 'requirements.txt') }}

- name: Install Buildozer
  run: pip install --upgrade buildozer cython==0.29.36

- name: Build debug APK
  env:
    ANDROIDAPI: "35"
    ANDROIDMINAPI: "24"
  run: buildozer android debug

- name: Upload APK artifact
  uses: actions/upload-artifact@v4
  with:
    name: alltagshelfer-debug.apk
    path: dist/*.apk
    retention-days: 14
```

Empfehlung: **Self-hosted Runner** mit gecachtem SDK/NDK, damit
Folgeruns < 5 min sind. Für Public-Open-Source ist der `ubuntu-latest`-
Runner ok, dauert aber ~25 min beim ersten Run.

## 6. Signierung

### Buildozer-Release-Signierung

Env-Vars (in CI als Secrets):

| Variable | Inhalt |
| -------- | ------ |
| `P4A_RELEASE_KEYSTORE` | Pfad oder Base64-Inhalt (entpacken in Workflow) |
| `P4A_RELEASE_KEYSTORE_PASSWD` | Keystore-Passwort |
| `P4A_RELEASE_KEYALIAS` | Alias |
| `P4A_RELEASE_KEYALIAS_PASSWD` | Alias-Passwort |

Im Workflow:

```yaml
- name: Restore upload keystore
  run: |
    echo "${{ secrets.UPLOAD_KEYSTORE_BASE64 }}" | base64 -d > /tmp/upload.jks
    echo "P4A_RELEASE_KEYSTORE=/tmp/upload.jks" >> $GITHUB_ENV
  env:
    P4A_RELEASE_KEYSTORE_PASSWD: ${{ secrets.UPLOAD_KEYSTORE_PASSWD }}
    P4A_RELEASE_KEYALIAS: ${{ secrets.UPLOAD_KEY_ALIAS }}
    P4A_RELEASE_KEYALIAS_PASSWD: ${{ secrets.UPLOAD_KEY_ALIAS_PASSWD }}

- name: Release build
  run: buildozer android release

- name: Verify signature
  run: |
    apksigner verify --verbose dist/alltagshelfer-*-release.apk
```

### Play App Signing

- **Upload-Key** verbleibt bei uns (für CI-Signierung).
- **App-Signing-Key** verwaltet Google nach Onboarding.
- Wiederherstellungs-Backup des Upload-Keys: physisch + Passwort-
  Manager, dokumentiert in `docs/android/secrets-runbook.md` (privat,
  nicht im Repo).

## 7. Release-Pipeline (Tag `v*`)

```yaml
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify version match
        run: python -m tools.playstore_check --only versioning --strict
      - name: Build signed AAB
        run: buildozer android release   # AAB-Flag ergänzen sobald Buildozer it
      - name: Upload to Play (internal)
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.PLAY_SERVICE_ACCOUNT_JSON }}
          packageName: de.alltagshelfer.alltagshelfer
          releaseFiles: dist/*.aab
          track: internal
          status: completed
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: dist/*.aab
```

## 8. Staged Rollout

Promotion-Reihenfolge in Play Console:

1. **Internal Testing** - bei jedem Tag.
2. **Closed Testing (Alpha)** - manuell promovieren, mind. 7 Tage warten.
3. **Production** - Staged Rollout startet bei 10 %, Schritte 25 % ->
   50 % -> 100 %, je 24-48 h Beobachtung.

CI kann den ersten Promotion-Schritt automatisieren; alles ab Production
ist **manuell** (4-Augen-Prinzip).

## 9. Rollback-Strategie

- Play Console: **"Halt rollout"** stoppt weitere Auslieferung sofort.
- Mit "Resume rollout" kann fortgesetzt werden.
- **Echtes Rollback** ist nicht möglich (Versionscodes sind monoton).
  Stattdessen:
  1. Hotfix-Tag mit erhöhtem `versionCode`.
  2. Bugfix oder Re-Submission alter Funktionalität.
  3. Schneller Internal/Closed-Test, dann Production.

## 10. Hotfix-Strategie

```text
  v1.4.0 (prod, broken)
       │
       ├── hotfix/v1.4.1   ──fix──►  PR ──► CI grün ──► tag v1.4.1
       │
       ▼
   merge zurück nach main
```

- Hotfix-Branch wird immer vom **letzten Production-Tag** abgezweigt,
  nicht von `main`, damit unfertige Features nicht mitlaufen.
- Nach Tag-Release: cherry-pick in `main` und alle aktiven
  `release/*`-Branches.

## 11. Automatische Dependency-Updates

- **Dependabot** (oder Renovate) aktivieren für `pip` und `gradle`.
- Wöchentlich, Auto-Merge nur bei Patch-Releases + grünem CI.
- Minor/Major-Releases: PR-Review verpflichtend.

`.github/dependabot.yml` (empfohlen):

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: monthly
  - package-ecosystem: gradle      # später, sobald Native-Modul existiert
    directory: "/android"
    schedule:
      interval: weekly
```

## 12. Security-Scans im CI

- `pip-audit` -> CVSS-Schwelle 7
- `gitleaks` -> jeder PR + main
- `mobsfscan` -> Manifest, smali-Heuristik (sobald APK-Artefakt da)
- `bandit -ll` -> Python-Static-Security
- `semgrep` (optional, regelbasiert)

## 13. Quality-Gates

Vor Merge in `main`:

- [ ] Lint grün
- [ ] Unit + Integration grün
- [ ] Compliance-Checker grün
- [ ] Coverage Δ >= -2 %
- [ ] Security-Scans ohne neue High/Critical

Vor Tag-Release:

- [ ] alle obigen
- [ ] APK/AAB-Größen-Trend ohne Anomalie
- [ ] manuelle Smoke (siehe [06_QA_STRATEGY.md](06_QA_STRATEGY.md))
- [ ] Release-Notes in `CHANGELOG.md`
- [ ] Privacy Policy URL live (HTTP 200)

## 14. Notification & Reporting

- Slack/Discord-Webhook in CI für Build-Failures.
- Wöchentlicher Reporting-Job postet:
  - Coverage-Trend
  - APK-Größen-Trend
  - Crash-Rate-Top-3
  - Offene High-CVEs

## 15. Lokale Dev-Loop

```bash
# Python-Tests
python -m unittest discover -s tests

# Compliance lokal
python -m tools.playstore_check --strict

# KivyMD-App lokal (Desktop-Iteration)
python -m mobile.app

# Buildozer-Debug-Build (WSL2/Linux)
buildozer android debug

# Schnellinstallation auf Gerät
adb install -r dist/alltagshelfer-*-arm64-v8a-debug.apk
adb logcat | grep -i python
```

## Release-Build (signiertes AAB)

Der Workflow [`.github/workflows/android-release.yml`](../../.github/workflows/android-release.yml)
baut auf **manuelle Auslösung** (`workflow_dispatch`) ein signiertes
**App Bundle** (`bin/*.aab`, da `android.release_artifact = aab` in
`buildozer.spec`). Er lädt nichts automatisch zu Google Play hoch, sondern
stellt das AAB als Build-Artefakt bereit; der Upload bleibt eine bewusste
Hand-Aktion (Play App Signing übernimmt die finale Signatur).

Vor dem Build läuft `playstore_check --strict` als Gate. Die Signierung
nutzt `python-for-android` über vier GitHub-Secrets:

| Secret | Inhalt |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | `base64 -w0 upload.keystore` |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore-Passwort |
| `ANDROID_KEY_ALIAS` | Alias des Upload-Keys |
| `ANDROID_KEY_ALIAS_PASSWORD` | Passwort des Alias |

Die verwendete Community-Action (`ArtemSBulgakov/buildozer-action`) stellt
SDK/NDK bereit; vor produktivem Einsatz vom Release-Owner prüfen und auf
einen Commit-SHA pinnen.

## Privacy-Policy-Hosting (erreichbare URL)

Google Play verlangt eine **öffentlich erreichbare** Datenschutz-URL. Der
Workflow [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml)
rendert `legal/DATENSCHUTZ.md` nach `site/privacy/index.html` und deployt
es via GitHub Pages. Einmalige Einrichtung (Repo-Settings, nicht im Code
automatisierbar):

1. **Settings → Pages → Source: GitHub Actions** aktivieren.
2. Workflow „Privacy-Policy Pages" einmal manuell starten
   (`workflow_dispatch`).
3. Resultierende URL: `https://<owner>.github.io/<repo>/privacy/`
   (für dieses Repo: `https://toto241.github.io/ZunaroDo/privacy/`).
4. **Settings → Secrets and variables → Actions → Variables**:
   `PRIVACY_POLICY_URL` auf diese URL setzen. Der Compliance-Job
   „Privacy-Policy URL erreichbar" prüft dann per HEAD-Request HTTP 200
   (ohne gesetzte Variable wird der Schritt nur übersprungen).
5. Dieselbe URL im **Play-Console-Store-Listing** unter „Datenschutz­erklärung"
   eintragen.

## Laufzeit-/Geräte-Qualität (über statische Checks hinaus)

Google bewertet App-Qualität primär am **Laufzeitverhalten auf echten
Geräten** (Android Vitals, Pre-Launch-Report). Dafür gibt es zusätzlich
zu den Unit-/Compliance-Checks:

- **UI-Boot-Smoke** ([`.github/workflows/ui-runtime.yml`](../../.github/workflows/ui-runtime.yml)):
  startet die echten Oberflächen statt nur statisch zu prüfen.
  - `desktop-gui-smoke`: baut die customtkinter-App unter `xvfb` auf,
    ruft `_refresh_all` und fängt Render-/Boot-Crashes
    ([tests/test_gui_boot_smoke.py](../../tests/test_gui_boot_smoke.py)).
  - `mobile-kivy-smoke`: bootet die KivyMD-App headless (Mock-Window)
    und baut alle fünf Tabs
    ([tests/test_mobile_boot_smoke.py](../../tests/test_mobile_boot_smoke.py)).
  - Beide Jobs sind **zunächst beratend** (`continue-on-error: true`), da
    ohne lokale Ausführungs-Umgebung erstellt. Nach dem ersten grünen Lauf
    vom Release-Owner verpflichtend machen (Flag entfernen).
- **Android Robo/Monkey** ([`.github/workflows/android-robo.yml`](../../.github/workflows/android-robo.yml),
  manuell): baut ein Debug-APK und stresst es mit `monkey` auf einem
  Emulator; bricht bei `FATAL EXCEPTION`/ANR ab.
- **Pre-Launch-Report (maßgeblich):** Upload in den Internal-Track lässt
  Google die App auf **echten Geräten** testen (Crashes, Accessibility,
  Sicherheit) — der kostenlose, authoritative Weg; siehe
  [11_PLAY_SUBMISSION.md](11_PLAY_SUBMISSION.md).
- **Android Vitals** (Crash-free ≥ 99,5 %, ANR < 0,47 %) werden erst nach
  Veröffentlichung gemessen und sind in der Release-Checkliste (Abschnitt M)
  als Gate hinterlegt.
