# Changelog

Alle relevanten Aenderungen am Projekt - chronologisch absteigend.

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
