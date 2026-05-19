# Changelog

Alle relevanten Aenderungen am Projekt - chronologisch absteigend.

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
