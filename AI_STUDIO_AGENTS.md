# AGENTS.md – Kontext-Brief für Toto241/ZunaroDo

Folgt der AGENTS.md-Konvention (ein „README für KI-Agenten") und fasst den vorhandenen
Stand zusammen, damit Build Mode oder ein Folge-Agent das Projekt mit Kontext neu aufbaut –
Build Mode importiert kein bestehendes Repository.

## Tech Stack

Python, Docker, Source structure, Automated tests

## Build-Mode-Kompatibilität

- Frontend: nicht erkannt (unknown)
- Backend: Python
- Persistenz: relational (auf Cloud SQL abbilden)

## Befehle

- Installation: python -m pip install -r requirements.txt
- Entwicklung: python main.py
- Build: nicht erkannt
- Tests: pytest

## Schlüssel-Abhängigkeiten (Versionen halten)

- customtkinter: 5.2.0
- cryptography: 42.0.0

## Wichtige Dateien

- README.md
- requirements.txt
- pyproject.toml
- Dockerfile
- docker-compose.yml
- .env.example

## Verhaltens-Spezifikationen (beim Re-Build erhalten)

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

## Konventionen & Sicherheit

- Secrets ausschließlich server-seitig (GEMINI_API_KEY wird in Build Mode automatisch gesetzt); `.env.example` mit leeren Werten pflegen.
- Bestehende öffentliche Schnittstellen und Geschäftslogik erhalten, sofern nicht ausdrücklich anders gewünscht.
- In kleinen, überprüfbaren Schritten arbeiten und Build-/Runtime-Fehler sofort beheben.
