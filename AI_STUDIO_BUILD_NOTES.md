# AI Studio Build – Hinweise

Diese Datei passt den Handoff an die realen Fähigkeiten und Grenzen von Google AI Studio Build Mode an (Repository Toto241/ZunaroDo).

## Stack-Kompatibilität

- Frontend: nicht erkannt — kein Frontend erkannt (Default React + Vite)
- Backend: Python — nicht direkt abbildbar (nur Node.js verfügbar)
- Persistenz: relational (auf Cloud SQL abbilden)
- Starter-Tier-Deploy (bis 2 Apps ohne Billing): eher nicht – Billing/GCP-Projekt nötig

## Stack im Prompt pinnen (gegen halluzinierte Pakete)

- customtkinter: 5.2.0
- cryptography: 42.0.0

## Zusätzlich anzuhängende Kontext-Artefakte

- docs/ai-studio/contracts/openapi.json — API-Contract (Endpunkte 1:1 abbilden)
- docs/ai-studio/contracts/capabilities.json — Capabilities inkl. destructive/internal-Flags
- docs/ai-studio/contracts/schema.sql — DDL des echten Schemas
- docs/ai-studio/contracts/schema.prisma — Prisma-Modell (Cloud-SQL-/Postgres-Abbildung)
- ANFORDERUNGEN.md — Anforderungen/Akzeptanzkriterien (R1–R10)
- docker-compose.yml — Container-Setup (Laufzeit-/Service-Kontext)

Regenerieren mit `python -m tools.gen_ai_studio_contracts` (Drift-Gate:
`--check`).

## Empfohlene AI Chips

- keine spezifischen AI Chips empfohlen

## Design-Referenzen (Sketch-Upload / Annotation Mode)

- UI_CONCEPT.md — vollständiges UI-/UX-Konzept (als Re-Build-Vorlage)
- assets/store/phone-1.png, phone-2.png, phone-3.png — Screen-Referenzen

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
- Desktop-/Nicht-Web-Stack erkannt (CustomTkinter) – Build Mode erzeugt ausschließlich Web-Apps. Dieses Repo ist kein direkter Build-Mode-Kandidat: entweder als Web-App neu konzipieren oder den Handoff an einen code-fähigen Agenten (Claude/Codex/Gemini CLI) geben, der das bestehende Repo bearbeitet.
- Build Mode bietet als Server-Runtime nur Node.js – ein Python-Backend müsste in Node neu umgesetzt oder durch client-/serverlose Logik ersetzt werden.
- Persistenz erkannt (relational (auf Cloud SQL abbilden)) – auf den Build-Mode-Pfad (Firestore/Cloud SQL) abbilden.
- Zusätzlich als Attachment anhängen: docker-compose.yml.
- Vorhandene Tests definieren erwartetes Verhalten – dieses beim Re-Build erhalten.
- Build Mode importiert keine bestehenden Repositories – dies ist ein Re-Build-mit-Kontext-Handoff, kein Code-Import.

- `GEMINI_API_KEY` wird in Build Mode automatisch als server-seitiges Secret gesetzt – nicht in den Client legen.
- Secrets werden beim GitHub-Export nicht mitexportiert; nach ZIP-Download `.env` lokal neu setzen.
- Ein „System Instructions"-Feld ist im Build Mode nicht gesichert vorhanden – die Kernregeln stehen daher zusätzlich im Prompt-Kopf.

## Datenmodelle / API-Contracts (eingebettet)

### docker-compose.yml (Container-Setup)

```
version: "3.9"

services:
  sync:
    build: .
    image: alltagshelfer-sync:latest
    container_name: alltagshelfer-sync
    restart: unless-stopped
    ports:
      - "5151:5151"
    volumes:
      # Persistente Sync-Daten ausserhalb des Containers
      - ./data:/data
      # Optional: TLS-Zertifikate fuer HTTPS-Modus
      # - ./certs:/certs:ro
    environment:
      ALLTAGSHELFER_SYNC_DIR: /data
      # Optional: gemeinsamer Auth-Token, den die Clients mitsenden muessen
      # ALLTAGSHELFER_SYNC_TOKEN: ${SYNC_TOKEN:-}
    # Falls TLS gewuenscht ist (Cert+Key in /certs gemounted):
    # command:
    #   - python
    #   - -m
    #   - services.sync_server
    #   - --host=0.0.0.0
    #   - --port=5151
    #   - --log=/data/sync_events.jsonl
    #   - --cert=/certs/server.crt
    #   - --key=/certs/server.key
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5151/health',timeout=3).status==200 else 1)"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

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
