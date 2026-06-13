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

## KI-Backend: Google Gemini (verbindlich)

Die KI-Funktionen der App MÜSSEN über **Google Gemini** laufen – kein anderer
LLM-Anbieter (Projektprinzip „Nur Gemini als LLM", siehe ARCHITECTURE.md /
ANFORDERUNGEN.md §9). Im Build Mode wird `GEMINI_API_KEY` automatisch als
**server-seitiges** Secret bereitgestellt; nutze es ausschließlich serverseitig,
nie im Client.

- **Default-Modell:** `gemini-2.5-flash` (über eine Env-/Settings-Variable
  überschreibbar, vgl. `ALLTAGSHELFER_GEMINI_MODEL`).
- **KI-getriebene Funktionen** (Rest läuft regelbasiert/offline): der
  **Assistent-Chat** (Tool-Use-Loop mit Function-Calling über die Capabilities),
  `inbox.analyze_mail` (+ `inbox.import_eml` / `inbox.fetch_imap`) und
  `social.draft_message`. Alle anderen Endpunkte aus `openapi.json` sind
  deterministisch und brauchen kein LLM.
- **Pflichtverhalten erhalten** (ANFORDERUNGEN.md §9 / FR-F):
  Function-Calling über das Capability-Schema, Confirm-Callback vor
  destruktiven Aktionen, gemessener Token-Verbrauch, robuste Fehler-/
  Rate-Limit-Behandlung und der **Halluzinations-Schutz** im Posteingang
  (LLM-Vorschläge nur gegen die Allowlist `{contracts.add,
  contracts.report_price_change, family.add_order, calendar.add_event}` und das
  Pflichtparameter-Schema validiert übernehmen).
- **Offline-Fallback** (optional, empfohlen): Ohne gültigen Key bleibt die App
  über den regelbasierten Pfad nutzbar – keine harte Gemini-Abhängigkeit für
  Kernfunktionen (Datenschutz-Prinzip, ANFORDERUNGEN.md PA-01/PA-02).

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
