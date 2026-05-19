# Architektur - Alltagshelfer

Diese Datei beschreibt die Architektur in Schichten, nicht nach Modulen.
Ein neuer Beitragender soll nach 15 Minuten Lesen wissen, wo welche Art
Logik hingehoert.

## Leitprinzipien

1. **Datenschutz vor Komfort.** Daten bleiben lokal in einer SQLite-DB
   (optional SQLCipher-verschluesselt). Cloud-OCR ist abgeschaltet,
   das LLM (Google Gemini) sieht nur eine vom Nutzer freigegebene
   Auswahl an Capabilities und Antworten.
2. **Module sind steckbar.** Jedes Fachmodul implementiert
   `ModuleInterface` und meldet seine Faehigkeiten als `Capability`-Objekte
   an. Das Restsystem (LLM, GUI, Sync) interagiert nur ueber diese
   Capability-Schnittstelle - nie direkt mit Repos.
3. **Einseitige Abhaengigkeiten.** Module duerfen `services/*` und die
   Datenschicht nutzen. Services wissen nichts ueber Module. Die GUI
   ist passiv: sie ruft die Registry, die ruft Module.
4. **Nur Gemini als LLM.** Anthropic- oder OpenAI-Bindings sind
   bewusst nicht vorgesehen. Wer einen Drittanbieter benoetigt, schreibt
   einen eigenen Adapter, der `LlmProvider` implementiert.

## Schichten (aussen nach innen)

```
+--------------------------------------------------------+
|  Praesentation:  gui.py  (CTk)   |  __main__ / CLI     |
+--------------------------------------------------------+
|  Orchestrierung: core.interface (ModuleRegistry,       |
|                   ModuleContext, Capability)           |
+--------------------------------------------------------+
|  Module:         modules/contracts.py  modules/finance |
|                   modules/calendar.py  modules/social  |
|                   modules/family.py    modules/notes   |
|                   modules/inbox.py     modules/templates|
+--------------------------------------------------------+
|  Services:       services/output      services/backup  |
|                   services/sync       services/ical    |
|                   services/vcard      services/ocr     |
|                   services/print      services/config  |
|                   services/escaping   services/logging |
+--------------------------------------------------------+
|  Persistenz:     database.py (Repos)   models.py       |
+--------------------------------------------------------+
|  Storage:        SQLite / SQLCipher                    |
+--------------------------------------------------------+
```

## Schluesselbegriffe

### Capability

Eine `Capability` ist ein **vom LLM (und der GUI) aufrufbarer
Funktionseintrag**. Sie traegt:

- `name` - global eindeutiger Identifier, z.B. `contracts.add`.
- `description` - menschliche Erklaerung, wird ins LLM-Tool-Schema gemappt.
- `parameters` - JSON-Schema-Subset (Typen + `_required`-Flag).
- `handler` - aufrufbares Python-Callable, gibt ein `dict` zurueck.
- `destructive` - schreibend? Wird fuer Audit-Log und Permission-Checks
  verwendet.
- `internal` - nicht an das LLM weitergegeben (z.B. ICal-Import oder
  Cross-Modul-Cleanup).

### ModuleRegistry

Die Registry sammelt Capabilities aus allen geladenen Modulen, mappt sie
zu LLM-Tool-Schemas (`tool_schemas()`) und stellt einen einzigen
`dispatch(name, args) -> dict` zur Verfuegung. Hier sitzen:

- Permission-/Kategorie-Checks
- Audit-Hook fuer destruktive Calls (`set_audit_hook`)
- Sync-Hook (in `SyncedRegistry`-Wrapper) fuer die Replikation

### ModuleContext

Wird bei `register()` an jedes Modul gereicht und erlaubt Cross-Modul-
Aufrufe **ohne Direkt-Import** (`ctx.call("notes.cleanup_for_entity",
entity_type=..., entity_id=...)`). So bleibt die Modulgrenze sauber.

## Datenschicht und Migration

- `database.py` haelt fuer jede Entitaet ein Repository (`ContractRepository`,
  `ExpenseRepository`, ...). Repos kapseln SQL.
- `CURRENT_SCHEMA_VERSION` + `_migrate_schema()` fuehren idempotente
  Migrationen aus. Versions-Tracking laeuft ueber `PRAGMA user_version`.
- Soft-Delete: Tabellen tragen ein `deleted_at`-Feld; `list_all` filtert
  per Default auf "nicht geloescht", `list_deleted` zeigt den Papierkorb,
  `restore` und `purge` schliessen den Lebenszyklus.
- `ON DELETE SET NULL` fuer Fremdschluessel (z.B. `owner_id` auf
  family_members) wirkt erst nach **purge**, nicht nach Soft-Delete.

## Synchronisation

- Lamport-Clock-basiertes CRDT: jede destruktive Operation bekommt eine
  monotone Sequenznummer.
- `SyncedRegistry` umhuellt die echte Registry und exportiert
  Aenderungen in den konfigurierten `SyncProvider` (Datei-basiert oder
  HTTP).
- Konflikte werden last-writer-wins aufgeloest, wobei "writer" die
  hoechste Clock-Sequenz ist.

## Logging und Audit

- `services.logging_setup.configure_logging` setzt einen
  RotatingFileHandler unter `logs/` plus Konsole.
- Audit-Log via `AuditLogRepository` schreibt jeden erfolgreichen,
  destruktiven Aufruf mit Capability, Argumenten und (heuristisch
  extrahiertem) Entity-Bezug.

## Konfiguration

`services/config.py` liefert ein `AppConfig`-Dataclass aus drei Quellen
in fester Reihenfolge:

1. Defaults im Code (`DEFAULTS`).
2. `SettingsRepository` (DB) - via GUI editierbar.
3. Umgebungsvariablen (`ENV_MAP`) - haben Vorrang.

`SECRET_KEYS` werden **nie** in die DB geschrieben (API-Keys, Passwoerter),
nur per Env-Var oder Keyring entgegengenommen.

## Tests

- `tests/test_smoke.py` - Hauptregressionssuite (147 Tests),
  jedes Modul + Capability mindestens einmal abgedeckt.
- `tests/test_integration.py` - mockt SMTP/IMAP/OCR/Print sowie TLS.
- `tests/test_property.py` - optionale Hypothesis-Tests fuer Invarianten.
- `tests/test_performance.py` - Regressionsbudget fuer Hot-Pfade.
- `tests/test_gui_smoke.py` - Import-/Signatur-Smoke ohne Tk-Display.
- Coverage-Konfiguration in `.coveragerc`.

## Was hier *nicht* hingehoert

- Geschaefts-/Domain-Logik in der GUI (gehoert ins Modul).
- LLM-Aufrufe ausserhalb des Assistant-Layers (gehen ueber Registry).
- Direkter SQL-Zugriff aus einem Modul auf Tabellen eines anderen Moduls
  (gehoert hinter ein Capability- oder Repo-Interface).
