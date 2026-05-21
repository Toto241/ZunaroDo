# Schema-Migrationen

Wenn die Anwendung startet, prueft sie `PRAGMA user_version`. Falls die
gefundene Version kleiner als `CURRENT_SCHEMA_VERSION` ist, laufen alle
Migrationen ab dieser Version automatisch durch. Datenverlust wird
vermieden, indem alle Migrationen *additiv* sind (neue Spalten/Indizes,
keine Drops).

## Version 1 - Basisschema

- Tabellen fuer Vertraege, Termine, Ausgaben, Kontakte, Familienmitglieder,
  Notizen, Einkaufsliste, Auftraege, Vorschlaege.
- Fremdschluessel mit `ON DELETE SET NULL` zwischen den Tabellen.

## Version 2 - Soft-Delete und Erweiterungen

Hinzugefuegt:

- `contracts.deleted_at` (TEXT, NULL)
- `expenses.deleted_at` (TEXT, NULL)
- `calendar_events.deleted_at` (TEXT, NULL)
- `social_contacts.deleted_at` (TEXT, NULL)
- `family_members.deleted_at` (TEXT, NULL)
- Tabelle `audit_log` (capability, args_json, entity_type, entity_id,
  created_at).
- Tabelle `task_templates` (title, interval_days, description).
- Tabelle `note_attachments` (note_id, entity_type, entity_id) -
  n:m-Verknuepfung.

Indizes:

- `idx_notes_attachment(entity_type, entity_id)`
- `idx_audit_log_created_at(created_at DESC)`

## Version 3 - Prioritaeten & Kategorien fuer Auftraege

Hinzugefuegt (additiv, beide via `_ensure_column`):

- `household_orders.priority` (TEXT, Default `'normal'`) - Werte
  `hoch` | `mittel` | `normal`. Steuert die Sortierung in `family.orders`.
- `household_orders.category` (TEXT, Default `''`) - frei waehlbare
  Kategorie zum Filtern (`family.orders` mit `category`).

Bestandszeilen erhalten die Defaults; der Migrations-Roundtrip ist in
`tests/test_priority_category.py` (`TestOrderSchemaMigration`) abgedeckt.

## Roundtrip-Tests

Jede Migration wird durch einen Test in `tests/test_smoke.py` abgedeckt,
der sicherstellt:

1. Eine frische DB enthaelt am Ende `CURRENT_SCHEMA_VERSION`.
2. Eine "alte" DB (Version 1) wird sauber auf Version 2 gezogen.
3. Vorhandene Datensaetze bleiben erhalten.

## Wann braucht es eine neue Migration?

- Neue Spalte? -> Migration.
- Neue Tabelle? -> Migration.
- Bestehende Spalte umbenennen oder Typ aendern? -> Migration **mit
  expliziter Backfill-Strategie**. Bitte vor dem Implementieren im Review
  abstimmen.
- Index hinzu? -> Migration.
- Nur Default-Wert in `models.py`? -> keine Migration noetig.

## Manuell auf eine bestimmte Version migrieren

Normalerweise unnoetig - der Startup macht das automatisch. Falls doch:

```python
from database import Database, _migrate_schema
db = Database("alltagshelfer.db")
_migrate_schema(db.conn)
```
