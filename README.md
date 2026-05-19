# Alltagshelfer

Datenschutzfreundlicher Alltagsassistent für den deutschsprachigen Raum
mit **acht Fachmodulen**, einem **Dashboard**, **Google Gemini** als
optionalem KI-Backend, **Mehrgeräte-Synchronisation** (Datei oder HTTP,
optional HTTPS), **optionaler SQLCipher-Verschlüsselung**,
**Volltextsuche**, **CSV-Export**, **Online-Backup**, einem **CLI** und
einer **CustomTkinter-GUI** mit DE/EN-Lokalisierung.

## Schnellstart

```bash
pip install -r requirements.txt

# Konsolen-Demo (Offline-Modus, alles tut auch ohne Netz)
python main.py

# Mit alternativem Profil (eigene DB-Datei + State-Dir)
ALLTAGSHELFER_PROFILE=anna python main.py
# oder ueber den CLI-Wrapper
python __main__.py --profile anna

# GUI mit allen Tabs
python gui.py

# Subcommands ueber python __main__.py
python __main__.py --diagnose
python __main__.py --gui
python __main__.py --backup
python __main__.py --list-backups
python __main__.py --restore backups/alltagshelfer-20260519-185747.db
python __main__.py --export
python __main__.py --import ausgaben/export-20260519-185747
python __main__.py --sync-server --port 5151
```

### Optionale Erweiterungen

```bash
# Google Gemini als KI-Backend
pip install google-generativeai
GOOGLE_API_KEY=... python gui.py

# Verschluesselte DB (SQLCipher)
pip install sqlcipher3-binary
ALLTAGSHELFER_DB_KEY=mein-passwort python gui.py

# Mehrgeraete-Sync via geteiltem Ordner
ALLTAGSHELFER_SYNC_DIR=C:\Users\me\Dropbox\alltagshelfer python gui.py

# Oder via HTTP-Sync-Server
python __main__.py --sync-server --port 5151
ALLTAGSHELFER_SYNC_URL=http://server:5151 python gui.py

# Server mit TLS und Token
python __main__.py --sync-server --port 5151 \
  --cert server.pem --key server.key \
  --token "geheim"

# Mail per IMAP holen
ALLTAGSHELFER_IMAP_HOST=imap.example.com \
ALLTAGSHELFER_IMAP_USER=... \
ALLTAGSHELFER_IMAP_PASS=... \
python gui.py

# OCR fuer Kassenbons (Tesseract ODER easyocr)
pip install pytesseract Pillow
# oder
pip install easyocr
```

Tests: `python -m unittest discover tests` — 80+ Tests grün.

## Module (acht aktiv)

| Modul | Name | Aufgabe |
| --- | --- | --- |
| A | Vertrags- & Fristenmanager | Verträge, Kündigungsfristen, **Kündigungsschreiben** (PDF + Mail + Druck), Preisänderungen, **Lösch-Capability**, Person-Zuordnung |
| B | Finanz-Cockpit | Ausgaben, monatliche Belastung, Aggregate pro Person/Kategorie, **Preisgedächtnis**, OCR, Lösch-Capability |
| C | Termine & Kalender | Termine, Garantien, TÜV, Steuerfristen, Geburtstage; Kategorie-Whitelist; Recurrence-Validierung |
| D | Familie & Haushalt | Mitglieder (mit Geburtstag), Aufgaben (Rotation mit **Catch-Up** verpasster Zyklen), Aufträge, Einkaufsliste, Lösch-Capability |
| E | Soziale Pflege | Kontakte mit Rhythmus, LLM-generierter Nachrichten-Entwurf, Lösch-Capability |
| – | Tagesstruktur | Energie-Tagebuch (persistiert), einfache Empfehlung |
| – | Posteingang | Mail-Analyse regelbasiert + LLM-basiert, `.eml`-Import, IMAP, zentrale Vorschlags-Ablage, **Inline-Editor** für Vorschläge |
| – | Volltextsuche | `system.search` quer durch Verträge/Ausgaben/Termine/Familie/Aufträge/Kontakte/Vorschläge |
| – | Statistiken & Trends | `stats.expenses_per_month`, `stats.expenses_per_category`, `stats.contracts_overview`, `stats.yearly_summary`, **`stats.export_yearly_pdf`** |

GUI hat dafür einen eigenen **Statistiken-Tab** mit Canvas-Bar-Chart über die letzten 12 Monate, Vertragsübersicht und Jahressumme.

Außerdem stehen drei Standard-Export-Capabilities zur Verfügung — alle ohne externe Pakete, alles lokal:

- `calendar.export_ical(path)` → `.ics` (RFC 5545), in Google/Apple/Outlook/Thunderbird importierbar
- `social.export_vcard(path)` → `.vcf` (RFC 6350 v3.0), in jedes Adressbuch importierbar
- `stats.export_yearly_pdf(path, year)` → druckbarer PDF-Jahresbericht (via fpdf2)

## Die drei Schnittstellen

1. **Front-End ↔ Modul** – `ModuleRegistry.dispatch(name, args)`
2. **Modul ↔ Modul** – `ModuleContext.call(...)` (lose Kopplung über die Registry, mit Re-Entry-Schutz im Sync-Hook)
3. **Dashboard** – `ModuleRegistry.collect_events(...)` aggregiert Events aller Module chronologisch

Weitere Detail-Methoden auf der Registry: `get_capability(name)` (für dynamische Formulare in der GUI), `destructive_capability_names()` (Confirm-Dialog im Assistant), `module_states()`, `set_module_enabled()`.

## Google Gemini

[services/gemini.py](services/gemini.py) implementiert das LLM-Backend hinter der provider-neutralen [services/llm.py](services/llm.py). Aktiv, sobald `GOOGLE_API_KEY` (oder `GEMINI_API_KEY`) gesetzt UND `google-generativeai` installiert ist; sonst läuft der Offline-Modus mit regelbasiertem Intent-Router.

Implementierte LLM-Features:

- **Tool-Use-Schleife** mit Funktionsaufrufen über `function_declarations`
- **Konversationsverlauf** wird zwischen Aufrufen erhalten (`Assistant._history`)
- **Streaming** für Text-Teile (im Stream-Callback)
- **Token-Verbrauch** wird gemessen (`Assistant.token_usage`)
- **Confirm-Callback** vor destruktiven Capabilities
- **Robuste Fehlerbehandlung** — Netz/Rate-Limit liefert eine Nutzer-Meldung statt Crash
- **Halluzinations-Schutz** im Inbox-Modul: LLM-Vorschläge werden gegen eine Allowlist und das Pflichtparameter-Schema validiert, bevor sie in der Ablage landen

## Mehrgeräte-Synchronisation

Zwei austauschbare Provider, beide implementieren dieselbe kleine Schnittstelle:

- **FileSyncProvider** – Event-Log in einem geteilten Ordner (z. B. Dropbox/OneDrive/Netzlaufwerk).
- **HttpSyncProvider** – HTTP/HTTPS-Sync gegen [services/sync_server.py](services/sync_server.py).

Architektur:

```text
geteilter Speicherort/
└── sync_events.jsonl   # eine JSON-Zeile pro Mutation mit Geräte-UUID

lokales Profil/
├── device_id           # eigene UUID (einmalig erzeugt)
└── sync_seen.json      # bereits angewendete Event-IDs (atomar geschrieben)
```

Standard-`DEFAULT_SYNCED_CAPABILITIES` umfasst alle relevanten Mutationen aus Modulen A–E (Verträge, Ausgaben, Termine, Familie/Aufgaben/Aufträge/Einkaufsliste, Kontakte). Re-Entry-Schutz: nested Aufrufe innerhalb eines bereits geloggten synced Calls werden nicht doppelt geschrieben — der äußere Aufruf trägt den Effekt beim Replay zuverlässig nach.

Server-Features:

- **Periodischer Hintergrund-Worker** (`PeriodicSyncWorker`) holt fremde Events alle `sync.interval_seconds` Sekunden
- **Automatische Log-Kompaktierung** auf Server- und Client-Seite (`MAX_LOG_LINES`)
- **Bearer-Token** über `--token` (oder `ALLTAGSHELFER_SYNC_TOKEN`)
- **TLS** über `--cert PATH --key PATH`
- **Warnung** beim Start ohne Token auf öffentlicher Bind-Adresse

## SQLCipher-Verschlüsselung

[database.py](database.py) wählt automatisch zwischen Klartext und SQLCipher:

- `ALLTAGSHELFER_DB_KEY` nicht gesetzt → Klartext (Default)
- Key gesetzt + `sqlcipher3` installiert → verschlüsselt
- Key gesetzt + `sqlcipher3` fehlt → harter Fehler (kein stilles Unverschlüsselt-Fallback)

Der Schlüssel wird als Hex-Form `x'<hex>'` an `PRAGMA key` übergeben — keine Quote/Backslash-Probleme. Mindestlänge 8 Zeichen, NUL-Bytes werden abgelehnt.

**Online-Backup** ([services/backup.py](services/backup.py)):

- Plain SQLite: SQLite-eigene `Connection.backup()`-API (sicher während Schreiboperationen)
- SQLCipher: `ATTACH DATABASE ... KEY '...'; SELECT sqlcipher_export(...)` — das Backup ist seinerseits eine verschlüsselte SQLCipher-Datei mit demselben (oder einem neuen) Schlüssel

## CLI-Subcommands

```text
python __main__.py [keine Args]   Konsolen-Demo (main.py)
                  --profile <n>   globales Flag - waehlt das aktive Profil
                  --gui           startet die GUI
                  --diagnose      Statusbericht (Plattform, Pakete, OCR-Engines)
                  --sync-server   HTTP/HTTPS-Sync-Server starten
                  --backup [pfad] DB online sichern
                  --restore <pfad> DB wiederherstellen (App muss aus sein)
                  --list-backups [verz]  Backups anzeigen
                  --list-profiles erkennbare Profile auflisten
                  --export [verz] CSV-Export aller Entitäten
                  --import <verz> CSV-Import aus einem Export-Verzeichnis
```

## Multi-User-Profile

Pro Profil eine eigene DB-Datei + eigenes State-Verzeichnis ([services/profile.py](services/profile.py)). Familienmitglieder können auf demselben Rechner getrennte Daten halten.

- Default: alle bisherigen Dateinamen bleiben (`alltagshelfer_demo.db`, `.alltagshelfer-state/`)
- Profil `anna`: `alltagshelfer_demo_anna.db`, `.alltagshelfer-state-anna/`
- Aktivierung per Umgebungsvariable (`ALLTAGSHELFER_PROFILE=anna`) oder CLI-Flag (`--profile anna`)
- GUI zeigt das aktive Profil in der Sidebar an
- `--list-profiles` listet erkennbare Profile (anhand vorhandener State-Verzeichnisse)
- Profilnamen werden auf `[A-Za-z0-9_-]` reduziert und auf 32 Zeichen begrenzt

## Zeitstempel & UTC

Alle internen Zeitstempel (`created_at`, `updated_at`, `changed_at` etc.) werden seit Version 0.7 in UTC mit ISO-Format mit `+00:00`-Suffix gespeichert ([database.py:_now_utc_iso](database.py)). Sync-Events benutzen ebenfalls UTC — damit sind alle Timestamps zonenunabhängig vergleichbar und über Geräte hinweg sortierbar.

## CSV-Export und -Import

[services/export.py](services/export.py) schreibt je eine CSV pro Entität (`contracts.csv`, `expenses.csv`, `calendar.csv`, `social.csv`, `family.csv`). Format: UTF-8-BOM + Strichpunkt → Excel-DE erkennt Spalten ohne Konfiguration. Datumsfelder im ISO-Format.

[services/import_csv.py](services/import_csv.py) ist der Spiegel: liest dieselben CSV-Dateien aus einem Verzeichnis und legt die Einträge an. Die ID-Spalte wird ignoriert — alles bekommt neue IDs. Ungültige Datumsangaben landen als `NULL`, statt den Import abzubrechen. Für einen exakten 1:1-Round-Trip ist `--backup`/`--restore` der bessere Weg.

## Auto-Backup

[services/backup.py:AutoBackupWorker](services/backup.py) zieht periodisch ein Backup und räumt alte Snapshots automatisch auf. Konfigurierbar in den App-Settings:

- `backup.auto_enabled` — true/false (Default: false)
- `backup.directory` — Zielverzeichnis (Default: `backups`)
- `backup.retention_count` — Anzahl Backups, die behalten werden (Default: 10)
- `backup.interval_hours` — Intervall in Stunden (Default: 24)

Im GUI-Daten-Tab steht zusätzlich ein „Backup jetzt erstellen"-Button.

## Onboarding

Beim ersten Start einer neuen DB zeigt die GUI einen Dialog mit zwei Optionen:

- „Beispieldaten laden" — bringt 2 Verträge, 3 Familienmitglieder und ein paar Termine mit
- „Leer starten" — komplett leere DB, der Nutzer trägt selbst ein

Vorher wurden Demo-Daten ungefragt automatisch eingespielt.

## Volltextsuche

`system.search(query, limit=50)` durchsucht alle Repositories (Verträge, Ausgaben, Termine, Mitglieder, Aufträge, Kontakte, Vorschläge) und liefert vereinheitlichte Treffer mit `source`/`entity_id`/`title`/`detail`. Mindestlänge 2 Zeichen.

## Statistiken & Trends

[modules/statistics.py](modules/statistics.py) liefert einfache Aggregate, ohne eine Diagramm-Library zu brauchen:

- `stats.expenses_per_month` — Summe pro Monat für die letzten N Monate
- `stats.expenses_per_category` — Aggregat pro Kategorie für ein Jahr
- `stats.contracts_overview` — Anzahl, Monats-/Jahressumme, Top-3-Kostentreiber
- `stats.yearly_summary` — Jahresüberblick mit Top-Kategorien und Monatsdurchschnitt

## Internationalisierung

[services/i18n.py](services/i18n.py) lädt Sprachdateien aus [locales/](locales/):

- `de.json` — Standardsprache mit ~80 Keys
- `en.json` — Englisch-Fallback mit denselben Keys

Spracheinstellung über `i18n.language` in den App-Settings (Default `de`). Fallback-Kette: angeforderte Sprache → DE → Key selbst. Unbekannte Sprachen fallen auf DE zurück.

Aktuell übersetzt: Tab-Labels, Sidebar, Dashboard, Suche, Verlauf, Chat-Bubbles, Settings-Texte, Proposal-Editor, Modul-Verwaltung, Inbox-Aktionen, **Verträge-Formular**, **Finanzen-Formular**, **Familie (alle vier Sub-Tabs inkl. Mitglieder, Aufgaben, Aufträge, Einkaufsliste)**, sämtliche `common.*`-/`form.*`-/`action.*`-Buttons (rund 100 Strings).

## Proaktive Benachrichtigungen

[services/scheduler.py](services/scheduler.py) prüft im Hintergrund (APScheduler oder Thread-Fallback) regelmäßig `registry.collect_events()` und schickt Desktop-Notifikationen (plyer mit Fallback) für anstehende Ereignisse innerhalb `notify.warn_within_days`.

## GUI-Tabs (zwölf)

```text
Dashboard – Vertraege – Familie – Finanzen – Kalender – Sozial
   – Posteingang – Statistiken – Daten – Assistent – Suche – Verlauf
   – Module – Einstellungen
```

Bemerkenswerte Features:

- **Posteingang**: IMAP-Abruf im Worker-Thread (kein Einfrieren), Inline-Editor für Vorschläge mit form-generierten Feldern aus dem Capability-Schema
- **Statistiken**: Bar-Chart der letzten 12 Monate über `tk.Canvas` (keine Diagramm-Library nötig), Vertragsübersicht, Jahressumme
- **Daten**: Backup/Export/Import via Buttons, Anzeige des aktiven Profils, Datei-Picker für CSV-Import
- **Module**: Switches pro Modul, persistiert in der DB
- **Einstellungen**: alle nicht-geheimen Konfig-Werte editierbar; Geheimnisse (API-Keys etc.) ausschließlich per Env-Var
- **Verlauf**: zeigt `assistant_log` (User vs. Assistent)
- **Suche**: einheitliche Trefferdarstellung mit Quellen-Tag

## Konfigurations-System

[services/config.py](services/config.py): Defaults < DB-Werte < Umgebungsvariablen. Geheime Felder werden nicht persistiert. Konfigurierbar sind unter anderem:

- `gemini.api_key`, `gemini.model`, `gemini.max_iterations`, `gemini.max_tokens`
- `imap.host`/`user`/`pass`/`folder`
- `smtp.host`/`port`/`user`/`pass`/`sender`/`starttls`
- `sync.dir`, `sync.enabled`, `sync.interval_seconds`
- `db.key`, `notify.warn_within_days`, `i18n.language`

## Projektstruktur

```text
.
├── models.py
├── database.py                 SQLite (+ optional SQLCipher) + Thread-Safety
├── core/interface.py           Drei Schnittstellen + Enable/Disable + get_capability
├── modules/                    Acht Fachmodule
├── services/
│   ├── llm.py                  Provider-Vertrag (provider-agnostisch)
│   ├── gemini.py               Gemini-Client
│   ├── sync.py                 Datei- und HTTP-Sync-Provider + Worker
│   ├── sync_server.py          HTTP/HTTPS-Sync-Server
│   ├── output.py               PDF + Mail-Entwurf + SMTP + Druck
│   ├── ocr.py                  Tesseract + easyocr (lokal, keine Cloud)
│   ├── notifier.py             Desktop-Notifikation
│   ├── scheduler.py            Proaktive Hintergrund-Checks
│   ├── backup.py               Online-Backup (Plain + SQLCipher) + AutoBackupWorker
│   ├── export.py               CSV-Export aller Entitäten
│   ├── import_csv.py           CSV-Import (Spiegel zum Export)
│   ├── ical.py                 iCalendar-Export (.ics)
│   ├── vcard.py                vCard-Export (.vcf)
│   ├── reports.py              PDF-Jahresbericht (fpdf2)
│   ├── config.py               Konfigurations-System
│   └── i18n.py                 Lokalisierung
├── locales/                    de.json, en.json (~100 Keys)
├── assistant.py                LLM-agnostisch
├── gui.py                      CustomTkinter-GUI mit zwölf Tabs
├── main.py                     Konsolen-Demo
├── __main__.py                 CLI-Subcommands
├── diagnose.py                 Status-Bericht
├── tests/test_smoke.py         80+ Tests
└── requirements.txt
```

## Status & bewusst offen geblieben

- **DST/Timezone-Audit** — Sync-Timestamps sind bereits UTC; weitere Date-Felder sind lokale Zeit (für Single-User unkritisch)
- **Multi-User-Profile auf einem Gerät** — keine getrennten Profile vorgesehen
- **i18n-Vollausbau** — Formularfeld-Labels in den einzelnen Modul-Tabs und Capability-Descriptions sind weiterhin hartcodiert deutsch
- **Eigenes TLS für eingebetteten Server** — Zertifikate via `--cert/--key` werden unterstützt; Erstellung übernimmt der Nutzer (z. B. via `openssl req`)
