# Testkonzept Android-App (Kotlin / Jetpack Compose / Firebase / Play Console)

Stand: 2026-05-20.
Stack-Annahme: Kotlin 2.x, Android Gradle Plugin 8.x, Jetpack Compose
(Material 3), Firebase (Auth, Firestore oder Realtime DB, Cloud Messaging,
Crashlytics, Remote Config, Analytics), Hilt/Koin als DI, Coroutines/Flow,
Room für Offline-Cache, WorkManager, Google Play Console mit Closed-Testing-
Track.

Dieses Dokument ist normativ: Es definiert *was* getestet wird, *wie* es
automatisiert wird, *wer* manuell testet und *wann* eine Veröffentlichung
freigegeben wird. Jede Abweichung muss im Release-Protokoll begründet
werden.

---

## Inhalt

1. [Testziel](#1-testziel)
2. [Testszenarien mit unterschiedlicher Mitgliederanzahl](#2-testszenarien-mit-unterschiedlicher-mitgliederanzahl)
3. [Kombinatorische Tests von Aufgaben und Funktionen](#3-kombinatorische-tests-von-aufgaben-und-funktionen)
4. [Vollautomatische Teststrategie](#4-vollautomatische-teststrategie)
5. [Testdaten und Testnutzer](#5-testdaten-und-testnutzer)
6. [Google-Play Closed Testing](#6-google-play-closed-testing)
7. [14-Tage-Testplan](#7-14-tage-testplan)
8. [Automatisierte Kombinatorik](#8-automatisierte-kombinatorik)
9. [CI/CD-Integration](#9-cicd-integration)
10. [Ergebnisformat A–K](#10-ergebnisformat-ak)
    - [A. Vollständiges Testkonzept (Übersicht)](#a-vollstandiges-testkonzept-ubersicht)
    - [B. Automatisierte Testarchitektur](#b-automatisierte-testarchitektur)
    - [C. Kombinatorische Testmatrix](#c-kombinatorische-testmatrix)
    - [D. Rollen- und Mitglieder-Testfälle](#d-rollen--und-mitglieder-testfalle)
    - [E. Aufgaben- und Funktions-Testfälle](#e-aufgaben--und-funktions-testfalle)
    - [F. 14-Tage-Testplan für ≥ 12 Tester](#f-14-tage-testplan-fur--12-tester)
    - [G. Tester-Onboarding-Vorlage](#g-tester-onboarding-vorlage)
    - [H. Feedback- und Fehlerberichts-Vorlagen](#h-feedback--und-fehlerberichts-vorlagen)
    - [I. CI/CD-Testpipeline](#i-cicd-testpipeline)
    - [J. Go-/No-Go-Kriterien für Play-Store-Veröffentlichung](#j-go--no-go-kriterien-fur-play-store-veroffentlichung)
    - [K. Maßnahmenplan bei Fehlern oder Google-Ablehnung](#k-massnahmenplan-bei-fehlern-oder-google-ablehnung)

---

## 1. Testziel

### 1.1 Übergeordnete Ziele

| Nr. | Ziel | Mess­barer Nachweis |
| --- | --- | --- |
| Z1 | **Technische Stabilität** | Crash-Free-Users ≥ 99,5 % über 7 Tage in Crashlytics; ANR-Rate < 0,47 % (Google-Schwelle: 0,47 %) |
| Z2 | **Fachliche Korrektheit** | 100 % der akzeptierten User-Stories haben grüne Integrationstests; Pareto-90-% der manuellen Akzeptanztests bestanden |
| Z3 | **Rollen & Berechtigungen korrekt** | Berechtigungsmatrix-Test deckt 100 % der Rolle×Aktion-Paare; 0 unerwartet erlaubte Aktionen |
| Z4 | **Aufgaben-/Funktionskombinationen** | Pairwise-Matrix abgedeckt (≥ 95 % der 2-fach-Kombinationen); Property-Tests grün |
| Z5 | **Google-Play-Readiness** | Pre-Launch Report ohne kritische Crashes; Data-Safety-Form aktuell; Closed Test ≥ 14 Tage / ≥ 12 Tester nachgewiesen |
| Z6 | **Nachweisbare Qualität** | Vollständiger Test-Audit-Trail (CI-Logs, Crashlytics, Firebase Test Lab, Tester-Feedback) für 30 Tage archiviert |

### 1.2 Nicht-Ziele (Out of Scope)

- Performance-Optimierung jenseits gemessener Engpässe.
- Lokalisierungs-Qualität (Übersetzungen) — separater LQA-Prozess.
- Penetrationstest durch externes Red-Team (separates Mandat).

### 1.3 Definition of Done für „testbereit“

Ein Build gilt als testbereit, wenn:
- alle Unit-, Integrations- und UI-Tests in CI grün sind,
- statische Analyse (Lint, Detekt, Ktlint) keine Errors meldet,
- Code-Coverage **Domain ≥ 80 %**, **Data-Layer ≥ 70 %**, **UI ≥ 50 %** (gemessen mit Kover/JaCoCo),
- der Smoke-Test auf Firebase Test Lab (4 Referenzgeräte) durchläuft,
- Crashlytics für die letzte interne Build-Version keine ungeklärten Crashes mit > 5 Vorkommen zeigt.

---

## 2. Testszenarien mit unterschiedlicher Mitgliederanzahl

Eine **Gruppe** (Workspace/Familie/Team) ist die organisatorische Einheit
mit beliebig vielen Mitgliedern. Jede Mitglied­schaft hat eine **Rolle**
(`OWNER`, `ADMIN`, `MEMBER`, `GUEST`) und einen **Status** (`INVITED`,
`ACTIVE`, `INACTIVE`, `REMOVED`).

### 2.1 Mitglieder-Szenario-Matrix

| ID | Mitglieder | Verteilung Rollen | Zweck |
| --- | --- | --- | --- |
| M-01 | 1 (nur Owner) | OWNER:1 | Einzelperson-Modus, kein Sharing, keine Berechtigungslogik |
| M-02 | 2 | OWNER:1, MEMBER:1 | minimaler Mehrnutzerfall, 1:1-Sync |
| M-03 | 3–5 | OWNER:1, ADMIN:1, MEMBER:n | typische Familie/Kleinteam |
| M-04 | 6–11 | OWNER:1, ADMIN:2, MEMBER:n, GUEST:1 | mittleres Team mit Gast |
| M-05 | 12 | OWNER:1, ADMIN:2, MEMBER:8, GUEST:1 | exakt Play-Mindesttester­zahl |
| M-06 | 20+ | OWNER:1, ADMIN:3, MEMBER:15, GUEST:3 | Skalierungs-/Last-Test |
| M-07 | gemischter Status | ACTIVE:60 %, INVITED:20 %, INACTIVE:10 %, REMOVED:10 % | Realität: nicht alle aktiv |
| M-08 | nur INVITED | INVITED:5, OWNER:1 | Pending-State, Gruppe „leer aktiv“ |
| M-09 | REMOVED-Reactivation | REMOVED:1 wird re-invited | Edge: Daten-Recovery / Rechte |

### 2.2 Geprüfte Aspekte je Szenario

Für jedes M-Szenario laufen folgende Prüfungen automatisiert + ggf. manuell:

| Aspekt | Automatisiert | Manuell | Werkzeug |
| --- | --- | --- | --- |
| Einladung erzeugen (Deep-Link, E-Mail, Code) | ✅ | ✅ | Espresso + Firebase Dynamic-Links Emulator |
| Registrierung (E-Mail/Pass, Google-SSO) | ✅ | ✅ | Auth-Emulator |
| Login (1./2./n. Gerät) | ✅ | ✅ | UI-Test + reales Gerät |
| Rollenvergabe (Owner → andere) | ✅ | ✅ | Firestore-Emulator + Espresso |
| Rechteprüfung (Berechtigungsmatrix) | ✅ | – | parametrisierter JUnit5-Test |
| Aufgabenverteilung (assign, reassign) | ✅ | ✅ | Compose-UI-Test |
| Synchronisierung (Realtime + offline merge) | ✅ | ✅ | Firestore-Emulator + Test Lab |
| Push-Benachrichtigungen | ✅ | ✅ | FCM-Test-API + Maestro |
| Konflikte (gleichzeitige Edits) | ✅ | ✅ | Property-Test + 2-Gerät-Maestro-Flow |
| Entfernen + erneut Hinzufügen | ✅ | ✅ | Integrationstest |

### 2.3 Detail: Konflikt-Test bei gleichzeitiger Nutzung

```kotlin
@Test
fun simultaneousEditOnSameTask_lastWriteWins_withConflictBanner() = runTest {
    val task = seed.createTask(group = G_M05, assignee = aliceId)
    coroutineScope {
        launch { simulate(alice).editTitle(task.id, "Title-A") }
        launch { simulate(bob).editTitle(task.id, "Title-B") }
    }
    awaitSync()
    val final = repo.task(task.id)
    assertThat(final.title).isAnyOf("Title-A", "Title-B")
    assertThat(events.last()).isInstanceOf(ConflictResolved::class.java)
}
```

Erwartung: **Letzter-schreibt-gewinnt** mit sichtbarem Konflikt-Banner und
nachvollziehbarem Audit-Log in `task_history/`.

---

## 3. Kombinatorische Tests von Aufgaben und Funktionen

### 3.1 Aufgaben-Dimensionen

| Dimension | Werte |
| --- | --- |
| Art | `STANDARD`, `CHECKLIST`, `APPROVAL`, `EVENT` |
| Wiederholung | `ONE_OFF`, `DAILY`, `WEEKLY`, `MONTHLY`, `CUSTOM_RRULE` |
| Priorität | `LOW`, `NORMAL`, `HIGH`, `URGENT` |
| Frist | `NONE`, `FUTURE`, `TODAY`, `OVERDUE` |
| Erinnerung | `OFF`, `15M`, `1H`, `1D`, `CUSTOM` |
| Bestätigung | `NONE`, `SELF`, `OWNER_CONFIRM` |
| Belohnung/Bewertung | `NONE`, `POINTS`, `STARS_1_5` |
| Status | `OPEN`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `CANCELED`, `OVERDUE`, `REASSIGNED` |

### 3.2 Funktions-Dimensionen (Kontext)

| Dimension | Werte |
| --- | --- |
| Rolle | `OWNER`, `ADMIN`, `MEMBER`, `GUEST` |
| Mitgliederanzahl | `1`, `2`, `3–5`, `6–11`, `12`, `20+` |
| Gerätezustand | `FOREGROUND`, `BACKGROUND`, `DOZE`, `KILLED` |
| Netz | `ONLINE`, `OFFLINE`, `SLOW_2G`, `FLAKY` |
| Push | `ENABLED`, `DISABLED`, `BLOCKED_OS` |
| Sync | `INSTANT`, `BATCHED`, `OFFLINE_QUEUE` |
| App-Lifecycle | `COLD_START`, `WARM_START`, `PROCESS_DEATH_RESTORE` |
| Gerätewechsel | `SAME_DEVICE`, `NEW_DEVICE_SAME_USER`, `TRANSFER` |
| Android-Version | `8 (API 26)`, `10 (29)`, `12 (31)`, `14 (34)`, `15 (35)` |
| Bildschirmgröße | `compact`, `medium`, `expanded`, `large`, `foldable` |

### 3.3 Kombinatorische Reduktion

Volle Kombination: 4·5·4·4·5·3·3·8 · 4·6·4·4·3·3·3·3·5·5 = **9,4 Mrd.**
Nicht testbar. Daher:

- **Pairwise Testing (allpairs/PICT/Jenny)** auf alle Aufgaben×Funktion-Dimensionen → ~ 320 Testfälle.
- **Risikopriorisierung**: Rolle/Frist/Sync sind Risiko-Hot-Spots → 3-fach-Coverage statt 2-fach.
- **Property-Based Tests (Kotest-property)** auf Domain-Logik (Recurrence, Permission, Conflict-Resolution).
- **Szenario-Tests** für 25 reale End-to-End-Stories (siehe E).

Siehe auch [Abschnitt 8](#8-automatisierte-kombinatorik) und [Anhang C](#c-kombinatorische-testmatrix).

---

## 4. Vollautomatische Teststrategie

### 4.1 Testpyramide (Sollverteilung)

```
        ┌───────────────────┐
        │   E2E / Maestro   │   ~5 %    (≤ 60 Flows, Test Lab + Maestro)
        ├───────────────────┤
        │  UI / Compose UI  │   ~15 %   (Screen- und Navigation-Tests)
        ├───────────────────┤
        │  Integration      │   ~30 %   (Repo+Emulator, ViewModel+Flow)
        ├───────────────────┤
        │  Unit             │   ~50 %   (Domain, Mapper, Use-Cases)
        └───────────────────┘
```

### 4.2 Test-Layer und Werkzeuge

| Layer | Werkzeug | Lauf-Umgebung | Trigger |
| --- | --- | --- | --- |
| **Unit** | JUnit 5, Kotest, MockK, Turbine, kotlinx-coroutines-test | JVM | jeder Commit |
| **Robolectric-Unit** | Robolectric 4.x | JVM | jeder Commit |
| **Integration** | Firebase Emulator Suite (Auth, Firestore, Functions, FCM, Storage), Room in-memory, Hilt-Test-Module | JVM/Android | jeder PR |
| **UI** | Compose-UI-Test (`createComposeRule`), Espresso für AndroidView-Interop, Accessibility-Test über `SemanticsNode` | Android, Gradle Managed Devices | jeder PR |
| **E2E** | Maestro Flows (yaml), Firebase Test Lab (Robo + Instrumented) | Cloud-Devices | nightly + Pre-Release |
| **API/Backend** | JUnit + Firebase Functions Emulator + Firestore-Security-Rules Test (`@firebase/rules-unit-testing`) | Node + JVM | jeder PR |
| **Lasttests** | k6 (gegen Functions), Firebase Performance, manueller 30-Gerät-Test im Test Lab | Cloud | nightly |
| **Statisch** | Android Lint, Detekt, Ktlint, Spotless | JVM | jeder Commit |
| **Coverage** | Kover (oder JaCoCo) | JVM | jeder PR |
| **Sicherheit** | dependencycheck, OWASP Mobile Top-10-Checklist, Firebase App Check | – | Pre-Release |

### 4.3 Konkrete Beispiel-Snippets

**Domain-Unit (Recurrence):**

```kotlin
class RecurrenceEngineTest : FunSpec({
    test("WEEKLY MON,WED produces next 4 dates") {
        val r = Recurrence(rule = "FREQ=WEEKLY;BYDAY=MO,WE")
        r.nextN(from = LocalDate.parse("2026-05-18"), n = 4) shouldBe listOf(
            LocalDate.parse("2026-05-18"),
            LocalDate.parse("2026-05-20"),
            LocalDate.parse("2026-05-25"),
            LocalDate.parse("2026-05-27"),
        )
    }
})
```

**Property-Test (Berechtigung):**

```kotlin
class PermissionPropertyTest : FunSpec({
    test("GUEST darf niemals andere Mitglieder entfernen") {
        checkAll(Arb.member(role = Arb.of(Role.GUEST)), Arb.member()) { actor, target ->
            permission.canRemove(actor, target) shouldBe false
        }
    }
})
```

**Compose-UI-Test:**

```kotlin
@get:Rule val compose = createAndroidComposeRule<MainActivity>()

@Test fun taskList_showsOverdueBadge_whenDueInPast() {
    seed.with { task(due = yesterday) }
    compose.onNodeWithTag("task-row").assertContentDescriptionContains("überfällig")
}
```

**Firestore-Security-Rules-Test (Node-Seite):**

```js
testEnv.authenticatedContext('guestUid').firestore()
  .doc('groups/g1/tasks/t1').delete()
  .then(() => fail('GUEST darf keine Tasks löschen'))
  .catch(() => pass());
```

### 4.4 Pflichtgeräte (Gradle Managed Devices)

```kotlin
testOptions {
  managedDevices {
    devices {
      maybeCreate<ManagedVirtualDevice>("pixel2_api26").apply { device = "Pixel 2"; apiLevel = 26; systemImageSource = "aosp" }
      maybeCreate<ManagedVirtualDevice>("pixel5_api31").apply { device = "Pixel 5"; apiLevel = 31; systemImageSource = "aosp-atd" }
      maybeCreate<ManagedVirtualDevice>("pixel7_api34").apply { device = "Pixel 7"; apiLevel = 34; systemImageSource = "google-atd" }
      maybeCreate<ManagedVirtualDevice>("foldable_api34").apply { device = "Pixel Fold"; apiLevel = 34; systemImageSource = "google-atd" }
      maybeCreate<ManagedVirtualDevice>("tablet_api34").apply { device = "Pixel Tablet"; apiLevel = 34; systemImageSource = "google-atd" }
    }
    groups { maybeCreate("ci_smoke").targetDevices.addAll(listOf(devices["pixel5_api31"], devices["pixel7_api34"])) }
  }
}
```

### 4.5 Release-Gate-Tests

Vor jedem Upload in Play Console (Internal/Closed/Production) **muss** der
Release-Gate-Job durchlaufen (siehe [I](#i-cicd-testpipeline)):

1. Volle Test-Pyramide grün.
2. Coverage-Schwellen erreicht.
3. Lint/Detekt: 0 Errors, ≤ 5 Warnings (Whitelist im Repo).
4. Firebase Test Lab Robo + Instrumented Smoke grün.
5. Maestro Pre-Release-Suite (15 Flows) grün.
6. Pre-Launch Report durchgelaufen, 0 kritische Crashes.
7. APK/AAB signiert, ProGuard/R8 ohne unerwartete Drops.
8. Datenschutz-Manifest und Data-Safety-Form unverändert oder reviewt.

---

## 5. Testdaten und Testnutzer

### 5.1 Synthetische Testnutzer

Ein Kotlin-Modul `:test-fixtures` erzeugt deterministische Nutzer:

```kotlin
object Fixtures {
    fun group(size: Int, seed: Long = 42L): GroupFixture = ...
    fun user(role: Role = MEMBER, status: Status = ACTIVE): User = ...
    fun tasks(group: GroupFixture, n: Int, rng: Random): List<Task> = ...
}
```

Profile (entspricht M-01..M-09):

| Profil | Größe | Rollen | Aufgaben |
| --- | --- | --- | --- |
| `SOLO` | 1 | OWNER | 10 ONE_OFF |
| `COUPLE` | 2 | OWNER, MEMBER | 30 gemischt |
| `FAMILY_5` | 5 | OWNER, ADMIN, 3×MEMBER (2 Kinder = GUEST) | 80 |
| `TEAM_11` | 11 | OWNER, 2×ADMIN, 7×MEMBER, GUEST | 150 |
| `BETA_12` | 12 | analog Closed-Test-Verteilung | 200 |
| `STRESS_50` | 50 | breit gemischt | 5 000 |

### 5.2 Realistische Nutzungsdaten

- Aufgabenverteilung folgt einer Power-Law (wenige Power-Nutzer, viele Gelegenheitsnutzer).
- Zeitstempel werden in Wochenrhythmen (Werktage vs. Wochenende) verteilt.
- Push-Reactions: 30 % öffnen, 50 % swipen weg, 20 % ignorieren.

### 5.3 Seed, Reset, Isolation

- Jeder Integrationstest startet mit `firebase emulators:exec` und einem frischen Snapshot.
- Snapshots liegen unter `test-fixtures/snapshots/<profile>.json` und werden via `firebase firestore:import` geladen.
- `TestApplication` bindet Hilt-Test-Module → keine echten Netz-/Auth-Aufrufe.
- Trennung `staging` vs. `production`:
  - separate **Firebase-Projekte** (`zunarodo-staging`, `zunarodo-prod`),
  - separate **Play-Console-Apps** für Closed Testing (Internal-App-Sharing),
  - separate Crashlytics-Streams und Analytics-Properties.

### 5.4 Sensitive Daten

- Testdaten enthalten **keine echten PII**.
- Bilder sind Lizenz-freie Avatare (`https://api.dicebear.com/...`).
- E-Mails verwenden die Domain `@tester.zunarodo.app` (eigene Catch-All-Inbox).

---

## 6. Google-Play Closed Testing

### 6.1 Anforderungen (offiziell, Stand 2026-05)

- Closed-Testing-Track in der Play Console.
- **Mindestens 12 Tester**, die dem Test aktiv beitreten (Opt-in via Link).
- **Mindestens 14 zusammenhängende Tage** ununterbrochen aktiver Test.
- Tester müssen die App **tatsächlich nutzen** (Google misst Installation und Engagement).
- App muss alle Inhaltsrichtlinien erfüllen, Data-Safety-Form ausgefüllt sein.
- Nach Abschluss: „Apply for production access“ in der Play Console.

### 6.2 Tester-Pool und Verteilung

- Eine **Google-Group** `zunarodo-closed-testers@googlegroups.com` als Tester-Liste.
- Tester treten dem Test über den **Opt-in-Link** (Closed-Testing-Track) bei.
- Builds werden über den **Internal-App-Sharing-Link** zusätzlich verteilt (für Hotfixes).

### 6.3 Übersicht der Lieferobjekte

| Objekt | Ort | Verantwortlich |
| --- | --- | --- |
| Tester-Onboarding | [G](#g-tester-onboarding-vorlage) | Test-Lead |
| Einladungstext | [G.2](#g2-einladungstext-e-mail) | Test-Lead |
| Testanleitung | [G.3](#g3-testanleitung-1-pager) | Test-Lead |
| Tägliche Testaufgaben | [F](#f-14-tage-testplan-fur--12-tester) | Test-Lead |
| Feedbackformular | [H.1](#h1-feedbackformular) | Tester |
| Fehlerbericht-Vorlage | [H.2](#h2-fehlerbericht-vorlage) | Tester |
| Testkalender 14 Tage | [F](#f-14-tage-testplan-fur--12-tester) | Test-Lead |
| Mindestnutzungsszenarien | [G.4](#g4-mindestnutzungsszenarien-pro-tester) | Tester |
| Nachweisdokumentation | [J](#j-go--no-go-kriterien-fur-play-store-veroffentlichung) | Test-Lead |
| Kriterien Produktionsreife | [J](#j-go--no-go-kriterien-fur-play-store-veroffentlichung) | Test-Lead |

### 6.4 Nachweispflicht gegenüber Google

Google verlangt bei Production-Antrag *implizit*, dass der Test echt
stattgefunden hat (Engagement-Metriken). Wir dokumentieren zusätzlich
freiwillig:

- Liste der Tester (Pseudonym + Beitrittsdatum + Engagement-Tage).
- Anzahl Sessions/Tester pro Tag (Firebase Analytics).
- Crash-Free-Users-Verlauf (Crashlytics-Export).
- Feedback-Threads (Formular-Export).
- Build-Liste (Versionscodes) und Release-Notes je Build.

Diese Dokumentation wird im Repo unter `release/closed-test-<datum>/`
versioniert.

---

## 7. 14-Tage-Testplan

Detailliert in [Anhang F](#f-14-tage-testplan-fur--12-tester). Kurzform:

| Tag | Fokus | Mind. Aktion pro Tester | Erfolgs-KPI |
| --- | --- | --- | --- |
| 1 | Installation, Registrierung, Profil, erste Aufgabe | 5 Schritte | ≥ 12 Tester onboarded |
| 2 | Mitglieder einladen, Rollen vergeben | 1 Einladung, 1 Annahme | ≥ 10 Gruppen mit ≥ 2 Mitgliedern |
| 3 | Aufgaben zuweisen | 3 Tasks, davon 1 fremd zugewiesen | ≥ 90 % Zustellung |
| 4 | Erinnerungen testen | 1 Reminder, 1 Benachrichtigung quittieren | Push-Zustellrate ≥ 95 % |
| 5 | Fristen, wiederkehrende Aufgaben | 1 wiederkehrend, 1 mit Frist | Recurrence läuft korrekt |
| 6 | Offline-Modus | 5 Aktionen offline | Sync ohne Verlust |
| 7 | Synchronisierung, App-Neustart | App killen, neu starten | Daten konsistent |
| 8 | parallele Nutzung mehrerer Mitglieder | 2 Tester editieren gleichzeitig | Konfliktbanner sichtbar |
| 9 | Konflikte, Reassign | Aufgabe neu zuweisen | Audit-Log korrekt |
| 10 | Geräte/Android-Versionen | Test auf 2. Gerät | UI ok, Sync ok |
| 11 | Dark Mode, Barrierefreiheit, TalkBack | 5 Minuten TalkBack | A11y-Score ≥ 90 |
| 12 | Fehlerberichte, Logs | Crashlytics-Ausweitung | 0 P0-Crashes übrig |
| 13 | Fix-Validierung, Regression | Re-Test der gemeldeten Bugs | 100 % der P0/P1 verifiziert |
| 14 | Abschluss-Feedback, Go-/No-Go | Tester füllt End-Survey | Go-Quote ≥ 80 % der Tester |

---

## 8. Automatisierte Kombinatorik

### 8.1 Pairwise mit PICT

Eingabedatei `tests/combinatorics/tasks.pict`:

```
Role:         OWNER, ADMIN, MEMBER, GUEST
Members:      1, 2, 5, 11, 12, 20
TaskKind:     STANDARD, CHECKLIST, APPROVAL, EVENT
Recurrence:   ONE_OFF, DAILY, WEEKLY, MONTHLY, CUSTOM
Priority:     LOW, NORMAL, HIGH, URGENT
Due:          NONE, FUTURE, TODAY, OVERDUE
Reminder:     OFF, 15M, 1H, 1D, CUSTOM
Confirm:      NONE, SELF, OWNER
Reward:       NONE, POINTS, STARS
Device:       phone_compact, phone_medium, foldable, tablet
Api:          26, 29, 31, 34, 35
Network:      ONLINE, OFFLINE, SLOW, FLAKY
Push:         ON, OFF, BLOCKED
Lifecycle:    FOREGROUND, BACKGROUND, DOZE, KILLED

# Constraints (offensichtlich unsinnige Kombinationen ausschließen)
IF [Role] = "GUEST" THEN [Confirm] <> "OWNER";
IF [Push] = "BLOCKED" THEN [Reminder] = "OFF";
IF [Recurrence] = "ONE_OFF" THEN [Due] <> "NONE";
```

Erzeugt ~ 320 Testfälle, die als parametrisierte JUnit5-Tests gegen einen
**Headless-Simulator** laufen.

### 8.2 Property-Based Testing (Kotest-property)

- **Recurrence-Engine**: Property „für jeden gültigen RRULE liefert
  `next()` Monoton-Wachsende, vom Start unabhängige Daten“.
- **Permission-Engine**: Property „kein GUEST kann jemals destruktive
  Aktion ausführen“.
- **Conflict-Resolver**: Property „bei beliebiger Edit-Reihenfolge ist das
  Endergebnis von der Reihenfolge unabhängig, wenn keine echten Konflikte
  bestehen“ (Konvergenz-Eigenschaft).

### 8.3 Risikopriorisierung

| Risiko-Cluster | 2-fach | 3-fach |
| --- | --- | --- |
| Auth × Sync × Netz | – | ✅ |
| Rolle × Aktion × Resource | – | ✅ |
| Recurrence × Zeitzone × DST | – | ✅ |
| Push × Doze × Foreground | ✅ | – |
| Bildschirm × Android-Version | ✅ | – |
| Dark Mode × Sprache | ✅ | – |

### 8.4 Grenzwerte und Äquivalenzklassen

| Eingabe | Äquivalenzklassen | Grenzwerte |
| --- | --- | --- |
| Titel-Länge | leer / 1–80 / > 80 | 0, 1, 80, 81 |
| Mitglieder pro Gruppe | 0, 1, 12, max (50) | 0, 1, 11, 12, 49, 50, 51 |
| Frist (Δ Tage) | < 0, 0, > 0 | -1, 0, 1, 365 |
| Recurrence-Schritt | 1..n | 1, 2, 100, 999 |

### 8.5 Zufallsbasierte Tests (Fuzzing)

- `runBlocking { fuzz(5_000) { simulate(randomGroup(), randomAction()) } }`
  täglich nightly auf einer separaten Test-Lab-VM, Coverage-getrackt mit
  Kover-IC.

---

## 9. CI/CD-Integration

### 9.1 Jobs und Trigger

| Job | Trigger | Inhalt | Dauer-Budget |
| --- | --- | --- | --- |
| `verify-fast` | jeder Commit auf jedem Branch | Lint, Detekt, Ktlint, Unit, Robolectric | ≤ 6 min |
| `verify-pr` | jeder PR auf `main`/`develop` | + Integration (Emulator), Compose-UI, Coverage | ≤ 20 min |
| `nightly` | täglich 02:00 UTC | + Maestro-Suite (alle 60 Flows), Pairwise-Suite, Fuzz, Lasttests | ≤ 90 min |
| `pre-release` | manuell + Tag `release/*` | + Firebase Test Lab (Robo + Instrumented), Lighthouse-/Compose-Perf | ≤ 120 min |
| `closed-test-upload` | Tag `closed/*` | pre-release + AAB-Signatur + Play-Console-Upload (Internal → Closed) | ≤ 60 min |
| `production-upload` | manuell, nach Go-Entscheidung | closed-test-upload + Promote-Track | ≤ 30 min |

### 9.2 Blockier-Regeln

Ein Build wird **blockiert**, wenn:

- Unit-/Integration-/UI-Tests fehlschlagen.
- Coverage unter Schwelle fällt (Δ < -1 % gegenüber `main`).
- Lint-Errors > 0 oder Detekt-Errors > 0.
- Firebase Test Lab kritischen Crash meldet.
- ANR/Crash-Rate der letzten 24 h (Crashlytics) > Schwelle in `pre-release`.
- Play-Pre-Launch-Report Severity-„blocker“ liefert.
- AAB-Signatur fehlt oder Versions-Code nicht inkrementiert.
- Data-Safety-Form-Hash sich ohne Review geändert hat (siehe `tools/check-datasafety.kts`).

### 9.3 GitHub-Actions-Beispiel (`.github/workflows/android.yml`)

```yaml
name: android-verify
on:
  push:
    branches: [main, develop, "release/**", "closed/**"]
  pull_request:
jobs:
  verify-fast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: 21 }
      - uses: gradle/actions/setup-gradle@v3
      - run: ./gradlew ktlintCheck detekt lint testDebugUnitTest koverXmlReport
      - uses: actions/upload-artifact@v4
        with: { name: coverage, path: "**/kover/report.xml" }

  verify-pr:
    needs: verify-fast
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    services:
      firebase:
        image: andreysenov/firebase-tools
        ports: [9099:9099, 8080:8080, 9199:9199, 5001:5001]
    steps:
      - uses: actions/checkout@v4
      - run: firebase emulators:exec --only auth,firestore,functions,storage \
                 "./gradlew connectedDebugAndroidTest pixel5_api31Group"

  nightly:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - run: ./gradlew :app:assembleDebugAndroidTest
      - run: gcloud firebase test android run \
                 --type instrumentation \
                 --app app/build/outputs/apk/debug/app-debug.apk \
                 --test app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk \
                 --device model=Pixel7,version=34 \
                 --device model=Pixel2,version=26
      - run: maestro test maestro/flows --include-tags=nightly

  pre-release:
    if: startsWith(github.ref, 'refs/tags/release/')
    runs-on: ubuntu-latest
    steps:
      - run: ./gradlew :app:bundleRelease
      - run: ./scripts/release-gate.sh
      - run: ./gradlew publishBundleToInternalTrack    # gradle-play-publisher
```

### 9.4 Pre-Release-Gate-Skript (Auszug)

```bash
#!/usr/bin/env bash
set -euo pipefail
./gradlew connectedReleaseAndroidTest
./gradlew kover-verify  # bricht ab, wenn Schwellen unterschritten
maestro test maestro/flows --include-tags=release-gate
./tools/check-datasafety.kts
./tools/check-anr-budget.kts
./tools/check-crashfree.kts --threshold 99.5
```

---

## 10. Ergebnisformat A–K

### A. Vollständiges Testkonzept (Übersicht)

Dieses Dokument **ist** das Testkonzept. Im Repo gepflegt als
`TESTING.md` mit verlinkten Anhängen unter `tests/concept/` (Markdown +
PICT-Inputs). Versionierung über Git; Änderungen am Konzept laufen über
PR-Review (mind. ein Reviewer aus QA, ein Reviewer aus Engineering).

Kapitel-Mapping:

| Kapitel | Inhalt | Verantwortlich |
| --- | --- | --- |
| 1 Testziel | Was, warum, wie gemessen | QA-Lead |
| 2 Mitglieder-Szenarien | Gruppengrößen, Rollen | Engineering + QA |
| 3 Aufgaben/Funktions-Kombinatorik | Dimensionen, Reduktion | QA |
| 4 Teststrategie | Pyramide, Tools, Layer | Engineering |
| 5 Testdaten | Fixtures, Seeds, Isolation | Engineering |
| 6 Closed Testing | Play-Anforderung, Pool | Test-Lead |
| 7 14-Tage-Plan | Tester-Tagesplan | Test-Lead |
| 8 Auto-Kombinatorik | Pairwise, Property, Fuzz | QA |
| 9 CI/CD | Jobs, Gates | DevOps |
| 10/A–K | Anhänge | je nach Anhang |

### B. Automatisierte Testarchitektur

#### B.1 Modul-Layout

```
app/                       # Android-App (UI)
core-domain/               # Pure Kotlin, Use-Cases, Models, Rules
core-data/                 # Repos, Room, Firebase-Adapter
core-ui/                   # gemeinsame Compose-Komponenten
feature-tasks/             # Tasks-Feature
feature-groups/            # Gruppen & Rollen
feature-notifications/     # FCM + Reminders
test-fixtures/             # Seed-Daten, Faker, Profile
test-rules/                # JUnit-Rules (Hilt, Coroutine, Firebase)
maestro/                   # E2E-Flows (yaml)
tests/concept/             # PICT-Files, Generators, Reports
tools/                     # Release-Gate-Skripte
```

#### B.2 Test-Module-Dependencies (Auszug `app/build.gradle.kts`)

```kotlin
dependencies {
    // Pyramide
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
    testImplementation("io.mockk:mockk:1.13.10")
    testImplementation("io.kotest:kotest-runner-junit5:5.8.0")
    testImplementation("io.kotest:kotest-property:5.8.0")
    testImplementation("app.cash.turbine:turbine:1.0.0")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.0")
    testImplementation("org.robolectric:robolectric:4.12")

    androidTestImplementation("androidx.compose.ui:ui-test-junit4:1.6.7")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation("com.google.dagger:hilt-android-testing:2.51")
    androidTestImplementation("com.google.firebase:firebase-firestore-ktx") // mit Emulator
}
```

#### B.3 Berechtigungs-Engine als Testobjekt

```kotlin
data class Permission(val role: Role, val action: Action, val target: Target)

class PermissionEngine {
    fun isAllowed(p: Permission): Boolean = when (p.role) {
        OWNER -> true
        ADMIN -> p.action !in setOf(Action.DELETE_GROUP, Action.TRANSFER_OWNERSHIP)
        MEMBER -> p.action in MEMBER_ALLOWED
        GUEST  -> p.action in GUEST_ALLOWED
    }
}
```

Parametrisierter Test deckt **Rolle × Action × Target** zu 100 % ab.

#### B.4 Test-Runner-Konfiguration

- `useJUnitPlatform()` aktiviert in Gradle.
- `@HiltAndroidTest` für Android-Tests; Test-Module ersetzen Firebase-
  Bindings durch Emulator-Bindings.
- `TestApplication` registriert in Manifest-Stub unter
  `app/src/androidTest/AndroidManifest.xml`.

### C. Kombinatorische Testmatrix

Vollständiger Generator (Auszug, Pseudo-Format der PICT-Ausgabe):

| # | Role | Members | TaskKind | Recur | Prio | Due | Remind | Confirm | Reward | Device | API | Net | Push | Life |
| -- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | OWNER | 1 | STANDARD | ONE_OFF | NORMAL | TODAY | OFF | NONE | NONE | phone_medium | 34 | ONLINE | ON | FG |
| 2 | OWNER | 12 | CHECKLIST | WEEKLY | HIGH | FUTURE | 1H | SELF | POINTS | foldable | 31 | OFFLINE | ON | BG |
| 3 | ADMIN | 5 | APPROVAL | MONTHLY | URGENT | OVERDUE | 1D | OWNER | STARS | tablet | 35 | FLAKY | OFF | DOZE |
| 4 | MEMBER | 2 | EVENT | CUSTOM | LOW | NONE | OFF | NONE | NONE | phone_compact | 26 | SLOW | BLOCKED | KILLED |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 320 | GUEST | 20 | STANDARD | DAILY | NORMAL | TODAY | 15M | NONE | NONE | phone_medium | 34 | ONLINE | ON | FG |

Die Datei `tests/concept/pict/tasks.pict` ist die normative Quelle. Der
Generator-Befehl im Repo:

```bash
pict tests/concept/pict/tasks.pict /o:3 > tests/concept/pict/matrix-3wise.tsv
```

Eine JUnit5-`@ParameterizedTest` liest die TSV und führt die Fälle gegen
einen Headless-Simulator und gegen den Emulator-Stack aus.

### D. Rollen- und Mitglieder-Testfälle

#### D.1 Berechtigungsmatrix (Soll)

| Aktion | OWNER | ADMIN | MEMBER | GUEST |
| --- | --- | --- | --- | --- |
| Gruppe erstellen | ✅ | – | – | – |
| Gruppe löschen | ✅ | – | – | – |
| Eigentum übertragen | ✅ | – | – | – |
| Mitglied einladen | ✅ | ✅ | – | – |
| Mitglied entfernen | ✅ | ✅ | – | – |
| Rolle ändern | ✅ | ✅ (nicht OWNER) | – | – |
| Aufgabe erstellen | ✅ | ✅ | ✅ | – |
| Aufgabe zuweisen | ✅ | ✅ | ✅ (sich selbst) | – |
| Aufgabe schließen | ✅ | ✅ | ✅ (eigene/zugewiesene) | – |
| Aufgabe sehen | ✅ | ✅ | ✅ | ✅ (markiert „public“) |
| Kommentar | ✅ | ✅ | ✅ | ✅ |
| Push-Settings ändern | ✅ (für sich) | ✅ (für sich) | ✅ (für sich) | ✅ (für sich) |
| Daten exportieren | ✅ | ✅ | – | – |

#### D.2 Testfall-Beispiele

| ID | Vorbedingung | Aktion | Erwartung |
| --- | --- | --- | --- |
| TC-R-001 | M-03, ADMIN aktiv | ADMIN versucht OWNER-Rolle einem anderen zu geben | abgelehnt mit `ERR_FORBIDDEN_TRANSFER` |
| TC-R-014 | M-05, INVITED | INVITED öffnet App | Onboarding zur Annahme der Einladung |
| TC-R-022 | M-06, REMOVED | REMOVED öffnet Deep-Link | Hinweis „Zugriff entzogen“ + Re-Invite möglich |
| TC-R-031 | M-04, GUEST | GUEST versucht Task zu löschen | UI-Button ausgegraut + Server-side verweigert |
| TC-R-040 | M-02 | OWNER 1 löscht eigenes Konto | Gruppe übergeht an ADMIN oder wird archiviert |
| TC-R-051 | M-07, 60 % aktiv | OWNER sieht Mitgliederliste | Active/Inactive/Invited sortiert nach Status |
| TC-R-060 | M-09 | REMOVED wird re-invited | alte Aufgabenzuweisungen bleiben anonymisiert |

(Vollständige Liste: 80 TCs unter `tests/concept/cases/roles.csv`.)

### E. Aufgaben- und Funktions-Testfälle

#### E.1 Funktions-Slices

Jede Funktion hat **vier Slice-Typen**:

1. **Happy Path** (UI + Domain + Sync)
2. **Edge** (Grenzwerte, Sonderzeichen, große Mengen)
3. **Error** (Netz weg, Server 500, Rechte fehlen)
4. **Offline-Recovery** (Aktion offline, Sync später)

#### E.2 Auswahl wichtiger Testfälle

| ID | Funktion | Slice | Vorbedingung | Schritte | Erwartung |
| --- | --- | --- | --- | --- | --- |
| TC-F-101 | Aufgabe erstellen | Happy | M-03, MEMBER | „Neue Aufgabe“ → Titel → Speichern | Aufgabe sichtbar in < 1 s; Push an Assignee |
| TC-F-102 | Aufgabe erstellen | Edge | Titel = 80 Zeichen + Emoji | Speichern | gespeichert; korrekt gerendert |
| TC-F-103 | Aufgabe erstellen | Error | Offline + Konflikt | Speichern offline, Edit auf 2. Gerät | Konfliktbanner; LWW; History-Eintrag |
| TC-F-110 | Wiederkehrende Aufgabe | Happy | weekly Mo+Mi | 4 Wochen vorspulen (Testtaktung) | 8 Instanzen erzeugt |
| TC-F-111 | Wiederkehrende Aufgabe | DST | März-DST | Recurrence läuft über DST-Wechsel | keine Doppel-/Ausfall-Instanz |
| TC-F-120 | Frist + Erinnerung | Happy | Reminder 1 h vor Frist | Frist auf t+1h | Push exakt zur Erinnerungs­zeit |
| TC-F-121 | Frist | Edge | Frist gleich Now | – | sofort „überfällig“ markiert |
| TC-F-130 | Bestätigung | OWNER_CONFIRM | MEMBER schließt | – | Status „warten auf OWNER“; Owner bekommt Push |
| TC-F-140 | Belohnung Sterne | Happy | nach Abschluss bewerten | 1–5 Sterne | gespeichert + Verlauf |
| TC-F-150 | Parallel | Happy | 2 Tester ändern Status | – | finaler Status gewinnt LWW; beide sehen identisch |
| TC-F-160 | Reassign | Happy | MEMBER → ADMIN | – | alte Push entfernt, neue Push gesendet |
| TC-F-170 | Abbrechen | Happy | OWNER bricht ab | – | Status `CANCELED`, kein Reminder mehr |
| TC-F-180 | Überfällig | Happy | Frist überschritten | – | Banner rot; tägliche Erinnerung optional |
| TC-F-190 | Push deaktiviert OS | – | Push BLOCKED | Reminder fällig | App-interner Hinweis statt Push; kein Crash |
| TC-F-200 | App Cold Start nach Process Death | – | Process killed nach Edit | App neu öffnen | letzte Aktion sichtbar + sync |

(Vollständig: 220 TCs unter `tests/concept/cases/tasks.csv`.)

### F. 14-Tage-Testplan für ≥ 12 Tester

Allgemeine Regeln:

- Jeder Tester legt einen **Account auf einem realen Gerät** an.
- Tagesaktionen dauern realistisch 5–15 Minuten.
- Jede Aktion ist im Feedbackformular zu quittieren (Bullet: erledigt /
  Problem / Frage).

#### Tag 1 — Onboarding

- App über Closed-Testing-Link installieren.
- Konto erstellen (E-Mail oder Google-SSO).
- Profil ausfüllen (Name, Avatar).
- Erste Aufgabe „Testkalender öffnen“ erstellen.
- Push-Berechtigung erteilen.
- KPIs: Crash-Free 100 %, Onboarding < 3 min.

#### Tag 2

- Eine andere Testperson per E-Mail einladen.
- Eingehende Einladung annehmen.
- Rolle ADMIN an eine Person vergeben.
- KPIs: Einladung-Zustellung ≥ 95 %.

#### Tag 3

- Drei Aufgaben erstellen (eigene + 2 zugewiesen).
- Eine Aufgabe an ADMIN-Tester zuweisen.
- Eine Aufgabe schließen.

#### Tag 4

- Eine Aufgabe mit Erinnerung 15 min anlegen.
- Push aktiv quittieren.
- Eine Aufgabe mit Frist `+1d` erstellen.

#### Tag 5

- Eine wiederkehrende Aufgabe (täglich) anlegen.
- Über 2 Tage beobachten, ob Instanzen erscheinen (Tag 5+6).
- Eine Aufgabe stornieren.

#### Tag 6

- App auf Flugmodus stellen.
- 5 Aktionen (Erstellen, Schließen, Kommentieren) offline ausführen.
- Flugmodus ausschalten.
- KPI: keine verlorenen Aktionen.

#### Tag 7

- App in den Hintergrund schieben.
- Gerät neu starten.
- App öffnen → Daten konsistent?
- Manueller Sync („Pull-to-Refresh“).

#### Tag 8

- Zu zweit gleichzeitig dieselbe Aufgabe editieren (Titel/Notiz).
- Beobachten: Konfliktbanner, finaler Zustand identisch.

#### Tag 9

- Aufgabe neu zuweisen.
- Aufgabe abbrechen.
- Aufgabe überfällig werden lassen (Frist gestern).

#### Tag 10

- Wenn möglich: App auf zweitem Gerät installieren (Tablet/anderes Handy).
- Anmelden, Daten prüfen.
- Eine Aktion auf Gerät A, eine auf Gerät B, abgleichen.

#### Tag 11

- Dark Mode aktivieren.
- TalkBack (Android-Screenreader) für 5 Minuten testen.
- Schriftgröße auf „Sehr groß“ stellen.
- Notiert: Lesbarkeit, Tap-Targets.

#### Tag 12

- Letzte aufgetretene Probleme melden (Formular [H.2](#h2-fehlerbericht-vorlage)).
- Crashes auflisten (Crashlytics-Stream wird zusammengeführt).
- KPI: keine ungeklärten P0-Crashes.

#### Tag 13

- Fixes wurden im Testtrack als neue Version verteilt.
- Tester verifizieren ihre vorher gemeldeten Bugs.
- Re-Test der relevanten Flows.

#### Tag 14

- Abschluss-Survey (Feedbackformular).
- Go-/No-Go-Stimme pro Tester.
- Test-Lead aggregiert Engagement, Crashes, Feedback → Entscheidung.

### G. Tester-Onboarding-Vorlage

#### G.1 Tester-Steckbrief (vor Annahme)

```
Name / Pseudonym:
Gerät (Modell + Android-Version):
Bildschirmgröße:
Sprache:
Verfügbarkeit nächste 14 Tage:
Vorerfahrung mit Beta-Tests:
Bereit, 15 min/Tag aktiv zu nutzen?  [ ja / nein ]
```

#### G.2 Einladungstext (E-Mail)

```
Betreff: Du bist eingeladen: Closed-Beta für „Zunarodo“ (14 Tage)

Hallo {Name},

du bist eingeladen, an unserem geschlossenen Test für die Android-App
„Zunarodo“ teilzunehmen. Der Test dauert 14 Tage (vom {start} bis {end}).
Wir suchen mindestens 12 Personen, die die App täglich kurz nutzen, um
Stabilität und Bedienbarkeit nachzuweisen — eine Pflichtanforderung von
Google Play.

So machst du mit:

1. Tritt unserer Google-Gruppe bei: {google-group-url}
2. Öffne den Opt-in-Link am Smartphone: {play-optin-url}
3. Installiere die App über den Play-Store (Test-Track sichtbar nach
   Annahme).
4. Folge dem Tagesplan aus diesem Dokument: {testplan-url}
5. Probleme/Feedback bitte ins Formular: {feedback-url}

Dein Einsatz: ca. 5–15 Minuten pro Tag.
Vergütung: {…} (oder „keine, Dank in den Credits“).
Datenschutz: keine personenbezogenen Daten Dritter, Testdaten werden nach
Abschluss gelöscht (außer aggregierte Statistiken).

Bei Fragen: {kontakt-email}.

Danke!
{Test-Lead}
```

#### G.3 Testanleitung (1-Pager)

```
1.  Installation: Folge dem Opt-in-Link, dann Play Store. Akzeptiere
    Push-Berechtigung.
2.  Pseudonym: Bitte realistisch, aber keine echten Klarnamen Dritter
    eintragen.
3.  Tagesplan: siehe 14-Tage-Plan. Lege dir eine Erinnerung um die
    gleiche Tageszeit.
4.  Feedback: Nach jeder Sitzung kurz ins Formular.
5.  Bug melden: Sofort melden, wenn etwas abstürzt, hängt oder unklar
    ist. Screenshot reicht.
6.  Datenschutz: Keine echten Daten Dritter eintragen (Namen, Adressen,
    Konten). Verwende erfundene Test-Daten.
7.  Notfall: Wenn die App gar nicht startet, schreib uns sofort —
    Hotfix-Build via Internal-App-Sharing möglich.
```

#### G.4 Mindestnutzungsszenarien pro Tester

Jeder Tester muss in den 14 Tagen mindestens:

- 1 Gruppe erstellen oder beitreten,
- 5 Aufgaben erstellen,
- 3 Aufgaben abschließen,
- 1 wiederkehrende Aufgabe anlegen,
- 1 Aufgabe zuweisen oder zugewiesen bekommen,
- 1 Push-Benachrichtigung erhalten und quittieren,
- 1 Offline-Aktion durchführen,
- die App mindestens an 10 von 14 Tagen öffnen.

### H. Feedback- und Fehlerberichts-Vorlagen

#### H.1 Feedbackformular

Tägliches Kurzformular (Google Forms / Tally / eigener Endpoint):

```
Tester-Pseudonym:
Tag (1–14):
Aktionen heute: [Mehrfachauswahl]
   ☐ Onboarding   ☐ Aufgabe erstellt   ☐ Mitglied eingeladen
   ☐ Rolle vergeben   ☐ Aufgabe abgeschlossen   ☐ Push erhalten
   ☐ Offline-Aktion   ☐ Sync ausgelöst   ☐ Konflikt erlebt
Dauer der Nutzung heute (min):
Probleme aufgetreten?  [ja / nein]
Falls ja, kurzbeschreibung:
Subjektives Urteil heute (1–5 Sterne):
Anmerkung:
```

#### H.2 Fehlerbericht-Vorlage

```
Titel: <kurz, sprechend>
Datum/Zeit:
App-Version (vom „Über“-Screen): z. B. 1.0.0 (build 1234)
Gerät / Android-Version:
Reproduktionsschritte:
   1.
   2.
   3.
Erwartet:
Tatsächlich:
Schweregrad: [P0 Crash | P1 Funktion blockiert | P2 Störend | P3 Kosmetik]
Screenshots / Bildschirmaufnahme: [Anhang]
Logs (falls aktiviert): [Anhang]
Tritt reproduzierbar auf? [immer / oft / selten / einmal]
Workaround gefunden?
```

#### H.3 Crash-Triage

| Stufe | Definition | Maßnahme |
| --- | --- | --- |
| P0 | App stürzt sofort beim Start oder bricht zentrale Funktion ab | Hotfix-Build innerhalb 24 h |
| P1 | wichtige Funktion blockiert für ≥ 10 % der Nutzer | Fix im nächsten Closed-Build |
| P2 | störend, Workaround vorhanden | Fix vor Production |
| P3 | kosmetisch | optional, ggf. Backlog |

### I. CI/CD-Testpipeline

(Detail siehe [Abschnitt 9](#9-cicd-integration).)

Diagramm:

```
   Commit ──► verify-fast (Lint/Detekt/Ktlint/Unit/Robolectric)
                 │
                 ▼
   PR ─────────► verify-pr (+ Integration/Compose-UI/Coverage)
                 │
                 ▼
   merge to develop ─► nightly (Maestro, Pairwise, Fuzz, Lasttests)
                 │
                 ▼
   tag release/* ─► pre-release (Test Lab Robo+Instrumented, Perf, Gate)
                 │
                 ▼
   tag closed/* ──► closed-test-upload (gradle-play-publisher → Closed)
                 │
                 ▼
   manuell ──────► production-upload (Promote-Track)
```

Blockier-Logik liegt in `scripts/release-gate.sh`; jeder Schritt schreibt
JSON-Reports nach `build/reports/release-gate/<timestamp>/`, die als
GitHub-Artefakt 90 Tage gespeichert werden.

### J. Go-/No-Go-Kriterien für Play-Store-Veröffentlichung

Eine Veröffentlichung in Production ist **freigegeben (Go)**, wenn **alle**
folgenden Kriterien erfüllt sind. Andernfalls: **No-Go**.

| Kriterium | Schwelle | Quelle |
| --- | --- | --- |
| Crash-Free-Users (7 Tage Closed) | ≥ 99,5 % | Crashlytics |
| ANR-Rate | < 0,47 % | Play Console / Crashlytics |
| Closed-Test-Dauer | ≥ 14 zusammenhängende Tage | Play Console |
| Tester-Mindestzahl | ≥ 12 aktiv beigetreten | Play Console |
| Tester-Engagement | ≥ 70 % der Tester ≥ 10 Tage aktiv | Analytics |
| Pre-Launch Report | 0 „blocker“ / „high“ ungelöst | Play Console |
| Manuelle Akzeptanz | 100 % der P0/P1-Bugs verifiziert geschlossen | Tracking-System |
| Automatisierte Tests | alle CI-Jobs grün auf Release-Tag | CI |
| Coverage | Domain ≥ 80 %, Data ≥ 70 %, UI ≥ 50 % | Kover |
| Berechtigungs­matrix | 0 Abweichungen | Test-Report |
| Data-Safety-Form | aktuell + Hash unverändert oder reviewt | Repo + Play Console |
| Datenschutzerklärung | online, Link in Play-Listing | externer Host |
| Inhaltsrichtlinien | Self-Assessment durchlaufen | Play Console |
| Tester-Feedback | ≥ 80 % „Go“-Stimmen im Abschluss-Survey | Formular |
| Lokalisierung | Deutsch + Englisch vollständig, keine Platzhalter | i18n-Lint |
| Versions-Code | inkrementiert, signiert | Gradle |
| ProGuard/R8 | keine ungewollten Drops; Mapping in Play hochgeladen | Build |
| App-Bundle-Größe | < 150 MB (Base-APK < 75 MB) | Build |

Ein Verstoß gegen **eine** Spalte → **No-Go**, Maßnahmenplan greift ([K](#k-massnahmenplan-bei-fehlern-oder-google-ablehnung)).

### K. Maßnahmenplan bei Fehlern oder Google-Ablehnung

#### K.1 Während des Closed Tests

| Symptom | Sofort-Aktion | Folge-Aktion |
| --- | --- | --- |
| P0-Crash bei ≥ 1 Tester | Build sperren, Crashlytics-Issue P0 | Hotfix in 24 h, neuer Closed-Build, 14-Tage-Zähler läuft *nicht* zurück, aber Engagement wird neu gewichtet |
| Engagement < Schwelle | Re-Engagement-Mail Tag 7 + 10 | ggf. Tester-Pool erweitern auf 15–18 |
| Tester-Ausfall (< 12 aktiv) | nachrekrutieren binnen 72 h | sicherstellen, dass die letzten 14 Tage ununterbrochen 12 Tester aktiv waren |
| Sync-Verlust gemeldet | Property-Test reproduzieren | Fix + Regressionstest; History-Audit |
| Push nicht zugestellt | FCM-Konfiguration prüfen, Topic-Subscription | Re-Test mit „Send to single device“ |

#### K.2 Bei Google-Ablehnung

Google teilt Ablehnungsgründe in der Play Console mit. Häufige Kategorien
und Antworten:

| Ablehnungsgrund | Maßnahme |
| --- | --- |
| Nutzerdaten-Richtlinie / Data Safety inkonsistent | Data-Safety-Form mit tatsächlichen Datentypen abgleichen (Firebase Auth, Firestore-Felder, Crashlytics, Analytics), Datenschutzerklärung anpassen, erneut einreichen |
| Hinweis auf irreführende Funktionsbeschreibung | Store-Listing kürzen/präzisieren; Screenshots aktualisieren |
| Berechtigungs-Übersteuerung (z. B. unnötig SMS) | Permissions aus Manifest entfernen, R8 prüft auf unused |
| Crash-Quote zu hoch (Pre-Launch / Vitals) | crashs aus Vitals exportieren, P0/P1 fixen, neuen Closed-Build verteilen, ≥ 7 Tage warten |
| Closed-Test-Anforderungen nicht erfüllt | Nachweis-Dokumentation ergänzen (Engagement-Liste, Build-Log, Tester-Statements), Production-Antrag wiederholen |
| Background-Location o. ä. ohne klaren Use-Case | Feature entfernen oder klaren Begründungstext + Demo-Video einreichen |
| Inhalts-Rating falsch | erneutes Rating-Assessment, ggf. ältere Altersfreigabe |

#### K.3 Rollback-Strategie

- **Sofort-Rollback**: Halten des Production-Releases (Staged Rollout 1 %
  als Default; bei Crash-Spike Halt auf 0 %).
- **Stop Rollout** + neuer Production-Track mit Hotfix; ProGuard-Mapping
  mitliefern.
- Nutzer-Kommunikation: In-App-Banner (Remote Config Flag
  `rollback_notice`).

#### K.4 Nach Veröffentlichung

- **Tägliche Vitals-Überwachung** (Crashlytics-Slack-Webhook).
- **Wöchentliche Regressions-Suite** (Maestro) gegen Production-Build.
- **Monatliches Test-Konzept-Review** (dieses Dokument).
- Schwellen werden quartalsweise an Google-Vorgaben angepasst.

---

## Anhang: Verzeichnisstruktur Tests im Repo

```
tests/
  concept/
    pict/                    # PICT-Inputs für Pairwise/3-wise
    cases/                   # CSVs mit TC-IDs (R-, F-, M-)
    scenarios/               # Maestro-Yamls (referenziert von maestro/)
    reports/                 # generierte Reports (CI lädt sie hoch)
  property/                  # Kotest-property-Tests
  fixtures/                  # Faker, Seeds
  performance/               # k6, Benchmark-Suites
maestro/
  flows/                     # E2E
release/
  closed-test-<datum>/       # Nachweis für Google
```

---

## Glossar

- **Closed Testing** — Track in der Play Console, sichtbar nur für
  eingeladene Tester; Pflichtphase für neue persönliche Developer-Accounts.
- **Pairwise / 2-wise Coverage** — Testfall-Auswahl, in der jedes
  Wertepaar zweier Dimensionen mindestens einmal vorkommt.
- **Robo-Test** — automatisierter explorativer Test von Firebase Test
  Lab, der die UI crawlt.
- **Maestro Flow** — deklaratives Yaml-Skript für End-to-End-Mobile-Tests.
- **App Check** — Firebase-Mechanismus, der Backend-Aufrufe nur von der
  echten App akzeptiert (gegen Bot-Traffic).
- **ANR** — Application Not Responding; Android-Schwelle 5 s
  Main-Thread-Blockade.

---

*Eigentümer dieses Dokuments: QA-Lead. Letzte Review: 2026-05-20.
Nächste Pflicht-Review: vor jedem Production-Release.*

---

# Teil II — Negativ-, Datenschutz- und Compliance-Konzept

Erweitert Teil I (Stack-Konzept) um harte Negativ-, Datenschutz-,
Sicherheits- und Play-Compliance-Anforderungen. Ziel: **vor** dem
Upload in die Play Console werden technische, datenschutzrechtliche
und richtlinienseitige Verstöße automatisiert erkannt und blockiert.

## Inhalt Teil II

11. [Negativtests](#11-negativtests)
12. [Datenschutztests](#12-datenschutztests)
13. [Nachweisdokumentation für Google Play](#13-nachweisdokumentation-fur-google-play)
14. [Go-/No-Go-Kriterien (Erweiterung)](#14-go--no-go-kriterien-erweiterung)
15. [CI/CD-Integration (Erweiterung)](#15-cicd-integration-erweiterung)
16. [Ergebnisformat A–L](#16-ergebnisformat-al)

---

## 11. Negativtests

Negativtests sind verpflichtend. Eine grüne Negativtest-Suite ist
Voraussetzung für jeden Closed-Test- oder Production-Build.

### 11.1 Kritikalitätsstufen

| Stufe | Bedeutung | Beispiel | Build-Wirkung |
| --- | --- | --- | --- |
| **C0 Blocker** | App startet nicht, Daten gehen verloren, Sicherheitslücke | SQL-Injection im Login | sofortiger Stop, kein Upload |
| **C1 Critical** | Kernfunktion bricht ohne Recovery | Sync löscht lokale Änderungen | Stop, Hotfix Pflicht |
| **C2 Major** | Funktion bricht, Workaround existiert | Falsche Fehlermeldung bei 401 | Fix vor Release |
| **C3 Minor** | UX-Aussetzer, kein Datenverlust | Toast-Text vertauscht | Backlog, optional vor Release |
| **C4 Cosmetic** | Optik | Padding falsch | Backlog |

### 11.2 Risikomatrix (Eintritts­wahrscheinlichkeit × Schaden)

| Wahrscheinlichkeit \ Schaden | gering | mittel | hoch | kritisch |
| --- | --- | --- | --- | --- |
| selten | C4 | C3 | C2 | C1 |
| möglich | C3 | C2 | C1 | C0 |
| häufig | C2 | C1 | C0 | C0 |
| sicher | C1 | C0 | C0 | C0 |

C0 + C1 sind automatisch **No-Go**. C2 ist No-Go ohne dokumentierte
Mitigation. C3/C4 sind dokumentationspflichtig.

### 11.3 Negativtest-Matrix

#### A. Benutzerbezogene Negativtests

| ID | Eingabe / Situation | Erwartetes Verhalten | Krit. |
| --- | --- | --- | --- |
| N-A-01 | Registrierung mit ungültiger E-Mail | UI-Fehler, kein Auth-Call | C1 |
| N-A-02 | Eingabe > 10 000 Zeichen | gestutzt oder Fehler, kein Crash | C1 |
| N-A-03 | Sonderzeichen (Emoji, Steuerzeichen, NUL) | gespeichert oder verworfen, kein Crash | C1 |
| N-A-04 | SQL-Injection in Namensfeld | gespeichert literal, keine SQL-Ausführung | C0 |
| N-A-05 | Doppelter Account (gleiche E-Mail) | Auth-Server blockt, UI-Fehler | C1 |
| N-A-06 | Gesperrter Nutzer logged sich ein | UI-Fehler „Konto gesperrt“ | C1 |
| N-A-07 | Gelöschter Nutzer öffnet Deep-Link | Hinweis + Onboarding für Re-Invite | C1 |
| N-A-08 | Abgelaufene Session | automatischer Logout, sanfter Re-Auth | C1 |
| N-A-09 | Paralleler Login (2 Geräte) | beide aktiv, Konflikte über LWW | C1 |
| N-A-10 | Manipulierte Rolle (Client setzt OWNER) | Server lehnt ab, UI-Fehler | C0 |
| N-A-11 | Unvollständiges Profil | Onboarding blockt Funktion bis Pflichtfeld | C2 |

#### B. Netzwerk- und Synchronisationsfehler

| ID | Situation | Erwartetes Verhalten | Krit. |
| --- | --- | --- | --- |
| N-B-01 | kein Internet | Banner, Offline-Modus | C1 |
| N-B-02 | instabile Verbindung | Retry mit Backoff | C2 |
| N-B-03 | sehr langsame Verbindung (2 G) | Spinner, Timeout > 30 s | C2 |
| N-B-04 | Server Timeout 504 | Klare Fehlermeldung | C2 |
| N-B-05 | Verbindungsabbruch mitten in PUT | Retry oder lokale Queue | C1 |
| N-B-06 | Offline-Edit → Online-Sync | Konflikt-Resolution wendet LWW | C1 |
| N-B-07 | Paralleles Edit auf 2 Geräten | Konflikt-Banner, Audit-Eintrag | C1 |

#### C. Gerätebezogene Fehler

| ID | Situation | Erwartetes Verhalten | Krit. |
| --- | --- | --- | --- |
| N-C-01 | Speicher voll | Speichern liefert UI-Fehler, kein Crash | C1 |
| N-C-02 | Akku-Sparmodus | Sync läuft im erlaubten Fenster | C2 |
| N-C-03 | App im Hintergrund OOM-killed | Process-Death-Restore, ViewModel-State | C1 |
| N-C-04 | Crash mitten im Schreiben | DB konsistent (Transaktion) | C0 |
| N-C-05 | Geräte-Neustart | App startet sauber | C1 |
| N-C-06 | Android 10–16 | UI funktioniert, keine ANR | C1 |
| N-C-07 | Bildschirmgrößen compact–expanded | Layout responsive | C2 |
| N-C-08 | Rotation während Aktion | State erhalten | C2 |
| N-C-09 | Dark Mode | Kontraste WCAG AA | C2 |
| N-C-10 | Sprache RTL / lange Strings | UI bricht nicht | C2 |

#### D. Sicherheits- und Manipulationstests

| ID | Situation | Erwartetes Verhalten | Krit. |
| --- | --- | --- | --- |
| N-D-01 | Root-Gerät | Hinweis, App Check verweigert sensible Aktionen | C1 |
| N-D-02 | Emulator | App Check verweigert oder loggt | C1 |
| N-D-03 | Debugger angehängt | Sensitive Aktionen sperren | C1 |
| N-D-04 | Modifizierte APK / fehlende Signatur | Integritätsprüfung schlägt fehl | C0 |
| N-D-05 | Frida/Hooking | App Check / Play Integrity verweigert | C1 |
| N-D-06 | unsicherer Deep-Link (Daten in URL) | Validierung, kein blindes Vertrauen | C0 |
| N-D-07 | exported Activity ohne Schutz | nicht vorhanden / explizit dokumentiert | C0 |
| N-D-08 | implicit Intent mit Daten | nur expliziter Intent für sensible Daten | C1 |
| N-D-09 | Klartext-Traffic (`http://`) | network-security-config blockt | C0 |
| N-D-10 | WebView ohne `setJavaScriptEnabled=false` | nur explizit erlaubt + URL-Whitelist | C1 |

#### E. API- und Backend-Negativtests

| ID | Situation | Erwartetes Verhalten | Krit. |
| --- | --- | --- | --- |
| N-E-01 | ungültiger Token | 401 → Re-Auth-Flow | C1 |
| N-E-02 | abgelaufener Token | Refresh, sonst Logout | C1 |
| N-E-03 | fehlende Authentifizierung | Rules verweigern | C0 |
| N-E-04 | manipulierter Request-Body | Server-side-Validierung | C0 |
| N-E-05 | fehlende Datenfelder | Default oder Fehler, kein Crash | C1 |
| N-E-06 | unerwartete Server-Antwort (HTML statt JSON) | sauber abgefangen | C1 |
| N-E-07 | DB-Fehler / Constraint-Violation | Retry oder UI-Fehler | C1 |
| N-E-08 | Rate-Limit 429 | Backoff, kein Loop | C1 |
| N-E-09 | fehlerhafte Push (FCM-Payload korrupt) | Crash-frei, optional Log | C1 |

### 11.4 Automatisierung in CI

Alle N-IDs sind im Repo unter `tests/concept/test_negative_*.py` als
parametrisierte Tests umgesetzt. Pro PR muss die Negativ-Suite grün
sein. Nightly läuft zusätzlich Fuzzing (Property-Tests + zufalls­basiert)
über Eingabefelder.

---

## 12. Datenschutztests

### 12.1 Grundprinzipien

- **DSGVO-Konformität**: Art. 6 Rechtsgrundlage je Verarbeitung,
  Art. 13/14 Informationspflichten, Art. 15–22 Betroffenenrechte.
- **Datensparsamkeit**: nur was nachweislich nötig ist.
- **Privacy by Design**: lokal-first, Verschlüsselung, kein Tracking
  ohne aktive Einwilligung.
- **Transparenz**: Datenschutzerklärung + In-App-Hinweise.

### 12.2 Datenerhebungs-Inventar

| Datenkategorie | Zweck | Rechtsgrundlage | Empfänger | Aufbewahrung |
| --- | --- | --- | --- | --- |
| E-Mail (Konto) | Login, Pwd-Reset | Vertrag (Art. 6 I b) | App-Backend | bis Kontolöschung |
| Profilname | Anzeige in Gruppen | Vertrag | App-Backend, Gruppe | bis Kontolöschung |
| Aufgaben, Notizen, Termine | Kernfunktion | Vertrag | App-Backend, Gruppe | bis Löschung durch Nutzer |
| Crashlytics-Reports | Stabilität | Berechtigtes Interesse (Art. 6 I f) | Google | 90 Tage |
| Analytics (anonymisiert) | Produktverbesserung | Einwilligung (Art. 6 I a) | Google | 14 Monate |
| Push-Token (FCM) | Benachrichtigung | Vertrag | Google FCM | bis Logout / Token-Refresh |
| App-Logs (lokal) | Debug, Support | Berechtigtes Interesse | nur lokal | rotierend 7 Tage |
| App-Check-Token | Anti-Bot | Berechtigtes Interesse | Google | Session |

### 12.3 Datenschutz-Testmatrix

#### A. Datenerhebung

| ID | Prüfung | Methode | Krit. |
| --- | --- | --- | --- |
| P-A-01 | Liste der erhobenen Datentypen identisch zu Data-Safety-Form | manueller Abgleich + CI-Hash | C0 |
| P-A-02 | Keine Tracking-IDs ohne Opt-in | statische Code-Analyse + Init-Reihenfolge-Test | C0 |
| P-A-03 | Analytics nur nach `consent=granted` | Espresso/Compose-Test | C1 |
| P-A-04 | Drittanbieter-SDKs in `docs/sdk-inventory.md` aufgeführt | CI-Diff | C1 |

#### B. Nutzerrechte

| ID | Prüfung | Methode | Krit. |
| --- | --- | --- | --- |
| P-B-01 | „Konto löschen“ in Settings sichtbar (Play-Pflicht) | Compose-UI-Test | C0 |
| P-B-02 | Kontolöschung entfernt serverseitige + lokale Daten | Integrationstest | C0 |
| P-B-03 | Datenexport liefert valides JSON/CSV | E2E-Test | C1 |
| P-B-04 | Widerruf einer Einwilligung wirkt unmittelbar | Integrationstest | C1 |
| P-B-05 | Profildaten editierbar | UI-Test | C2 |
| P-B-06 | Lokale Daten lassen sich löschen | Integrationstest | C1 |

#### C. Berechtigungen

| ID | Prüfung | Methode | Krit. |
| --- | --- | --- | --- |
| P-C-01 | AndroidManifest enthält nur dokumentierte Permissions | CI-Linter | C0 |
| P-C-02 | Laufzeit-Permission-Rationale vor System-Dialog | UI-Test | C1 |
| P-C-03 | Hintergrund-Permissions begründet im Play-Listing | Doc-Review | C1 |
| P-C-04 | Kamera/Mikrofon/Standort nur On-Demand | UI-Test + Code-Review | C0 |

#### D. Datensicherheit

| ID | Prüfung | Methode | Krit. |
| --- | --- | --- | --- |
| P-D-01 | HTTPS-only (`usesCleartextTraffic=false`) | Manifest-Check | C0 |
| P-D-02 | network-security-config aktiv | Manifest-Check | C0 |
| P-D-03 | Token in EncryptedSharedPreferences / Keystore | Code-Audit + Test | C0 |
| P-D-04 | Keine PII in Logs | Regex-Scan auf E-Mail/Telefon/Adresse | C0 |
| P-D-05 | Keine PII in Crashlytics-Custom-Keys | Code-Review | C1 |
| P-D-06 | Firestore-Rules verweigern Default-Read/Write | Rules-Unit-Test | C0 |
| P-D-07 | Datenlecks zwischen Tenants verhindert | Multi-Tenant-Test | C0 |
| P-D-08 | Backup-Tag in Manifest gezielt gesetzt (`allowBackup=false` oder mit Regel) | Manifest-Check | C0 |

#### E. Drittanbieter-SDKs

| SDK | gesammelte Daten | Speicherort | Aufbewahrung | Löschkonzept |
| --- | --- | --- | --- | --- |
| Firebase Auth | E-Mail-Hash, Refresh-Token | Google-DC EU | bis Kontolöschung | Auth-Account-Delete |
| Firestore | Nutzdaten | Google-DC EU | bis Nutzerlöschung | per Cloud-Function `deleteUserData` |
| FCM | Push-Token, Topic-Abos | Google | bis Token-Refresh | bei Logout invalidiert |
| Crashlytics | Stacktrace, Geräteinfo (anonym) | Google | 90 Tage | Self-Delete via Console |
| Analytics | Event-Namen, Pseudo-ID | Google | 14 Monate | Console-Reset / Opt-out |
| App Check | Integrity-Token | Google | Session | n/a |
| Remote Config | nichts (nur Read) | – | – | n/a |

### 12.4 Datenflussdiagramm (textuell)

```
[ Android-App ]
   │  TLS 1.2+
   ├── Auth   → Firebase Auth (EU, Refresh-Token rotiert)
   ├── Daten  → Firestore (EU, RBAC durch Rules)
   ├── Push   → FCM (Token rotiert bei Login)
   ├── Crash  → Crashlytics (anonymisiert, kein PII-Custom-Key)
   ├── Stats  → Analytics (nur nach Consent, IP-Anonymisierung)
   └── Check  → App Check (anti-bot, Session-only)

Lokal (Sandbox /data/data/<pkg>/):
   ├── EncryptedSharedPreferences (Token, Settings)
   ├── Room-DB (Offline-Cache, SQLCipher)
   └── Logs (rotierend, max 7 Tage, ohne PII)
```

### 12.5 Berechtigungs-Inventar (Soll)

| Manifest-Permission | App-Bedarf? | Begründung |
| --- | --- | --- |
| `INTERNET` | ja | Backend-Calls |
| `ACCESS_NETWORK_STATE` | optional | Online/Offline-Banner |
| `POST_NOTIFICATIONS` (API 33+) | ja | Erinnerungen |
| `RECEIVE_BOOT_COMPLETED` | nein | nicht nötig |
| `READ_EXTERNAL_STORAGE` | nein | SAF + Scoped Storage |
| `WRITE_EXTERNAL_STORAGE` | nein | dito |
| `CAMERA` | nur On-Demand | Avatar / Beleg-Foto |
| `RECORD_AUDIO` | nein | – |
| `ACCESS_FINE_LOCATION` | nein | – |
| `SYSTEM_ALERT_WINDOW` | nein | – |

### 12.6 DSGVO-Checkliste

- [ ] Datenschutzerklärung verlinkt im Play-Listing und in der App.
- [ ] Verzeichnis der Verarbeitungstätigkeiten (VVT) gepflegt.
- [ ] Auftragsverarbeitungsverträge mit Google (DPA) abgeschlossen.
- [ ] Drittlandtransfer (EU-US-DPF) dokumentiert.
- [ ] TOMs (technisch-organisatorische Maßnahmen) beschrieben.
- [ ] Lösch- und Auskunftsroutine getestet.
- [ ] DPIA durchgeführt, falls Risikoschwellen erreicht.
- [ ] Cookie-/Tracking-Hinweis falls relevant (WebView-Onboarding etc.).

### 12.7 Google Play Data-Safety-Vorlage

```
Welche Daten werden erhoben? Welche geteilt? Verschlüsselung in Transit? Löschbar?

Persönliche Daten
  - Name (erhoben, nicht geteilt, verschlüsselt, löschbar)
  - E-Mail (erhoben, nicht geteilt, verschlüsselt, löschbar)
Nutzergenerierte Inhalte
  - Aufgaben/Notizen (erhoben, nicht geteilt, verschlüsselt, löschbar)
App-Aktivität
  - App-Interaktionen (erhoben, nicht geteilt, verschlüsselt, löschbar)
Diagnose
  - Absturzlogs (erhoben, an Google, verschlüsselt, löschbar)
  - Diagnosedaten (erhoben, an Google, verschlüsselt, löschbar)
Geräte- oder andere Kennungen
  - keine
```

---

## 13. Nachweisdokumentation für Google Play

### 13.1 Ordnerstruktur

```
release/closed-test-<YYYY-MM-DD>/
  README.md                       # Übersicht des Releases
  testers.csv                     # Pseudonym, Beitritt, Engagement-Tage
  feedback/
    day-01.csv .. day-14.csv
  bugs/
    <id>.md
  crashes/
    crashlytics-export.csv
    anr-export.csv
  stats/
    sessions-per-tester.csv
    crash-free-users.csv
  builds/
    versionCode-1234-changelog.md
  scans/
    dependency-scan.json
    lint.html
    detekt.html
    proguard-mapping.txt
  privacy/
    data-safety.json
    permission-matrix.md
    sdk-inventory.md
  go-no-go.md                     # Aggregation siehe Anhang J/J2
```

### 13.2 Closed-Testing-Nachweise

- Tester-Pool: `testers.csv` mit ≥ 12 Einträgen, Beitritt vor Tag 1,
  Engagement ≥ 10/14 Tage in `sessions-per-tester.csv`.
- Feedback-Aggregation pro Tag (`feedback/day-XX.csv`) inkl. Sternebewertung.
- Bug-Stand: `bugs/*.md` nach P0/P1/P2/P3, Anzahl offen am Ende = 0 für P0/P1.
- Crash-Statistik: 7-Tage-Crash-Free-Users ≥ 99,5 %.

### 13.3 Qualitäts­nachweise

- `scans/lint.html`, `scans/detekt.html` ohne Errors.
- `scans/kover.xml` mit Coverage-Schwellen erreicht.
- `builds/versionCode-XXXX-changelog.md` enthält Test-Matrix-Status,
  unterstützte Android-Versionen, Geräteliste (Test Lab + Tester).
- `stats/`-Exporte aus Crashlytics + Vitals.

### 13.4 Datenschutz-Nachweise

- `privacy/data-safety.json` (Hash im Repo getrackt) entspricht dem
  Play-Console-Formular.
- `privacy/permission-matrix.md` listet jede Manifest-Permission samt
  Use-Case.
- `privacy/sdk-inventory.md` listet jede SDK + Datenfluss + DPA-Status.

### 13.5 Sicherheits­nachweise

- `scans/dependency-scan.json` mit 0 kritischen CVEs.
- ProGuard/R8-Mapping (`scans/proguard-mapping.txt`) in Play hochgeladen.
- Manifest-Audit: keine Debug-Flags, `usesCleartextTraffic=false`,
  `android:allowBackup` bewusst gesetzt.
- Pre-Launch Report aus Play Console ohne kritische Findings.

### 13.6 Release-Dokumentation

- `release-notes-<versionCode>.md` (kurz, Nutzerperspektive).
- `known-limitations-<versionCode>.md` (Defekte, die mit dieser
  Version bewusst ausgeliefert werden).
- `rollback-plan-<versionCode>.md` (Schritte für Stop-Rollout und
  Rückzug auf vorigen Track).

### 13.7 Review-Vorbereitung

Vor Klick auf „Submit for review“:

- Data-Safety-Form gespeichert + Hash gleich `data-safety.json`.
- Inhaltsbewertung aktuell.
- Zielgruppe + Inhaltskategorie eingestellt.
- Screenshots aktuell (Material 3, Dark Mode, Tablet).
- Datenschutzerklärung-URL erreichbar (CI prüft 200 OK).
- Promo-Video optional, ohne externe Tracker.

---

## 14. Go-/No-Go-Kriterien (Erweiterung)

Dies ist Anhang **J2** und ergänzt Anhang J aus Teil I. Ein Build wird
nur ausgeliefert, wenn **alle** Kriterien aus J **und** J2 erfüllt sind.

### 14.1 Technisch (J2-T)

| ID | Kriterium | Schwelle |
| --- | --- | --- |
| J2-T-01 | keine offenen C0/C1-Bugs | 0 |
| J2-T-02 | Crash-Free-Users (Closed 7 Tage) | ≥ 99,5 % |
| J2-T-03 | ANR-Rate | < 0,47 % |
| J2-T-04 | Kaltstart < 2 s auf Pixel 5 | ja |
| J2-T-05 | Sync-Konflikt-Reproduktion grün | ja |
| J2-T-06 | Push-Zustellrate (testweise) | ≥ 95 % |

### 14.2 Sicherheit (J2-S)

| ID | Kriterium | Schwelle |
| --- | --- | --- |
| J2-S-01 | 0 kritische CVE (Dependency-Scan) | 0 |
| J2-S-02 | 0 Hardcoded Secrets (Regex-Scan) | 0 |
| J2-S-03 | keine Debug-Features in Release-Build | bestätigt |
| J2-S-04 | TLS only, network-security-config aktiv | ja |
| J2-S-05 | App Check + Play Integrity scharf | ja |

### 14.3 Datenschutz (J2-P)

| ID | Kriterium | Schwelle |
| --- | --- | --- |
| J2-P-01 | Datenschutzerklärung erreichbar | 200 OK |
| J2-P-02 | Data-Safety-Hash unverändert oder reviewt | ja |
| J2-P-03 | nur dokumentierte Manifest-Permissions | ja |
| J2-P-04 | Kontolöschung in der App vorhanden | ja |
| J2-P-05 | Datenexport funktioniert | ja |
| J2-P-06 | keine PII in Logs (Scan) | 0 Treffer |

### 14.4 Qualität (J2-Q)

| ID | Kriterium | Schwelle |
| --- | --- | --- |
| J2-Q-01 | Unit/Integration/UI-Tests grün | 100 % |
| J2-Q-02 | Coverage Domain/Data/UI | 80/70/50 % |
| J2-Q-03 | Multi-Device-Smoke (4 Referenzgeräte) | grün |
| J2-Q-04 | Android 10–16 grün | grün |
| J2-Q-05 | Regression-Suite (Maestro) grün | grün |

### 14.5 Performance (J2-F)

| ID | Kriterium | Schwelle |
| --- | --- | --- |
| J2-F-01 | Kaltstart auf P50 | < 2 s |
| J2-F-02 | Speicher-Peak im Hot-Path | < 250 MB |
| J2-F-03 | Frame-Drop-Rate (Compose-Bench) | < 0,5 % |
| J2-F-04 | Daten-Sync pro Tag (Median) | < 5 MB |

### 14.6 Play-Store (J2-G)

| ID | Kriterium | Schwelle |
| --- | --- | --- |
| J2-G-01 | Closed Test ≥ 14 Tage + ≥ 12 Tester | erfüllt |
| J2-G-02 | keine Richtlinien­verstöße im Self-Assessment | 0 |
| J2-G-03 | targetSdk = Play-aktueller Wert (≥ 35) | ja |
| J2-G-04 | Store-Listing vollständig (DE + EN) | ja |
| J2-G-05 | Pre-Launch Report ohne Blocker | grün |

### 14.7 Eskalationsstufen

| Stufe | Auslöser | Folge | Verantwortlich |
| --- | --- | --- | --- |
| E0 | C0-Bug nach Production-Upload | Stop Rollout (0 %), Hotfix in 24 h | Release-Lead |
| E1 | C1-Bug im Closed Test | Build aus dem Track ziehen, Fix-Build | Engineering-Lead |
| E2 | Datenschutz-Vorfall | DPO informieren, ggf. 72-h-Meldung | DPO + Legal |
| E3 | Google-Ablehnung | Maßnahmen aus Anhang K, neue Submission | Release-Lead |

---

## 15. CI/CD-Integration (Erweiterung)

Diese Jobs ergänzen die Pipeline aus Kapitel 9.

| Job | Trigger | Inhalt |
| --- | --- | --- |
| `negative` | jeder PR | parametrisierte Negativtests (`tests/concept/test_negative_*`) |
| `privacy-scan` | jeder PR | Regex-Scan auf Secrets/PII, HTTPS-only, Permissions-Drift, legal/-Docs |
| `dependency-scan` | nightly + pre-release | OWASP-Check, Trivy, gradle-versions-Plugin |
| `manifest-audit` | jeder PR + pre-release | Manifest-Diff vs. erlaubte Liste |
| `data-safety-diff` | jeder PR | Hash von `privacy/data-safety.json` vs. letzte Review |
| `rules-tests` | jeder PR | Firestore-Rules-Unit-Tests |
| `playstore-checklist` | pre-release + closed | `tools/playstore_check.py` (existiert bereits im Repo) |

**Build-Blocker**: Wenn `negative`, `privacy-scan`, `manifest-audit`,
`data-safety-diff`, `rules-tests` oder `playstore-checklist` rot sind,
verweigert der Release-Gate-Job den Upload.

---

## 16. Ergebnisformat A–L

| Anhang | Lieferobjekt | Speicherort |
| --- | --- | --- |
| A | Negativtest-Konzept | Abschnitt 11 + `tests/concept/test_negative_*.py` |
| B | Datenschutz-Teststrategie | Abschnitt 12 + `tests/concept/test_privacy_*.py` |
| C | Google-Play-Nachweisdokumentation | Abschnitt 13 + `release/closed-test-*/` |
| D | Go-/No-Go-Entscheidungssystem | Abschnitt 14 (J2) + `tests/concept/test_release_gate.py`, `test_release_gate_extended.py` |
| E | Risikomatrix | Abschnitt 11.2 |
| F | Build-Blockierungsregeln | Abschnitt 9.2 + 15 + `tools/test_protocol.py` |
| G | Release-Freigabeprozess | Abschnitt 14.7 + `tools/test_protocol.py` |
| H | Datenschutz-Checklisten | Abschnitt 12.6 + 12.5 |
| I | Sicherheits-Checklisten | Abschnitt 14.2 |
| J | CI/CD-Validierungen | Abschnitt 9 + 15 |
| K | Vorlagen für Tester-Feedback / Fehlerberichte | Anhang G/H aus Teil I + `release/closed-test-*/feedback,bugs/` |
| L | Finale Google-Play-Review-Checkliste | Abschnitt 13.7 + Anhang J/J2 |

---

*Teil II Eigentümer: QA-Lead + DPO + Release-Lead. Letzte Review: 2026-05-20.*
