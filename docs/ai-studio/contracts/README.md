# AI-Studio-Contracts (maschinenlesbar)

Diese Artefakte sind **aus dem echten Code generiert** und dienen als
verbindlicher Contract für einen Web-/Node-Re-Build in Google AI Studio Build
Mode (oder jede andere Portierung). Build Mode importiert kein bestehendes
Repository – diese Dateien geben ihm das Gerüst, **damit Capabilities und
Datenmodell 1:1 statt geraten** entstehen.

| Datei | Inhalt | Quelle |
| --- | --- | --- |
| `openapi.json` | OpenAPI 3.1 – je Capability ein `POST /api/<name>` mit Request-Body = Parameter-Schema, inkl. `x-destructive`/`x-internal` | `core.interface.ModuleRegistry.tool_schemas()` |
| `capabilities.json` | Vollständige Capability-Liste (Name, Modul, Beschreibung, Parameter, Flags) + Listen der destruktiven/internen Capabilities | `ModuleRegistry.all_capabilities()` |
| `schema.sql` | DDL des tatsächlichen SQLite-Schemas (alle Tabellen) | `sqlite_master` (aus `database.py`) |
| `schema.prisma` | Aus dem Schema abgeleitetes Prisma-Datenmodell (Näherung für Cloud SQL/Postgres) | `PRAGMA table_info` je Tabelle |

## Regenerieren

```bash
python -m tools.gen_ai_studio_contracts          # schreibt die vier Dateien
python -m tools.gen_ai_studio_contracts --check  # CI-Gate: exit 1 bei Drift
```

## Nutzung im Build Mode

1. Alle vier Dateien als **Attachments** hochladen (zusätzlich zu
   `ANFORDERUNGEN.md`, `UI_CONCEPT.md` und den Screenshots).
2. Build Mode anweisen, die Node-Endpunkte exakt nach `openapi.json` zu
   erzeugen und die Persistenz nach `schema.prisma`/`schema.sql` auf
   Cloud SQL/Postgres abzubilden.
3. `x-destructive: true` markiert Endpunkte, die ein Bestätigungs-/Audit-
   Verhalten brauchen (vgl. `ANFORDERUNGEN.md` FR-X-04, PA-06);
   `x-internal: true` sind nicht für das LLM/öffentliche API gedacht.

## Grenzen

- Das Prisma-Modell leitet **keine** Relationen (`@relation`) ab – die
  SQLite-Fremdschlüssel laufen über `ON DELETE SET NULL` (siehe
  [ARCHITECTURE.md](../../../ARCHITECTURE.md)) und sind vor dem Einsatz manuell
  zu ergänzen.
- Zeit-/Datumsfelder sind als `String` (ISO-8601 UTC) modelliert – bewusst,
  passend zur Persistenz (vgl. `ANFORDERUNGEN.md` PA-07/DA).
- Der Contract beschreibt das **Verhalten**, nicht die Tier-Sperren – die
  Lizenz-Logik (`services/license_gate.py`) ist orthogonal und beim Re-Build
  separat abzubilden (`ANFORDERUNGEN.md` §10).
