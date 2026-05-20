# Release- und Compliance-Center (Admin/Developer-Panel)

Stand: 2026-05-20. Begleitend zu [TESTING.md](TESTING.md) und
[PLAYSTORE.md](PLAYSTORE.md). Dieses Dokument ist die normative
Grundlage zur Umsetzung eines professionellen QA-, Release- und
Compliance-Cockpits für eine Android-App, die mit Kotlin, Jetpack
Compose, Material 3, Firebase und der Google Play Console ausgeliefert
wird.

Das Panel ist **Compose Multiplatform** (Android + Desktop + Web mit
Compose-for-Web), mit Backend in Kotlin/JVM (Ktor) und Firebase als
Datenrücken. Es ist kein End-User-Frontend, sondern ein internes
Werkzeug für den App-Ersteller, das QA-Lead, DPO und Release-Lead
parallel nutzen.

---

## Inhalt

- [A. Vollständiges UI-/UX-Konzept](#a-vollstandiges-ui--ux-konzept)
- [B. Architekturdiagramme](#b-architekturdiagramme)
- [C. Navigationsstruktur](#c-navigationsstruktur)
- [D. Komponentenübersicht](#d-komponentenubersicht)
- [E. Datenmodelle](#e-datenmodelle)
- [F. Dashboard-Layouts](#f-dashboard-layouts)
- [G. Compose-Komponentenstruktur](#g-compose-komponentenstruktur)
- [H. Backend-/API-Anforderungen](#h-backend--api-anforderungen)
- [I. Firebase-Struktur](#i-firebase-struktur)
- [J. Test- und Release-Workflows](#j-test--und-release-workflows)
- [K. Go-/No-Go-Logik](#k-go--no-go-logik)
- [L. Google-Play-Upload-Prozess](#l-google-play-upload-prozess)
- [M. Reporting-System](#m-reporting-system)
- [N. Sicherheits- und Datenschutzmodule](#n-sicherheits--und-datenschutzmodule)
- [O. Implementierungsstrategie](#o-implementierungsstrategie)

---

## A. Vollständiges UI-/UX-Konzept

### A.1 Personas

| Persona | Verantwortung | Bevorzugte Sicht |
| --- | --- | --- |
| **Release-Lead** | Go/No-Go-Entscheidung, Upload | Dashboard + Release-Center + Play-Upload |
| **QA-Lead** | Testabdeckung, Negativtests, Bugs | Testcenter + Geräteverwaltung + Reports |
| **DPO / Privacy-Owner** | DSGVO, Data Safety, Berechtigungen | Compliance-Center + Reports |
| **Entwicklung** | CI-Logs, Crashlytics, Fixes | Live-Monitoring + Testcenter |
| **Tester-Koordinator** | Closed-Test-Pool | Closed-Testing-Center |
| **Management** | Burndown, Quality KPIs | Dashboard + PDF-Reports |

### A.2 Design-Tokens (Material 3)

```kotlin
object Tokens {
    // Farben
    val Primary       = Color(0xFF0B5FFF)    // markant, ruhig
    val Secondary     = Color(0xFF6750A4)    // Material-Default-Anker
    val Success       = Color(0xFF1B873B)
    val Warning       = Color(0xFFB54708)
    val Error         = Color(0xFFB42318)
    val Info          = Color(0xFF175CD3)
    val NeutralBg     = Color(0xFFF7F8FA)
    val NeutralBgDark = Color(0xFF0F1115)

    // Status-Ampel (immer kontrastreich, A11y-tauglich)
    val StatusGo      = Color(0xFF1B873B)
    val StatusHold    = Color(0xFFB54708)
    val StatusBlock   = Color(0xFFB42318)
    val StatusUnknown = Color(0xFF6B7280)

    // Spacing-Skala (4-pt-Grid)
    val s0 = 0.dp; val s1 = 4.dp; val s2 = 8.dp; val s3 = 12.dp
    val s4 = 16.dp; val s5 = 24.dp; val s6 = 32.dp; val s8 = 48.dp

    // Typografie
    val DisplayL = TextStyle(fontSize = 36.sp, lineHeight = 44.sp, fontWeight = FontWeight.SemiBold)
    val TitleL   = TextStyle(fontSize = 22.sp, lineHeight = 28.sp, fontWeight = FontWeight.Medium)
    val Body     = TextStyle(fontSize = 14.sp, lineHeight = 20.sp)
    val Mono     = TextStyle(fontFamily = FontFamily.Monospace, fontSize = 13.sp)
}
```

### A.3 Layout-Grid

- 12-Spalten-Grid, max. 1440 dp Inhaltsbreite, 24-dp-Gutter.
- **Adaptive Breakpoints** (Compose `WindowSizeClass`):

| Bereich | Breite | Layout |
| --- | --- | --- |
| compact | < 600 dp | bottom-nav, eine Spalte |
| medium | 600–839 dp | rail-nav, ein/zwei Spalten |
| expanded | 840–1199 dp | rail-nav, zwei/drei Spalten |
| large | ≥ 1200 dp | drawer-nav, drei Spalten + Detail-Pane |

### A.4 Interaktions-Prinzipien

1. **Status zuerst**: jede Karte hat oben einen Status-Pill (GO/HOLD/BLOCK/UNKNOWN) — sichtbar in < 200 ms ohne Hover.
2. **Drill-down**: ein Klick auf eine Kennzahl öffnet das Detail-Pane (Side-Sheet) ohne Routing-Wechsel.
3. **Live ist Default**: Live-Ansichten haben einen sichtbaren „Live-Indikator“ (pulsierender grüner Punkt) + Auto-Refresh-Throttle.
4. **Filter sind sticky**: Filter im URL-Querystring, daher teilbar und lesbar.
5. **Animationen ≤ 200 ms**: Standard-Easing `FastOutSlowIn`; reduzierte Bewegung respektiert `LocalReducedMotion`.
6. **Tastatur first**: alle Aktionen sind über Shortcuts erreichbar (siehe [D.6](#d6-keyboard-shortcuts)).
7. **A11y**: WCAG 2.2 AA als Mindest­ziel; Compose `semantics`-Annotations für jeden Status-Pill und Chart.

### A.5 Dark/Light-Mode

- Standard: System-Default (`isSystemInDarkTheme()`).
- Override pro Nutzer (`UserSettings.theme = AUTO|LIGHT|DARK`).
- Dark-Mode-Kontrastziel: 4.5:1 für Text, 3:1 für Status-Pills.
- Status-Ampel-Farben haben separate Dark-Varianten (`StatusGoDark = Color(0xFF34A853)` etc.).

---

## B. Architekturdiagramme

### B.1 Logische Schichten

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Compose-UI-Layer                            │
│  Screens · BottomNav · NavigationRail · Side-Sheet · Charts          │
├──────────────────────────────────────────────────────────────────────┤
│                       Feature-Module (DDD)                           │
│  feature-dashboard · feature-tests · feature-devices                 │
│  feature-closed-testing · feature-compliance · feature-release       │
│  feature-play-upload · feature-reports · feature-monitoring          │
├──────────────────────────────────────────────────────────────────────┤
│                    Domain (Use-Cases, Modelle)                       │
│  GoNoGoEngine · TestRunOrchestrator · ComplianceAuditor              │
│  TesterRegistry · ReportGenerator · ReleaseGateEvaluator             │
├──────────────────────────────────────────────────────────────────────┤
│                    Daten (Repos, Mappers)                            │
│  Firestore · Realtime DB · REST-Client · WebSocket-Client            │
│  Lokale Caches (Room) · Crashlytics-Export · Play-Developer-API      │
├──────────────────────────────────────────────────────────────────────┤
│                    Cross-Cutting                                     │
│  Auth (Firebase Auth + RBAC) · Logging · Feature-Flags · Telemetry   │
└──────────────────────────────────────────────────────────────────────┘
```

### B.2 System­topologie

```
                                                ┌───────────────────┐
                                                │  Play Console      │
                                                │  Developer API     │
                                                └────────▲──────────┘
                                                         │  REST
        ┌──────────────────┐    Ktor REST/WS   ┌─────────┴─────────┐
        │ Admin-Panel App  │ ◀────────────────▶│ QA-Backend (Kotlin/│
        │ Compose Multiplat│                   │ JVM, Ktor + Coroutines)│
        └────────▲─────────┘                   └─────┬──────────────┘
                 │                                   │
                 │  Firebase SDK                     │  Admin-SDK
                 ▼                                   ▼
        ┌──────────────────────────────────────────────────────────┐
        │                       Firebase                            │
        │  Auth · Firestore · Storage · Functions · FCM · Crashlytics│
        │  Performance · Remote Config · App Check                  │
        └─────────────▲─────────────────────────────────▲──────────┘
                      │                                 │
            ┌─────────┴────────┐               ┌────────┴────────┐
            │ GitHub Actions   │               │ Firebase Test    │
            │ Build / Tests    │ ───CD──────▶  │ Lab + Robo       │
            └──────────────────┘               └──────────────────┘
```

### B.3 Datenfluss (Test → Dashboard)

```
GitHub Actions:
  pytest → junit.xml → tools/test_protocol.py
                       → protocol.json (gleiche Struktur wie heute)
                       → upload zur QA-Backend-API (POST /runs)

QA-Backend:
  validiert & persistiert TestRun → Firestore (collection /runs/{id})
                                    + Realtime-DB-Channel (Push)
  feuert FCM-Topic „run-completed“ an Panel-Clients

Panel-Client (Compose):
  abonniert Firestore + RTDB-Channel
  re-rendert Dashboard, ggf. Notification anzeigen
```

---

## C. Navigationsstruktur

### C.1 Routen­baum

```
/
├── dashboard
├── tests
│   ├── overview
│   ├── runs/{runId}
│   ├── matrix/{matrixId}
│   ├── flaky
│   └── coverage
├── devices
│   ├── pool
│   ├── farm
│   ├── network-profiles
│   └── activity
├── closed-testing
│   ├── overview
│   ├── testers
│   ├── feedback
│   ├── crashes
│   └── calendar
├── compliance
│   ├── privacy
│   │   ├── data-flow
│   │   ├── permissions
│   │   ├── data-safety
│   │   └── sdk-inventory
│   ├── security
│   │   ├── scans
│   │   ├── secrets
│   │   ├── webviews
│   │   └── exported-activities
│   └── audits/{auditId}
├── release
│   ├── overview
│   ├── go-no-go
│   ├── notes
│   ├── rollback
│   └── changelog
├── play
│   ├── bundles
│   ├── store-listing
│   ├── reviews
│   └── policy-checks
├── reports
│   ├── library
│   └── builder
├── monitoring
│   ├── live
│   ├── logs
│   └── alerts
└── settings
    ├── account
    ├── roles
    ├── integrations
    ├── theme
    └── feature-flags
```

### C.2 Tiefen-Limit

Maximal **3 Klicks** vom Dashboard bis zu jedem Detail.

### C.3 URL-Schema

- Path-Segmente sind sprechend, in englischer Kebab-Case.
- Filter über Query-Strings: `/tests/runs?marker=privacy&status=failed&since=2026-05-13`.
- Permalink-Buttons in jedem Detail (Copy URL → Clipboard).

---

## D. Komponenten­übersicht

### D.1 Statusanzeige

```
StatusPill(state: StatusState, label: String, badgeCount: Int? = null)

  GO ●  green-700 / on-green
  HOLD ●  amber-700 / on-amber
  BLOCK ●  red-700 / on-red
  UNKNOWN ●  gray-500 / on-gray
```

- Größen: `Small (24 dp)`, `Default (32 dp)`, `Large (40 dp)`.
- Mit Tooltip für Erklärung, Tap zum Springen ins Detail.

### D.2 Karten­katalog

| Komponente | Zweck | Inhalt |
| --- | --- | --- |
| `KpiCard` | Eine Kennzahl + Trend | Wert, Δ-Pfeil, Sparkline, Subtitel |
| `StatusCard` | Domain-Status (Tests/Security/...) | StatusPill, 2–3 KPIs, CTA |
| `ChecklistCard` | Mehrere Bedingungen | Liste mit ●/✔/✘ Items |
| `TimelineCard` | Verlauf eines Builds | vertikale Liste mit Zeitstempeln |
| `GaugeCard` | Crash-Free, Coverage | radial-Gauge 0–100 % |
| `HeatmapCard` | Test x Gerät | Grid mit Status-Farben |
| `LogStreamCard` | Live-Log | virtualisierte Liste + Filter |
| `EvidenceCard` | Nachweis-Dokumente | Liste mit Hash + Download |
| `TesterCard` | Closed-Test-Profil | Avatar, Engagement-Tage, Bewertung |

### D.3 Diagramme

- **Sparkline** (Compose Canvas) — Trend einer KPI über 14 Tage.
- **Gauge** — 270°-Bogen, Wert in Mitte, Soll-Schwelle als Strich.
- **Heatmap** — n × m Grid, 6 Farben (UNKNOWN/PASS/FLAKY/FAIL/SKIP/RUNNING).
- **Burndown** — Linien-Chart über Tage / Tester-Engagement.
- **Calendar-Strip** — 14 Tage horizontal, Status pro Tag.

### D.4 Side-Sheet vs. Modal

- **Side-Sheet (rechts)**: Detail-Ansicht zu einer Listen-Zeile (nicht-modal, beibehält Listen-Scroll).
- **Modal-Dialog (zentriert)**: Bestätigung kritischer Aktionen (Promote-to-Production, Stop-Rollout).

### D.5 Toaster + Notification-Center

- Snackbars für Erfolg/Hinweise (max. 5 s).
- Persistente Notifications im Bell-Icon oben rechts; jede mit Severity + Drilldown-Link.

### D.6 Keyboard-Shortcuts

| Shortcut | Aktion |
| --- | --- |
| `g d` | Go to Dashboard |
| `g t` | Go to Tests |
| `g c` | Go to Compliance |
| `g r` | Go to Release |
| `?` | Shortcut-Übersicht |
| `Cmd/Ctrl + K` | Globales Such-Palette |
| `Cmd/Ctrl + .` | Aktuelle Aktion ausführen (z. B. Run start) |
| `Esc` | Side-Sheet schließen |

---

## E. Datenmodelle

Alle Modelle sind Kotlin `data class` + `@Serializable` (kotlinx-
serialization). Backend persistiert sie nach Firestore mit gleichem
Schema (Camel-Case bleibt).

```kotlin
@Serializable enum class StatusState { GO, HOLD, BLOCK, UNKNOWN }
@Serializable enum class TestStatus  { PASSED, FAILED, ERROR, SKIPPED, RUNNING }
@Serializable enum class Severity    { P0, P1, P2, P3 }
@Serializable enum class Role        { OWNER, ADMIN, QA, DPO, RELEASE, VIEWER }

@Serializable data class Project(
    val id: String, val name: String, val packageName: String,
    val targetSdk: Int, val minSdk: Int, val versionCode: Long,
    val versionName: String, val playTrack: String,           // "internal" | "closed" | "production"
)

@Serializable data class TestRun(
    val id: String, val projectId: String, val triggeredBy: String,
    val triggeredAt: Instant, val finishedAt: Instant?,
    val branch: String, val commitSha: String,
    val totals: TestTotals,
    val byMarker: Map<String, MarkerStats>,
    val records: List<TestRecord>,
    val decision: StatusState, val reasons: List<String>,
    val artifacts: Artifacts,
)

@Serializable data class TestTotals(
    val passed: Int, val failed: Int, val error: Int,
    val skipped: Int, val durationSec: Double, val count: Int,
)

@Serializable data class MarkerStats(
    val marker: String, val count: Int, val passed: Int,
    val failed: Int, val error: Int, val skipped: Int, val durationSec: Double,
)

@Serializable data class TestRecord(
    val id: String, val classname: String, val name: String,
    val status: TestStatus, val durationSec: Double, val message: String,
)

@Serializable data class Artifacts(
    val junitUrl: String?, val protocolMdUrl: String?,
    val protocolJsonUrl: String?, val coverageUrl: String?,
)

@Serializable data class Device(
    val id: String, val label: String, val type: DeviceType,
    val androidApi: Int, val screenClass: ScreenClass,
    val status: DeviceStatus, val owner: String?, val lastSeen: Instant,
)

@Serializable enum class DeviceType   { EMULATOR, PHYSICAL, TEST_LAB, REMOTE }
@Serializable enum class ScreenClass  { COMPACT, MEDIUM, EXPANDED, LARGE, FOLDABLE }
@Serializable enum class DeviceStatus { READY, BUSY, OFFLINE, BROKEN }

@Serializable data class Tester(
    val id: String, val pseudonym: String, val email: String,
    val joinedAt: Instant?, val engagementDays: Int,
    val sessionsTotal: Int, val rating: Int?,
    val device: String, val androidApi: Int,
)

@Serializable data class ClosedTestPlan(
    val id: String, val projectId: String, val startedAt: Instant?,
    val targetDays: Int = 14, val minTesters: Int = 12,
    val activeTesters: Int, val engagedTesters: Int,
    val cohort: List<Tester>,
)

@Serializable data class GoNoGoVerdict(
    val decision: StatusState, val reasons: List<String>,
    val criteria: List<GoNoGoCriterion>, val evaluatedAt: Instant,
)

@Serializable data class GoNoGoCriterion(
    val id: String,                 // z. B. "J2-T-02"
    val label: String,
    val state: StatusState,
    val value: String,              // gemessener Wert
    val threshold: String,          // Sollwert
    val evidence: String?,          // Link auf Artefakt
)

@Serializable data class BugReport(
    val id: String, val title: String, val severity: Severity,
    val status: String,             // OPEN, IN_PROGRESS, VERIFIED, CLOSED
    val reporter: String, val createdAt: Instant,
    val crashlyticsIssueId: String?, val artefacts: List<String>,
)

@Serializable data class PrivacyAudit(
    val id: String, val runAt: Instant,
    val cleartextHttp: Int, val hardcodedSecrets: Int,
    val piiInLogs: Int, val undocumentedPermissions: List<String>,
    val verdict: StatusState,
)

@Serializable data class ComplianceReport(
    val id: String, val createdAt: Instant,
    val format: String,             // PDF, HTML, MD, JSON, CSV
    val url: String, val sha256: String, val coveredCriteria: List<String>,
)
```

### E.1 Schemastabilität

- Felder werden niemals umbenannt. Entfernen erfolgt über
  „deprecated“-Markierung mit 6 Monaten Toleranz.
- Neue Felder sind immer optional (Nullable + Default), damit alte
  Clients weiterhin lesen.

---

## F. Dashboard-Layouts

### F.1 Hauptdashboard (expanded ≥ 1200 dp)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Logo  | Projekt: Zunarodo (v1.2.0, code 1234)  Branch: main   [Bell] [Avatar] │
├──────┬──────────────────────────────────────────────────────────────────┤
│      │  ┌──────── Release-Reifegrad ────────┐ ┌──── Closed-Test ─────┐ │
│  D   │  │ GO ●  78 %                          │ │ Tag 9/14   12/14 active│ │
│  T   │  │ 3 offene Bedingungen                │ │ ⌛ 5 Tage verbleiben    │ │
│  G   │  └─────────────────────────────────────┘ └────────────────────────┘ │
│  C   │  ┌── Tests ──┐ ┌── Crash-Free ──┐ ┌── Privacy ──┐ ┌── Security ─┐│
│  P   │  │ 937 ✅     │ │  99,82 %        │ │  ●●●●●●●●●●  │ │ ●●●●●●●○○  ││
│  R   │  │  +12 / 24 h │ │ ▲ 0,4 pp        │ │ 0 Findings   │ │ 1 Mid CVE  ││
│  L   │  └────────────┘ └─────────────────┘ └──────────────┘ └────────────┘│
│  M   │  ┌────── Live-Monitoring ──────────────────────────────────────┐ │
│      │  │ ⦿ pytest concept-suite running (53 % · 1m12s)              │ │
│      │  │ ⦿ Maestro PixelFold-Smoke queued                            │ │
│      │  │ ⦿ Crashlytics: 2 neue Issues (P1)                           │ │
│      │  └─────────────────────────────────────────────────────────────┘ │
│      │  ┌────── 14-Tage-Burndown ─────────────────────────────────────┐ │
│      │  │  Crashes: ▁▂▃▂▁▁▂▃▂▂▁▁▁▁  Engagement: ▇▇▇▇▆▆▇▇▇▇▆▇▇▇      │ │
│      │  └─────────────────────────────────────────────────────────────┘ │
└──────┴──────────────────────────────────────────────────────────────────┘
```

### F.2 Testcenter (Liste + Detail-Pane)

```
┌──────────────────────┬──────────────────────────────────────────────────┐
│ Filter               │ Run #4711 · pytest · main@a1b2c3                 │
│ ──────────────────   │                                                  │
│ Marker ▼ [privacy]   │ Status: GO ●   Dauer: 2:39  Tests: 937 + 3 skip  │
│ Status ▼ [failed]    │ ─────────────────────────────────────────────── │
│ Seit ▼ [7d]          │ Bereiche                                         │
│ ──────────────────   │  ● Members 18/18 · 70,7 s                         │
│ Runs                 │  ● Roles 69/69 · 1,0 s                            │
│ ──────────────────   │  ● Pairwise 13/13 · 9,5 s                         │
│ #4711 · GO · 2:39 ✓ │  ● Property 29/29 · 10,5 s                        │
│ #4710 · GO · 2:42 ✓ │  ● Negative 48/48 · 11,1 s                        │
│ #4709 · BLOCK · …✗  │  ● Privacy 244/244 · 4,3 s                        │
│ #4708 · GO · 2:39 ✓ │  ● Security 22/22 · 0,0 s                         │
│ #4707 · HOLD · …    │  ● Release-Gate 159/159 · 1,3 s                   │
│ #4706 · GO · 2:35 ✓ │                                                  │
│ #4705 · GO · 2:38 ✓ │  [JUnit XML] [protocol.md] [protocol.json]       │
└──────────────────────┴──────────────────────────────────────────────────┘
```

### F.3 Closed-Testing-Center

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Closed-Test-Pool  · Plan #11  · Start: 2026-05-11  Heute: Tag 9/14      │
├─────────────────────────────────────────────────────────────────────────┤
│  Aktiv: 12/14   Engagement ≥ 10 Tage: 10  Crash-Free 7d: 99,82 %        │
│  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  │
│                                                                         │
│  Tester                       Engagement   Gerät         Notes  Rating  │
│  ──────────────────────────────────────────────────────────────────────│
│  T01  AlexB    ●●●●●●●●○○      8/14        Pixel 5 (31)  3      ★★★★    │
│  T02  ChrisG   ●●●●●●●●●●     10/14        Pixel 7 (34)  1      ★★★★★   │
│  T03  Dany     ●●○○○○○○○○      2/14        Galaxy S22    0      ★★      │
│  …                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### F.4 Compliance-Center

```
┌──────────────── Datenschutz-Audit · 2026-05-20 ─────────────────────────┐
│ Cleartext-HTTP:       0 / 0 Whitelist                  GO ●            │
│ Hardcoded Secrets:    0                                GO ●            │
│ PII in Logs:          0                                GO ●            │
│ Permissions ungewollt: 0  (Soll: INTERNET, POST_NOTIFS) GO ●            │
│ DSGVO-Docs:           Datenschutz/Impressum/AGB/Widerruf ✓ GO ●        │
│ Lösch-Capability:     family.delete_member ✓            GO ●           │
│ Data-Safety-Hash:     09f3...e4   (review: 2026-05-19)  GO ●            │
└─────────────────────────────────────────────────────────────────────────┘
```

### F.5 Release-Center

```
┌────────────── Release v1.2.0 (versionCode 1234) ─────────────────────────┐
│   GO ●   alle 36 Bedingungen erfüllt                                     │
│                                                                          │
│ Technik (J2-T)      ✔ 6/6     Sicherheit (J2-S)   ✔ 5/5                  │
│ Datenschutz (J2-P)  ✔ 6/6     Qualität (J2-Q)     ✔ 5/5                  │
│ Performance (J2-F)  ✔ 4/4     Play-Store (J2-G)   ✔ 5/5                  │
│                                                                          │
│ [Promote to Closed]  [Promote to Production]  [Stop Rollout]             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## G. Compose-Komponentenstruktur

### G.1 Modul-Layout (Gradle, Compose Multiplatform)

```
admin-panel/
  app-android/                        # Android-Entry
  app-desktop/                        # JVM-Desktop-Entry
  app-web/                            # Compose-for-Web (Wasm)
  core-design/                        # Theme, Tokens, Components-Catalog
  core-domain/                        # Use-Cases, Models (E)
  core-data/                          # Firestore-, REST-, WS-Repos
  core-net/                           # Ktor-Client + DTO + Mapping
  core-auth/                          # Firebase Auth + RBAC
  feature-dashboard/
  feature-tests/
  feature-devices/
  feature-closed-testing/
  feature-compliance/
  feature-release/
  feature-play-upload/
  feature-reports/
  feature-monitoring/
  shared-charts/                      # Sparkline, Gauge, Heatmap
  shared-fixtures/                    # Mocks für Previews
backend/
  qa-api/                             # Ktor-Modul
  qa-functions/                       # Firebase Functions (TS)
tools/
  ingest-protocol/                    # CLI: protocol.json → API
  ingest-crashlytics/                 # CLI/Cron
```

### G.2 Beispiel — KpiCard

```kotlin
@Composable
fun KpiCard(
    title: String,
    value: String,
    state: StatusState = StatusState.UNKNOWN,
    delta: String? = null,
    spark: List<Float>? = null,
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
) {
    ElevatedCard(
        modifier = modifier
            .defaultMinSize(minWidth = 240.dp, minHeight = 116.dp)
            .clickable(enabled = onClick != null) { onClick?.invoke() }
            .semantics { contentDescription = "$title $value, Status $state" },
        shape = MaterialTheme.shapes.large,
    ) {
        Column(Modifier.padding(Tokens.s4)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(title, style = MaterialTheme.typography.titleSmall)
                StatusPill(state = state, size = StatusPillSize.Small)
            }
            Spacer(Modifier.height(Tokens.s2))
            Text(value, style = Tokens.DisplayL)
            if (delta != null) Text(
                delta,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            spark?.let {
                Spacer(Modifier.height(Tokens.s2))
                Sparkline(values = it, modifier = Modifier.height(28.dp).fillMaxWidth())
            }
        }
    }
}
```

### G.3 Screen-Skelett (Dashboard)

```kotlin
@Composable
fun DashboardScreen(vm: DashboardViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()
    when (val s = state) {
        is DashboardUiState.Loading -> ScreenSpinner()
        is DashboardUiState.Error   -> ScreenError(s.message, onRetry = vm::refresh)
        is DashboardUiState.Ready   -> DashboardContent(s, onSlice = vm::open)
    }
}

@Composable
private fun DashboardContent(state: DashboardUiState.Ready, onSlice: (Slice) -> Unit) {
    LazyVerticalGrid(
        columns = GridCells.Adaptive(minSize = 240.dp),
        contentPadding = PaddingValues(Tokens.s4),
        horizontalArrangement = Arrangement.spacedBy(Tokens.s3),
        verticalArrangement   = Arrangement.spacedBy(Tokens.s3),
    ) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            ReleaseReadinessCard(state.release, onClick = { onSlice(Slice.RELEASE) })
        }
        item { KpiCard("Tests",       state.tests.label,       state.tests.state, spark = state.tests.spark) }
        item { KpiCard("Crash-Free",  "${state.crashFree}%",   state.crashFreeState) }
        item { KpiCard("Privacy",     state.privacy.label,     state.privacy.state) }
        item { KpiCard("Security",    state.security.label,    state.security.state) }
        item(span = { GridItemSpan(maxLineSpan) }) {
            LiveActivityCard(state.live)
        }
    }
}
```

### G.4 State-Management

- **Unidirektional**: ViewModel hält `MutableStateFlow<UiState>`.
- **Use-Cases** liefern `Flow<DomainModel>`; ViewModel mappt zu `UiState`.
- **Side-Effects** über `Channel<Effect>` (Toast, Navigation, Confirmation).
- **DI**: Hilt (Android), Koin (Desktop), beide gemeinsam für Compose-Multiplatform.

---

## H. Backend-/API-Anforderungen

### H.1 REST-Endpunkte (Ktor)

| Methode | Pfad | Zweck |
| --- | --- | --- |
| GET | `/projects` | Liste der Projekte (RBAC) |
| GET | `/projects/{id}/dashboard` | aggregierte Dashboard-Daten |
| POST | `/projects/{id}/runs` | neuen TestRun anlegen (CI uploadet `protocol.json`) |
| GET | `/projects/{id}/runs?since=…` | TestRuns paginiert |
| GET | `/runs/{id}` | Detail-TestRun |
| GET | `/runs/{id}/artifacts/{name}` | signed-URL auf JUnit/Markdown |
| GET | `/projects/{id}/devices` | Geräte-Pool |
| POST | `/projects/{id}/devices/{deviceId}/lease` | Gerät reservieren |
| POST | `/projects/{id}/devices/{deviceId}/release` | Reservierung beenden |
| GET | `/projects/{id}/closed-test/current` | aktiver Plan |
| POST | `/projects/{id}/closed-test/{planId}/invite` | Tester einladen |
| GET | `/projects/{id}/compliance/latest` | letzte Privacy-Audit |
| POST | `/projects/{id}/compliance/run` | neuen Audit triggern |
| GET | `/projects/{id}/release/go-no-go` | Verdict + Begründung |
| POST | `/projects/{id}/release/promote` | Promote internal→closed→production |
| POST | `/projects/{id}/release/stop-rollout` | Rollout anhalten |
| GET | `/projects/{id}/reports?type=…` | Reports |
| POST | `/projects/{id}/reports/generate` | Report generieren (PDF/HTML/MD/CSV/JSON) |

### H.2 WebSocket-Kanäle

| Channel | Payload | Zweck |
| --- | --- | --- |
| `/ws/runs/{runId}` | TestRecord-Events | Live-Testlauf-Stream |
| `/ws/projects/{id}/logs` | LogLine | Live-Logs aller CI-Jobs |
| `/ws/projects/{id}/devices` | DeviceStatusUpdate | Geräte-Status-Push |
| `/ws/projects/{id}/notifications` | Notification | Bell-Icon-Updates |

Backpressure: jedes Channel-Frame ≤ 64 KB; bei Overload werden
TestRecords gestapelt (mind. 50 ms). Wiederverbindung mit
exponential-backoff (max 30 s).

### H.3 Authentifizierung

- **Firebase Auth (ID-Token)** als Standard, signed JWT.
- Backend verifiziert Token (firebase-admin), bindet RBAC aus Firestore.
- Für CI-Uploads: **Service-Account-Schlüssel** + kurzlebige API-Keys
  (1 h TTL, in Functions ausgestellt).

### H.4 Rate-Limits

| Endpoint | Limit |
| --- | --- |
| `POST /runs` | 30/min pro Projekt |
| `POST /reports/generate` | 5/min pro User |
| `POST /release/promote` | 1/min pro Projekt |

---

## I. Firebase-Struktur

### I.1 Firestore-Collections

```
projects/{projectId}                       # Project
  members/{uid}                            # Rolle, JoinedAt
  runs/{runId}                             # TestRun
    records/{recordId}                     # TestRecord (Sub-Collection für Pagination)
  devices/{deviceId}                       # Device
  testers/{testerId}                       # Tester
  closedTestPlans/{planId}                 # ClosedTestPlan
  audits/{auditId}                         # PrivacyAudit
  releases/{releaseId}                     # ReleaseSnapshot
  reports/{reportId}                       # ComplianceReport
  bugs/{bugId}                             # BugReport
  notifications/{notificationId}           # Notification
users/{uid}
  settings                                 # UserSettings
```

### I.2 Security-Rules-Skizze

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{db}/documents {
    function authed() { return request.auth != null; }
    function role(pid) {
      return get(/databases/$(db)/documents/projects/$(pid)/members/$(request.auth.uid)).data.role;
    }
    function isViewer(pid) { return authed() && role(pid) in ['OWNER','ADMIN','QA','DPO','RELEASE','VIEWER']; }
    function isEditor(pid) { return authed() && role(pid) in ['OWNER','ADMIN','QA','DPO','RELEASE']; }
    function isReleaseLead(pid) { return authed() && role(pid) in ['OWNER','RELEASE']; }

    match /projects/{pid} {
      allow read: if isViewer(pid);
      allow write: if false;            // nur über Cloud-Function

      match /runs/{runId} {
        allow read: if isViewer(pid);
        allow create: if isEditor(pid) || request.auth.token.ci == true;
        allow update, delete: if isReleaseLead(pid);
        match /records/{recordId} {
          allow read: if isViewer(pid);
          allow write: if false;        // nur via Functions
        }
      }
      match /releases/{relId} {
        allow read: if isViewer(pid);
        allow write: if isReleaseLead(pid);
      }
      // ... weitere Subcollections analog
    }
  }
}
```

### I.3 Cloud Functions

| Trigger | Funktion | Aufgabe |
| --- | --- | --- |
| onCreate `runs/{id}` | `aggregateRun` | KPIs aggregieren, Notifications senden |
| HTTPS `evaluateGate` | `evaluateGate` | Go/No-Go-Verdict bilden + speichern |
| HTTPS `generateReport` | `generateReport` | PDF/HTML/MD aus Templates erzeugen |
| Scheduled (täglich) | `dailyDigest` | Tagesreport an Slack/Email |
| Scheduled (alle 5 min) | `liveSnapshot` | Live-Indikatoren aktualisieren |
| onWrite `bugs/{id}` | `bugSlack` | Slack-Webhook für P0/P1 |

### I.4 Storage-Bereiche

```
gs://qa-artifacts/<projectId>/
  runs/<runId>/junit.xml
  runs/<runId>/protocol.md
  runs/<runId>/protocol.json
  runs/<runId>/coverage.html
  releases/<releaseId>/release-notes.md
  releases/<releaseId>/proguard-mapping.txt
  reports/<reportId>.pdf
  reports/<reportId>.csv
```

Storage-Rules: nur signed-URLs (24 h TTL) für authentifizierte Viewer.

### I.5 Remote Config

- Feature-Flags: `dashboard.live_logs_enabled`, `play_upload_enabled`,
  `auto_go_no_go_strict`.
- Schwellen: `gate.crash_free_threshold = 99.5`,
  `gate.coverage_domain_min = 80`, `gate.min_testers = 12`,
  `gate.min_test_days = 14`.

### I.6 App Check

- Server-Endpoints prüfen App-Check-Token.
- Lokal-Entwicklung: Debug-Token via Firebase Console.

---

## J. Test- und Release-Workflows

### J.1 Test-Workflow (CI → Panel)

```
GitHub Actions: pytest →  python -m tools.test_protocol --all
                       →  POST /projects/{id}/runs   (mit api-key)
                            ├── enthält protocol.json
                            └── lädt junit.xml + protocol.md zu Storage
                       →  Cloud-Function aggregateRun
                            ├── Aggregat in /runs/{id} schreiben
                            └── Notification: „Run {id} {decision}“
                       →  Panel: Realtime-Update über Firestore-Listener
```

### J.2 Aktionen aus dem Panel

| Aktion | UI-Pfad | Backend-Auswirkung |
| --- | --- | --- |
| „Run starten“ | `Tests → Run new` | `workflow_dispatch` via GitHub-API |
| „Gerät reservieren“ | `Devices → Lease` | Test-Lab-Lock + 60 min TTL |
| „Audit starten“ | `Compliance → Run` | Function `runAudit` |
| „Promote to Closed“ | `Release → Promote` | Play-Track-API + Gate-Check |
| „Stop Rollout“ | `Release → Halt`   | Play-API set rollout = 0 % |

### J.3 Release-Workflow

```
PR → green CI → tag release/x.y.z
              → Workflow „pre-release“
                  ├── pytest concept + property + smoke
                  ├── lint/detekt/coverage
                  ├── privacy-scan
                  ├── manifest-audit
                  ├── Test-Lab Robo + Instrumented
                  └── Maestro release-gate-Suite
              → POST /release/snapshot
              → Panel: Release-Card aktualisiert
              → Manuell: „Promote to Closed“
                  ├── gradle-play-publisher publish
                  └── Closed-Test-Plan starten
              → 14 Tage Closed-Test (Panel überwacht)
              → Go/No-Go bestätigen
              → „Promote to Production“ (Staged Rollout 1 %)
              → Vitals-Monitor 24 h
              → Rollout aufdrehen (10 %, 50 %, 100 %)
```

---

## K. Go-/No-Go-Logik

### K.1 Entscheidungs-Engine

```kotlin
data class GateInputs(
    val totals: TestTotals,
    val byMarker: Map<String, MarkerStats>,
    val crashFreeUsers7d: Double,
    val anrRate: Double,
    val openP0Bugs: Int, val openP1Bugs: Int,
    val testersActive: Int, val testDaysCompleted: Int,
    val engagedTesters: Int,
    val cleartextHttp: Int, val hardcodedSecrets: Int,
    val undocumentedPermissions: List<String>,
    val targetSdk: Int, val signingValid: Boolean,
    val privacyPolicyReachable: Boolean,
    val dataSafetyHashMatches: Boolean,
    val coverageDomainPct: Int, val coverageDataPct: Int, val coverageUiPct: Int,
    val coldStartMs: Int,
)

object GoNoGoEngine {
    fun evaluate(input: GateInputs, cfg: Thresholds): GoNoGoVerdict {
        val crit = mutableListOf<GoNoGoCriterion>()

        // ----------- J2-T (Technik) -----------
        crit += oneCheck("J2-T-01", "Keine offenen C0/C1-Bugs",
            ok = input.openP0Bugs == 0 && input.openP1Bugs == 0,
            value = "P0=${input.openP0Bugs}, P1=${input.openP1Bugs}",
            threshold = "0/0")
        crit += oneCheck("J2-T-02", "Crash-Free-Users",
            ok = input.crashFreeUsers7d >= cfg.crashFree,
            value = "${input.crashFreeUsers7d}%", threshold = "${cfg.crashFree}%")
        crit += oneCheck("J2-T-03", "ANR-Rate",
            ok = input.anrRate < cfg.anrRate,
            value = "${input.anrRate}%", threshold = "< ${cfg.anrRate}%")

        // ----------- J2-S (Security) -----------
        crit += oneCheck("J2-S-02", "Hardcoded Secrets",
            ok = input.hardcodedSecrets == 0,
            value = "${input.hardcodedSecrets}", threshold = "0")
        crit += oneCheck("J2-S-04", "TLS-only",
            ok = input.cleartextHttp == 0,
            value = "${input.cleartextHttp}", threshold = "0")

        // ----------- J2-P (Privacy) -----------
        crit += oneCheck("J2-P-01", "Datenschutzerklärung erreichbar",
            ok = input.privacyPolicyReachable, value = "—", threshold = "200")
        crit += oneCheck("J2-P-02", "Data-Safety-Hash unverändert oder reviewt",
            ok = input.dataSafetyHashMatches, value = "—", threshold = "✓")
        crit += oneCheck("J2-P-03", "Nur dokumentierte Permissions",
            ok = input.undocumentedPermissions.isEmpty(),
            value = input.undocumentedPermissions.joinToString(),
            threshold = "[]")

        // ----------- J2-Q (Qualität) -----------
        crit += oneCheck("J2-Q-01", "Test-Suite grün",
            ok = input.totals.failed == 0 && input.totals.error == 0,
            value = "${input.totals.failed}+${input.totals.error}", threshold = "0+0")
        crit += oneCheck("J2-Q-02 (Domain)", "Coverage Domain",
            ok = input.coverageDomainPct >= cfg.coverageDomain,
            value = "${input.coverageDomainPct}%", threshold = "${cfg.coverageDomain}%")

        // ----------- J2-F (Performance) -----------
        crit += oneCheck("J2-F-01", "Kaltstart P50",
            ok = input.coldStartMs < cfg.coldStartMs,
            value = "${input.coldStartMs} ms", threshold = "< ${cfg.coldStartMs} ms")

        // ----------- J2-G (Play-Store) -----------
        crit += oneCheck("J2-G-01a", "≥ ${cfg.minTesters} Tester",
            ok = input.testersActive >= cfg.minTesters,
            value = "${input.testersActive}", threshold = "≥ ${cfg.minTesters}")
        crit += oneCheck("J2-G-01b", "≥ ${cfg.minDays} Closed-Test-Tage",
            ok = input.testDaysCompleted >= cfg.minDays,
            value = "${input.testDaysCompleted}", threshold = "≥ ${cfg.minDays}")
        crit += oneCheck("J2-G-03", "targetSdk aktuell",
            ok = input.targetSdk >= cfg.targetSdkMin,
            value = "${input.targetSdk}", threshold = "≥ ${cfg.targetSdkMin}")
        crit += oneCheck("J2-G-04", "Signierung gültig",
            ok = input.signingValid, value = "—", threshold = "✓")

        val decision = when {
            crit.any { it.state == StatusState.BLOCK } -> StatusState.BLOCK
            crit.any { it.state == StatusState.HOLD }  -> StatusState.HOLD
            else                                       -> StatusState.GO
        }
        val reasons = crit.filter { it.state != StatusState.GO }.map { "${it.id}: ${it.label}" }
        return GoNoGoVerdict(decision, reasons, crit, Clock.System.now())
    }

    private fun oneCheck(id: String, label: String, ok: Boolean,
                          value: String, threshold: String): GoNoGoCriterion {
        val s = if (ok) StatusState.GO else StatusState.BLOCK
        return GoNoGoCriterion(id, label, s, value, threshold, evidence = null)
    }
}
```

### K.2 Schwellen aus Remote Config

Werte werden aus Remote Config gezogen, sodass eine Anpassung kein
Re-Deploy braucht. Default-Werte stehen in `core-data` als Fallback,
falls Remote Config nicht erreichbar ist.

### K.3 Sichtbarkeit

- Jede Bedingung wird in der `GoNoGoCard` als grün/gelb/rot mit
  Tooltip („Quelle: TestRun #4711“) sichtbar.
- Klick auf eine Bedingung springt direkt in die zugehörige Beweisstelle
  (Run, Audit, Tester-Pool).

---

## L. Google-Play-Upload-Prozess

### L.1 Pre-Upload-Checks (vom Panel erzwungen)

1. AAB signiert und Versions-Code inkrementiert.
2. ProGuard/R8-Mapping vorhanden.
3. Store-Listing-Felder vollständig (DE + EN, Screenshots, Promo).
4. Data-Safety-Form gespeichert + Hash gleich Repo-Hash.
5. Datenschutzerklärung-URL erreichbar (CI prüft 200 OK).
6. Inhaltsbewertung aktuell.
7. Targeting (Zielgruppe, Altersfreigabe) gesetzt.
8. Releaseskanal definiert (Closed / Production + Rollout-Prozent).
9. Pre-Launch-Report-Ergebnis vorhanden.

### L.2 Upload-Pfad

```
Panel: „Promote to Closed“
   ├── Pre-Upload-Checks (siehe oben)
   ├── Bestätigungs-Dialog (Modal)
   ├── Backend startet Cloud-Function `promoteRelease`
   │     └── ruft Play-Developer-API
   │           ├── edits.bundles.upload
   │           ├── edits.tracks.update (track=closed, status=completed)
   │           └── edits.commit
   ├── Panel zeigt Live-Fortschritt (3 Schritte) im Side-Sheet
   └── Bei Erfolg: Notification + ReleaseSnapshot aktualisiert
```

### L.3 Rollback

- „Stop Rollout“ setzt `userFraction = 0`.
- „Rollback to previous“ setzt den vorherigen Versionscode wieder als
  aktiv in der gleichen Track-Stage.
- Beide Aktionen erzeugen einen **AuditTrail-Eintrag** mit Begründung.

### L.4 Optional: Tools/CLI

Der Panel-Backend nutzt intern Library-Code, der auch als Standalone-
CLI verfügbar ist:

```
qa-cli promote --project zunarodo --track production --rollout 0.01
qa-cli halt    --project zunarodo
qa-cli report  --project zunarodo --type pdf --window 14d
```

---

## M. Reporting-System

### M.1 Reporttypen

| Typ | Inhalt | Formate |
| --- | --- | --- |
| `test-run` | Ein TestRun (analog zu `protocol.md`) | MD, HTML, PDF, JSON |
| `closed-test` | Engagement, Crashes, Feedback | PDF, HTML, CSV |
| `compliance` | Privacy + Security | PDF, HTML, JSON |
| `release` | Go/No-Go-Verdict + Snapshot | PDF, HTML, MD |
| `management` | KPIs, Trends, Risiken | PDF, HTML |

### M.2 Generator

```
ReportGenerator(template, data) → ByteArray
```

- Templates in `qa-functions/templates/{name}.hbs` (Handlebars).
- PDF via `wkhtmltopdf` (oder Playwright-Print) im Functions-Container.
- Reports werden in Storage abgelegt + im Firestore-Index referenziert.

### M.3 Verteilung

- Auto-Email an Verteiler (DPO, Release-Lead, Management) konfigurierbar.
- Direkter Slack-Webhook für „management“ und „release“ Reports.
- Permalink (Storage signed-URL, 7 d TTL).

### M.4 Lokaler Prototyp

Eine lauffähige Vorschau dieses Konzepts liegt in
[`tools/dashboard.py`](tools/dashboard.py): sie konsumiert
`tests/concept/reports/protocol.json` und rendert ein statisches HTML-
Dashboard mit Status-Pills, KPI-Karten und Test-Liste — damit ist der
Reporting-Teil ohne Cloud-Infrastruktur lokal demonstrierbar.

---

## N. Sicherheits- und Datenschutzmodule

### N.1 Audit-Subsystem

| Subsystem | Quelle | Frequenz |
| --- | --- | --- |
| HTTPS-only-Scan | Repo-Scan (regex) | jeder PR |
| Secret-Scanner | GitHub Secret Scanning + Repo-Regex | jeder PR + täglich |
| Manifest-Audit | Manifest-Permissions vs. Whitelist | jeder PR |
| Dependency-Scan | OWASP, Trivy, gradle-versions | nightly + pre-release |
| Webview-/Intent-Audit | Statische Analyse über AndroidLint | nightly |
| Crashlytics-PII-Audit | Custom-Keys-Inspector | nightly |

### N.2 Visualisierung

- **Risikomatrix-Heatmap** (4 × 4) — pro Befund x Severity.
- **Datenschutz-Ampel** — eine `StatusPill` pro DSGVO-Artikelgruppe (6, 13/14, 15–22, 32, 33, 35).
- **Permission-Diff** — Diff zwischen Manifest-State und Whitelist.

### N.3 Datenflussdiagramm

Live aus Firestore + Build-Konfiguration erzeugbar. Renderung im Panel
mittels Mermaid-Compose-Wrapper (`shared-charts/mermaid.kt`) — derselbe
Quell-Text wie in `TESTING.md` Kapitel 12.4.

### N.4 Lösch-/Auskunfts-Workflows

- **DSGVO-Auskunftsanfrage**: Knopf „Auskunft generieren“ erzeugt ein
  ZIP mit allen Daten zu einem User (E-Mail-Hash + UID).
- **Löschanfrage**: Cloud-Function `deleteUserData` löscht über Tenant
  + entkoppelt Referenzen.

---

## O. Implementierungsstrategie

### O.1 Phasenplan (12 Monate)

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| 0 | 2 Wochen | Repo, Design-Tokens, Auth-Stub, leere Module |
| 1 | 4 Wochen | Dashboard + Testcenter (read-only) + Ingest aus `protocol.json` |
| 2 | 4 Wochen | Geräteverwaltung + Live-Monitoring (WebSocket) |
| 3 | 4 Wochen | Closed-Testing-Center + Tester-Pool + Feedback |
| 4 | 6 Wochen | Compliance-Center + Audit-Subsystem + Reports |
| 5 | 4 Wochen | Release-Center + Go/No-Go-Engine + Audit-Trail |
| 6 | 4 Wochen | Play-Upload + Play-API-Integration |
| 7 | 4 Wochen | Reporting-System mit allen Formaten |
| 8 | 4 Wochen | Härtung, Performance, A11y, Internationalisierung |
| 9 | 4 Wochen | Multiplatform-Polish (Desktop/Web), Onboarding |
| 10 | 2 Wochen | Beta intern, Doku, Schulungen |
| 11 | 2 Wochen | GA-Rollout |

### O.2 Erfolgsmessung

- **Time-to-Verdict**: Zeit von Commit bis Go/No-Go im Panel ≤ 15 min.
- **MTTR**: Mean Time to Resolve P0/P1 ≤ 24 h.
- **Adoption**: ≥ 95 % der Release-Entscheidungen erfolgen über das Panel.
- **Audit-Decken**: 100 % der Releases haben generierte Reports
  archiviert.

### O.3 Risiken und Mitigation

| Risiko | Mitigation |
| --- | --- |
| Play-API-Rate-Limit | Backoff + lokale Queue; nur Release-Lead-Aktionen passieren API |
| Realtime-Last bei vielen Tests | Server-side-Aggregation, batched WS-Frames |
| Firestore-Kosten | TestRecords nach 90 Tagen ins Storage-CSV exportieren |
| RBAC-Bugs | Security-Rules-Unit-Tests, jeder Endpoint hat Negativ-Test |
| Vendor-Lock-in (Firebase) | Datenmodelle Datenbank-agnostisch, Repo-Pattern |

### O.4 Test- und Qualitätsplan für das Panel selbst

- Compose-UI-Tests pro Screen (Compose `createComposeRule`).
- ViewModel-Unit-Tests mit Turbine.
- Backend-Integrationstests mit Firebase-Emulator.
- E2E-Smoke via Maestro auf Android-App-Variante.
- Snapshot-Tests für alle Karten (Paparazzi/Shot).
- A11y-Pflicht: TalkBack-Sweep einmal pro Release.

### O.5 Liefer-Reihenfolge der erforderlichen Module

1. `core-design`, `core-auth`, `core-domain`, `core-data`.
2. `feature-dashboard` + Ingest-CLI.
3. `feature-tests` + WebSocket-Live-Logs.
4. `feature-devices` + `feature-closed-testing`.
5. `feature-compliance`.
6. `feature-release` + Go-/No-Go-Engine.
7. `feature-play-upload` + `feature-reports`.
8. `feature-monitoring` (final).

---

## Anhang: Mapping zu bestehenden Artefakten

| Bereich | Quelle im Repo |
| --- | --- |
| Test-Konzept | [TESTING.md](TESTING.md) |
| Closed-Testing-Anforderungen | [TESTING.md](TESTING.md) §6 + §13, [PLAYSTORE.md](PLAYSTORE.md) |
| Negativ-/Privacy-/Compliance | [TESTING.md](TESTING.md) Teil II §11–14 |
| Go/No-Go-Engine | [TESTING.md](TESTING.md) Anhang J + J2 |
| Protokoll-Generator (Vorlage) | [tools/test_protocol.py](tools/test_protocol.py) |
| Dashboard-Prototyp (HTML) | [tools/dashboard.py](tools/dashboard.py) |
| Pairwise-/Matrix-Artefakt | [tests/concept/reports/pairwise-matrix.tsv](tests/concept/reports/pairwise-matrix.tsv) |

---

*Eigentümer: QA-Lead, Release-Lead, DPO, Engineering-Lead.
Letzte Review: 2026-05-20. Pflicht-Review vor Phase-Übergang.*
