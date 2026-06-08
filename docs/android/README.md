# Android-/Google-Play-Compliance-Suite

Diese Suite ist die **Single Source of Truth** für alle technischen, sicherheits-,
qualitäts- und richtlinienbezogenen Anforderungen, die ZunaroDo
auf Android und im Google Play Store erfüllen muss.

Sie ist doppelspurig angelegt:

- **Aktuell (Ist-Zustand):** Python + KivyMD, gebaut via `buildozer` /
  `python-for-android`. Siehe [buildozer.spec](../../buildozer.spec).
- **Zukunftsfähig (Soll-Architektur):** Kotlin + Jetpack Compose, modular,
  CI/CD-getrieben - so dass eine spätere Native-Migration oder ein
  Native-Modul für Performance-kritische Pfade ohne Architektur-Rewrites
  möglich ist.

Jedes Dokument enthält **konkrete Maßnahmen für das aktuelle Setup** plus
**Native-Vorgaben** für den Fall, dass eine Kotlin/Compose-Variante gebaut
wird.

## Dokumenten-Index

| Nr.  | Dokument | Zweck |
| ---- | -------- | ----- |
| 01   | [Architektur & Projektstruktur](01_ARCHITECTURE.md) | Schichten, Module, Naming, Build-Typen, Flavors |
| 02   | [Play-Store-Compliance-Checkliste](02_PLAYSTORE_COMPLIANCE.md) | API-Level, Manifest, verbotene APIs, Richtlinien |
| 03   | [Sicherheitsrichtlinie](03_SECURITY.md) | Secrets, TLS, Speicher, R8, Tamper-Schutz |
| 04   | [Datenschutz & Berechtigungen](04_PRIVACY_PERMISSIONS.md) | Datenfluss, Permission-Matrix, SDK-Inventar, Data-Safety-Form |
| 05   | [Performance-Standards](05_PERFORMANCE.md) | Startup, ANR, Memory, APK-Größe, Baseline Profiles |
| 06   | [QA-Strategie](06_QA_STRATEGY.md) | Unit/UI/E2E, Geräte-Matrix, Coverage |
| 07   | [CI/CD-Konzept](07_CICD.md) | GitHub Actions, Signierung, Release-Pipeline, Branching |
| 08   | [Accessibility & UX](08_ACCESSIBILITY.md) | Screenreader, Kontraste, Touch-Targets, dynamische Texte |
| 09   | [Release-Checkliste](09_RELEASE_CHECKLIST.md) | Pre-Flight-Liste vor jedem Play-Store-Upload |
| 10   | [Typische Ablehnungsgründe & Gegenmaßnahmen](10_REJECTION_REASONS.md) | Realer Katalog inkl. Maßnahmen |
| 11   | [Play-Console-Einreichung](11_PLAY_SUBMISSION.md) | Hand-Schritte (Data-Safety, Content-Rating, Assets, Identität) mit generierten Antworten |
| 12   | [Play Billing Integration](12_PLAY_BILLING_INTEGRATION.md) | Roadmap Google Play Billing (Kivy/Buildozer) |

## Automatisierte Prüfmechanismen

Quelle: [tools/playstore_check.py](../../tools/playstore_check.py)

```bash
# Alle Checks ausführen (exit 0 = okay, >0 = mindestens eine Verletzung)
python -m tools.playstore_check --strict

# Einzelne Kategorien
python -m tools.playstore_check --only manifest,permissions,sdk
python -m tools.playstore_check --json > playstore_report.json
```

Der Checker prüft u.a.:

- `targetSdkVersion`, `minSdkVersion`, `compileSdkVersion`
- Manifest-Permissions vs. Whitelist
- Hardcoded Secrets / Keys im Repo
- Klartext-Kommunikation (`http://`)
- Exportierte Komponenten ohne `permission`-Attribut
- Debug-Logs / `print()` in Release-Pfaden
- Versionscode/-name-Konsistenz
- Lizenz-/Datenschutz-Dokumente vorhanden
- Verbotene/veraltete APIs (Heuristik)
- Drittanbieter-SDK-Inventar im Sync mit `04_PRIVACY_PERMISSIONS.md`

Die CI ruft denselben Checker im Workflow
[`.github/workflows/android-compliance.yml`](../../.github/workflows/android-compliance.yml)
auf - jeder PR muss grün sein.

## Reihenfolge der Adoption

1. **Sofort (Sprint 0):** API-Level auf 35 anheben (Play Store
   Mindestanforderung ab August 2025), `tools/playstore_check.py` in CI
   verdrahten, Datenschutz- und SDK-Inventar mit dem Ist-Stand befüllen.
2. **Kurz (1-2 Wochen):** R8/ProGuard-Equivalent (`p4a --release` mit
   Stripping) konfigurieren, signierten Release-Build, Data-Safety-Form
   vorbereitet.
3. **Mittel (4-6 Wochen):** Tests-Matrix in CI (mind. Python 3.10-3.12 +
   Android-Emulator-Smoketest via reactivecircus/android-emulator-runner).
4. **Lang:** Native Kotlin/Compose-Modul oder kompletter Native-Rewrite
   nach Architekturvorgabe in [01_ARCHITECTURE.md](01_ARCHITECTURE.md).

## Beziehung zu existierender Doku

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Architektur der Python-Schicht.
  Bleibt führend für Domain/Module/DB.
- [MOBILE.md](../../MOBILE.md) - KivyMD-spezifische Frontend-Erklärung.
  Wird inhaltlich nicht dupliziert, sondern referenziert.
- [legal/](../../legal/) - Datenschutz, AGB, Impressum. Pflicht-Artefakte
  für den Play-Store-Eintrag.

## Wer ist verantwortlich?

| Rolle | Verantwortung |
| ----- | ------------- |
| Dev-Lead | Architektur-Konformität (01), Code-Reviews gegen Standards |
| Security-Owner | 03, 04, Secret-Scanning, Pen-Test-Rotation |
| Release-Owner | 07, 09, signierte Builds, Play-Console-Uploads |
| QA-Owner | 06, 08, Geräte-Matrix, Crash-Triage |
| Datenschutzbeauftragter | 04 - SDK-Inventar, Data-Safety-Form, DSGVO-Konformität |
