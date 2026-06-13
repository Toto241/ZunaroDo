# AI Studio Prompt

Ich möchte das Repository Toto241/ZunaroDo in Google AI Studio Build Mode als bestehendes Projektkonzept weiterentwickeln. Nutze die angehängten Handoff-Dateien als verbindlichen Kontext und erhalte die vorhandene Geschäftslogik.

## Arbeitsauftrag

1. Lies zuerst die Attachments AI_STUDIO_CONTEXT.md, AI_STUDIO_BUILD_NOTES.md, AI_STUDIO_AGENTS.md, REPO_SUMMARY.md, ARCHITECTURE.md, ANFORDERUNGEN.md, TESTING.md, SECURITY.md, PRIVACY.md, .env.example und optional repo-analysis.json.
2. Lies die **maschinenlesbaren Contracts** unter docs/ai-studio/contracts/ (openapi.json, capabilities.json, schema.sql, schema.prisma) und die **UI-Referenz** (UI_CONCEPT.md + Screenshots assets/store/phone-*.png). Bilde die Endpunkte 1:1 zu openapi.json und die Persistenz nach schema.prisma/schema.sql ab.
3. Erstelle oder aktualisiere die App mit einer sauberen, wartbaren Full-Stack-Struktur für Build Mode.
4. Nutze serverseitige API-Endpunkte für Secret- oder API-Key-abhängige Funktionen; Secret-Werte kommen ausschließlich aus Settings > Secrets.
5. Implementiere robuste Fehlerzustände, Ladezustände und verständliche UI-Texte. Erhalte die in ANFORDERUNGEN.md beschriebenen Geschäftsregeln (Soft-Delete-Lebenszyklus, Bestätigung nur bei kritischen/destruktiven Aktionen, Tier-Sperren).
6. Erzeuge oder verbessere Tests passend zum erkannten Stack.
7. Prüfe Build-/Runtime-Fehler in AI Studio und behebe sie, bevor du Deployment oder GitHub-Export empfiehlst.

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

- customtkinter: >= 5.2.0 (Referenz; nur als Desktop-Original relevant, nicht für die Web-Neufassung)
- cryptography: >= 42.0.0 (Referenz; Ed25519-Lizenz-Token, siehe ANFORDERUNGEN.md §10/LI-10)

Beachte die Build-Mode-Grenzen in AI_STUDIO_BUILD_NOTES.md (Stack-Support, Persistenz, AI Chips, Secrets).

## Mitzuliefernde Contracts & Referenzen (Attachments)

- docs/ai-studio/contracts/openapi.json — API-Contract (Endpunkte 1:1)
- docs/ai-studio/contracts/capabilities.json — Capability-Liste inkl. Flags
- docs/ai-studio/contracts/schema.sql / schema.prisma — Persistenz-Abbildung
- ANFORDERUNGEN.md — Akzeptanzkriterien / Geschäftsregeln (R1–R10)
- UI_CONCEPT.md + assets/store/phone-*.png — UI-/UX-Referenz

## Sicherheitshinweis

- Es liegen **keine** Secrets im Repository. Secret-Namen stehen mit leerem
  Wert in `.env.example`; echte Werte ausschließlich unter Settings > Secrets.
  (Frühere automatische Scans meldeten `.mypy_cache/**/keyring/*` – das ist ein
  lokaler, via `.gitignore` ausgeschlossener Typcheck-Cache, **nicht** im Git
  und kein App-Secret.)
