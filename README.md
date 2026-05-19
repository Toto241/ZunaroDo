# Alltagshelfer – Prototyp

Lauffähiger Prototyp des datenschutzfreundlichen Alltagsassistenten mit
**vier Fachmodulen**, einem **Dashboard**, einem **Ausgabedienst** und
**drei Schnittstellen**, über die alle Teile miteinander interagieren.

## Schnellstart

```bash
cd alltagshelfer
python main.py        # Konsolen-Demo (zeigt alle Module und Schnittstellen)
python gui.py         # grafische Oberflaeche mit Dashboard + Posteingang

# optional mit echtem LLM statt Offline-Router:
ANTHROPIC_API_KEY=sk-... python main.py
```

Abhängigkeiten: `pip install customtkinter fpdf2`

## Module

| Modul | Name | Aufgabe |
|---|---|---|
| A | Vertrags- & Fristenmanager | Verträge, Kündigungsfristen, **Kündigungsschreiben**, Preisänderungen |
| B | Finanz-Cockpit | Ausgaben + monatliche Belastung |
| D | Familie & Haushalt | Mitglieder, wiederkehrende Aufgaben (Rotation), **einmalige Aufträge** |
| – | Posteingang & Vorschläge | **Mail-Analyse** und zentrale **Vorschlags-Ablage** |

Der **Ausgabedienst** (`services/output.py`) ist kein Fachmodul, sondern
Infrastruktur: er erzeugt druckbare PDFs und Mail-Entwürfe (`.eml`). So
muss kein Modul selbst Drucker- oder SMTP-Logik nachbauen.

## Die drei Schnittstellen

1. **Front-End ↔ Modul** – `ModuleRegistry.dispatch(name, args)`.
   Assistent und GUI rufen Modul-Funktionen generisch im Tool-Use-Format auf.
2. **Modul ↔ Modul** – `ModuleContext.call(...)`. Ein Modul nutzt
   Funktionen anderer Module, ohne sie zu kennen (lose Kopplung).
3. **Dashboard** – `ModuleRegistry.collect_events(...)`. Jedes Modul
   liefert über `get_events()` anstehende Ereignisse; sie werden
   chronologisch zusammengeführt.

## Die vier umgesetzten Funktionen

**1 – Kündigungsschreiben.** `contracts.generate_cancellation` erzeugt aus
den Vertragsdaten ein fristgerechtes Schreiben mit berechnetem
Kündigungstermin – als druckbares **PDF** und als **Mail-Entwurf**, beides
über den Ausgabedienst.

**2 – Aufträge mit gezielter Verteilung.** Modul D kennt jetzt zwei
Aufgabentypen: wiederkehrende Haushaltsaufgaben *mit Rotation* und
einmalige **Aufträge**, die gezielt einer Person zugewiesen werden
(`family.add_order`, `family.orders`, `family.complete_order`). Offene
Aufträge erscheinen automatisch im Dashboard.

**3 – Mail-Analyse.** Das Modul Posteingang analysiert eingefügten
Mail-Text (`inbox.analyze_mail`) und erkennt regelbasiert Muster wie
Preiserhöhungen oder neue Verträge.

**4 – Zentrale Vorschlags-Ablage.** Erkannte Muster werden **nicht
automatisch eingetragen**, sondern als *Vorschlag* abgelegt. Jeder
Vorschlag trägt eine Ziel-Capability. Erst beim Bestätigen
(`inbox.accept_proposal`) wird diese aufgerufen – das zuständige Modul
prüft und übernimmt die Daten. Der Mensch entscheidet vor dem Schreiben.

```
Mail-Text -> Analyse -> Vorschlag in der Ablage
                            |
               Nutzer prueft (uebernehmen / ablehnen)
                            |
        uebernehmen -> Ziel-Capability -> zustaendiges Modul traegt ein
```

## Projektstruktur

```
alltagshelfer/
├── models.py            Datenklassen (inkl. HouseholdOrder, Proposal)
├── database.py          SQLite-Schema + Repositories
├── core/interface.py    Die drei Schnittstellen
├── modules/
│   ├── contracts.py     Modul A (+ Kündigungsschreiben)
│   ├── finance.py       Modul B
│   ├── family.py        Modul D (+ Aufträge)
│   └── inbox.py         Modul Posteingang (Mail-Analyse + Vorschläge)
├── services/
│   └── output.py        Ausgabedienst (PDF + Mail-Entwurf)
├── assistant.py         KI-Assistent (API- oder Offline-Modus)
├── gui.py               Oberfläche: Dashboard, Posteingang, Assistent
└── main.py              Konsolen-Demo
```

## Status & Grenzen des Prototyps

- Der Posteingang analysiert **eingefügten** Mail-Text bzw. `.eml`-Dateien.
  Ein echter IMAP-Postfachzugriff wäre ein späterer, separater Schritt.
- Die Mail-Analyse ist regelbasiert (Stichworte, Beträge, Datum). Im
  API-Modus ließe sich die Erkennung durch das LLM ersetzen.
- Erzeugte PDFs/Mail-Entwürfe liegen im Ordner `ausgaben/`.
- Modul C (Termine/Kalender) ist als Platz im Raster vorgesehen, aber
  noch nicht umgesetzt.
