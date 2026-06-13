# AI Studio Prompt

Ich möchte das Repository Toto241/ZunaroDo in Google AI Studio Build Mode als bestehendes Projektkonzept weiterentwickeln. Nutze die angehängten Handoff-Dateien als verbindlichen Kontext und erhalte die vorhandene Geschäftslogik.

## Arbeitsauftrag

1. Lies zuerst die Attachments AI_STUDIO_CONTEXT.md, AI_STUDIO_BUILD_NOTES.md, AI_STUDIO_AGENTS.md, REPO_SUMMARY.md, ARCHITECTURE.md, TESTING.md, SECURITY.md, PRIVACY.md, .env.example und optional repo-analysis.json.
2. Erstelle oder aktualisiere die App mit einer sauberen, wartbaren Full-Stack-Struktur für Build Mode.
3. Nutze serverseitige API-Endpunkte für Secret- oder API-Key-abhängige Funktionen; Secret-Werte kommen ausschließlich aus Settings > Secrets.
4. Implementiere robuste Fehlerzustände, Ladezustände und verständliche UI-Texte.
5. Erzeuge oder verbessere Tests passend zum erkannten Stack.
6. Prüfe Build-/Runtime-Fehler in AI Studio und behebe sie, bevor du Deployment oder GitHub-Export empfiehlst.

## Erkannter Tech Stack

Python, Docker, Source structure, Automated tests

## Befehle aus dem Repository

- Installieren: python -m pip install -r requirements.txt
- Entwickeln: python main.py
- Bauen: nicht erkannt
- Testen: pytest

## Deployment-Kontext

- Starter Tier geeignet: nein
- Benötigt Datenbank: ja
- Benötigt Firebase: nein
- Benötigt externe APIs: nein
- Benötigt wahrscheinlich Billing: ja

## Stack-Vorgabe

Das erkannte Frontend (nicht erkannt) wird von Build Mode nicht direkt unterstützt. Implementiere die App als React (Default) oder Angular und übernimm die fachliche Logik. Die folgenden Versionen beschreiben die bestehende Implementierung als Referenz, nicht als Paket-Vorgabe für die Neufassung: Das erkannte Backend (Python) ist nicht als Node.js-Server abbildbar – setze die Server-Logik in Node.js neu um oder verlagere sie client-/serverless.

- customtkinter: 5.2.0
- cryptography: 42.0.0

Beachte die Build-Mode-Grenzen in AI_STUDIO_BUILD_NOTES.md (Stack-Support, Persistenz, AI Chips, Secrets).

## Fehlende Handoff-Dateien

- AI_STUDIO_CONTEXT.md
- AI_STUDIO_PROMPT.md
- AI_STUDIO_SYSTEM_INSTRUCTIONS.md
- AI_STUDIO_WEB_UI_STEPS.md

## Warnungen

- Mögliche Secret- oder Credential-Dateien gefunden: .mypy_cache/3.10/keyring/credentials.data.json, .mypy_cache/3.10/keyring/credentials.meta.json
