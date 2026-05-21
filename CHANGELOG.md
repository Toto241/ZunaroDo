# Changelog

Alle relevanten Aenderungen am Projekt - chronologisch absteigend.

## [Unreleased]

### Neu

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
