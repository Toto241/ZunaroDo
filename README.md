# Alltagshelfer

Lauffähiger Prototyp eines datenschutzfreundlichen Alltagsassistenten mit
**sieben Fachmodulen**, einem **Dashboard**, einem **Ausgabedienst**, einem
**proaktiven Scheduler** und **drei Schnittstellen**, über die alle Teile
miteinander interagieren.

## Schnellstart

```bash
pip install -r requirements.txt
python main.py        # Konsolen-Demo (zeigt alles End-to-End)
python gui.py         # GUI mit allen Tabs

# optional mit echtem LLM:
ANTHROPIC_API_KEY=sk-... python main.py

# optional Mails per IMAP:
ALLTAGSHELFER_IMAP_HOST=imap.example.com \
ALLTAGSHELFER_IMAP_USER=... \
ALLTAGSHELFER_IMAP_PASS=... \
python gui.py
```

Tests: `python -m unittest discover tests`

## Module

| Modul | Name | Aufgabe |
| --- | --- | --- |
| A | Vertrags- & Fristenmanager | Verträge, Kündigungsfristen, **Kündigungsschreiben** (PDF + Mail-Entwurf + Druck), Preisänderungen, **Person-Zuordnung** |
| B | Finanz-Cockpit | Ausgaben (mit Person), monatliche Belastung, **Aggregate pro Person/Kategorie**, **Preisgedächtnis**, **OCR für Kassenbons** |
| C | Termine & Kalender | Termine, Garantien, TÜV, **Steuerfristen**, Geburtstage (aus Modul D) |
| D | Familie & Haushalt | Mitglieder (mit Geburtstag), Aufgaben (Rotation), Aufträge (gezielt), **Einkaufsliste** |
| E | Soziale Pflege | Wichtige Kontakte mit Wunsch-Rhythmus, Nachrichten-Entwurf |
| – | Tagesstruktur | Scaffold: Energie-Tagebuch, einfache Empfehlung |
| – | Posteingang | Mail-Analyse (Text, **.eml**, **IMAP** optional), zentrale Vorschlags-Ablage |

## Die drei Schnittstellen

1. **Front-End ↔ Modul** – `ModuleRegistry.dispatch(name, args)`
2. **Modul ↔ Modul** – `ModuleContext.call(...)` (lose Kopplung)
3. **Dashboard** – `ModuleRegistry.collect_events(...)` aggregiert über alle Module

## Infrastruktur-Dienste (kein Fachmodul)

- [services/output.py](services/output.py) – PDF-Erzeugung, Mail-Entwurf (.eml), echter **SMTP-Versand** (mit `SmtpConfig`), **Drucken** über `print_file()` (OS-spezifisch)
- [services/ocr.py](services/ocr.py) – Tesseract-basierte Kassenbon-Erkennung (optional)
- [services/notifier.py](services/notifier.py) – Desktop-Notifikationen (plyer + Fallback)
- [services/scheduler.py](services/scheduler.py) – proaktiver Hintergrund-Scheduler (APScheduler + Thread-Fallback)

## Person-Zuordnung als Querschnitt

`family.members` ist die zentrale Personen-Quelle. Verträge (`contracts.add owner_id=…`) und Ausgaben (`finance.add_expense owner_id=…`) referenzieren Mitglieder darüber – ohne dass A oder B Modul D direkt kennen. Die Aggregate `finance.expenses_by_person` und `finance.expenses_by_category` werten das aus.

## Posteingang & Vorschlags-Ablage

```text
Mail (Text / .eml / IMAP)  ->  Analyse  ->  Vorschlag in der Ablage
                                              |
                                Nutzer prueft (uebernehmen / ablehnen)
                                              |
                  uebernehmen  ->  Ziel-Capability  ->  Modul traegt ein
```

Nichts wird ungeprüft eingetragen. Jeder Vorschlag trägt eine Ziel-Capability; das zuständige Modul prüft beim Übernehmen.

## Projektstruktur

```text
.
├── models.py                   Datenklassen
├── database.py                 SQLite-Schema + Repositories (+ Migrations-Hilfe)
├── core/
│   ├── interface.py            Die drei Schnittstellen
├── modules/
│   ├── contracts.py            Modul A (+ Kündigung + Person)
│   ├── finance.py              Modul B (+ Aggregate + Preisgedächtnis + OCR)
│   ├── family.py               Modul D (+ Aufträge + Einkaufsliste + Geburtstag)
│   ├── calendar.py             Modul C (+ Steuerfristen, Geburtstag-Sync)
│   ├── social.py               Modul E
│   ├── daystructure.py         Tagesstruktur-Scaffold
│   └── inbox.py                Mail-Analyse + .eml + IMAP + Vorschläge
├── services/
│   ├── output.py               PDF, Mail-Entwurf, SMTP, Druck
│   ├── ocr.py                  Kassenbon-OCR (optional)
│   ├── notifier.py             Desktop-Notifikation
│   └── scheduler.py            Proaktiver Hintergrund-Check
├── assistant.py                KI-Assistent (API- oder Offline-Modus, mit Log)
├── gui.py                      CTk-GUI: 8 Tabs
├── main.py                     Konsolen-Demo
├── tests/
│   └── test_smoke.py           Smoke-Tests
└── requirements.txt
```

## Neues Modul hinzufügen

1. Klasse von `ModuleInterface` ableiten, `module_id` + `display_name` + `get_capabilities()` setzen
2. Optional `get_events()` für Dashboard-Einträge implementieren
3. Optional `on_register(context)` überschreiben, um auf andere Module zuzugreifen
4. In [main.py:build_registry](main.py) eine Zeile ergänzen – fertig

Weder [assistant.py](assistant.py) noch [gui.py](gui.py) müssen angefasst werden; das neue Modul erscheint automatisch in Sidebar, Dashboard und Assistenten-Capability-Liste.

## Bewusst offen gelassen

- **SQLCipher-Verschlüsselung** der DB – auf Windows aufwendig zu installieren; im Code als Kommentar dokumentiert
- **Mehrgeräte-Synchronisation** für Familie – Single-Device-Modell deckt 80 % ab, ein Sync wäre ein Architekturschritt für sich
- **LLM-basierte Mail-Analyse** – aktuell regelbasiert; ein API-Mode-Ersatz in [modules/inbox.py](modules/inbox.py) ist absichtlich kompakt gehalten
- **GUI-Modul-Verwaltung** über die Sidebar (z. B. Modul deaktivieren) – nicht eingebaut
