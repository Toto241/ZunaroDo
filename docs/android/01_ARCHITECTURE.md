# 01 - Architektur & Projektstruktur

## 1. Leitprinzipien

1. **Klare Schichten:** UI / Domain / Data. Keine Schicht überspringt
   die nächste; UI ruft nie direkt SQL, Domain kennt keine Widgets.
2. **Single-Activity-Architektur** (für Native): eine Activity hostet
   Compose-Navigation. Fragmente nur dort, wo Drittbibliotheken sie
   erzwingen.
3. **Reaktiv:** `StateFlow` / `Flow` (Kotlin) bzw. `EventDispatcher` +
   `bind()` (KivyMD) statt Polling.
4. **Modular:** Domain ist GUI-frei und auf Desktop wie Android lauffähig
   (im Repo bereits umgesetzt: [core/](../../core/), [modules/](../../modules/),
   [services/](../../services/)).
5. **Offline-First:** Die App muss ohne Netzwerk funktionieren. Netzwerk
   ist Optimierung, nicht Voraussetzung.
6. **Testbar:** Jede Schicht ist isoliert testbar (Domain ohne DB, Repos
   gegen In-Memory-DB, UI gegen Fakes).

## 2. Soll-Architektur Kotlin/Jetpack Compose (für Native-Migration)

```text
app/                           # Application module (single-activity)
core/
  core-common/                 # Result<T>, Dispatchers, Logger-Interface
  core-ui/                     # Theme, design tokens, reusable composables
  core-testing/                # Test rules, fakes, fixtures
data/
  data-db/                     # Room DAOs + Entities (1:1 mit Python-Schema)
  data-network/                # Retrofit + OkHttp + interceptors
  data-prefs/                  # DataStore (Preferences + Proto)
  data-sync/                   # CRDT/Lamport-Clock-Port aus services/sync.py
domain/
  domain-contracts/            # UseCases je Fachmodul
  domain-finance/
  domain-calendar/
  ...
feature/
  feature-dashboard/           # Compose-Screen + ViewModel
  feature-contracts/
  feature-finance/
  feature-calendar/
  feature-more/
build-logic/                   # convention plugins (gradle)
```

### Schichtregeln (enforced via Gradle convention-plugin + Detekt)

| Schicht  | Darf importieren | Darf NICHT importieren |
| -------- | ---------------- | ----------------------- |
| feature  | domain, core-ui, core-common | data, andere features |
| domain   | core-common | data, feature, android.* |
| data     | core-common | feature, domain.* (außer Interfaces) |
| core-ui  | core-common, compose | data, domain, feature |

Domain-Modul **darf keine `android.*`-Klasse** importieren - JVM-pur,
damit es im Desktop-/Server-Kontext wiederverwendbar bleibt.

## 3. Aktuelle Architektur (KivyMD/Python) - Soll-Zustand

Das Python-Setup ist bereits sauber geschichtet ([ARCHITECTURE.md](../../ARCHITECTURE.md)),
behält diese Trennung aber explizit für Android bei:

```text
mobile/                # Präsentationsschicht (KivyMD) - Android-only
mobile/screens/        # je Screen 1 Datei, dünn, nutzt mobile/helpers.py
mobile/helpers.py      # GUI-freie Formatierungs-/Aggregationslogik (testbar)
core/                  # Capability/Registry-Interface
modules/               # Domain (gemeinsam mit Desktop)
services/              # Cross-Cutting (Sync, Logging, Config, Output, Backup)
database.py            # Persistenz (SQLite + Repos)
```

Pflicht-Regeln (siehe auch `core/interface.py`):

- **Kein** direkter `database.*`-Import in `mobile/`. Zugriff nur über
  `registry.dispatch(...)`.
- **Kein** `print()` in Production-Code - immer `logging.getLogger(...)`,
  konfiguriert über `services.logging_setup.configure_logging`.
- **Keine** Sekretab direkt in der DB (`SECRET_KEYS` in
  `services/config.py`); auf Android stattdessen Android Keystore via
  `pyjnius`-Brücke vorbereiten.

## 4. Dependency Injection

| Stack | Empfehlung | Begründung |
| ----- | ---------- | ---------- |
| Kotlin/Native | **Hilt** | Erstklassiger Compose-Support, Android-Lifecycle-Aware. Koin nur, wenn KMP geplant ist. |
| Python/Kivy | Construction via Registry | bereits umgesetzt; kein zusätzlicher DI-Container nötig. |

## 5. Naming- & Package-Konventionen

### Native (Kotlin)

- Package: `de.alltagshelfer.<schicht>.<feature>` -
  z.B. `de.alltagshelfer.feature.contracts.ui`.
- Klassen: `PascalCase`, Suffixe verpflichtend:
  - ViewModels: `*ViewModel`
  - Screens (Composable): `*Screen` / `*Route` (Wrapper)
  - DAOs: `*Dao`
  - UseCases: Verb-zuerst (`GetContractsUseCase`, `AddExpenseUseCase`)
  - Repositories: `*Repository` (Interface) / `*RepositoryImpl` (Impl)
- Tests: `*Test` (Unit), `*UiTest` (Compose), `*E2eTest` (Maestro/UIAutomator).

### Python (Ist)

- Module: `snake_case` (bereits konsistent).
- Klassen: `PascalCase`.
- Capabilities: `<modul>.<verb_oder_substantiv>` - z.B. `contracts.add`.
- Tests: `tests/test_<bereich>.py`, Klassen `Test<Sache>`.

## 6. Build-Typen & Flavors

### Build-Typen (Kotlin/Gradle)

```kotlin
android {
  buildTypes {
    debug {
      isMinifyEnabled = false
      isDebuggable = true
      applicationIdSuffix = ".debug"
      versionNameSuffix = "-debug"
      // Crashlytics aus, Strict-Mode an
    }
    release {
      isMinifyEnabled = true
      isShrinkResources = true
      proguardFiles(
        getDefaultProguardFile("proguard-android-optimize.txt"),
        "proguard-rules.pro")
      signingConfig = signingConfigs.getByName("release")
    }
  }
  flavorDimensions += "env"
  productFlavors {
    create("staging") {
      dimension = "env"
      buildConfigField("String", "API_BASE", "\"https://staging.api.alltagshelfer.de\"")
      applicationIdSuffix = ".staging"
    }
    create("production") {
      dimension = "env"
      buildConfigField("String", "API_BASE", "\"https://api.alltagshelfer.de\"")
    }
  }
}
```

Resultierende Varianten: `stagingDebug`, `stagingRelease`,
`productionDebug`, `productionRelease`. Im Play Store landet **nur**
`productionRelease`.

### Buildozer-Equivalent (Ist)

Buildozer kennt keine Flavors. Stattdessen:

- **Debug-Build:** `buildozer android debug` - signiert mit Debug-Key.
- **Release-Build:** `buildozer android release` + Upload-Signierung
  über `p4a.bootstrap = sdl2 --release` + env-vars `P4A_RELEASE_KEYSTORE`,
  `P4A_RELEASE_KEYSTORE_PASSWD`, `P4A_RELEASE_KEYALIAS_PASSWD`,
  `P4A_RELEASE_KEYALIAS`.
- **Staging vs. Production:** über Build-time-Env-Vars steuern, z.B.
  `ALLTAG_API_BASE` (in `services/config.py` lesen).

## 7. Navigation

### Native

- `androidx.navigation:navigation-compose`
- Typed Routes (Compose Navigation 2.8+): jeder Screen hat eine
  `@Serializable`-Route-Klasse, keine String-Konkatenation.
- Tiefe Verschachtelung vermeiden - flache Top-Level-Nav mit Bottom-Bar.

### KivyMD (Ist)

- `MDBottomNavigation` mit 5 Items (siehe [mobile/app.py](../../mobile/app.py)).
- Sub-Screens via `MDDialog(type="custom")` als modale Eingaben.
- Kein eigener Router-Stack nötig; Kivy `ScreenManager` reicht.

## 8. Zentrale Fehlerbehandlung

### Pattern (sprachunabhängig)

```text
Fehler -> Kategorisierung -> User-Message + Telemetry + (optional) Retry
```

Kategorien:

| Kategorie | Beispiel | Reaktion |
| --------- | -------- | -------- |
| `User`    | Validierung scheitert | Inline-Fehlertext, kein Crash, keine Telemetrie |
| `Network` | Timeout, 5xx | Retry mit Backoff, Snackbar "offline?" |
| `Storage` | DB-Lock | Retry, dann Datenexport-Empfehlung |
| `Fatal`   | DB-Schema-Mismatch | Crashlytics + abort + Recovery-Dialog |

### Kotlin

```kotlin
sealed interface AppError {
  data class User(val msg: String): AppError
  data class Network(val cause: Throwable): AppError
  data class Storage(val cause: Throwable): AppError
  data class Fatal(val cause: Throwable): AppError
}

sealed interface Result<out T> {
  data class Success<T>(val value: T): Result<T>
  data class Failure(val error: AppError): Result<Nothing>
}
```

### Python (Ist)

`registry.dispatch` returnt **immer** ein Dict mit `ok: bool` und
`error: str | None`. Module raisen nie nach außen; alle Exceptions
werden im Handler gefangen, gelogged und als `{"ok": false, "error": ...}`
geliefert. Diese Konvention ist bereits implementiert und MUSS für
mobile Stabilität strikt eingehalten werden (siehe `core/interface.py`).

## 9. Logging-Konzept

| Aspekt | Native | KivyMD/Python |
| ------ | ------ | -------------- |
| Library | `Timber` + `androidx.tracing` | `logging` + `RotatingFileHandler` |
| Sinks | logcat (debug), Crashlytics (release) | `logs/*.log`, Größe begrenzt, rotierend |
| PII-Filter | Pflicht: `Timber.Tree`-Subklasse strippt E-Mail/IBAN-Patterns | Pflicht: bereits in `services/logging_setup.py`-Hook ergänzen |
| Release-Level | `INFO+` | `INFO+`, `DEBUG` nur via Env-Flag |
| Tag-Konvention | `de.alltagshelfer.<feature>` | Logger-Name = Modul-Pfad |

Niemals in Logs:

- Klartext-Passwörter, API-Keys, JWT-Tokens
- vollständige E-Mail-Adressen (nur Hash oder Domain-Teil)
- IBAN, Kreditkarten, persönliche Adressen
- LLM-Prompt-Inhalte des Nutzers

## 10. Offlinefähigkeit

- **DB ist Single Source of Truth.** Netzwerk schreibt nur in DB,
  nie direkt in UI-State.
- **Sync ist optional und idempotent.** Lamport-Clock-CRDT
  ([services/sync.py](../../services/sync.py)) bleibt unverändert auch
  in Native-Variante (Algorithmus portierbar).
- **WorkManager** (Native) bzw. `services/scheduler.py` + Foreground-
  Service (Kivy via `android.runnable`) für Hintergrund-Sync.
- Connectivity-Check via `ConnectivityManager.NetworkCallback`
  (Native) / `plyer.connectivity` (Kivy). Niemals via fehlerhaften
  Ping-Aufruf an Drittservices.

## 11. Compose-spezifische Vorgaben (Native)

- **State Hoisting:** Composables sind stateless wo möglich; State liegt
  im ViewModel als `StateFlow`. Lokale UI-Drafts via `remember`.
- **Stability:** alle Data-Klassen, die in Composable-Parametern landen,
  sind `@Immutable` oder `kotlinx.collections.immutable`.
- **Recomposition-Hygiene:** kein `mutableStateOf(...)` für sich häufig
  ändernde Werte, die nicht in der UI landen.
- **Side-Effects:** `LaunchedEffect(key)` mit stabilem Key,
  `DisposableEffect` für Listener.
- **Theming:** Material 3, `ColorScheme` aus Tokens
  (`core-ui/Theme.kt`); kein Hardcoded-Hex außerhalb von Tokens.

## 12. Was NICHT erlaubt ist

- `Context` als Singleton irgendwo speichern (Memory Leak).
- `runBlocking` außerhalb von Tests.
- `findViewById` in einer Compose-only-App.
- `print()` / `System.out.println` im Production-Code (Lint-Regel
  enforce).
- Cross-Modul-Imports, die die Schicht-Regel verletzen (Konvention-
  Plugin verhindert es im Native-Build).
- Direkter SQL-Zugriff aus der UI-Schicht (in Kivy wie in Compose).
