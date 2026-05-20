# 06 - QA-Strategie

## 1. Testpyramide

```text
        E2E / Maestro  (5-10 %)        ← Smoke gegen echten/emulierten Build
       ----------------------
     UI / Compose-Tests        (15-25 %)
   --------------------------------
 Integration / Repo+DB              (20-30 %)
-------------------------------------------
Unit (helpers, mappers, viewmodels)  (40-60 %)
```

Coverage-Ziel: **>= 80 %** auf Domain + Repos, **>= 60 %** auf
ViewModels/Helpers, **>= 30 %** auf reine UI.

Aktueller Stand (Python):
- `tests/test_smoke.py` mit 147 Regressionstests
- `tests/test_mobile_helpers.py` (28 Tests für reine Logik)
- `tests/test_integration.py`, `test_property.py`, `test_performance.py`

Diese Suite bleibt **autoritativ**. Native-Tests kommen erst mit
Native-Migration.

## 2. Pflicht-Test-Arten

### 2.1 Unit-Tests

- Reine Logik, keine I/O, kein Mocking von Frameworks.
- Native: JUnit5 + `kotlin.test`, `Turbine` für Flows, `MockK` für
  Test-Doubles.
- Python: `unittest` (bereits Standard im Repo) + `hypothesis` für
  Properties.

**Was MUSS Unit-getestet sein:**
- Jede Capability in `core.interface.ModuleRegistry`.
- Jede Helper-Funktion in `mobile/helpers.py`.
- Jede Domain-UseCase im Native-Modul.
- Lizenz-Validierung (`license_token.py`).

### 2.2 Repository-/Integrationstests

- Gegen echte DB-Instanz (in-memory bzw. `:memory:`).
- Schema-Migrationen Round-Trip getestet.
- Sync-Conflict-Tests: Replay zweier divergenter Branches.

**Pflicht-Szenarien:**
- Schema-Upgrade von Version N -> N+1 mit Seed-Daten.
- Soft-Delete + Restore + Purge.
- Concurrent-Write (zwei Repos schreiben gleichzeitig).

### 2.3 UI-Tests

**Compose (Native):**
- `createAndroidComposeRule<MainActivity>()` mit Hilt-Test.
- Pro Screen mind. 1 Test:
  - Initial-Render passt.
  - User-Interaktion ruft erwarteten UseCase auf (über Fake-VM).
  - Error-State wird dargestellt.

**KivyMD (Ist):**
- Pflicht: Logik in `mobile/helpers.py` ist headless testbar.
- Optional: `kivy.tests` headless Touch-Sim - aufwendig, nur für
  kritische Screens.
- Realistischer Ansatz: Manuelles Smoke-Skript via `python -m mobile.app`
  + 5-Punkt-Checklist (vgl. [09_RELEASE_CHECKLIST.md](09_RELEASE_CHECKLIST.md)).

### 2.4 End-to-End-Tests

- **Maestro** (YAML-Flows) ist die bevorzugte Wahl: läuft auch gegen
  einen frisch installierten APK in einem Emulator.
- Pflicht-Flows:
  1. App-Start -> Bottom-Nav alle 5 Tabs -> kein Crash.
  2. Vertrag anlegen -> in Liste sichtbar -> löschen -> nicht mehr
     sichtbar.
  3. Ausgabe anlegen -> Summe stimmt -> Export starten -> Datei
     existiert.
  4. Settings -> Datenschutz öffnen -> Datei lesbar.
  5. Lizenz-Aktivierung mit Test-Token -> Pro-Funktionen freigeschaltet.

### 2.5 Multi-Device-Matrix

Pflicht-Geräteliste je Release:

| Größe   | OS-Versionen | Beispielgerät |
| ------- | ------------ | ------------- |
| Phone klein 5" | Android 7 (API 24), 10, 13 | Pixel 4a |
| Phone medium 6" | Android 11, 14 | Pixel 6 |
| Phone groß 6.7" | Android 14, 15 | Pixel 8 Pro |
| Foldable | Android 14 | Pixel Fold |
| Tablet 7" | Android 13 | Galaxy Tab S6 Lite |
| Tablet 10" | Android 14 | Pixel Tablet |

Tests auf API 24 (Min) und API 35 (Target) sind **Pflicht**.

Empfehlung: **Firebase Test Lab** Robo + Maestro - bezahlbare Cloud-
Lösung, kein eigener Geräte-Pool nötig.

### 2.6 Variation Coverage

Pro Pflicht-Flow zusätzlich testen:

- Rotation Portrait -> Landscape -> Portrait
- Dark-Mode an / aus
- Schriftgröße XL (Accessibility, sys-setting `font_scale = 1.5`)
- Sprache Deutsch + Englisch
- Offline-Modus (Flugmodus)
- Niedrigspeicher (`adb shell am send-trim-memory <pid> RUNNING_LOW`)

## 3. Coverage-Reporting

| Tool | Sprache | Output |
| ---- | ------- | ------ |
| `coverage.py` | Python | HTML + XML, bereits in `.coveragerc` |
| JaCoCo | Native Kotlin | XML, Codecov-Upload |

CI lädt Coverage zu Codecov hoch; PR-Kommentar zeigt Delta.
**Regression > 2 %** ist Block.

## 4. Lint, Style, Statik

| Tool | Zweck | Modus |
| ---- | ----- | ----- |
| `ruff` / `flake8` | Python-Lint | CI-Block |
| `black` | Python-Format | CI-Verify-Mode |
| `mypy --strict` | Python-Typen | CI-Block (Repo nutzt `.mypy_cache`) |
| `bandit` | Python-Security | CI-Block |
| `pip-audit` | Python-CVE | CI-Block bei CVSS >= 7 |
| `ktlint` | Kotlin-Format | CI-Verify-Mode |
| `Detekt` | Kotlin-Static-Analysis | CI-Block |
| Android Lint (`lint --fatal`) | Manifest, Resources, APIs | CI-Block |
| `mobsfscan` | Android-Security-Statik | CI-Warn |

## 5. Crash-Analyse

- Crashlytics (Firebase) oder Sentry (self-hosted bevorzugt aus DSGVO-
  Sicht).
- **Opt-in** in der App (siehe [04_PRIVACY_PERMISSIONS.md](04_PRIVACY_PERMISSIONS.md)).
- Crashes mit > 0,2 % User-Impact werden zu P1.
- Wöchentlicher Triage-Termin, Owner = Tech-Lead.
- Erste 48 h nach Rollout: Crash-Dashboard aktiv beobachten,
  Rollout-Stopp via Play-Console-Halted-Rollout, falls Schwelle reißt.

## 6. Manuelle Test-Checkliste pro PR

Nicht jeder PR braucht alles, aber jeder UI-PR mindestens:

- [ ] Build lokal grün (`pytest` / `gradle assembleDebug`)
- [ ] App startet
- [ ] Betroffener Screen funktioniert (Golden Path)
- [ ] Mind. 1 Edge-Case (leerer State, Fehler-State)
- [ ] Dark-Mode noch okay
- [ ] Keine Logs mit PII

## 7. Testdaten

- Repo enthält Demo-DB (`alltagshelfer_demo.db`) - **nicht in Release**.
- Buildozer-Spec sollte `source.exclude_exts = db,sqlite` enthalten
  (ist bereits gesetzt). Aktueller Check: ✓
- Fixture-Generator: `tests/conftest.py` (anlegen, falls noch nicht
  vorhanden) - liefert deterministische Seed-Daten.

## 8. Offline-Tests

Pflicht-Suite "Offline":

- App-Start ohne Netzwerk.
- Capability-Aufrufe (`contracts.add` etc.) funktionieren.
- Sync-Worker queued ausgehende Diffs.
- Bei Reconnect: Replay läuft fehlerfrei.

## 9. Accessibility-Tests

Siehe [08_ACCESSIBILITY.md](08_ACCESSIBILITY.md). In QA-Kontext:

- `accessibility-test-framework` (Native) - Compose-Test-Helper.
- TalkBack manuell durch alle Bottom-Nav-Bereiche.
- Schriftvergrößerung 130 %, 150 %, 200 % - kein Clipping.

## 10. Test-Automation in CI

Konkrete Schritte siehe [07_CICD.md](07_CICD.md). Kurzfassung:

- **Pre-Push (Hook):** `pytest -x` (Python).
- **PR Open:** Lint + Unit + Coverage + Compliance-Checker.
- **PR Merge in main:** Full Suite + APK-Build (Debug) + Macrobench
  Smoke.
- **Tag `v*`:** Release-Pipeline mit AAB, Signierung, Internal-Track-
  Upload.

## 11. Manuelle Pre-Production-Smoke (vor jedem Production-Push)

5-Punkte-Smoke direkt am Test-Device (15 Min):

1. Frische Installation (vorher deinstallieren).
2. Onboarding durchspielen, Datenschutz-Dialog erscheint, Privacy
   PDF/HTML öffnet.
3. Alle 5 Bottom-Nav-Tabs öffnen.
4. Einen Vertrag, eine Ausgabe, einen Termin anlegen + löschen.
5. Settings -> "Alle Daten löschen" testen (separates Testgerät!).

## 12. Definition of Done (DoD) je Feature

- [ ] Code + Tests gemerged.
- [ ] Coverage gleich oder höher.
- [ ] Lint/Detekt/MyPy grün.
- [ ] Compliance-Checker grün.
- [ ] Manuelle Smoke auf einem Mid-Range-Device.
- [ ] Doku aktualisiert, falls Berechtigung/SDK/Datenfluss berührt.
- [ ] CHANGELOG-Eintrag.

## 13. Bug-Triage-Schema

| Schweregrad | Definition | SLA |
| ----------- | ---------- | --- |
| P0 (Stop) | Datenverlust, Sicherheitsvorfall, > 5 % Crash-Rate | Hotfix innerhalb 24 h |
| P1 (Hoch) | Kernfunktion broken (Anlegen, Sync) | nächster Release, < 1 Woche |
| P2 (Mittel) | Auffälliges Verhalten, Workaround vorhanden | nächster Sprint |
| P3 (Niedrig) | Kosmetik | Backlog |
