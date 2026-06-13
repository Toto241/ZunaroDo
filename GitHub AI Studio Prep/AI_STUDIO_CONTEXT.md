# AI Studio Context

## Repository

Toto241/ZunaroDo

URL: https://github.com/Toto241/ZunaroDo
Branch: main

## Projektziel

Dieses Repository soll in Google AI Studio Build Mode nachvollziehbar weiterentwickelt werden. Diese Datei beschreibt den vorhandenen Stand und dient als Attachment-Kontext, weil Build Mode bestehende GitHub-Repositories nicht als vollständige Arbeitskopie importiert.

## Erkannter Tech Stack

Python, Docker, Source structure, Automated tests

## Wichtige erkannte Dateien

- README.md
- requirements.txt
- pyproject.toml
- Dockerfile
- docker-compose.yml
- .env.example

## Startbefehle

- Installation: python -m pip install -r requirements.txt
- Entwicklung: python main.py
- Build: nicht erkannt
- Tests: pytest

## Umgebungsvariablen

- GOOGLE_API_KEY
- ALLTAGSHELFER_GEMINI_MODEL
- ALLTAGSHELFER_FORCE_GEMINI_REST
- ALLTAGSHELFER_DB_KEY
- ALLTAGSHELFER_BACKUP_KEY
- ALLTAGSHELFER_IMAP_HOST
- ALLTAGSHELFER_IMAP_USER
- ALLTAGSHELFER_IMAP_PASS
- ALLTAGSHELFER_IMAP_FOLDER
- ALLTAGSHELFER_SYNC_DIR
- ALLTAGSHELFER_SYNC_URL
- ALLTAGSHELFER_SYNC_TOKEN
- ALLTAGSHELFER_DEVICE_ID
- ALLTAGSHELFER_SYNC_LOG
- ALLTAGSHELFER_PROFILE
- ALLTAGSHELFER_DATA_DIR
- ALLTAGSHELFER_CONFIG_DIR
- ALLTAGSHELFER_LOG_LEVEL
- ALLTAGSHELFER_PAIRING_BACKEND
- ALLTAGSHELFER_PLATFORM
- ZUNARODO_PLAY_VERIFY_URL

Echte Secret-Werte in Google AI Studio nur unter Settings > Secrets eintragen, nicht in Prompt oder Attachments.

## Deployment-Einschätzung

- Starter Tier geeignet: nein
- Benötigt Datenbank: ja
- Benötigt Firebase: nein
- Benötigt externe APIs: nein
- Benötigt wahrscheinlich Billing: ja

## README-Auszug

# ZunaroDo

Datenschutzfreundlicher Alltagsassistent für den deutschsprachigen Raum
mit **acht Fachmodulen**, einem **Dashboard**, **Google Gemini** als
optionalem KI-Backend, **Mehrgeräte-Synchronisation** (Datei oder HTTP,
optional HTTPS), **optionaler SQLCipher-Verschlüsselung**,
**Volltextsuche**, **CSV-Export**, **Online-Backup**, einem **CLI** und
einer **CustomTkinter-GUI** mit DE/EN-Lokalisierung.

## Schnellstart

```bash
pip install -r requirements.txt

# Konsolen-Demo (Offline-Modus, alles tut auch ohne Netz)
python main.py

# Mit alternativem Profil (eigene DB-Datei + State-Dir)
ALLTAGSHELFER_PROFILE=anna python main.py
# oder ueber den CLI-Wrapper
python __main__.py --profile anna

# GUI mit allen Tabs
python gui.py

# Subcommands ueber python __main__.py
python __main__.py --diagnose
python __main__.py --gui
python __main__.py --backup
python __main__.py --list-backups
python __main__.py --restore backups/alltagshelfer-20260519-185747.db
python __main__.py --export
python __main__.py --import ausgaben/export-20260519-185747
python __main__.py --sync-server --port 5151
```

### Desktop-Start und Dialogverhalten

Die Desktop-App startet dauerhaft als **ZunaroDo** im hellen Windows-11-Stil,
unabhaengig vom System-Dark-Mode. Normale CRUD-Aktionen wie Anlegen,
Bearbeiten, Soft-Delete, Wiederherstellen, Abhaken oder das Uebernehmen von
Inbox-Vorschlaegen laufen ohne zusaetzlichen Bestaetigungsdialog.

Geschuetzt bleiben kritische Aktionen mit dauerhaftem oder gebuendeltem
Datenverlust: Purge-Operationen, archivierte Inbox-Vorschlaege gesammelt
loeschen sowie endgueltiges Loeschen von Notizen oder Vorlagen. Der KI-
Assistent fordert dafuer weiterhin eine ausdrueckliche Freigabe an.

### Optionale Erweiterungen

```bash
# Google Gemini als KI-Backend
pip install google-generativeai
GOOGLE_API_KEY=... python gui.py

# Verschluesselte DB (SQLCipher)
pip install sqlcipher3-binary
ALLTAGSHELFER_DB_KEY=mein-passwort python gui.py

# Mehrgeraete-Sync via geteiltem Ordner
ALLTAGSHELFER_SYNC_DIR=C:\Users\me\Dropbox\alltagshelfer python gui.py

# Oder via HTTP-Sync-Server
python __main__.py --sync-server --port 5151
ALLTAGSHELFER_SYNC_URL=http://server:5151 python gui.py

# Server mit TLS und Token
python __main__.py --sync-server --port 5151 \
  --cert server.pem --key server.key \
  --token "geheim"

# Mail per IMAP holen
ALLTAGSHELFER_IMAP_HOST=imap.example.com \
```

… (gekürzt)

## Build-Mode-Kompatibilität

- Frontend: nicht erkannt (unknown)
- Backend: Python
- Persistenz: relational (auf Cloud SQL abbilden)

Schlüssel-Abhängigkeiten (Referenz des Desktop-Originals, nicht Pflicht für die Web-Neufassung):
- customtkinter: >= 5.2.0
- cryptography: >= 42.0.0

Details und Grenzen siehe AI_STUDIO_BUILD_NOTES.md.

## Maschinenlesbare Contracts

Aus dem echten Code generiert (via `python -m tools.gen_ai_studio_contracts`),
als Attachments mitliefern:

- `docs/ai-studio/contracts/openapi.json` — Capability-API (Endpunkte 1:1)
- `docs/ai-studio/contracts/capabilities.json` — Capabilities inkl. Flags
- `docs/ai-studio/contracts/schema.sql` / `schema.prisma` — Persistenz
- `ANFORDERUNGEN.md` — Anforderungen/Akzeptanzkriterien (R1–R10)
- `UI_CONCEPT.md` + `assets/store/phone-*.png` — UI-/UX-Referenz

## Hinweis zu Secrets

Es liegen **keine** Secrets im Repository. Secret-Namen stehen leer in
`.env.example`; echte Werte ausschließlich unter Settings > Secrets. Ein
früherer automatischer Scan meldete `.mypy_cache/**/keyring/*` – das ist ein
lokaler, via `.gitignore` ausgeschlossener mypy-Cache, **nicht** im Git und
kein App-Secret.
