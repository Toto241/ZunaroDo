# 05 - Performance-Standards

## 1. Performance-Budget

Verbindliche Schwellen - bei Überschreitung Release-Halt:

| Metrik | Schwelle | Messung |
| ------ | -------- | ------- |
| Cold-Start (App-Time-to-Interactive) | <= **2 000 ms** (Mid-Range, Android 12) | Macrobench (Native) / `time` zwischen App-Start und `Window.on_draw` (Kivy) |
| Warm-Start | <= 800 ms | wie oben |
| ANR-Rate (Play-Vitals) | < 0,47 % | Play Console |
| Crash-Rate (User-perceived) | < 1,09 % | Play Console |
| Frame-Rate (Listen-Scroll) | >= 55 fps avg, 0 % "frozen frames" über 700 ms | Profiler / `dumpsys gfxinfo` |
| Memory (Heap idle) | <= 80 MB auf 2-GB-RAM-Device | `meminfo` |
| APK/AAB-Größe | <= **40 MB** Download, <= 120 MB installiert | Bundle-Analyzer / `du -h` |
| Netzwerkaufrufe auf Main Thread | **0** | StrictMode / Code-Scan |
| Baseline-Profile-Coverage | >= 80 % der Hot-Startup-Pfade | Native-Macrobench-Report |

## 2. Startup-Optimierung

### Native (Kotlin)

- **App-Startup-Library:** Initialisierer (`androidx.startup`) statt
  ContentProvider-Hacks.
- **WorkManager.initialize**: manuell (kein Auto-Init), erst nach
  `onCreate`-finish.
- Hilt-Aggregating: alle Aufträge in `@HiltAndroidApp` schlank halten.
- **Baseline Profiles** (Macrobenchmark generieren -> ins AAB packen):

```kotlin
@OptIn(ExperimentalBaselineProfilesApi::class)
@get:Rule val baselineProfileRule = BaselineProfileRule()

@Test
fun startupProfile() = baselineProfileRule.collect(
  packageName = "de.alltagshelfer",
  profileBlock = { startActivityAndWait() }
)
```

### KivyMD (Ist)

- **Kein** SQL bei `App.build()`: DB-Open ja, aber keine Queries
  synchron - Dashboard lädt **nach** dem ersten Frame.
- `Clock.schedule_once(self._load_data, 0)` für initiale DB-Fetches.
- KivyMD-Theming einmal setzen, danach Cache nutzen.
- Splash-Bild (`presplash.filename`) als 9-Patch, klein halten (<200 KB),
  reduziert wahrgenommene Startzeit.
- Schwerer Import (`google-generativeai`, `Pillow`) **lazy** -
  `import` erst beim ersten Bedarf.

## 3. ANR-Vermeidung

| Regel | Native | Kivy |
| ----- | ------ | ---- |
| Kein I/O auf Main | Coroutines `Dispatchers.IO` | Threading via `mainthread` decorator / `Clock.schedule_once`; schwere Calls in `Thread`/`asyncio` |
| Kein DB-Write auf Main | Room mit `suspend`/Flow | `services.workers`-Modul (async-fähig) wo möglich |
| Kein synchrones Logging > 5 ms | `Timber` async sink | `logging.handlers.QueueHandler` |
| Kein Layout > 16 ms im Listen-Scroll | Compose-Stable-Types, `LazyColumn` | KivyMD `RecycleView` für Listen > 50 Einträge |

## 4. Memory

- **Bitmaps**: in Listen `Coil`/`Glide` (Native) mit `crossfade` + Disk-
  Cache; Kivy: `AsyncImage` mit Cache-Strategie.
- Bildkomprimierung beim Beleg-Import: WebP-Compression vor Speichern
  (Pillow `quality=75`).
- Object-Pools nur für nachweislich heiße Pfade.
- `LeakCanary` (Native, Debug-only) - bei jedem Leak -> Issue.
- `gc.set_threshold(700, 10, 5)` bleibt Default; explizites `gc.collect()`
  nur im Backup-Worker nach großen Operationen.

## 5. APK/AAB-Größe

### Ist-Stand bei Buildozer

- `armeabi-v7a` + `arm64-v8a` -> APK enthält beide -> doppelt so groß.
- **Empfehlung:** App Bundle (AAB) statt fat-APK, dann verteilt Play
  Store je Gerät die richtige ABI.

### Vorgaben

- **App Bundle**: ja, immer.
- **Resources**: `densitySplits` für `mdpi`/`hdpi`/`xhdpi`/...; keine
  PNG-Resources im `drawable/`-Default-Ordner.
- **Locale-Splits**: ja, nur tatsächlich genutzte Sprachen (`de`, `en`).
- **Unused Resources**: Lint-Regel + R8 Resource-Shrinking.
- **Native Libs** (Kivy):
  - `python-for-android` strippt Debug-Symbole automatisch im
    `--release`-Build.
  - Optionale Bibliotheken (z.B. `Pillow`-Plugins) deaktivieren, wenn
    nicht genutzt.

### Native-spezifisch

```kotlin
android {
  bundle {
    language { enableSplit = true }
    density  { enableSplit = true }
    abi      { enableSplit = true }
  }
}
```

## 6. Network-Effizienz

- **Komprimierung:** OkHttp default mit gzip; Sync-Server liefert gzip.
- **Caching:** ETag/`Last-Modified` an Server, Client mit `If-None-Match`.
- **Batching:** Sync-Diffs in 5-Sekunden-Bucket aggregieren statt pro
  Capability-Aufruf einen POST.
- **Background-Sync-Frequenz**:
  - WorkManager Periodic >= 15 min (Min-Intervall),
  - Realtime nur bei Foreground-App.
- **Retry-Policy:** exponentielles Backoff, Jitter, Max 5 Versuche.
- **Connectivity-aware:** vor Sync-Request `ConnectivityManager`
  prüfen.

## 7. Hintergrundarbeit

- **WorkManager** für alles ab "Sync-Job".
- Periodisch >= 15 min Intervall.
- `Constraints.Builder().setRequiredNetworkType(NetworkType.UNMETERED)`
  für große Synchronisationen.
- `setRequiresBatteryNotLow(true)` standardmäßig.
- Foreground-Service nur, wenn ohne UI eine zeitkritische User-Aktion
  läuft (z.B. Export). Mit `foregroundServiceType="dataSync"` + Notification.

## 8. UI-Smoothness

### Compose

- `LazyColumn`/`LazyRow` mit `key = { it.id }` - sonst Recompose-Storm.
- `derivedStateOf` für teure Berechnungen.
- `remember` nur für stabile Werte.
- `produceState` für asynchrone Quellen.
- Compose-Compiler-Metriken: in CI sammeln (Skip-Rate >= 80 %).

### KivyMD

- `RecycleView` für Listen > 30 Items.
- Touch-Events nicht in `bind`-Callbacks blockieren.
- Animationen mit `Animation(duration=0.18)` - länger als 250 ms wirkt
  träge.

## 9. Profiling-Tools (Pflicht-Setup)

| Tool | Wofür | Häufigkeit |
| ---- | ----- | ---------- |
| Android Studio Profiler | CPU, Memory, Network | pro Feature-Sprint |
| `dumpsys gfxinfo` | Frame-Stats | bei jedem Release-Build |
| `adb shell am start -W de.alltagshelfer/.MainActivity` | Startup-Zeit | CI-Smoke |
| `simpleperf` | Native-Profiling (auch für Python-Native-Calls) | bei Verdacht auf Hotspot |
| Macrobench-Compose (Native) | Startup / Scroll | bei Release-Branch |
| `tracing-perfetto` | Pflichthärtung | bei Performance-Regression |

## 10. StrictMode

In **Debug-Builds** Pflicht:

```kotlin
// Application.onCreate()
if (BuildConfig.DEBUG) {
  StrictMode.setThreadPolicy(StrictMode.ThreadPolicy.Builder()
    .detectAll().penaltyLog().build())
  StrictMode.setVmPolicy(StrictMode.VmPolicy.Builder()
    .detectAll().penaltyLog().build())
}
```

Für Kivy: kein direktes Äquivalent. Workaround: Custom-Check, der vor
jedem Repo-Call die Main-Thread-Identität verifiziert und bei Verstoß
ein Warn-Log schreibt (Hook in `database.py`).

## 11. Lazy Loading & Paging

- Listen mit > 200 Einträgen: **Paging 3** (Native) / manuelles Paging
  in `mobile/helpers.py` mit `offset`/`limit`-Queries (Repo-Schicht).
- Bilder nie eager; `Coil`/`Glide` löst sich selbst.
- Settings-Screen sub-pages: Lazy-Compose-Loading.

## 12. Caching-Strategien

| Daten | Strategie |
| ----- | --------- |
| Statische Refs (Tier-Modell, Affiliate-Liste) | im RAM, beim App-Start aus Settings geladen |
| Sync-Diffs | Append-only-Queue auf Disk, Replay nach Reboot |
| LLM-Antworten | nicht cachen (Datenschutz) |
| OCR-Ergebnis | optional: Hash(Bild) -> JSON-Cache 30 Tage |
| User-Avatare | Coil/Glide-Disk-Cache, 50 MB max |

## 13. Compose Recomposition Hygiene

- Compose Stability Reports in CI (`-P android.experimental.enableCompositionMetrics=true`).
- Falls Skip-Rate < 80 %: Review pflicht.
- Häufige Übeltäter:
  - `List<T>` ohne `ImmutableList`
  - `() -> Unit`-Lambdas inline -> mit `remember` stabilisieren oder
    Klassen-Methoden referenzieren

## 14. Performance-Regressions-Suite

Pflicht-Suite:

- Startup-Smoke: `adb shell am start -W ...` in CI -> Wert ins
  Vitals-CSV.
- Frame-Bench: Macrobench (Native) -> Trend-Report.
- APK-Größen-Trend: `bundletool dump manifest` + Größen-Report im PR
  posten.
- Memory-Smoke: app installieren, idle 30 s, `meminfo` snapshot.

## 15. Konkrete Action Items für aktuellen Code

- [ ] `mobile/screens/dashboard.py` (vermutet): DB-Queries
  asynchronisieren, falls aktuell synchron im `_refresh`.
- [ ] `presplash.filename` setzen (in `buildozer.spec` aktuell
  auskommentiert).
- [ ] AAB-Build statt fat-APK aktivieren.
- [ ] `gemini`-Import in `services/gemini.py` als Lazy-Import in den
  Aufrufpfad, damit App-Start nicht das LLM-SDK initialisiert.
- [ ] `Pillow`-Import vermeiden, solange keine Beleg-Bildverarbeitung
  aktiv ist.
