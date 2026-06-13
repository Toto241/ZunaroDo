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

- Dockerfile — Container-Setup (Laufzeit-/Service-Kontext)

## Empfohlene AI Chips

- keine spezifischen AI Chips empfohlen

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
- Desktop-/Nicht-Web-Stack erkannt (CustomTkinter) – Build Mode erzeugt ausschließlich Web-Apps. Dieses Repo ist kein direkter Build-Mode-Kandidat: entweder als Web-App neu konzipieren oder den Handoff an einen code-fähigen Agenten (Claude/Codex/Gemini CLI) geben, der das bestehende Repo bearbeitet.
- Build Mode bietet als Server-Runtime nur Node.js – ein Python-Backend müsste in Node neu umgesetzt oder durch client-/serverlose Logik ersetzt werden.
- Persistenz erkannt (relational (auf Cloud SQL abbilden)) – auf den Build-Mode-Pfad (Firestore/Cloud SQL) abbilden.
- Zusätzlich als Attachment anhängen: Dockerfile.
- Vorhandene Tests definieren erwartetes Verhalten – dieses beim Re-Build erhalten.
- Build Mode importiert keine bestehenden Repositories – dies ist ein Re-Build-mit-Kontext-Handoff, kein Code-Import.

- `GEMINI_API_KEY` wird in Build Mode automatisch als server-seitiges Secret gesetzt – nicht in den Client legen.
- Secrets werden beim GitHub-Export nicht mitexportiert; nach ZIP-Download `.env` lokal neu setzen.
- Ein „System Instructions"-Feld ist im Build Mode nicht gesichert vorhanden – die Kernregeln stehen daher zusätzlich im Prompt-Kopf.

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
