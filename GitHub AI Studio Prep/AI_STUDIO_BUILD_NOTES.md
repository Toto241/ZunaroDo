# AI Studio Build – Hinweise

Diese Datei passt den Handoff an die realen Fähigkeiten und Grenzen von Google AI Studio Build Mode an (Repository Toto241/ZunaroDo).

## Stack-Kompatibilität

- Empfohlenes Ziel: Antigravity (Arbeit am bestehenden Code – siehe Hinweise)
- Modell/Kontext: Gemini 3 Pro, ~1 Mio. Token Kontextfenster (Gemini 2.5 Pro bis 2 Mio.)
- Frontend: nicht erkannt — kein Frontend erkannt (Default React + Vite)
- Backend: Python — nicht direkt abbildbar (nur Node.js verfügbar)
- Persistenz: relational (auf Cloud SQL abbilden)
- Starter-Tier-Deploy (bis 2 Apps ohne Billing): eher nicht – Billing/GCP-Projekt nötig

## Stack im Prompt pinnen (gegen halluzinierte Pakete)

- customtkinter: 5.2.0
- cryptography: 42.0.0

## Zusätzlich anzuhängende Kontext-Artefakte

- Dockerfile — Container-Setup (Laufzeit-/Service-Kontext)
- docs/ai-studio/contracts/openapi.json — API-Contract (OpenAPI) (API-Contract als Attachment beilegen)
- docs/ai-studio/contracts/schema.prisma — Datenmodell (Prisma) (Datenmodell als Attachment beilegen)

## Empfohlene AI Chips

- keine spezifischen AI Chips empfohlen

## Empfohlene Build-Mode-Tools

- keine spezifischen Build-Mode-Tools empfohlen

## Design-Referenzen (Sketch-Upload / Annotation Mode)

- keine erkannt

## Verhaltens-Spezifikationen (aus Tests – beim Re-Build erhalten)

- tests/__init__.py
- tests/concept/__init__.py
- tests/concept/matrix.py
- tests/concept/pairwise.py
- tests/concept/roles.py
- tests/concept/test_build_status.py
- tests/concept/test_control_panel.py
- tests/concept/test_dashboard_generator.py
- tests/concept/test_gitignore_completeness.py
- tests/concept/test_gui_free_tier_boot.py
- tests/concept/test_gui_refresh_guards.py
- tests/concept/test_gui_widget_guards.py
- tests/concept/test_md_to_html.py
- tests/concept/test_members_scenarios.py
- tests/concept/test_negative_inputs.py

## Wichtige Hinweise

- Kein eindeutiges Frontend erkannt – Build Mode erzeugt standardmäßig React + Vite.
- Desktop-/Nicht-Web-Stack erkannt (CustomTkinter) – Build Mode erzeugt ausschließlich Web-Apps. Dieses Repo ist kein direkter Build-Mode-Kandidat: entweder als Web-App neu konzipieren oder den Handoff an einen code-fähigen Agenten (Google Antigravity, Claude/Codex/Gemini CLI) geben, der das bestehende Repo bearbeitet.
- Build Mode bietet als Server-Runtime nur Node.js – ein Python-Backend müsste in Node neu umgesetzt oder durch client-/serverlose Logik ersetzt werden.
- Persistenz erkannt (relational (auf Cloud SQL abbilden)) – auf den Build-Mode-Pfad (Firestore/Cloud SQL) abbilden.
- Zusätzlich als Attachment anhängen: Dockerfile, docs/ai-studio/contracts/openapi.json, docs/ai-studio/contracts/schema.prisma.
- Vorhandene Tests definieren erwartetes Verhalten – dieses beim Re-Build erhalten.
- Dieses Repo ist nur eingeschränkt ein Build-Mode-Kandidat. Empfohlene Alternative: Google Antigravity (agenten-/repo-zentriert, arbeitet am bestehenden Code; AI Studio kann seit I/O 2026 direkt dorthin exportieren) oder Firebase Studio (kann bestehende Repos importieren).
- Build Mode importiert keine bestehenden Repositories – dies ist ein Re-Build-mit-Kontext-Handoff, kein Code-Import.

- `GEMINI_API_KEY` wird in Build Mode automatisch als server-seitiges Secret gesetzt – nicht in den Client legen.
- Secrets werden beim GitHub-Export nicht mitexportiert; nach ZIP-Download `.env` lokal neu setzen.
- Ein „System Instructions"-Feld ist im Build Mode nicht gesichert vorhanden – die Kernregeln stehen daher zusätzlich im Prompt-Kopf.
- Build Mode baut standardmäßig React + Vite – beim externen Deploy (Netlify/Vercel) gegen den „weißen Bildschirm" in `vite.config.ts` `base: '/'` setzen.
- Laufzeit der erzeugten App: Gemini-Aufrufe brauchen für neue Konten Prepaid-Billing (seit 23.03.2026); Quoten gelten pro Google-Cloud-Projekt (nicht pro Key). 429/RESOURCE_EXHAUSTED mit exponentiellem Backoff abfangen.

## Datenmodelle / API-Contracts (eingebettet)

### Dockerfile (Container-Setup)

```
# Dockerfile - nur fuer den Sync-Server.
#
# Die Desktop-GUI laeuft NICHT im Container (kein Display).
# Der Container betreibt ausschliesslich `python -m services.sync_server`.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build-Tools fuer optionale Native-Pakete (sqlcipher3, cryptography)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libsqlcipher-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sync-Daten landen in /data und werden ueber ein Volume bereitgestellt
RUN mkdir -p /data
VOLUME ["/data"]

ENV ALLTAGSHELFER_SYNC_DIR=/data

EXPOSE 5151

# Healthcheck ueber GET /health (siehe sync_server.py)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        sys.exit(0 if urllib.request.urlopen('http://localhost:5151/health',timeout=3).status==200 else 1)" \
        || exit 1

CMD ["python", "-m", "services.sync_server", "--host", "0.0.0.0", "--port", "5151", "--log", "/data/sync_events.jsonl"]

```

### docs/ai-studio/contracts/openapi.json (API-Contract (OpenAPI))

```
{
  "openapi": "3.1.0",
  "info": {
    "title": "ZunaroDo Capability API",
    "version": "1.0.0",
    "description": "Aus core.interface.ModuleRegistry generierter Capability-Contract. Jede Capability ist ein einzelner Dispatch-Aufruf (ModuleRegistry.dispatch) und wird hier als POST-Endpunkt abgebildet. Quelle der Wahrheit ist der Code; diese Datei via tools/gen_ai_studio_contracts.py erzeugen."
  },
  "servers": [
    {
      "url": "/",
      "description": "App-Backend"
    }
  ],
  "paths": {
    "/api/calendar.add_event": {
      "post": {
        "operationId": "calendar_add_event",
        "summary": "Legt einen Termin an (einmalig oder wiederkehrend).",
        "tags": [
          "calendar"
        ],
        "x-destructive": false,
        "x-internal": false,
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "title": {
                    "type": "string",
                    "description": "Bezeichnung des Termins"
                  },
                  "due_date": {
                    "type": "string",
                    "description": "Datum ISO (YYYY-MM-DD)"
                  },
                  "category": {
                    "type": "string",
                    "description": "termin, garantie, tuev, steuer, geburtstag, sonstiges"
                  },
                  "description": {
                    "type": "string",
                    "description": "Details"
                  },
                  "recurrence_days": {
                    "type": "integer",
                    "description": "Wiederholung in Tagen (z.B. 365 = jaehrlich)"
                  },
                  "person_id": {
                    "type": "integer",
                    "description": "Optional: betroffene Person (siehe family.members)"
                  }
                },
                "required": [
                  "title",
                  "due_date"
                ]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Ergebnis-Dict der Capability.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          },
          "402": {
            "description": "tier_locked - Capability im aktuellen Tier gesperrt."
          },
          "400": {
            "description": "Validierungsfehler (error-Feld)."
          }
        }
      }
    },
    "/api/calendar.delete_event": {
      "post": {
        "operationId": "calendar_delete_event",
        "summary": "Verschiebt einen Termin in den Papierkorb. Restore via calendar.restore_event; endgueltig erst via calendar.purge_event.",
        "tags": [
          "calendar"
        ],
        "x-destructive": true,
        "x-internal": false,
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "event_id": {
                    "type": "integer",
                    "description": "ID des Termins"
                  }
                },
                "required": [
                  "event_id"
                ]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Ergebnis-Dict der Capability.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          },
          "402": {
            "description": "tier_locked - Capability im aktuellen Tier gesperrt."
          },
          "400": {
            "description": "Validierungsfehler (error-Feld)."
          }
        }
      }
    },
    "/api/calendar.export_ical": {
      "post": {
        "operationId": "calendar_export_ical",
        "summary": "Exportiert alle Termine als iCalendar-Datei (.ics), die in jeden gaengigen Kalender importiert werden kann.",
        "tags": [
          "calendar"
        ],
        "x-destructive": false,
        "x-internal": false,
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "description": "Zielpfad (sollte auf .ics enden)"
                  }
                },
                "required": [
                  "path"
                ]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Ergebnis-Dict der Capability.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          },
          "402": {
            "description": "tier_locked - Capability im aktuellen Tier gesperrt."
          },
          "400": {
            "description": "Validierungsfehler (error-Feld)."
          }
        }
      }
    },
    "/api/calendar.import_ical": {
      "post": {
        "operationId": "calendar_import_ical",
        "summary": "Liest eine iCalendar-Datei (.ics) und legt die enthaltenen Termine an. Bestehende Termine werden NICHT veraendert - es entstehen neue Eintraege.",
        "tags": [
          "calendar"
        ],
        "x-destructive": true,
        "x-internal": true,
        "requestBody": {
          "required": true,
          "content": {
            "appl
… (gekürzt)
```

### docs/ai-studio/contracts/schema.prisma (Datenmodell (Prisma))

```
// Aus dem SQLite-Schema (database.py) abgeleitetes Prisma-Modell -
// NAEHERUNG fuer die Cloud-SQL-/Postgres-Abbildung im Build Mode.
// Beziehungen (@relation) sind bewusst NICHT abgeleitet (SQLite-
// FKs ueber ON DELETE SET NULL, siehe ARCHITECTURE.md) und vor dem
// Einsatz manuell zu ergaenzen. Generiert via tools/gen_ai_studio_contracts.py.

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model AppSettings {
  key String @id
  value String?
  updated_at String?

  @@map("app_settings")
}

model AssistantLog {
  id Int @id @default(autoincrement())
  role String?
  content String?
  created_at String?

  @@map("assistant_log")
}

model AuditLog {
  id Int @id @default(autoincrement())
  action String
  entity_type String?
  entity_id Int?
  details String?
  actor String?
  created_at String?

  @@map("audit_log")
}

model CalendarEvents {
  id Int @id @default(autoincrement())
  title String
  due_date String
  category String?
  description String?
  recurrence_days Int?
  person_id Int?
  created_at String?
  deleted_at String?

  @@map("calendar_events")
}

model Contracts {
  id Int @id @default(autoincrement())
  name String
  category String
  provider String?
  customer_number String?
  start_date String?
  minimum_term_months Int?
  notice_period_months Int?
  auto_renew_months Int?
  monthly_cost Float?
  currency String?
  notes String?
  status String?
  owner_id Int?
  created_at String?
  updated_at String?
  deleted_at String?

  @@map("contracts")
}

model DayEntries {
  id Int @id @default(autoincrement())
  day String
  level Int
  note String?
  created_at String?

  @@map("day_entries")
}

model Expenses {
  id Int @id @default(autoincrement())
  description String
  amount Float
  category String?
  spent_on String?
  owner_id Int?
  created_at String?
  deleted_at String?

  @@map("expenses")
}

model FamilyMembers {
  id Int @id @default(autoincrement())
  name String
  role String?
  birthday String?
  created_at String?
  deleted_at String?

  @@map("family_members")
}

model HouseholdOrders {
  id Int @id @default(autoincrement())
  title String
  assignee_id Int?
  due_date String?
  description String?
  status String?
  priority String?
  category String?
  created_at String?
  deleted_at String?

  @@map("household_orders")
}

model HouseholdTasks {
  id Int @id @default(autoincrement())
  title String
  interval_days Int?
  next_due String?
  current_index Int?
  created_at String?

  @@map("household_tasks")
}

model ModuleStates {
  module_id String @id
  enabled Int
  updated_at String?

  @@map("module_states")
}

model NoteAttachments {
  id Int @id @default(autoincrement())
  note_id Int
  entity_type String
  entity_id Int
  created_at String?

  @@map("note_attachments")
}

model Notes {
  id Int @id @default(autoincrement())
  title String
  content String?
  entity_type String?
  entity_id Int?
  created_at String?
  updated_at String?
  deleted_at String?

  @@map("notes")
}

model PriceHistory {
  id Int @id @default(autoincrement())
  contract_id Int
  old_cost Float?
  new_cost Float?
  changed_at String?

  @@map("price_history")
}

model PriceMemory {
  id Int @id @default(autoincrement())
  product String
  last_price Float?
  last_seen String?
  category String?
  created_at String?

  @@map("price_memory")
}

model Proposals {
  id Int @id @default(autoincrement())
  source String?
  summary String?
  target_capability String?
  payload String?
  status String?
  created_at String?

  @@map("proposals")
}

model ShoppingItems {
  id Int @id @default(autoincrement())
  name String
  quantity String?
  added_by_id Int?
  bought Int?
  created_at String?

  @@map("shopping_items")
}

model SocialContacts {
  id Int @id @default(autoincrement())
  name String
  relation String?
  cadence_days Int?
  last_contacted String?
  notes String?
  created_at String?
  deleted_at String?

  @@map("social_contacts")
}

model TaskRotation {
  id Int @id @default(autoincrement())
  task_id Int
  member_id Int
  position Int

  @@map("task_rotation")
}

model TaskTemplates {
  id Int @id @default(autoincrement())
  title String
  interval_days Int
  description String?
  created_at String?

  @@map("task_templates")
}

```

## Akzeptanzkriterien (aus Tests – Verhalten erhalten)

Diese Tests beschreiben erwartetes Verhalten; bilde es in der neuen App ab.

### tests/concept/__init__.py

```
"""
Konzept-Tests: automatisierte Umsetzung des Testkonzepts aus TESTING.md.

Aufbau (entspricht den Abschnitten 1-10 / A-K des Konzepts):

  fixtures.py             - synthetische Nutzer/Gruppen M-01..M-09 (Seed)
  pairwise.py             - All-Pairs-Algorithmus fuer Anhang C
  matrix.py               - Dimensionen + Constraints fuer die Matrix
  roles.py                - Berechtigungsmatrix (Anhang D)
  test_members_scenarios  - Mitglieder-Szenarien (Kapitel 2)
  test_roles_permissions  - Rollen-/Berechtigungstests (Anhang D)
  test_tasks_matrix       - kombinatorische Tests (Kapitel 3 + Anhang C/E)
  test_properties_concept - Property-Tests (Kapitel 8)
  test_release_gate       - Release-Gate (Kapitel 4.5 + Anhang J)
"""

```

### tests/concept/matrix.py

```
"""
Dimensionen und Constraints der kombinatorischen Testmatrix (Anhang C).

Die Werte sind 1:1 die im Konzept (TESTING.md, Kapitel 3) festgelegten -
mit zwei pragmatischen Anpassungen auf die reale Domaene dieses Repos:

  * Anstelle einer Cloud-Sync-Komponente steht hier die lokale Sync-Logik
    aus services/sync.py (Datei-/HTTP-Provider). Die Werte ONLINE/OFFLINE
    bleiben semantisch identisch.
  * "Recurrence" ist auf die App-Werte (1, 7, 14, 30 Tage) und ONE_OFF
    (None) abgebildet, weil HouseholdTask.interval_days int verlangt.

Constraints orientieren sich an Realitaets-Plausibilitaet:

  - Wer GUEST ist, kann nicht OWNER_CONFIRM verlangen.
  - PUSH=BLOCKED schliesst Reminder aus.
  - Eine ONE_OFF-Aufgabe hat per Definition eine Frist (nicht NONE).
"""
from __future__ import annotations


DIMENSIONS: dict[str, list] = {
    "role":       ["OWNER", "ADMIN", "MEMBER", "GUEST"],
    "members":    [1, 2, 5, 11, 12, 20],
    "task_kind":  ["STANDARD", "CHECKLIST", "APPROVAL", "EVENT"],
    "recurrence": ["ONE_OFF", "DAILY", "WEEKLY", "MONTHLY", "CUSTOM"],
    "priority":   ["LOW", "NORMAL", "HIGH", "URGENT"],
    "due":        ["NONE", "FUTURE", "TODAY", "OVERDUE"],
    "reminder":   ["OFF", "M15", "H1", "D1", "CUSTOM"],
    "confirm":    ["NONE", "SELF", "OWNER"],
    "reward":     ["NONE", "POINTS", "STARS"],
    "device":     ["phone_compact", "phone_medium", "foldable", "tablet"],
    "api":        [26, 29, 31, 34, 35],
    "network":    ["ONLINE", "OFFLINE", "SLOW", "FLAKY"],
    "push":       ["ON", "OFF", "BLOCKED"],
    "lifecycle":  ["FOREGROUND", "BACKGROUND", "DOZE", "KILLED"],
}


def constraint(case: dict) -> bool:
    """Filter fuer offensichtlich unsinnige Kombinationen."""
    if case.get("role") == "GUEST" and case.get("confirm") == "OWNER":
        return False
    if case.get("push") == "BLOCKED" and case.get("reminder") not in (
            None, "OFF"):
        return False
    if case.get("recurrence") == "ONE_OFF" and case.get("due") == "NONE":
        return False
    return True


def interval_for(recurrence: str) -> int | None:
    return {
        "ONE_OFF": None,
        "DAILY":   1,
        "WEEKLY":  7,
        "CUSTOM": 10,
        "MONTHLY": 30,
    }.get(recurrence)

```
