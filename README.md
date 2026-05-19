# Alltagshelfer

Datenschutzfreundlicher Alltagsassistent mit **sieben Fachmodulen**, einem
**Dashboard**, einem **proaktiven Scheduler**, **Mehrgeräte-Sync**,
optionaler **DB-Verschlüsselung**, **GUI-Modulverwaltung** und Anbindung
an **Google Gemini** über eine provider-agnostische LLM-Schnittstelle.

## Schnellstart

```bash
pip install -r requirements.txt
python main.py        # Konsolen-Demo
python gui.py         # GUI mit allen Tabs

# Mit Gemini (echtes LLM)
pip install google-generativeai
GOOGLE_API_KEY=... python gui.py

# Verschluesselte DB (SQLCipher)
pip install sqlcipher3-binary
ALLTAGSHELFER_DB_KEY=mein-geheimes-passwort python gui.py

# Mehrgeraete-Sync (geteilter Ordner, z.B. OneDrive/Dropbox)
ALLTAGSHELFER_SYNC_DIR=C:\Users\me\Dropbox\alltagshelfer python gui.py

# Optional: IMAP statt Mail-Text einfuegen
ALLTAGSHELFER_IMAP_HOST=imap.example.com \
ALLTAGSHELFER_IMAP_USER=... \
ALLTAGSHELFER_IMAP_PASS=... \
python gui.py
```

Tests: `python -m unittest discover tests` — 16 Tests grün.

## Module

| Modul | Name | Aufgabe |
| --- | --- | --- |
| A | Vertrags- & Fristenmanager | Verträge, Kündigungsfristen, **Kündigungsschreiben** (PDF + Mail + Druck), Preisänderungen, Person-Zuordnung |
| B | Finanz-Cockpit | Ausgaben, monatliche Belastung, Aggregate, Preisgedächtnis, OCR |
| C | Termine & Kalender | Termine, Garantien, TÜV, Steuerfristen, Geburtstage |
| D | Familie & Haushalt | Mitglieder, Aufgaben (Rotation), Aufträge, Einkaufsliste |
| E | Soziale Pflege | Kontakte mit Rhythmus, **LLM-generierter Nachrichten-Entwurf** |
| – | Tagesstruktur | Scaffold: Energie-Tagebuch |
| – | Posteingang | Mail-Analyse: regelbasiert + **LLM-basiert via Gemini**, .eml, IMAP, Vorschläge |

## Die drei Schnittstellen

1. **Front-End ↔ Modul** – `ModuleRegistry.dispatch(name, args)`
2. **Modul ↔ Modul** – `ModuleContext.call(...)`
3. **Dashboard** – `ModuleRegistry.collect_events(...)`

## Gemini-Integration

Implementiert in [services/gemini.py](services/gemini.py) hinter der
provider-neutralen Schnittstelle [services/llm.py](services/llm.py). Aus
der Analyse der bisherigen Anthropic-Anbindung in
[assistant.py](assistant.py) wurden folgende Erweiterungen abgeleitet
und in die Gemini-Variante eingebaut:

| Erweiterung | Wo |
| --- | --- |
| Konversationsverlauf pro Session | `Assistant._history` + Gemini-Chat |
| Konfigurierbare Iterations- und Token-Limits | `max_iterations`, `max_output_tokens` |
| Token-Verbrauch wird gemessen | `TokenUsage`, `Assistant.token_usage` |
| Stream-Callback für UI | `stream_callback`-Argument |
| Trennung statischer/dynamischer System-Prompt | erleichtert Gemini-Context-Caching |
| Provider-neutrales Tool-Schema | `Capability.to_provider_neutral_schema()` |
| **Bestätigung vor destruktiven Aufrufen** | `destructive: bool` an Capability + `ConfirmCallback`; GUI fragt per messagebox |
| Strukturierte Fehler aus Tool-Aufrufen | als `FunctionResponse.response.result` |

`Capability` liefert weiterhin auch `to_tool_schema()` im Anthropic-Stil,
womit ein Anthropic-Client jederzeit parallel ergänzt werden kann.

## SQLCipher-Verschlüsselung

[database.py](database.py) wählt automatisch zwischen Klartext-SQLite
und SQLCipher:

- `ALLTAGSHELFER_DB_KEY` nicht gesetzt → Klartext (Default)
- Key gesetzt + `sqlcipher3` installiert → verschlüsselt
- Key gesetzt + `sqlcipher3` fehlt → **harter Fehler** (kein stilles
  Unverschlüsselt-Fallback)

`db.encryption_mode` zeigt den aktiven Modus an.

## Mehrgeräte-Synchronisation

[services/sync.py](services/sync.py) implementiert einen Datei-basierten
Event-Log:

```text
geteilter Ordner/
└── sync_events.jsonl     # eine JSON-Zeile pro Mutation, mit Geräte-UUID

lokales Profil/
├── device_id             # eigene UUID (einmalig erzeugt)
└── sync_seen.json        # bereits angewendete Event-IDs
```

Ablauf: Aufrufe synchronisierungs-fähiger Capabilities (Standard:
`family.*`) werden mitprotokolliert. Beim Start spielt jedes Gerät
fremde, noch nicht gesehene Events nach (idempotent über Event-UUIDs).
Aktivieren über `ALLTAGSHELFER_SYNC_DIR`.

Bewusst klein gehalten: keine CRDTs, kein Server. Reicht für einen
Familienhaushalt; bei nicht-idempotenten Operationen gewinnt die
zuletzt angewendete Reihenfolge.

## GUI-Modulverwaltung

Neuer Tab **Module** in [gui.py](gui.py): jeder Modul-Eintrag hat einen
Switch. Deaktivierte Module liefern weder Capabilities noch Dashboard-
Eintraege, ihre Daten bleiben in der DB erhalten. `ModuleRegistry`
trägt das über `set_module_enabled`, `is_module_enabled` und
`module_states()`.

## Projektstruktur

```text
.
├── models.py
├── database.py                 SQLite (+ optional SQLCipher)
├── core/interface.py           Drei Schnittstellen + Enable/Disable
├── modules/                    A, B, C, D, E, Posteingang, Tagesstruktur
├── services/
│   ├── llm.py                  Provider-Vertrag
│   ├── gemini.py               Gemini-Client
│   ├── sync.py                 Mehrgeräte-Event-Log
│   ├── output.py               PDF + Mail + Druck + SMTP
│   ├── ocr.py                  Kassenbon-OCR (optional)
│   ├── notifier.py             Desktop-Notifikation
│   └── scheduler.py            Proaktive Hintergrund-Checks
├── assistant.py                LLM-agnostisch
├── gui.py                      CTk-GUI mit 9 Tabs (inkl. Modulverwaltung)
├── main.py                     Konsolen-Demo
├── tests/test_smoke.py         16 Tests
└── requirements.txt
```

## Was komplett umgesetzt ist

Aus den zuvor offen gelassenen Punkten:

- [x] **SQLCipher-DB-Verschlüsselung** – produktionsfähig, mit klarem
      Fehler bei fehlender Bibliothek
- [x] **Mehrgeräte-Sync** für Modul D – Datei-basiert, idempotent,
      mit Geräte-UUIDs und Replay
- [x] **LLM-basierte Mail-Analyse** über Gemini – läuft zusätzlich zur
      regelbasierten Erkennung
- [x] **GUI-Modulverwaltung** – Switch pro Modul, sofort wirksam
- [x] **Google Gemini** als KI-Backend hinter provider-neutraler
      Schnittstelle
- [x] **Anthropic-Schnittstelle analysiert** – die acht ableitbaren
      Erweiterungen (siehe Tabelle oben) sind in die Gemini-Variante
      eingeflossen
