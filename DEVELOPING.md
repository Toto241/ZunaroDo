# Entwickeln an ZunaroDo

Kurzleitfaden fuer alle, die hier mitarbeiten. Wer nur installieren
moechte: bitte die README lesen.

## Setup

```pwsh
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt        # optional: hypothesis, coverage
```

## Test-Pipeline

```pwsh
# Alles
python -m unittest discover tests

# Nur Smoke-Suite
python -m unittest tests.test_smoke

# Mit Coverage
coverage run -m unittest discover tests
coverage report
coverage html        # erzeugt htmlcov/
```

## Statische Analyse

```pwsh
python -m compileall .
# optional, wenn installiert:
mypy .
ruff check .
```

## Lokal die GUI starten

```pwsh
python -m gui
```

## CLI-Demo

```pwsh
python main.py
```

## Ein neues Modul anlegen

1. Eine Datei `modules/<name>.py` mit Klasse `XYZModule(ModuleInterface)`.
2. `module_id`, `display_name`, `get_capabilities()` implementieren.
3. Falls Cross-Modul-Calls noetig: `on_register(context)` ueberschreiben
   und `context` aufbewahren.
4. In `main.py::build_registry` einstecken.
5. Smoke-Test in `tests/test_smoke.py` ergaenzen.

### Conventions fuer Capabilities

- `<module_id>.<verb>` als Name. Beispiele: `notes.add`, `family.members`.
- Destruktive Aufrufe (schreiben/loeschen) tragen `destructive=True`.
- Intern-Aufrufe (z.B. Cross-Modul-Cleanup) bekommen `internal=True`,
  damit sie nicht ins LLM-Tool-Schema gelangen.
- Handler liefern **immer ein `dict`** zurueck. Fehler als
  `{"error": "..."}`. Erfolg mit `"status"`-Feld und Domain-Daten.
- Eingabe-Validierung passiert **im Handler**, nicht in der GUI.

## Konfiguration

Neue Schluessel in `services/config.py`:

1. `DEFAULTS` ergaenzen.
2. Falls per Env-Var ueberschreibbar: `ENV_MAP` ergaenzen.
3. Falls geheim: `SECRET_KEYS` ergaenzen - wird nie in die DB geschrieben.
4. Falls im `AppConfig`-Dataclass relevant: dort als Feld anlegen.

## Migrationen

Schema-Aenderung erfordert:

1. `CURRENT_SCHEMA_VERSION` in `database.py` erhoehen.
2. Migrations-Schritt in `_migrate_schema(conn)` ergaenzen, der idempotent
   ist und vorherige Versionen erkennt.
3. Roundtrip-Test in `test_smoke.py`.
4. Eintrag in `MIGRATIONS.md`.

## Git-Workflow

- `main` ist immer gruen (CI laeuft).
- Feature-Branches: `feat/<knappes-thema>`, Bugfix-Branches: `fix/<thema>`.
- Commits in der Imperativ-Form (`add`, `fix`, `refactor`).
- Vor dem Push: `python -m unittest discover tests` und `compileall`.

## Was du *nicht* tun solltest

- Keine LLM-Aufrufe ausserhalb von `assistant.py` / Registry.
- Kein `print()` in Produktiv-Code - statt dessen `services.logging_setup`.
- Keine direkten DB-Zugriffe aus der GUI - immer ueber Capabilities.
- Keine externen LLM-Anbieter (Anthropic, OpenAI, ...) - nur Gemini.
- Keine harten Pfade (`C:\Users\...`) - immer relativ + `pathlib`.
- Keine Geheimnisse in die DB schreiben.
