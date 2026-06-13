# Google AI Studio Web UI Steps

## Vorbereitete Eingaben

| AI-Studio-Oberfläche | Eintragen oder hochladen |
| --- | --- |
| Build Prompt / Chat Input | Inhalt von AI_STUDIO_PROMPT.md einfügen |
| Advanced Settings > System Instructions | Inhalt von AI_STUDIO_SYSTEM_INSTRUCTIONS.md einfügen, falls dieses Feld vorhanden ist – im reinen Build Mode sind die Kernregeln zusätzlich im Prompt-Kopf enthalten |
| Attachments / Datei-Upload | AI_STUDIO_CONTEXT.md, AI_STUDIO_BUILD_NOTES.md, AI_STUDIO_AGENTS.md, REPO_SUMMARY.md, ARCHITECTURE.md, **ANFORDERUNGEN.md**, TESTING.md, SECURITY.md, PRIVACY.md, .env.example, optional repo-analysis.json **sowie die Contracts `docs/ai-studio/contracts/openapi.json`, `capabilities.json`, `schema.sql`, `schema.prisma`** und die **UI-Referenzen `UI_CONCEPT.md` + `assets/store/phone-1.png`/`phone-2.png`/`phone-3.png`** (Design-Referenzen/Mockups) hochladen |
| Settings > Secrets | Secret-Namen aus .env.example anlegen und echte Werte nur dort eintragen |
| Code Tab | Generierten Code prüfen und Build-/Runtime-Fehler beheben lassen |
| GitHub Export | Erst nach erfolgreicher Preview in ein neues GitHub-Repository exportieren |
| Deploy > Cloud Run | Nur mit passendem Cloud Project, Billing und Secrets fortfahren |

## Reihenfolge

1. In AI Studio den Build-Modus öffnen und Web-App auswählen.
2. System Instructions aus AI_STUDIO_SYSTEM_INSTRUCTIONS.md setzen.
3. Handoff-Dateien als Attachments hinzufügen.
4. Prompt aus AI_STUDIO_PROMPT.md senden.
5. Falls .env.example Variablen enthält, diese unter Settings > Secrets mit echten Werten anlegen.
6. Preview und Code Tab prüfen; bei Fehlern Build Mode auffordern: "Fix any build issues with the current code."
7. Erst danach GitHub-Export oder Cloud-Run-Deployment starten.

## Wichtige Grenze

Google AI Studio Build Mode kann erzeugte Apps nach GitHub exportieren, aber bestehende GitHub-Repositories nicht als vollständige Arbeitskopie pullen. Dieses Paket ist deshalb ein strukturierter Prompt- und Attachment-Handoff.
