# Changelog

Alle relevanten Aenderungen am Projekt - chronologisch absteigend.

## [Unreleased]

### Neu

- **Anforderungsspezifikation** — `ANFORDERUNGEN.md`: konsolidiertes Lasten-/Pflichtenheft mit allen funktionalen und nicht-funktionalen Anforderungen, durchgaengigem ID-Schema (FR/NFR/PA/DA/SY/EN/KI/LI/CO/MO/IF/CFG/QA) und Traceability auf R1–R10.
- **Datenverzeichnis beim Start** — Beim Erststart waehlt der Nutzer ein Verzeichnis, in dem alle Laufzeitdateien liegen (DB, `ausgaben/`, `backups/`, Sync-State). Die Wahl wird gemerkt (`ALLTAGSHELFER_DATA_DIR` bzw. Zeiger-Datei im Konfig-Ordner) und vorhandene Daten werden hineinkopiert; spaeter aenderbar unter „Einstellungen → Datenverzeichnis“ (`services/datadir.py`).
- **Mobile-Lizenz-Gate** — `install_gate`, Grandfathering, Screen „Lizenz / Pro“ (Trial + Token).
- **Mobile-Datenexport** — CSV + JSON unter „Mehr → Daten exportieren“ (`export_all_json`).
- **Pro-Sync-Durchsetzung** — `services/sync_runtime.py`; Free-Tier kann Sync nicht aktivieren.
- **AI-Studio-Contracts** — `tools/gen_ai_studio_contracts.py` erzeugt aus der Registry und dem DB-Schema maschinenlesbare Contracts unter `docs/ai-studio/contracts/` (OpenAPI 3.1, Capability-Liste, `schema.sql`, `schema.prisma`); Drift-Test `tests/test_ai_studio_contracts.py`. AI-Studio-Handoff verdrahtet diese plus `UI_CONCEPT.md`/Screenshots und benennt Google Gemini als KI-Backend.
- **Store-Screenshots aus App-Daten** — `tools/capture_store_screenshots.py` rendert Play-Store-Phone-Screenshots (1080x1920) aus HeadlessApp-Demo-Daten; `gen_assets --check` gruen.
- **Play-Console-Runbooks** — `release/PLAY_CONSOLE_SETUP.md`, `release/CLOSED_TEST_RUNBOOK.md`, `release/create_upload_keystore.sh` (Linux/macOS).
- **Geraete-Verifikation** — `tools/verify_android_device.py` (SQLCipher-Header + ML-Kit via adb).

### Geändert

- **Legal finalisiert** — Impressum/AGB/Widerruf/Datenschutz ohne Platzhalter; `legal/provider.yml`.
- **Payment-Vorbereitung** — Ed25519-Public-Key im Release; `release/deploy-payment-server.md`.
- **playstore.yml** — Version 1.0.0 (code 2), Closed-Test-Nachweis, Production-Draft.
- **Marketing-Site** — FAQ, Screenshots, Support-Kontakt.
- **i18n** — Lizenz-/Export-Keys in allen Vollsprachen (de/en/fr/es/it/nl/pl/pt).
- **AGENTS.md** — 13 Module / 92 Capabilities (statt veralteter „8 domain modules“).
- **GO_LIVE_TODO.md** — Screenshots, Keystore-Helfer, Verifikations-Skript und Closed-Test-Runbook verdrahtet.

### Behoben

- **main.py Demo** — Mail-Analyse crasht nicht mehr bei Free-Tier (`tier_locked`).
- **CustomTkinter-Theme** — `CTkTabview`-Patch nur wenn Theme-Key existiert.
- **Sync-Server: Konstantzeit-Token** — `X-Sync-Token` wird via `hmac.compare_digest` geprueft (vorher `==`), schliesst ein Timing-Orakel auf das Token (`services/sync_server.py`).
- **Sync-Server: Rate-Limit-Speicher** — verwaiste Client-IPs werden aus dem Rate-Limit-Dict entfernt; ein oeffentlich gebundener Server waechst nicht mehr unbegrenzt pro Quell-IP (`services/sync_server.py`).
- **HttpSync: Thread-Safety** — `unseen_events` zieht einen Snapshot von `_seen` unter Lock (analog `FileSyncProvider`); verhindert „set changed size during iteration“ im Worker-Thread (`services/sync.py`).
- **Backup-Verifikation: kein os.environ-Mutieren** — `verify_backup` reicht den Schluessel explizit durch statt `ALLTAGSHELFER_DB_KEY` global zu poppen/restoren; schliesst ein TOCTOU, bei dem ein paralleles Database-Handle faelschlich den Plaintext-Pfad waehlte (`services/backup.py`).
- **Gemini: leere Antworten abfangen** — Non-Streaming-Pfad und `analyze_text` stuerzen bei geblockten/leeren Candidates nicht mehr ab (`response.candidates[0]`/`response.text`-Property); Verhalten jetzt symmetrisch zum Streaming-Pfad und zum REST-Client (`services/gemini.py`).
- **Familien-Rotation nach Mitglied-Loeschung** — Wird ein Rotationsmitglied endgueltig geloescht (CASCADE auf `task_rotation`), renormalisiert `delete_member` jetzt die betroffenen Aufgaben: Positionen werden luecklos neu vergeben und `current_index` angepasst, sodass der angezeigte Verantwortliche korrekt bleibt (bisher konnte bis zum naechsten `complete_task` die falsche Person erscheinen) (`database.py`).

## [1.0.0] - 2026-05-29

Erstes stabiles Release. Buendelt die seit 0.10.0 unter "Unreleased"
gefuehrten Aenderungen (Mobile-Profil-Umschalter, i18n-Vollausbau der
Phone-Texte, Supply-Chain-Haertung der CI) und vereinheitlicht die
Versionsangabe ueber pyproject.toml, buildozer.spec und Changelog.

### Neu

- **Profil-Umschalter im Mobile-UI** - der „Mehr"-Screen hat jetzt einen
  Eintrag „Profile (Gerät)", der die Geräte-Profile auflistet, das aktive
  markiert und Wechseln/Anlegen erlaubt (über die getesteten
  `system.profile*`-Capabilities; wirkt nach Neustart). Schließt die letzte
  UI-Lücke für die Multi-User-Profile. Neue `more.profiles`/`page.profiles`/
  `profiles.new_hint`/`action.create`-Keys in allen 8 Voll-Sprachen.

### Sicherheit / CI

- **buildozer-action auf Commit-SHA gepinnt** - die Community-Action in
  `android-release.yml` und `android-robo.yml` ist jetzt auf den
  v1-Commit-SHA `3808a27` festgenagelt (Supply-Chain-Härtung) statt auf den
  beweglichen Tag `@v1`.

### Geändert

- **i18n-Abschluss: „Mehr"-Menü & Sub-Page-Titel** - die Listen-Einträge im
  „Mehr"-Screen (Familie/Notizen/Inbox/Suche/Aufträge/Kontakte) und die
  Sub-Page-Titel sind nun ebenfalls lokalisiert (`more.*`/`page.*`-Keys).
  Damit gibt es im Phone-Client keine sichtbaren hartcodierten Labels mehr.
- **i18n-Ausbau Stufe 3: interpolierte Leertexte + Abschluss** -
  zählerbasierte Leertexte (Kalender „nächste {days} Tage", Finanzen
  „letzte {days} Tage") sind jetzt über Platzhalter-Keys
  (`calendar.empty`/`finance.recent_empty`) lokalisierbar - der Presenter
  liefert `empty_text_key` + `empty_text_params`, der Screen formatiert.
  Außerdem „Anstehend" (`dashboard.upcoming`) und die generische
  „Keine Einträge"-Liste (`common.no_entries`). Damit sind die sichtbaren
  Phone-Texte (Titel, Buttons, Labels, Leerzustände, Hinweise) lokalisierbar.
- **i18n-Ausbau Stufe 2: lokalisierbare Leer-/Hinweistexte (Presenter)** -
  die Presenter liefern neben dem deutschen `empty_text` jetzt zusätzlich
  einen i18n-Key (`empty_text_key`) bzw. die Suche einen `message_key`; die
  Screens lösen ihn über `i18n.t(...)` auf (deutscher Text bleibt Default).
  So sind Leerzustände (Verträge/Aufträge/Kontakte/Finanzen) und
  Such-Hinweise lokalisierbar, ohne den Presenter-Vertrag zu brechen - die
  headless Tests prüfen weiterhin Text **und** Key. Neue `*.empty`-Keys in
  `de.json`/`en.json`.
- **i18n-Ausbau der Mobile-Screens (erste Stufe)** - die Phone-Screens
  nutzten bisher gar kein i18n. Über den neuen Helfer
  [mobile/ui_text.py](mobile/ui_text.py) (`t(key, default)`, holt die
  Übersetzung aus der laufenden App, fällt sonst auf den deutschen Default
  zurück → kein Regressionsrisiko) sind jetzt Toolbar-Titel, Dialog-Titel
  und die Standard-Buttons (Speichern/Abbrechen/Löschen/Schließen) sowie
  gängige Feld-Labels über `i18n.t(...)` lokalisierbar. Datenwerte/Sentinels
  bleiben unangetastet. Neue Keys in `de.json`/`en.json`; Tests:
  [tests/test_ui_text.py](tests/test_ui_text.py). (Empty-States/Detailtexte
  folgen als nächste Stufe.)
- **i18n für die neuen Desktop-Labels** - die in dieser Session ergänzten
  Anzeige-Labels (Such-Filterzeile + Platzhalter, Auftrags-Prioritäts-/
  Kategorie-Feld, Dashboard-„Überfällig") laufen jetzt über `i18n.t(...)`
  mit Keys in `locales/de.json` + `locales/en.json`. Bewusst **nicht**
  übersetzt: Werte/Sentinels, die zugleich Logik/Backend-Argumente sind
  (Prioritätswerte `hoch/mittel/normal`, Kategorie-Filterwerte, „Alle",
  Ansicht-Umschalter), um Vergleichs-/Dispatch-Brüche zu vermeiden.
- **Desktop-GUI nutzt die geteilten Presenter** - die in dieser Session
  ergänzten Desktop-Flows (Volltextsuche inkl. Filter/Status, Auftrag
  anlegen/auflisten, Tages-/Wochen-Agenda) laufen jetzt über dieselbe
  headless getestete `app_core`-Presenter-Schicht wie Mobile - dieselbe
  Single Source of Truth, kein Desktop-spezifischer Doppel-Code mehr.
- **Presenter-/Headless-Schicht nach `app_core/` verschoben** - die zuvor
  unter `mobile/` liegende Presenter-/Helfer-/HeadlessApp-Schicht ist jetzt
  toolkit-neutral in `app_core/` und damit von Mobile **und** Desktop
  nutzbar; `mobile/*` sind schlanke Re-Export-Shims. Die Mobile-Screens
  Kalender und Finanzen delegieren nun ebenfalls an Presenter
  (`CalendarPresenter`, `FinancePresenter` inkl. `recent()`), sodass es im
  gesamten Mobile-Client keine doppelte Screen-Logik mehr gibt.

### Tests

- **Headless-/Presenter-Schicht als testbare App-Variante** - das
  Verhalten der Screens (Capability-Aufrufe + Anzeige-/Leer-/Fehlerzustände)
  liegt jetzt toolkit-unabhängig in [mobile/presenters.py](mobile/presenters.py);
  [mobile/headless_app.py](mobile/headless_app.py) (`HeadlessApp`) treibt es
  über dieselbe Registry ohne Display/Kivy. Die Kivy-Screens (Dashboard,
  Verträge, Suche, Aufträge) sind nun dünne Adapter ohne doppelte Logik.
  Damit ist das UI-Verhalten vollautomatisch testbar
  ([tests/test_presenters.py](tests/test_presenters.py),
  [tests/test_headless_app.py](tests/test_headless_app.py)) - genau die
  Tests, die sich mit der reinen Widget-UI nicht automatisieren ließen.
- **Laufzeit-/Geräte-Tests für Google-Qualitätskonformität** - neben den
  bisherigen Headless-Logik- und statischen Compliance-Checks gibt es jetzt
  echte UI-Laufzeittests: ein Desktop-GUI-Boot-Smoke unter Xvfb
  ([tests/test_gui_boot_smoke.py](tests/test_gui_boot_smoke.py)) und ein
  headless KivyMD-Boot-Smoke
  ([tests/test_mobile_boot_smoke.py](tests/test_mobile_boot_smoke.py)),
  ausgeführt von [`.github/workflows/ui-runtime.yml`](.github/workflows/ui-runtime.yml)
  (zunächst beratend). Dazu ein manueller Emulator-Monkey-Lauf
  ([`.github/workflows/android-robo.yml`](.github/workflows/android-robo.yml))
  als Repo-Pendant zu Googles Pre-Launch-Report. Beide Smoke-Tests skippen
  sauber, wo GUI/Kivy fehlen.
- **Automatisch erzwungene Anforderungs-Abdeckung** - neuer Meta-Test
  [tests/test_requirements_coverage.py](tests/test_requirements_coverage.py)
  prüft, dass jede Anforderung R1–R10 mindestens einer Testdatei zugeordnet
  ist, dass das Mapping nur bekannte IDs nutzt und dass jede gemappte Datei
  existiert und echte `test_*`-Fälle enthält. Damit färbt die CI automatisch
  rot, sobald eine Anforderung ohne Test bleibt oder eine Zuordnung ins
  Leere zeigt.
- **Import-Robustheit & Sync-Determinismus (R6/R5)** - neue Regressionstests:
  CSV-Import überspringt fehlerhafte Zeilen für alle Entitäten und fällt bei
  kaputten Werten auf Defaults zurück; iCal-Wiederholungen sind rund um die
  DST-Umstellung datumsstabil ([tests/test_import_robustness.py](tests/test_import_robustness.py)).
  Sync-Konflikte am selben Datensatz lösen sich deterministisch über den
  device_id-Tie-Break auf ([tests/test_sync_conflict.py](tests/test_sync_conflict.py)).

### Neu

- **TLS-Zertifikatserstellung für den Sync-Server** - neuer Helfer
  [services/tls_certs.py](services/tls_certs.py) erzeugt ein
  selbstsigniertes Cert+Key-Paar (RSA-2048, SubjectAltName für
  Hostname/localhost/127.0.0.1, Schlüssel 0600). `python -m
  services.sync_server --self-signed` erzeugt es bei Bedarf und startet den
  Server direkt mit TLS. `cryptography` wird lazy importiert; Tests
  ([tests/test_tls_certs.py](tests/test_tls_certs.py)) laufen auf CI und
  überspringen sauber, wo kein cryptography-Backend verfügbar ist.
- **Multi-User-Profile (Geräte-Profile)** - mehrere getrennte Datenbestände
  (je eigene DB + State) auf einem Gerät, umschaltbar über Neustarts hinweg.
  Toolkit-freier, vollautomatisch getesteter `ProfilesManager`
  ([app_core/profiles.py](app_core/profiles.py)) persistiert das aktive
  Profil in einer Pointer-Datei (Env `ALLTAGSHELFER_PROFILE` behält Vorrang);
  `bootstrap()` der Desktop-App berücksichtigt es beim Start. Über das neue
  Modul ([modules/profiles.py](modules/profiles.py)) sind
  `system.profiles` / `system.profile_create` / `system.profile_switch`
  per Assistent und UI nutzbar. Tests:
  [tests/test_profiles.py](tests/test_profiles.py). (Ein dedizierter
  Widget-Umschalter bleibt ein dünner UI-Folgeschritt.)
- **UI-Sichtbarkeit der neuen Funktionen (Desktop + Mobile)** - die zuvor
  nur über Capability/Assistent nutzbaren Features sind jetzt in der
  Oberfläche bedienbar: Such-Filter (Kategorie/Status/Zeitraum) im Such-Tab,
  Prioritäts- und Kategorie-Eingabe im Auftrags-Formular (samt Anzeige in der
  Liste), Kategorie-Filter in der Verträge-Liste, Beziehungs-Filter in der
  Kontakte-Liste sowie eine Tages-/Wochen-Agenda (`system.agenda`) als
  umschaltbare Dashboard-Ansicht ([gui.py](gui.py)).
- **Mobile-UI nachgezogen** - der Phone-Client erhält einen Such-Screen mit
  Filtern, einen Auftrags-Screen (Anlegen mit Priorität/Kategorie +
  Abhaken), einen Kontakte-Filter nach Beziehung, einen Kategorie-Filter in
  der Verträge-Liste und einen Wochen-Umschalter im Dashboard
  ([mobile/screens/more.py](mobile/screens/more.py),
  [mobile/screens/contracts.py](mobile/screens/contracts.py),
  [mobile/screens/dashboard.py](mobile/screens/dashboard.py)). Die Logik
  liegt in testbaren Helfern ([mobile/helpers.py](mobile/helpers.py)).

### Behoben

- **Mobile rief nicht existierende Capabilities auf** - `social.list_contacts`,
  `search.dashboard_summary`, `calendar.list_upcoming` und `inbox.list`
  existierten nie; die betroffenen Phone-Listen blieben dadurch stumm leer.
  Korrigiert auf `social.contacts`, `system.search`, `calendar.upcoming` und
  `inbox.proposals`. Ein neuer Guard-Test prüft fortan ohne Kivy, dass alle
  von Mobile-Screens genutzten Capabilities in der Registry existieren
  ([tests/test_mobile_screen_capabilities.py](tests/test_mobile_screen_capabilities.py)).
- **Play-Store-Compliance: Löschung, Data-Safety, Closed-Test** -
  Datenschutzerklärung dokumentiert jetzt den In-App-Voll-Löschpfad
  („Mehr → Alle Daten löschen"); die App ist lokal-first ohne
  Entwickler-Server/Konto. Data-Safety-Tests stellen sicher, dass die
  optionalen Online-Features (Gemini/IMAP) als optional + App-Funktionalität
  modelliert sind und nicht als Tracking/Sharing zählen. Neues Release-Gate
  `evaluate_closed_test_gate` ([tools/playstore_check.py](tools/playstore_check.py))
  verlangt vor „GO" sowohl ≥12 Tester/≥14 Tage als auch ein Closed-Test-
  Nachweisdokument; ein noch fehlender Nachweis ist im Pre-Merge-Check nur
  informativ (kein WARN/FAIL, damit `--strict` waehrend der Entwicklung
  nicht rot wird) - die GO-Entscheidung verlangt ihn dennoch.
  Tests: [tests/test_compliance_gates.py](tests/test_compliance_gates.py),
  [tests/test_data_safety.py](tests/test_data_safety.py).
- **POST_NOTIFICATIONS-Berechtigung (Play-Store, Android 13+)** -
  `buildozer.spec` und `playstore.yml` deklarieren jetzt
  `POST_NOTIFICATIONS` für die Erinnerungs-Benachrichtigungen. Wird die
  Berechtigung verweigert, bleibt die App nutzbar (der Notifier degradiert
  auf In-App/Print statt zu crashen). Keine sensible/verbotene Permission
  im Manifest. Tests:
  [tests/test_notifications_permission.py](tests/test_notifications_permission.py).
- **Tages-/Wochenübersicht (R1)** - neue Capability `system.agenda`
  ([modules/overview.py](modules/overview.py)) bündelt die Fristen aller
  aktiven Module und gruppiert sie nach Kalendertag (Standard: kommende 7
  Tage = Wochenübersicht); überfällige Einträge kommen separat zurück. Der
  `ModuleContext` exponiert dafür `collect_events`. Tests:
  [tests/test_overview.py](tests/test_overview.py).
- **Persistente Erinnerungs-Marker (R2)** - der `ProactiveScheduler`
  ([services/scheduler.py](services/scheduler.py)) speichert die bereits
  gemeldeten Erinnerungen atomar in `reminder_seen.json` im State-Ordner
  und lädt sie beim Start. Dadurch keine Doppelmeldung nach einem Neustart.
  Die Marker sind bewusst datumsfrei (`module_id` + Titel), sodass ein
  System-/Zeitzonensprung (DST) keine erneute Meldung auslöst; eine defekte
  State-Datei wird ignoriert. Tests:
  [tests/test_scheduler_reminders.py](tests/test_scheduler_reminders.py).
- **Prioritäten & Kategorie-Filter (R3)** - einmalige Aufträge haben jetzt
  eine Priorität (`hoch`/`mittel`/`normal`) und eine optionale Kategorie
  ([models.py](models.py), Schema-Migration v2→v3). `family.orders` sortiert
  nach Priorität und filtert optional nach Kategorie; `family.add_order`
  nimmt `priority`/`category` entgegen. Kategorie-/Beziehungs-Filter auch für
  `contracts.list` und `social.contacts`. Tests:
  [tests/test_priority_category.py](tests/test_priority_category.py).
- **Such-Filter (R4)** - `system.search` akzeptiert nun optionale Filter
  `date_from`/`date_to` (Zeitraum), `status` und `category`
  ([modules/search.py](modules/search.py)). Ein gesetzter Filter schliesst
  Quellen ohne das jeweilige Feld aus; bei gesetztem Filter entfaellt das
  2-Zeichen-Minimum fuer das Suchwort. Tests:
  [tests/test_search_filters.py](tests/test_search_filters.py).
- **Mehrsprachigkeit (i18n-Fundament)** - alle 24 EU-Amtssprachen sind
  als Locale-Datei angelegt ([locales/](locales/)). Vollstaendig
  uebersetzt: DE, EN, FR, ES, IT, NL, PL, PT; die uebrigen 16 Sprachen
  decken die Kern-UI (Navigation + Buttons) ab und fallen sonst auf
  Deutsch zurueck. Siehe [locales/README.md](locales/README.md).
- **Automatische Geraetesprache** - `detect_device_language()` in
  [services/i18n.py](services/i18n.py) erkennt die OS-Sprache (Android
  via pyjnius, Desktop via `locale`/Env). Der Settings-Wert
  `i18n.language = "auto"` aktiviert die automatische Wahl.
- **Sprachumschalter (Mobile)** - im "Mehr"-Screen
  ([mobile/screens/more.py](mobile/screens/more.py)); die Bottom-
  Navigation ist lokalisiert.
- **i18n-Wartungstool** - [tools/i18n_sync.py](tools/i18n_sync.py)
  prueft Key-Paritaet + Pflicht-Keys (`--check`, in der CI verankert)
  und zeigt die Abdeckung je Sprache (`--coverage`).
- **Voll-Loeschung der Nutzerdaten** (DSGVO Art. 17 / Play Store
  Data-Deletion) via [services/data_deletion.py](services/data_deletion.py)
  und `Database.wipe_all_data()`. Leert alle DB-Tabellen (mit VACUUM) und
  die Sandbox-Verzeichnisse. Mobile-UI: "Mehr" → "Alle Daten loeschen"
  mit ausdruecklicher Bestaetigung
  ([mobile/screens/more.py](mobile/screens/more.py)).
- **Data-Safety-Automatisierung** - [tools/data_safety.py](tools/data_safety.py)
  leitet die Play-"Data Safety"-Angaben aus den App-Fakten ab
  (`--generate`/`--markdown`) und prueft `playstore.yml` dagegen
  (`--check`, in der CI). Deckte eine Falschangabe auf (Firebase/Analytics
  im Mock, obwohl die App tracking-frei ist) - `playstore.yml` und der
  Sync-Mock sind nun wahrheitsgemaess (kein Sharing, kein SDK-Inventar).
- **Release-Checker erweitert** ([tools/playstore_check.py](tools/playstore_check.py))
  um `data_deletion`- und `i18n`-Checks.
- **Privacy-Policy-Hosting** - [tools/privacy_policy.py](tools/privacy_policy.py)
  rendert `legal/DATENSCHUTZ.md` zu einer self-contained, Pages-tauglichen
  HTML-Seite (`--build` → [site/](site/)) und prueft die
  Veroeffentlichungsreife (`--check`: offene Platzhalter, Platzhalter-URL;
  in der CI). GitHub-Pages-Deploy via
  [.github/workflows/pages.yml](.github/workflows/pages.yml) (manuell).
- **Store-Listing-Lokalisierungen** - [tools/store_listing.py](tools/store_listing.py)
  pflegt die `localizations` in `playstore.yml` (jetzt DE/EN/FR/ES/IT/NL/PL/PT)
  und setzt die Play-Laengenlimits durch (`--check`, in der CI;
  `--generate` mergt kuratierte Sprachen).
- **Mehrsprachige Rechtstexte (Mechanik)** - [services/legal.py](services/legal.py)
  loest Impressum/Datenschutz/AGB/Widerruf je Sprache auf und faellt auf
  Deutsch zurueck (`legal/<lang>/<DOK>.md`). Bewusst KEINE maschinelle
  Uebersetzung verbindlicher Rechtstexte; Coverage via
  `python -m tools.legal_status`.

## [0.10.0] - 2026-05-20

### Neu

- **Pricing-/Lizenz-System** ([services/licensing.py](services/licensing.py)).
  Fuenf Tiers: FREE, TRIAL (14 Tage), PRO_MONTHLY (6,99 EUR/Mo),
  PRO_ANNUAL (-20 %), PRO_FAMILY (Flat 12,99 EUR/Mo bis 5 Personen).
- **Enforcement-Gate** ([services/license_gate.py](services/license_gate.py)).
  Pre-Dispatch-Hook in `ModuleRegistry.dispatch` weist gesperrte
  Capabilities mit `tier_locked` ab. GUI markiert gesperrte Tabs mit
  `[Pro]`. Gemini-Client wird im FREE-Tier gar nicht erst initialisiert.
- **Ed25519-Lizenz-Token** ([services/license_token.py](services/license_token.py)).
  Offline-verifizierbarer Tamper-Schutz. Generator-CLI:
  [tools/gen_license.py](tools/gen_license.py).
- **Grandfathering-Migration** - Bestandsdaten beim Pricing-Launch
  werden einmalig markiert; Lesezugriff auf alle Module bleibt
  unbefristet, Pro-Features brauchen aber weiterhin ein Abo.
- **Pro-Aktivierungs-Flow mit Widerrufsverzicht** ([services/activation_flow.py](services/activation_flow.py)).
  Holt vor jeder Aktivierung die drei Bestaetigungen ein, die fuer das
  vorzeitige Erloeschen des 14-Tage-Widerrufsrechts (BGB §356 Abs. 5)
  noetig sind.
- **Legal-Templates** ([legal/](legal/)) - Vorlagen fuer Impressum,
  Datenschutz, AGB und Widerrufsbelehrung mit Platzhaltern.
- **Mobile-/CHF-Pricing** - 25 % Markup auf iOS/Android (App-Store-Cut),
  Konvertierungs-Helper fuer CHF mit 8,1 % CH-MwSt.

### Verifiziert

- 38 neue Tests in `TestLicensing` (Trial-Ablauf, Family-Cap, Grace-Period,
  Grandfathering, Token-Roundtrip + Tamper-Detection, Mobile-Markup,
  Widerrufsverzicht).

## [0.9.0] - 2026-05-19

### Neu

- **Android-Port** als zweite UI-Schicht (`mobile/`) auf Basis von
  **KivyMD**. Backend (Module, Registry, DB) wird 1:1 wiederverwendet.
- **Bottom-Navigation** mit 5 phone-optimierten Bereichen
  (Start, Vertraege, Finanzen, Termine, Mehr) statt 14 Desktop-Tabs.
- **Floating-Action-Button** auf allen Listen-Screens fuer Schnellanlage.
- **Material-3-Theme**, grosse Tap-Ziele (>=56dp), vertikale Listen
  statt Tabellen, Urgency-Farbcodierung fuer Fristen.
- **buildozer.spec** fuer Android-APK-Build via Buildozer/p4a
  (`arm64-v8a` + `armeabi-v7a`, API 33).
- **MOBILE.md** mit Build-Anleitung (WSL2/Ubuntu), Datenort-Erklaerung
  und Phone-UI-Patterns.
- **mobile/helpers.py** mit testbarer Pure-Logic
  (Currency-Format, days_until, relative_when, urgency_color, ...).
- 28 neue Unit-Tests in `tests/test_mobile_helpers.py`.

### Geaendert

- DB landet auf Android im sandboxed `user_data_dir` der App
  (kein anderer App-Zugriff moeglich - Datenschutz-Leitprinzip).

## [0.8.0] - 2026-05-19

### Neu

- **Soft-Delete (Papierkorb)** fuer Vertraege, Termine, Ausgaben, Kontakte
  und Haushaltsmitglieder: `*.delete` schiebt in den Papierkorb,
  `*.restore` holt zurueck, `*.purge` loescht endgueltig.
- **Aufgaben-Vorlagen** (`templates.add/list/apply/delete`) zur schnellen
  Instanzierung wiederkehrender Haushaltsaufgaben.
- **n:m-Notizverknuepfung** ueber `notes.add_attachment` und
  `notes.list_attachments` (eine Notiz kann an mehrere Entitaeten haengen).
- **Audit-Log** ueber Registry-Hook: alle destruktiven Capabilities werden
  mit Capability, Argumenten, Zeitstempel und Entity-ID persistiert.
- **Schema-Versionierung** via `PRAGMA user_version` mit Inline-Migration.
- **Backup-Verifikation**: `verify_backup()` oeffnet das Backup vor dem
  Bekanntgeben, defekte Sicherungen werden verworfen.
- **Rate-Limit** im HTTP-Sync-Server (Sliding-Window pro Client-IP).
- **Zentrales Logging** ueber `services.logging_setup` mit Rotation.
- **Backup-Schluessel** separat konfigurierbar (`backup.key`,
  `ALLTAGSHELFER_BACKUP_KEY`).
- **Integration-Tests** mit Mocks fuer SMTP/IMAP/OCR/Print sowie
  echtes TLS-Handshake-Beispiel fuer den Sync-Server.
- **Property-based Tests** (optional, ueber `hypothesis`).
- **Performance-Tests** zur Regressions-Erkennung.
- **Headless GUI-Smoke-Tests** ohne grafische Umgebung.

### Geaendert

- `services.escaping` zentralisiert Escape/Unescape fuer iCal und vCard.
- Default-DB-Pfad einheitlich `alltagshelfer.db` (CLI + GUI).
- `_cap_add` (Notes) erkennt `entity_id=0` korrekt (war truthiness-Bug).

### Korrigiert

- Cleanup verwaister Notizen erfolgt jetzt auf `purge` statt `delete`
  (Soft-Delete laesst Notizen erhalten - Restore funktioniert vollstaendig).

## [0.6.0] - 2026-05-19

### Neu

- **Google Gemini** als KI-Backend ueber provider-agnostische Schnittstelle
- **SQLCipher**-Verschluesselung der DB ueber `ALLTAGSHELFER_DB_KEY`
- **Mehrgeraete-Synchronisation** mit zwei Providern:
  - Datei-basiert (geteilter Ordner)
  - HTTP-Server (`python -m services.sync_server`)
- **Periodische Sync-Schleife** im Hintergrund, kompaktierter Log
- **Konfigurations-System**: Defaults < DB < Env-Vars
- **GUI-Modulverwaltung** mit persistenten Toggles
- **GUI-Einstellungen-Tab** fuer alle nicht-geheimen Werte
- **DayStructure** in DB persistiert
- **Threaded IMAP**-Abruf in der GUI
- **Robuste Gemini-Fehlerbehandlung** im Assistant
- **Streaming-Antworten** (zumindest fuer den reinen Text-Teil)
- **Operational**: pyproject.toml mit Pins, LICENSE, `__main__`, GitHub-Actions-CI

### Geaendert

- `Capability` liefert nur noch das Gemini-kompatible Schema (Anthropic entfernt)
- `has_capability` respektiert deaktivierte Module
- `CalendarRepository.list_upcoming` mutiert keine Objekte mehr (Kopien)
- Sync deckt jetzt Module A, B, C, D und E ab (zuvor nur D)
- `assistant_log` rotiert sich automatisch (Standard: 5000 Eintraege)

### Korrigiert

- Endlos-Rekursion im Sync-Hook (`SyncedRegistry` nutzt jetzt den
  Original-Dispatch)
- Mehrere mypy-Diagnosen zu loose typisierten Pfaden

## [0.5.0] - frueher

- Erstausbau mit Modul A, B, D, Posteingang, Dashboard, GUI
- Modul C (Kalender), Modul E (Soziale Pflege), DayStructure-Scaffold
- OCR-Stub, Proaktiver Scheduler, Person-Zuordnung
- Erste Tests
