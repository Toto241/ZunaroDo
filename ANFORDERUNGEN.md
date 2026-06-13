# Anforderungsspezifikation — ZunaroDo (Alltagshelfer)

> **Status:** 1.0.0 · **Stand:** 2026-06-13 · **Sprache:** Deutsch
> **Dokumenttyp:** Konsolidiertes Lasten- & Pflichtenheft (Single Source of
> Truth für sämtliche funktionalen und nicht-funktionalen Anforderungen).

Dieses Dokument führt **alle Anforderungen** des Projekts strukturiert
zusammen — abgeleitet aus dem Code (`modules/`, `services/`, `database.py`),
der bestehenden Fachdokumentation und dem Anforderungs-/Traceability-Schema
**R1–R10** (`tools/test_protocol.py`, `tests/TESTGAPS.md`). Es ergänzt die
vorhandene Doku, ohne sie zu duplizieren, und verlinkt jeweils auf die
maßgebliche Detailquelle.

## Inhaltsverzeichnis

1. [Zweck, Geltungsbereich & Vision](#1-zweck-geltungsbereich--vision)
2. [Stakeholder, Rollen & Zielgruppen](#2-stakeholder-rollen--zielgruppen)
3. [Begriffe & Referenzen](#3-begriffe--referenzen)
4. [Anforderungs-Taxonomie & ID-Schema](#4-anforderungs-taxonomie--id-schema)
5. [Übergreifende Produktanforderungen (PA)](#5-übergreifende-produktanforderungen-pa)
6. [Funktionale Anforderungen (FR) je Modul](#6-funktionale-anforderungen-fr-je-modul)
7. [Daten- & Persistenzanforderungen (DA)](#7-daten--persistenzanforderungen-da)
8. [Synchronisations- & Verschlüsselungsanforderungen (SY/EN)](#8-synchronisations--verschlüsselungsanforderungen-syen)
9. [KI-/LLM-Anforderungen (KI)](#9-ki-llm-anforderungen-ki)
10. [Lizenz-, Preis- & Bezahlanforderungen (LI)](#10-lizenz--preis--bezahlanforderungen-li)
11. [Rechtliche & Compliance-Anforderungen (CO)](#11-rechtliche--compliance-anforderungen-co)
12. [Mobile-/Android-Anforderungen (MO)](#12-mobile-android-anforderungen-mo)
13. [Schnittstellen-Anforderungen (IF)](#13-schnittstellen-anforderungen-if)
14. [Konfigurations-Anforderungen (CFG)](#14-konfigurations-anforderungen-cfg)
15. [Nicht-funktionale Anforderungen (NFR)](#15-nicht-funktionale-anforderungen-nfr)
16. [Qualitäts-, Test- & Release-Anforderungen (QA)](#16-qualitäts--test--release-anforderungen-qa)
17. [Traceability-Matrix (R1–R10)](#17-traceability-matrix-r1r10)
18. [Annahmen, Einschränkungen & offene Punkte](#18-annahmen-einschränkungen--offene-punkte)

---

## 1. Zweck, Geltungsbereich & Vision

**Vision.** ZunaroDo ist ein datenschutzfreundlicher Alltagsassistent für den
deutschsprachigen Raum, der private Organisations­aufgaben (Verträge, Finanzen,
Termine, Familie/Haushalt, soziale Pflege) in einer einzigen, **lokal-first**
Anwendung bündelt. Cloud-Funktionen (KI, Sync) sind **strikt optional** und
opt-in.

**Leitprinzip (übergeordnet allen Anforderungen).** *Datenschutz vor Komfort.*
Ohne explizit gesetzte Konfiguration verlässt **kein** Datum das Gerät. Daraus
leiten sich harte Constraints ab (siehe [§5](#5-übergreifende-produktanforderungen-pa),
[§11](#11-rechtliche--compliance-anforderungen-co), [§15](#15-nicht-funktionale-anforderungen-nfr)).

**Geltungsbereich.** Desktop-App (CustomTkinter), CLI, sowie Mobile-App
(KivyMD/Android). Alle drei Präsentationsschichten nutzen **dieselbe**
Capability-Registry, Datenbank und Geschäftslogik.

**Nicht im Geltungsbereich (bewusste Ausschlüsse).**

- Kein werbefinanzierter Tier, keine Tracking-Ads, kein Cookie-Banner.
- Keine Cloud-OCR (Google Vision / AWS Textract / Azure) — OCR bleibt lokal.
- Keine LLM-Anbindung außer Google Gemini (Drittanbieter nur via eigenem
  `LlmProvider`-Adapter).
- Kein Entwickler-seitiges Nutzerkonto / kein zentraler Server für Nutzerdaten.

## 2. Stakeholder, Rollen & Zielgruppen

| Rolle | Interesse / Verantwortung |
| --- | --- |
| Endnutzer (Privatperson, Familie) | Alltagsorganisation, volle Datenhoheit |
| Datenschutzbeauftragter | DSGVO-Konformität, Data-Safety-Form, SDK-Inventar (CO) |
| Security-Owner | Secret-Scanning, TLS, SQLCipher, Tamper-Schutz (EN, SY, CO) |
| Release-Owner | Signierte Builds, Play-Console-Upload, Release-Gate (QA, MO) |
| QA-Owner | Geräte-Matrix, Coverage, Crash-Triage (QA) |
| Dev-Lead | Architektur-Konformität, Capability-Verträge (IF) |
| Anbieter/Lizenzgeber | Lizenz-Token-Signatur, Preismodell, Payment (LI) |

**Zielgruppe:** Datenschutzbewusste Privatnutzer im DACH-Raum; sekundär die
24 EU-Amtssprachen (i18n). Barrierearme Nutzung ist Pflicht (NFR-A11Y).

## 3. Begriffe & Referenzen

**Begriffe.**

- **Capability** — vom LLM und der GUI aufrufbarer Funktionseintrag
  (`name`, `description`, `parameters`-JSON-Schema, `handler`, Flags
  `destructive`/`internal`). Zentrale Abstraktionseinheit.
- **ModuleRegistry / ModuleContext** — Orchestrierung; einziger Dispatch-Pfad
  (`dispatch(name, args)`), Cross-Modul-Aufrufe ohne Direkt-Import.
- **Soft-Delete-Lebenszyklus** — `delete` (Papierkorb) → `restore` → `purge`
  (endgültig). Standard für Module A–E.
- **Tier** — Lizenzstufe (Free, Trial, Pro monatlich/jährlich/Familie).

**Referenzdokumente (maßgeblich für Details).**

| Bereich | Quelle |
| --- | --- |
| Architektur (Python-Schicht) | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Capability-/API-Referenz | [API.md](API.md) |
| Mobile (KivyMD) | [MOBILE.md](MOBILE.md) |
| Android/Play-Compliance | [docs/android/](docs/android/) (01–13) |
| Datenschutz | [PRIVACY.md](PRIVACY.md), [legal/DATENSCHUTZ.md](legal/DATENSCHUTZ.md) |
| Sicherheit | [SECURITY.md](SECURITY.md), [docs/android/03_SECURITY.md](docs/android/03_SECURITY.md) |
| Bezahlung | [PAYMENT.md](PAYMENT.md) |
| Geräte-Kopplung | [PAIRING.md](PAIRING.md) |
| Migrationen | [MIGRATIONS.md](MIGRATIONS.md) |
| Zeitzonen-Audit | [docs/TIMEZONE_AUDIT.md](docs/TIMEZONE_AUDIT.md) |
| Testlücken/Coverage | [tests/TESTGAPS.md](tests/TESTGAPS.md) |
| Release-To-do | [release/GO_LIVE_TODO.md](release/GO_LIVE_TODO.md) |

## 4. Anforderungs-Taxonomie & ID-Schema

**Stabile Themen-IDs R1–R10** (kanonisch in `tools/test_protocol.py`,
Basis der Traceability-Matrix; jeder Test ist auf ≥1 R-Thema gemappt):

| ID | Thema |
| --- | --- |
| **R1** | Aufgaben- & Tagesplanung (Familie, Rotation, Catch-Up, Kalender) |
| **R2** | Erinnerungen & Benachrichtigungen (Scheduler, Persistenz, Systemzeit) |
| **R3** | Kategorien & Prioritäten (Filter/Sortierung) |
| **R4** | Suche & Filter (Volltextsuche, große Datenmengen) |
| **R5** | Datenpersistenz & Mehrgeräte-Sync (FileSync/HttpSync, Konflikt, Re-Entry, TLS/Token) |
| **R6** | Import/Export (CSV, ICS, VCF, PDF) |
| **R7** | Datenschutz & Sicherheit (Policy, Data-Safety, Consent, SQLCipher, Löschung) |
| **R8** | Stabilität & Tests (Smoke, Integration, GUI-Boot, Property/Fuzz, Negativ) |
| **R9** | Play-Store-Release (Check, Store-Listing, Release-Gate, Build/AAB) |
| **R10** | QA / Testübersicht (Protokoll- & Dashboard-Generatoren) |

**Detail-IDs** in diesem Dokument verfeinern die R-Themen:

- `PA-nn` Produktanforderung · `FR-<Modul>-nn` funktional je Modul ·
  `DA-nn` Daten · `SY-nn` Sync · `EN-nn` Verschlüsselung · `KI-nn` LLM ·
  `LI-nn` Lizenz/Preis · `CO-nn` Compliance/Recht · `MO-nn` Mobile ·
  `IF-nn` Schnittstelle · `CFG-nn` Konfiguration · `NFR-<Kat>-nn` ·
  `QA-nn` Qualität/Release.

**Priorität (MoSCoW):** **M** = Muss, **S** = Soll, **C** = Kann.
Ist kein Wert angegeben, gilt **M**.

---

## 5. Übergreifende Produktanforderungen (PA)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| PA-01 | Die App MUSS vollständig offline lauffähig sein; ohne gesetzte Env-/Konfig-Werte verlässt kein Datum das Gerät. | M | R7 |
| PA-02 | Alle Cloud-/Netz-Features (Gemini, IMAP/SMTP, HTTP-Sync, Play-Verify) sind opt-in und einzeln zuschaltbar. | M | R7 |
| PA-03 | Drei Präsentationsschichten (Desktop-GUI, CLI, Mobile) MÜSSEN dieselbe `build_registry(db, output)` und Datenbank verwenden — identische Capabilities, Regeln, Daten. | M | R8 |
| PA-04 | Geschäftslogik gehört ausschließlich in Module; GUI/CLI/Mobile sind passive Aufrufer der Registry. | M | R8 |
| PA-05 | Module sind steckbar (enable/disable, persistiert in DB); das Restsystem interagiert nur über die Capability-Schnittstelle. | M | R8 |
| PA-06 | Normale CRUD-Aktionen laufen ohne Bestätigungsdialog; nur kritische, irreversible Aktionen (Purge, Sammel-Löschungen, endgültiges Löschen von Notizen/Vorlagen) erfordern explizite Freigabe. | M | R7 |
| PA-07 | Alle internen Zeitstempel (`created_at`/`updated_at`/Sync) MÜSSEN UTC (ISO-8601 mit `+00:00`) sein; kalendarische Datumsfelder bleiben bewusst zeitzonenlose Kalendertage. | M | R1 |
| PA-08 | Die Desktop-App startet markenkonform als „ZunaroDo" im hellen Stil, unabhängig vom System-Dark-Mode. | S | R8 |
| PA-09 | Beim ersten Start einer neuen DB MUSS ein Onboarding-Dialog die Wahl „Beispieldaten laden" vs. „Leer starten" bieten (keine ungefragten Demo-Daten). | M | R7 |

## 6. Funktionale Anforderungen (FR) je Modul

Konvention: **(D)** = `destructive=True` (Audit-Log + ggf. Confirm/Lizenz-Gate),
**(I)** = `internal=True` (nicht an das LLM exponiert). Capability-Namen sind
verbindlich (LLM-Tool-Schema + GUI-Formulargenerierung).

### 6.A Modul A — Vertrags- & Fristenmanager (`modules/contracts.py`) · R1, R3

Zweck: Wiederkehrende Vertragskosten verwalten und Kündigungsfristen aus
Mindestlaufzeit, Kündigungsfrist und Auto-Verlängerung berechnen.

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-A-01 | `contracts.add` | Vertrag anlegen (Pflicht: `name`, `category`). |
| FR-A-02 | `contracts.list` | Aktive Verträge listen, optional nach Kategorie. |
| FR-A-03 | `contracts.set_owner` (D) | Vertrag einer Person zuordnen. |
| FR-A-04 | `contracts.upcoming_deadlines` | Anstehende Kündigungsfristen. |
| FR-A-05 | `contracts.report_price_change` (D) | Preisänderung speichern & historisieren (Preisgedächtnis, Differenz/`is_increase`). |
| FR-A-06 | `contracts.generate_cancellation` | Fristgerechtes Kündigungsschreiben (PDF + Mail-Entwurf + Druck) inkl. statischer Affiliate-Empfehlungen (kein Tracking). |
| FR-A-07 | `contracts.delete`/`restore`/`purge` (D) | Soft-Delete-Lebenszyklus; `purge` triggert `notes.cleanup_for_entity`. |
| FR-A-08 | `contracts.list_deleted` | Papierkorb anzeigen. |

**Geschäftsregeln:** Kategorie-Whitelist `{versicherung, mobilfunk, streaming,
strom, sonstiges}`; Fristberechnung berücksichtigt `minimum_term_months`,
`notice_period_months`, `auto_renew_months`.

### 6.B Modul B — Finanz-Cockpit (`modules/finance.py`) · R3

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-B-01 | `finance.add_expense` | Einmalige Ausgabe erfassen. |
| FR-B-02 | `finance.delete_expense`/`restore_expense`/`purge_expense` (D) | Soft-Delete-Lebenszyklus (+ Notizen-Cleanup bei Purge). |
| FR-B-03 | `finance.list_deleted` | Papierkorb. |
| FR-B-04 | `finance.expenses_by_category` | Aggregat pro Kategorie (optional Monat `YYYY-MM`). |
| FR-B-05 | `finance.expenses_by_person` | Aggregat pro Haushaltsmitglied (löst `owner_id` via `family.members`). |
| FR-B-06 | `finance.list_expenses` | Liste mit Summe. |
| FR-B-07 | `finance.monthly_overview` | Monatliche Belastung = einmalige Ausgaben + Vertragskosten (via Modul A). |
| FR-B-08 | `finance.remember_price` / `finance.price_memory` | Preisgedächtnis für Produktpreisvergleich. |
| FR-B-09 | `finance.scan_receipt` | OCR eines Kassenbons (lokal; siehe IF/Privacy). |

**Geschäftsregeln:** Fehlt Modul A, erscheint eine Dashboard-Warnung;
Monatsabschluss-Event am Monatsende.

### 6.C Modul C — Termine & Kalender (`modules/calendar.py`) · R1, R3, R6

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-C-01 | `calendar.add_event` | Termin (einmalig oder wiederkehrend) anlegen. |
| FR-C-02 | `calendar.list_events` | Alle Termine listen. |
| FR-C-03 | `calendar.upcoming` | Anstehende Termine (`horizon_days`, Default 90). |
| FR-C-04 | `calendar.import_ical` (D, I) | `.ics` importieren (neue Einträge; bestehende unverändert). |
| FR-C-05 | `calendar.export_ical` | Export als `.ics` (RFC 5545). |
| FR-C-06 | `calendar.delete_event`/`restore_event`/`purge_event` (D) | Soft-Delete-Lebenszyklus (+ Cleanup). |
| FR-C-07 | `calendar.list_deleted` | Papierkorb. |

**Geschäftsregeln:** Kategorie-Whitelist `{termin, garantie, tuev, steuer,
geburtstag, sonstiges}` (unbekannt → `sonstiges`); `recurrence_days` muss positiv
oder leer sein; deutsche Standard-Steuerfristen werden ergänzt; Geburtstage aus
`family.members` (29.02.→28.02. in Nicht-Schaltjahren). Import durchläuft die
`add_event`-Validierung.

### 6.D Modul D — Familie & Haushalt (`modules/family.py`) · R1, R3

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-D-01 | `family.members` / `add_member` | Haushaltsmitglieder (opt. Geburtstag → Kalender). |
| FR-D-02 | `family.delete_member`/`restore_member`/`purge_member` (D) | Lebenszyklus; Purge nutzt `ON DELETE SET NULL` für Referenzen (+ Notizen-Cleanup). |
| FR-D-03 | `family.list_deleted_members` | Papierkorb. |
| FR-D-04 | `family.add_task` / `tasks` | Wiederkehrende Aufgaben mit Rotation. |
| FR-D-05 | `family.complete_task` (D) | Abhaken; Rotation auf nächste Person; `next_due += interval_days`. |
| FR-D-06 | `family.bulk_complete_overdue` (D) | Alle überfälligen Aufgaben abhaken (Catch-Up via `ctx.call` → Sync-konsistent). |
| FR-D-07 | `family.add_order` / `orders` / `complete_order` (D) | Einmalige Aufträge (Priorität `{hoch, mittel, normal}`, opt. Kategorie-Filter). |
| FR-D-08 | `family.shopping_add` / `shopping_list` / `shopping_mark` | Gemeinsame Einkaufsliste (abhaken/entsperren). |

**Geschäftsregeln:** Mehrfach-Catch-Up verpasster Zyklen MUSS korrekt rotieren
(R1-Kernfall); stabile Prioritäts-Sortierung.

### 6.E Modul E — Soziale Pflege (`modules/social.py`) · R1, R6

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-E-01 | `social.add_contact` / `contacts` | Kontakt mit Wunsch-Rhythmus `cadence_days` (>0, Default 30); Resttage; Filter nach Beziehung. |
| FR-E-02 | `social.import_vcard` (D, I) / `export_vcard` | `.vcf` (RFC 6350 v3.0) Import/Export. |
| FR-E-03 | `social.delete_contact`/`restore_contact`/`purge_contact` (D) | Lebenszyklus (+ Cleanup). |
| FR-E-04 | `social.list_deleted` | Papierkorb. |
| FR-E-05 | `social.mark_contacted` | `last_contacted = heute`. |
| FR-E-06 | `social.draft_message` | Nachrichten-Entwurf (Offline-Vorlage `{kurz, treffen, geburtstag}` oder LLM-generiert). |

### 6.F Modul F — Posteingang & Vorschläge (`modules/inbox.py`) · R7

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-F-01 | `inbox.analyze_mail` | Mail-Text analysieren → Vorschläge (regelbasiert + optional LLM). |
| FR-F-02 | `inbox.proposals` | Offene Vorschläge listen. |
| FR-F-03 | `inbox.accept_proposal` (D) | Übernehmen → Ziel-Capability via `ctx.call`. |
| FR-F-04 | `inbox.reject_proposal` (D) / `bulk_reject_open` (D) | Ablehnen (einzeln/gesammelt). |
| FR-F-05 | `inbox.bulk_delete_archived` (D) | Archivierte (übernommen/abgelehnt) sammeln & löschen. |
| FR-F-06 | `inbox.update_proposal` (D) | Offenen Vorschlag vor Übernahme bearbeiten (Inline-Editor). |
| FR-F-07 | `inbox.import_eml` | `.eml`-Datei einlesen. |
| FR-F-08 | `inbox.fetch_imap` | Ungelesene Mails via IMAP (Credentials fehlen → übersprungen, nicht fatal). |

**Geschäftsregel (LLM-Halluzinations-Schutz, kritisch):** LLM-Vorschläge werden
gegen eine **Allowlist** `{contracts.add, contracts.report_price_change,
family.add_order, calendar.add_event}` **und** das Pflichtparameter-Schema
validiert, bevor sie in der Ablage landen. Regelbasierte Erkennung: Preiserhöhung,
Vertragsbestätigung, Aufgaben/Termine; Euro-/Datums-Extraktion per Regex.

### 6.G Modul G — Statistiken & Trends (`modules/statistics.py`) · R3, R6

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-G-01 | `stats.expenses_per_month` | Summe je Monat, letzte N (Default 12). |
| FR-G-02 | `stats.expenses_per_category` | Aggregat je Kategorie für ein Jahr. |
| FR-G-03 | `stats.contracts_overview` | Anzahl, Monats-/Jahressumme, Top-3-Kostentreiber. |
| FR-G-04 | `stats.yearly_summary` | Jahresüberblick: Summe, Top-5-Kategorien, Monatsschnitt. |
| FR-G-05 | `stats.export_yearly_pdf` | Druckbarer PDF-Jahresbericht (fpdf2). |

### 6.H Modul H — Tagesstruktur & Energie (`modules/daystructure.py`) · R1

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-H-01 | `day.log_energy` | Tag 1–5 bewerten (Upsert für heute). |
| FR-H-02 | `day.recent_entries` | Letzte Einträge (Limit, Default 30). |
| FR-H-03 | `day.recommendation` | Empfehlung aus den letzten 7 Einträgen. |

### 6.I Modul I — Volltextsuche (`modules/search.py`) · R4

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-I-01 | `system.search` | LIKE-Suche über Verträge, Ausgaben, Termine, Mitglieder, Aufträge, Kontakte, Vorschläge, Notizen; vereinheitlichte Treffer (`source`/`entity_id`/`title`/`detail`). |
| FR-I-02 | Filter | Optionale `date_from`/`date_to`, `status`, `category`; ein gesetzter Filter schließt Quellen ohne das Feld aus; Suche auch ohne Suchwort möglich (mit Filter). |
| FR-I-03 | Mindestlänge | ≥2 Zeichen ODER mindestens ein Filter; `limit` Default 50. |

### 6.J Modul J — Notizen (`modules/notes.py`)

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-J-01 | `notes.add` / `list` / `get` | Notiz (Pflicht `title`), optional gefiltert nach Entität. |
| FR-J-02 | `notes.update` (D) / `attach` (D) | Inhalt aktualisieren; an Entität heften/lösen. |
| FR-J-03 | `notes.delete` (D) | Endgültig löschen. |
| FR-J-04 | `notes.cleanup_for_entity` (D, I) | Alle Notizen einer Entität löschen (von A–E bei Purge gerufen). |
| FR-J-05 | `notes.add_attachment` (D) / `list_attachments` | n:m-Verknüpfungen. |

**Geschäftsregel:** erlaubte Entity-Types `{contracts, expenses, calendar,
social, family, orders}`; `title` darf nicht leer sein.

### 6.K Modul K — Tages-/Wochenübersicht (`modules/overview.py`) · R1

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-K-01 | `system.agenda` | Anstehende Fristen aller aktiven Module nach Kalendertag gruppiert (`horizon_days`, Default 7); Überfällige separat. |

**Geschäftsregel:** datums- statt zeitbasiert → robust gegen System-/DST-Sprünge
(kein Double-Counting); deutsche Wochentags-Labels.

### 6.L Modul L — Aufgaben-Vorlagen (`modules/templates.py`) · R1

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-L-01 | `templates.add` / `list` | Vorlage (Pflicht `title`, `interval_days` Default 7, >0). |
| FR-L-02 | `templates.delete` (D) | Vorlage löschen. |
| FR-L-03 | `templates.apply` (D) | Aus Vorlage instanziieren → `family.add_task` via `ctx.call` (Pflicht `assignees`, opt. `first_due`). |

### 6.M Modul M — Geräte-/Nutzer-Profile (`modules/profiles.py`) · R5, R7

| ID | Capability | Beschreibung |
| --- | --- | --- |
| FR-M-01 | `system.profiles` | Profile listen, aktives markieren. |
| FR-M-02 | `system.profile_create` | Profil anlegen (`name` reduziert auf `[A-Za-z0-9_-]`, max 32), aktiv setzen. |
| FR-M-03 | `system.profile_switch` | Aktives Profil wechseln (leer = Default); wirkt nach Neustart. |

**Geschäftsregel:** Profile sind auch im Free-Tier offen (Datentrennung ist kein
Pro-Feature). Pro Profil eigene DB-Datei + eigenes State-Verzeichnis.

### 6.X Modulübergreifende funktionale Regeln

| ID | Anforderung | R |
| --- | --- | --- |
| FR-X-01 | Jedes Modul liefert `get_events(horizon_days)` für Dashboard/Agenda; `ModuleRegistry.collect_events` aggregiert chronologisch. | R1 |
| FR-X-02 | Cross-Modul-Aufrufe ausschließlich über `ModuleContext.call(...)` (kein Direkt-Import, kein Fremd-SQL). | R8 |
| FR-X-03 | Validierungs-Standard: Pflichtfelder nicht leer, positive Integer-Validierung (`interval_days`/`recurrence_days`/`cadence_days` > 0), ISO-Datum mit klarer Fehlermeldung statt Crash. | R8 |
| FR-X-04 | Soft-Delete-Lebenszyklus (`delete`→`restore`→`purge`) gilt einheitlich für Module A–E; Purge räumt verwaiste Notizen auf. | R7 |

---

## 7. Daten- & Persistenzanforderungen (DA)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| DA-01 | Persistenz erfolgt in **SQLite** (optional SQLCipher), eine DB-Datei je Profil; jede Entität hinter einem Repository (SQL gekapselt). | M | R5 |
| DA-02 | Schema-Versionierung über `PRAGMA user_version`; `CURRENT_SCHEMA_VERSION = 3`; Migrationen idempotent (`_ensure_column` für partielle DBs). v1→v2: Soft-Delete-Spalten, Audit-Log, Task-Templates, Note-Attachments. v2→v3: `priority`+`category` für `household_orders`. | M | R5 |
| DA-03 | Soft-Delete via `deleted_at` auf contracts, expenses, calendar_events, social_contacts, family_members, household_orders, notes; `list_all` filtert Default „nicht gelöscht". | M | R7 |
| DA-04 | `ON DELETE SET NULL` für Fremdschlüssel (z. B. `owner_id`) wirkt erst nach **purge**, nicht nach Soft-Delete. | M | R5 |
| DA-05 | Thread-Sicherheit: `_SafeConnection`-Wrapper mit `RLock`, `check_same_thread=False`; Multi-Statement-Transaktionen unter `with db.lock`. | M | R5, R8 |
| DA-06 | Audit-Log (`audit_log`) schreibt jeden erfolgreichen destruktiven Call mit Capability, Argumenten, heuristischem Entity-Bezug; Index auf `entity_type+entity_id`. | M | R7 |
| DA-07 | Migrationen MÜSSEN zeilenerhaltend sein (bestehende Datensätze überleben Upgrade). | M | R5 |

## 8. Synchronisations- & Verschlüsselungsanforderungen (SY/EN)

### 8.1 Synchronisation (SY)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| SY-01 | Zwei austauschbare Provider gegen dieselbe Schnittstelle: **FileSyncProvider** (JSONL-Event-Log `sync_events.jsonl` im geteilten Ordner) und **HttpSyncProvider** (gegen `services/sync_server.py`). | M | R5 |
| SY-02 | Kausale Ordnung via **Lamport-Clock** (thread-sicher, monoton; Empfänger `max(lokal, empfangen)+1`); Sortier-Schlüssel `(lamport, timestamp, device_id, event_id)`; Events ohne Lamport-Feld laden als 0 (Backward-Compat). | M | R5 |
| SY-03 | Konfliktauflösung **Last-Writer-Wins**, deterministisch reihenfolge-unabhängig (Tie-Break über `device_id`). | M | R5 |
| SY-04 | **Re-Entry-Schutz**: thread-lokale Flags (`in_synced`, `replaying`) + `RLock` schützen `apply_remote` vor parallelen GUI-Dispatches; geschachtelte `ctx.call` innerhalb eines geloggten Calls werden nicht doppelt geschrieben. | M | R5 |
| SY-05 | **PeriodicSyncWorker**: Daemon-Thread, Default-Intervall 300 s (Minimum 10 s), Fehler werden geschluckt (kein Crash). | M | R5 |
| SY-06 | **Log-Kompaktierung** server- und clientseitig bei `MAX_LOG_LINES = 5000` (älteste verwerfen), lock-basiert. | M | R5 |
| SY-07 | HTTP-Server: **Bearer/Token-Auth** (`ALLTAGSHELFER_SYNC_TOKEN`), Rate-Limit 60 POSTs/60 s je Client-IP, **Warnung** beim Start ohne Token auf öffentlicher Bind-Adresse. | M | R5, R7 |
| SY-08 | **TLS** via `--cert/--key`; ohne Zertifikat erzeugt `--self-signed` eines (Default `./sync-cert.pem`/`./sync-key.pem`). | M | R5, R7 |
| SY-09 | `DEFAULT_SYNCED_CAPABILITIES` deckt die relevanten Mutationen aus A–E ab (contracts.add/report_price_change/set_owner, finance.add_expense/remember_price, calendar.add_event/delete_event, family.add_member/add_task/complete_task/add_order/complete_order/shopping_add/shopping_mark, social.add_contact/mark_contacted). | M | R5 |
| SY-10 | Geräte-Kopplung (Pairing) gemäß [PAIRING.md](PAIRING.md): KDF, Identität, Secure-Store; Backend `keyring` (Default) oder `memory` (Tests). | S | R5, R7 |

### 8.2 Verschlüsselung & Backup (EN)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| EN-01 | SQLCipher aktiv, wenn `ALLTAGSHELFER_DB_KEY` gesetzt **und** `sqlcipher3` installiert ist (`encryption_mode == "sqlcipher"`), sonst Klartext. | M | R7 |
| EN-02 | Schlüsselübergabe als Hex-Form `x'<hex>'` an `PRAGMA key` (keine Quote/Backslash/NUL-Probleme); Mindestlänge 8 Zeichen, NUL-Bytes abgelehnt (`ValueError`). | M | R7 |
| EN-03 | Desktop: kein stilles Unverschlüsselt-Fallback — Key gesetzt + `sqlcipher3` fehlt ⇒ harter `RuntimeError` mit Installationshinweis. (Mobile/Buildozer: definiertes degradiertes Verhalten dokumentieren.) | M | R7 |
| EN-04 | Schlüsselquellen in Reihenfolge: Env-Var → Android Hardware-Keystore (`de.alltagshelfer.dbkey.DbKeyProvider` via pyjnius) → None (Plain). | M | R7 |
| EN-05 | **Online-Backup** ohne App-Stop: Plain via `Connection.backup()`; SQLCipher via `ATTACH ... KEY ...; SELECT sqlcipher_export(...)` (Backup ist selbst verschlüsselt, opt. separater `ALLTAGSHELFER_BACKUP_KEY`). | M | R5, R7 |
| EN-06 | **AutoBackupWorker**: Daemon, Default 24 h, Retention 10, erstes Backup ~60 s nach Start; jedes Backup wird verifiziert (Schema lesbar), defekte Backups gelöscht, alte über Retention gepruned. | M | R5 |
| EN-07 | Backup-Dateiname sortierbar: `alltagshelfer-YYYYMMDD-HHMMSS.db` im Verzeichnis `backups` (konfigurierbar). | S | R6 |

## 9. KI-/LLM-Anforderungen (KI)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| KI-01 | LLM-Backend ist **provider-agnostisch** über `services/llm.py` (`LlmProvider`-Vertrag); einzige mitgelieferte Implementierung ist Google Gemini (`services/gemini.py`). | M | R7 |
| KI-02 | Aktivierung nur, wenn `GOOGLE_API_KEY`/`GEMINI_API_KEY` gesetzt **und** `google-generativeai` installiert; sonst Offline-Modus mit regelbasiertem Intent-Router. Im Free-Tier wird Gemini gar nicht initialisiert. | M | R7, R10 |
| KI-03 | **Tool-Use-Schleife** mit `function_declarations`; Default `max_iterations=12`, `max_output_tokens=2048` (konfigurierbar). | M | — |
| KI-04 | Konversationsverlauf bleibt zwischen Aufrufen erhalten (`Assistant._history`); **Streaming** der Text-Teile via `stream_callback`; **Token-Verbrauch** wird gemessen. | M | — |
| KI-05 | **Confirm-Callback** vor jeder destruktiven Capability (Nutzerfreigabe). | M | R7 |
| KI-06 | **Robuste Fehlerbehandlung**: Netz-/Rate-Limit-Fehler liefern Nutzermeldung statt Crash. | M | R8 |
| KI-07 | **Halluzinations-Schutz**: Das LLM sieht nur explizit übergebene Tool-Specs; Inbox-Vorschläge werden gegen Allowlist + Pflichtparameter-Schema validiert (siehe FR-F). | M | R7 |
| KI-08 | Der Default-Modell-Name (`gemini.model`, Default `gemini-2.5-flash`) ist konfigurierbar. | C | — |

## 10. Lizenz-, Preis- & Bezahlanforderungen (LI)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| LI-01 | Fünf Tiers, **kein** werbefinanzierter Tier: **Free** (1 Person, 2 Module Verträge+Familie, kein KI/Sync), **Trial** (14 Tage voller Pro, einmalig), **Pro monatlich**, **Pro jährlich** (−20 %), **Pro Familie** (Flat, bis 5 Personen). | M | — |
| LI-02 | Preise (brutto, inkl. 19 % USt.): Basis `6,99 €/Monat` (bis 2 Personen) + `1,99 €/Monat` je weiterer Person; Familie `12,99 €/Monat` Flat (Cap 5); Jahresrabatt 20 %. | M | — |
| LI-03 | Mobile (iOS/Android) erhalten **25 % Markup** (Store-Cut); CHF-Umrechnung via `convert_to_chf` (Rate 0,94, CH-MwSt 8,1 % statt DE 19 %). | M | — |
| LI-04 | `recommended_tier(persons)` empfiehlt den günstigsten passenden Tier (z. B. 4 Personen → Annual). | S | — |
| LI-05 | **Durchsetzung** via Pre-Dispatch-Hook (`services/license_gate.py`): gesperrte Capabilities liefern `{"tier_locked": True}`; GUI markiert gesperrte Modul-Tabs mit `[Pro]`. | M | R7 |
| LI-06 | **Immer offen** (Free): Suche, Statistiken, Notizen, Tagesstruktur, `system.*`, `stats.*`. | M | — |
| LI-07 | **Trial** einmalig 14 Tage, nicht durch Neuinstallation erneuerbar (`license.trial_started_at`). | M | — |
| LI-08 | **Grace-Period** 7 Tage nach Abo-Ablauf → danach Auto-Downgrade auf Free. | M | — |
| LI-09 | **Grandfathering**: Bestandsdaten beim Pricing-Launch behalten unbefristeten Lese-Zugriff auf alle Module (aber keine neuen Pro-Features wie KI/Sync). | M | — |
| LI-10 | **Tamper-Schutz (Ed25519)**: Pro-Status nur mit gültigem signiertem Token; reines DB-Setzen von `license.tier=pro_*` bleibt Free. Token-Format `<b64url(payload)>.<b64url(sig)>`, Offline-Verifikation, `REVOKED_TOKEN_IDS`. | M | R7 |
| LI-11 | **Aktivierungs-Flow (BGB §356 Abs. 5)**: vor Pro-Aktivierung drei aktive Bestätigungen (AGB/Datenschutz gelesen; sofortige Ausführung vor Fristablauf; Verlust des 14-Tage-Widerrufsrechts), GUI-agnostisch via Confirm-Callback; ohne alle drei → Ablehnung. | M | R7 |
| LI-12 | **Payment-Provider** provider-neutral: ExternalToken (manuell), Play Billing (`/verify/play` → signiertes Ed25519-Token; SKUs `zunarodo_pro_monthly/_yearly/_family`), Adapter für Paddle/Lemon/Stripe (Webhook → `PaymentEvent`, Idempotenz über `transaction_id`). | M | — |
| LI-13 | Affiliate-Empfehlungen sind statisch/kontextuell (Verbraucherzentrale, Stiftung Warentest), **ohne** Tracking/Cookies (DSGVO-konform). | M | R7 |

## 11. Rechtliche & Compliance-Anforderungen (CO)

> Detailquelle: [docs/android/](docs/android/) (insbes. 02/03/04/10/11),
> [legal/](legal/), [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md),
> [release/DATA_SAFETY_CONSOLE_ANSWERS.md](release/DATA_SAFETY_CONSOLE_ANSWERS.md).

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| CO-01 | **DSGVO-Datensparsamkeit**: lokale Datenhaltung, keine Tracking-SDKs; Gemini/IMAP als optionale App-Funktionalität modelliert, nicht für Werbung/Analytics geteilt. Rechtsgrundlage Art. 6 Abs. 1 lit. b DSGVO (lokal), lit. a (Einwilligung) für Gemini. | M | R7 |
| CO-02 | **Recht auf Löschung & Portabilität**: In-App-Vollöschung (`delete_all_user_data` / `Database.wipe_all_data`), aus dem Mobile-„Mehr"-Screen erreichbar; Komplett-Export (`export_all` / `export_all_json`); in [legal/DATENSCHUTZ.md](legal/DATENSCHUTZ.md) dokumentiert. **Vor erstem Release zwingend.** | M | R7 |
| CO-03 | **Data-Safety-Form** (Play Console) = „keine Daten erhoben" (solange kein Crash-/Analytics-SDK), `encrypted_in_transit: true`, `user_can_request_deletion: true`; konsistent zum SDK-Inventar in [docs/android/04_PRIVACY_PERMISSIONS.md](docs/android/04_PRIVACY_PERMISSIONS.md); maschinell geprüft (`tools/data_safety.py`). Inkonsistenz Form↔Policy ist häufiger Ablehnungsgrund. | M | R7, R9 |
| CO-04 | **Permission-Whitelist** (siehe Tabelle unten): nur `INTERNET`, `POST_NOTIFICATIONS`, optional `ACCESS_NETWORK_STATE`; keine sensiblen/verbotenen Permissions; Laufzeit-`POST_NOTIFICATIONS` (Android 13+), App bleibt bei Verweigerung nutzbar (degradiert). | M | R7, R9 |
| CO-05 | **Pflicht-Rechtstexte** vorhanden: Impressum (**§5 DDG**, löst seit Mai 2024 §5 TMG ab / §18 Abs. 2 MStV — in [legal/](legal/) auf DDG aktualisiert), Datenschutzerklärung (Art. 13 DSGVO, URL öffentlich/HTTP 200), AGB, Widerrufsbelehrung (DE+EN), mit `[PLATZHALTER]`; In-App in ≤2 Taps erreichbar; vor Veröffentlichung anwaltlich prüfen. | M | R9 |
| CO-06 | **Keine Klartext-Kommunikation**: `usesCleartextTraffic` false (HTTP nur localhost), keine `http://`-URLs in Release-Pfaden; keine hardcodierten Secrets im Repo (Gitleaks/Secret-Scan); exportierte Komponenten nur mit `permission`-Attribut/`exported`-Pflicht. | M | R7 |
| CO-07 | **Automatisierter Compliance-Check** `tools/playstore_check.py --strict` MUSS 0 FAIL liefern (SDK-Level, Manifest, verbotene APIs, Versionscode-Konsistenz, SDK-Inventar-Sync); CI-Gate `android-compliance.yml`, jeder PR grün. | M | R9 |
| CO-08 | **Content-Rating/Zielgruppe**: IARC USK 0/PEGI 3, „Mixed audiences" ab 13 J., keine Werbung, keine In-App-Käufe in der App (Lizenz extern via Browser-Redirect). | M | R9 |
| CO-09 | **Krypto-Vorgaben**: nur AES-GCM (symmetrisch) und Ed25519 (Signaturen); verboten DES/AES-ECB/MD5/SHA-1 (Sicherheit); Zufall aus `secrets`/`SecureRandom`. License-Signing-Key-Rotation alle 24 Monate. | M | R7 |
| CO-10 | **Tamper-/Tracking-Audit**: Secret-Scanning (CI), Pen-Test-Rotation (jährlich), `bandit`/`mobsfscan`/`pip-audit`; DSGVO-Meldepflicht 72 h (Art. 33) bei Incidents; Post-Mortem in `docs/incidents/`. | S | R7 |

**Permission-Matrix (Android, verbindlich):**

| Permission | Status | Runtime-Prompt | Begründung |
| --- | --- | --- | --- |
| `INTERNET` | ja | nein | Sync-Server + optional Gemini |
| `POST_NOTIFICATIONS` (API 33+) | optional | ja | Termin-Erinnerungen; bei Verweigerung degradiert |
| `ACCESS_NETWORK_STATE` | optional | nein | Connectivity-Check vor Sync |
| `READ/WRITE_EXTERNAL_STORAGE`, `MANAGE_EXTERNAL_STORAGE` | **verboten** | — | Scoped Storage; Photo-Picker statt Storage-Permission |
| `QUERY_ALL_PACKAGES`, `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, `SCHEDULE_EXACT_ALARM`, `RECEIVE_BOOT_COMPLETED` | **verboten** | — | nicht im Funktionsumfang / Play prüft Notwendigkeit |
| `CAMERA`, `READ_MEDIA_IMAGES`, Standort, Kontakte, SMS, Bluetooth, NFC, Biometrie | **verboten** | — | nicht benötigt (OCR über Photo-Picker) |

## 12. Mobile-/Android-Anforderungen (MO)

> Detailquelle: [MOBILE.md](MOBILE.md), [docs/android/01_ARCHITECTURE.md](docs/android/01_ARCHITECTURE.md),
> [docs/android/05_PERFORMANCE.md](docs/android/05_PERFORMANCE.md),
> [docs/android/08_ACCESSIBILITY.md](docs/android/08_ACCESSIBILITY.md),
> [buildozer.spec](buildozer.spec).

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| MO-01 | Zweite Präsentationsschicht in **KivyMD**, gebaut zur APK/AAB via **Buildozer/python-for-android**; nutzt dieselbe Registry/DB/Regeln wie Desktop. | M | R8 |
| MO-02 | Phone-reduziertes UI: 5 Bottom-Nav-Bereiche statt 14 Desktop-Tabs, vertikale Listen, FAB; Pure-Logik in `mobile/helpers.py` Kivy-entkoppelt und unittest-bar. | M | R8 |
| MO-03 | SDK-Level: `android.api = 35` (target/compile, Play-Mindestanforderung ab Aug 2025), `android.minapi = 24` (Android 7, ≥98 % Geräte), `android.ndk_api = 24`; Archs `arm64-v8a, armeabi-v7a` (+ x86_64 für Emulator-CI). | M | R9 |
| MO-04 | Auslieferung als **App Bundle (AAB)** mit **Play App Signing** (Google hält Signing-Key, Upload-Key lokal); `android:allowBackup="false"`; jede `Activity`/`Service`/`Receiver` mit explizitem `exported`-Attribut. | M | R9 |
| MO-05 | Versionscode strikt monoton steigend, in `buildozer.spec` (`android.numeric_version`) **und** `playstore.yml` (`identity.version_code`/`version_name`) synchron (aktuell 2 / 1.0.0); `versionName` SemVer. | M | R9 |
| MO-06 | Release-Build gestrippt/optimiert (R8/ProGuard-Äquiv. via `p4a --release --optimize-python`), signiert mit Upload-Keystore (vier CI-Secrets `ANDROID_KEYSTORE_BASE64`/`_PASSWORD`/`KEY_ALIAS`/`KEY_ALIAS_PASSWORD`); `.jks` nie im Git; Demo-DBs via `source.exclude_exts = db,sqlite` ausgeschlossen. | M | R9 |
| MO-07 | SQLCipher-Recipe baut für ARM (beide) + x86_64 (Schlüssel aus Android-Keystore); ML-Kit-OCR on-device; auf echtem Gerät zu verifizieren (offene Punkte in [release/GO_LIVE_TODO.md](release/GO_LIVE_TODO.md)). | M | R7, R9 |
| MO-08 | Closed-Testing-Gate: ≥12 Tester, ≥14 Tage; Nachweis in `release/closed-test-*.md`, geprüft durch `evaluate_closed_test_gate`. Rollout gestaffelt 5 %→20 %→50 %→100 % mit Vitals-Monitoring. | M | R9 |
| MO-09 | Store-Assets echt (keine Platzhalter): Icon/Adaptive-Icon/Presplash/Feature-Graphic (1024×500) + 3–8 echte In-App-Screenshots; Asset-Gate `tools/gen_assets.py --check` grün. | M | R9 |
| MO-10 | Hintergrund-Sync via WorkManager-Äquivalent mit Periodic-Intervall ≥15 min; Foreground-Service nur `dataSync`; keine Netzwerk-Aufrufe/DB-Writes im Main-Thread (ANR-Vermeidung). | M | R8, R9 |

**Geräte-Kopplung (Secure Pairing)** — Detail: [PAIRING.md](PAIRING.md):

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| MO-P1 | Gerätegebundene Identität: Ed25519-Langzeit-Schlüsselpaar lokal beim Erststart; privater Schlüssel verlässt das Gerät nie im Klartext; `device_id` (UUIDv4) + `device_name`. | M | R5, R7 |
| MO-P2 | Drei Kopplungswege: **QR-Code** (TTL 30 s–10 min, Default 1 min), **USB** (TTL ~60 s, kein Funk), **SMS-Link** (TTL 5 min–24 h, PIN out-of-band). | S | R5 |
| MO-P3 | Kryptografie: SPAKE2 (PAKE) über TLS-1.3-PSK, HKDF-SHA256-Ableitung, ChaCha20-Poly1305; gegenseitige Authentisierung **ohne Server/Konto**; Fingerprint SHA-256 als 5×4-Base32-Gruppen zum Out-of-Band-Vergleich. | M | R5, R7 |
| MO-P4 | Sichere Speicherung: privater Schlüssel + `sync_psk` + Einmal-Secrets im OS-Secure-Store (Android Keystore / Windows Credential Manager / iOS Keychain), **niemals** in DB; öffentliche Felder (`IK_pub_peer`, Fingerprint, Status) dürfen in die DB. | M | R7 |
| MO-P5 | Peer-Lebenszyklus `active → suspended → revoked`; Revocation löscht Schlüsselmaterial und sendet signierten Revocation-Event; Replay-Schutz via Nonce + Ablaufzeit + One-Time-Token. | M | R5, R7 |

## 13. Schnittstellen-Anforderungen (IF)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| IF-01 | **Front-End ↔ Modul**: einziger Dispatch-Pfad `ModuleRegistry.dispatch(name, args) -> dict`; Permission-/Kategorie-Checks und Audit-/Sync-Hooks sitzen hier. | M | R8 |
| IF-02 | **Modul ↔ Modul**: `ModuleContext.call(...)` (lose Kopplung, Re-Entry-Schutz im Sync-Hook). | M | R5, R8 |
| IF-03 | **Dashboard**: `ModuleRegistry.collect_events(...)` aggregiert Events aller Module chronologisch. | M | R1 |
| IF-04 | Registry-Hilfen: `get_capability`, `destructive_capability_names`, `tool_schemas`, `module_states`, `set_module_enabled`. | M | R8 |
| IF-05 | OCR-Engine-Priorität (alle lokal, keine Cloud): ML Kit (Android) → pytesseract (`deu`) → easyocr (`de`, gpu=False) → klarer Hinweis statt Crash. | M | R7 |
| IF-06 | Mail: SMTP-Versand (Kündigungen) und IMAP-Abruf im Worker-Thread (kein GUI-Einfrieren); SMTP-**Verbindungsdaten** (Host/Port/User/Sender/StartTLS) werden in der App (DB) konfiguriert — bewusst ohne eigene Env-Vars. Das **Passwort** (`smtp.pass`) ist ein `SECRET_KEY` und wird **nicht** in der DB persistiert (Keyring/Env-Var; siehe CFG-02). | M | R7 |
| IF-07 | Desktop-Notifikationen mit Fallback-Kette plyer → winsound+print → print (Timeout 10 s). | S | R2 |

## 14. Konfigurations-Anforderungen (CFG)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| CFG-01 | Konfig-Quellen in fester Reihenfolge: **Defaults (Code) < DB (`SettingsRepository`) < Umgebungsvariablen**. | M | R7 |
| CFG-02 | **SECRET_KEYS** (`gemini.api_key`, `imap.pass`, `smtp.pass`, `db.key`, `backup.key`) werden **nie** in die DB persistiert — nur Env-Var/Keyring. | M | R7 |
| CFG-03 | `i18n.language` Default `auto`; löst auf Gerätsprache auf, Fallback-Kette angeforderte Sprache → DE → Key selbst. | M | R8 |
| CFG-04 | Logging: Root-Logger `alltagshelfer`, Default INFO (`ALLTAGSHELFER_LOG_LEVEL`), optional RotatingFileHandler (2 MB, 5 Backups, UTF-8), `propagate=False`. | M | R8 |

**Env-Variablen-Matrix** (Quelle: [.env.example](.env.example)). `[SECRET]` =
nicht in DB:

| Variable | Zweck | Default/Hinweis |
| --- | --- | --- |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` `[SECRET]` | Gemini aktivieren | leer → Offline |
| `ALLTAGSHELFER_GEMINI_MODEL` | Modellwahl | `gemini-2.5-flash` |
| `ALLTAGSHELFER_FORCE_GEMINI_REST` | REST-Pfad erzwingen | Tests/Desktop |
| `ALLTAGSHELFER_DB_KEY` `[SECRET]` | SQLCipher Live-DB | leer → Klartext |
| `ALLTAGSHELFER_BACKUP_KEY` `[SECRET]` | separater Backup-Schlüssel | optional |
| `ALLTAGSHELFER_IMAP_HOST/USER/PASS/FOLDER` (`PASS` `[SECRET]`) | Mail-Import | `FOLDER`=INBOX |
| `ALLTAGSHELFER_SYNC_DIR` | Datei-Sync-Ordner | leer → kein Sync |
| `ALLTAGSHELFER_SYNC_URL` | HTTP-Sync-Server | — |
| `ALLTAGSHELFER_SYNC_TOKEN` `[SECRET]` | Sync-Auth | — |
| `ALLTAGSHELFER_DEVICE_ID` | stabile Geräte-ID | sonst UUID |
| `ALLTAGSHELFER_SYNC_LOG` | Server-Event-Log (JSONL) | — |
| `ALLTAGSHELFER_PROFILE` | benanntes Profil | Default-Profil |
| `ALLTAGSHELFER_DATA_DIR` / `ALLTAGSHELFER_CONFIG_DIR` | Verzeichnis-Override | portabel/Tests |
| `ALLTAGSHELFER_LOG_LEVEL` | Log-Level | INFO |
| `ALLTAGSHELFER_PAIRING_BACKEND` | keyring \| memory | keyring |
| `ALLTAGSHELFER_PLATFORM` | Plattform-Override (Mobile-Markup) | — |
| `ZUNARODO_PLAY_VERIFY_URL` | Play-Verify-Server-URL | ins Release gebacken |

> SMTP-**Verbindungsdaten** werden in der App (DB) konfiguriert (keine eigenen
> Env-Vars). Das **Passwort** `smtp.pass` ist `SECRET_KEY` (CFG-02) und landet
> nie in der DB — es kommt aus OS-Keyring oder Umgebung. Kein Widerspruch: nur
> nicht-geheime SMTP-Felder werden persistiert.

## 15. Nicht-funktionale Anforderungen (NFR)

### 15.1 Sicherheit (NFR-SEC) · R7

| ID | Anforderung |
| --- | --- |
| NFR-SEC-01 | Secrets nur aus Env-Var/Keyring, nie in DB/Git (Gitleaks-Konfiguration `.gitleaks.toml`). |
| NFR-SEC-02 | Optionale At-Rest-Verschlüsselung (SQLCipher) inkl. verschlüsselter Backups. |
| NFR-SEC-03 | Transport: TLS für HTTP-Sync; Token-Auth; Warnung bei ungesichertem öffentlichem Bind. |
| NFR-SEC-04 | Lizenz-Integrität via Ed25519; manipuliertes DB-Tier bleibt wirkungslos. |
| NFR-SEC-05 | LLM-Eingaben/-Ausgaben werden gegen Allowlist/Schema validiert (kein blindes Tool-Dispatch). |

### 15.2 Datenschutz (NFR-PRIV) · R7

| ID | Anforderung |
| --- | --- |
| NFR-PRIV-01 | Lokal-first: Default-Betrieb ohne jede Netzkommunikation. |
| NFR-PRIV-02 | Keine Tracking-/Analytics-/Werbe-SDKs; keine Cloud-OCR. |
| NFR-PRIV-03 | Vollständige In-App-Datenlöschung jederzeit erreichbar. |
| NFR-PRIV-04 | Data-Safety-Angaben konsistent zum tatsächlichen Datenfluss. |

### 15.3 Performance (NFR-PERF) · R4, R8

| ID | Anforderung |
| --- | --- |
| NFR-PERF-01 | Hot-Pfade (Suche, Aggregate) haben ein Regressionsbudget (`tests/test_performance.py`). |
| NFR-PERF-02 | IMAP/OCR/Backup laufen in Worker-Threads; UI friert nicht ein. |
| NFR-PERF-03 | Statistiken/Charts ohne externe Diagramm-Library (tk.Canvas), keine schweren Abhängigkeiten im Hot-Pfad. |
| NFR-PERF-04 | Mobile-Budgets (Release-Halt bei Überschreitung, [docs/android/05_PERFORMANCE.md](docs/android/05_PERFORMANCE.md)): Cold-Start ≤ 2000 ms, Warm-Start ≤ 800 ms, Listen-Scroll ≥ 55 fps, Heap idle ≤ 80 MB (2-GB-Gerät), AAB-Download ≤ 40 MB; 0 Netzwerk-/DB-Aufrufe im Main-Thread. |
| NFR-PERF-05 | Play-Vitals-Schwellen: **Crash-Rate < 1,09 %**, **ANR-Rate < 0,47 %** (User-perceived); Überschreitung stoppt den gestaffelten Rollout. |

### 15.4 Usability & UX (NFR-USE) · R8

| ID | Anforderung |
| --- | --- |
| NFR-USE-01 | Bestätigungsdialoge nur bei kritischen, irreversiblen Aktionen (PA-06). |
| NFR-USE-02 | Dynamische Formulare aus Capability-Parameter-Schema (GUI + Inbox-Inline-Editor). |
| NFR-USE-03 | Onboarding-Wahl Beispieldaten/leer beim ersten Start. |
| NFR-USE-04 | Aktives Profil sichtbar in der Sidebar. |

### 15.5 Internationalisierung (NFR-I18N) · R8

| ID | Anforderung |
| --- | --- |
| NFR-I18N-01 | **Benutzeroberfläche** vollständig gepflegt in **Deutsch (Standard) und Englisch** (`de.json`/`en.json`, ~100 Strings). `locales/` enthält darüber hinaus **24 EU-Amtssprach-Dateien**, die mindestens die Capability-Beschreibungen abdecken (NFR-I18N-02); Default/Fallback DE. |
| NFR-I18N-02 | Capability-Beschreibungen lokalisierbar (`cap.<name>.desc`) mit Fallback auf deutschen Originaltext. |
| NFR-I18N-03 | Sprach-Normalisierung (`de_DE.UTF-8` → `de`); unbekannte Sprache → DE; fehlender Key → DE → Key selbst. |

### 15.6 Barrierefreiheit (NFR-A11Y) · R8

Zielniveau **WCAG 2.2 Level AA**.

| ID | Anforderung |
| --- | --- |
| NFR-A11Y-01 | Screenreader-Unterstützung (TalkBack): Icons/Bilder mit `contentDescription`/Begleit-Label; reine Icon-Bedeutung nie ohne Text. |
| NFR-A11Y-02 | Kontraste: Text ≥ 4,5:1, UI-Komponenten ≥ 3:1; Dark-Mode mit lesbaren Kontrasten. |
| NFR-A11Y-03 | Touch-Targets ≥ 48 dp × 48 dp, Listen-Items ≥ 56 dp, Abstand ≥ 8 dp. |
| NFR-A11Y-04 | Dynamische Schriftgrößen (`sp`, nicht Pixel); kein Clipping bei System-Schrift bis 200 %. |
| NFR-A11Y-05 | Fehlermeldungen nennen Ursache **und** Nutzeraktion; destruktive Aktionen mit Undo-Snackbar (≈6 s). |

### 15.7 Portabilität & Betrieb (NFR-PORT/OPS) · R8, R9

| ID | Anforderung |
| --- | --- |
| NFR-PORT-01 | Python ≥ 3.10; Desktop (Windows/Linux/macOS), CLI, Android. |
| NFR-PORT-02 | Optionale Abhängigkeiten degradieren sauber (fehlt ein Paket → klarer Hinweis, kein Crash). |
| NFR-OPS-01 | Diagnose-Befehl (`--diagnose`) berichtet Plattform, Pakete, OCR-Engines. |

### 15.8 Zuverlässigkeit & Wartbarkeit (NFR-REL/MAINT) · R5, R8

| ID | Anforderung |
| --- | --- |
| NFR-REL-01 | Migrationen idempotent und zeilenerhaltend; Backups verifiziert. |
| NFR-REL-02 | Sync-Worker- und Scheduler-Fehler führen nie zum App-Absturz. |
| NFR-MAINT-01 | Strikte Schichtung: Module → Services → Persistenz; keine Rückwärts-Abhängigkeit, kein Fremd-SQL (ARCHITECTURE.md). |
| NFR-MAINT-02 | Lizenz-Schicht orthogonal (kein Modul kennt sie); Tier-Wechsel zur Laufzeit ohne Neustart wirksam. |

## 16. Qualitäts-, Test- & Release-Anforderungen (QA)

| ID | Anforderung | Prio | R |
| --- | --- | --- | --- |
| QA-01 | Regressionssuite `tests/test_smoke.py` deckt jedes Modul + jede Capability mindestens einmal ab. | M | R8 |
| QA-02 | Integrationstests mocken SMTP/IMAP/OCR/Print/TLS; Property-/Fuzz-Tests (Hypothesis) für Invarianten; Performance-Tests als Budget. | M | R8 |
| QA-03 | GUI-/Mobile-Boot-Smoke ohne Display; Import-/Signatur-Smoke. | M | R8 |
| QA-04 | Traceability: jeder Test ist auf ≥1 R-Thema gemappt (`tools/test_protocol.py` `FILE_REQUIREMENTS`); Dashboard-Matrix markiert Bereiche mit 0 Tests rot, <5 gelb. | M | R10 |
| QA-05 | Release-Gate vor jedem Upload: `tools/playstore_check.py --strict` (0 FAIL), `tools/data_safety.py --check`, `tools/privacy_policy.py --list-placeholders`, vollständige Testsuite grün. | M | R9 |
| QA-06 | Versionscode bei jedem Update gemeinsam erhöhen (`buildozer.spec` + `playstore.yml`), sonst FAIL. | M | R9 |
| QA-07 | Gestaffelter Rollout (5 %→20 %→50 %→100 %) mit Crash-/ANR-Monitoring. | S | R9 |
| QA-08 | CI: Android-Compliance-Workflow grün auf jedem PR; Emulator-Smoketest (Robo/Monkey). | M | R9 |

## 17. Traceability-Matrix (R1–R10)

Verknüpft die Themen-IDs mit den Detail-Anforderungen dieses Dokuments und der
maßgeblichen Test-/Code-Quelle (Coverage-Status laut [tests/TESTGAPS.md](tests/TESTGAPS.md)).

| R | Thema | Detail-IDs (dieses Dokument) | Repräsentative Tests | Status |
| --- | --- | --- | --- | --- |
| R1 | Aufgaben-/Tagesplanung | FR-A, FR-C, FR-D, FR-H, FR-K, FR-L, FR-X-01, PA-07 | test_overview, test_calendar_birthday, test_smoke | ✅ |
| R2 | Erinnerungen/Benachrichtigungen | IF-07, NFR-… | test_scheduler_reminders, test_notifications_permission | ✅ |
| R3 | Kategorien/Prioritäten | FR-A-02, FR-B-04, FR-D-07, FR-I-02 | test_priority_category | ✅ |
| R4 | Suche & Filter | FR-I-01..03, NFR-PERF-01 | test_search_filters, test_performance | ✅ |
| R5 | Persistenz & Sync | DA-*, SY-*, EN-05/06 | test_sync_conflict, test_sync_threadsafety, test_tls_certs | ✅ |
| R6 | Import/Export | FR-C-04/05, FR-E-02, FR-G-05, EN-07 | test_import_robustness, test_property | ✅ |
| R7 | Datenschutz & Sicherheit | EN-01..04, CO-*, KI-05/07, LI-10/11, CFG-02 | test_data_safety, test_data_deletion, test_compliance_gates | ✅ |
| R8 | Stabilität & Tests | PA-03..05, FR-X-02/03, NFR-* | test_smoke, test_integration, test_gui_boot_smoke | ✅ |
| R9 | Play-Store-Release | MO-03..09, CO-03/07, QA-05..08 | test_compliance_gates, test_data_safety | ✅ |
| R10 | QA/Testübersicht | QA-04 | test_requirements_coverage | ✅ |

## 18. Annahmen, Einschränkungen & offene Punkte

- **A1 — Single-User-Zeitzone:** Kalendarische Datumsfelder sind bewusst
  zeitzonenlos; ein Multi-Timezone-Szenario ist als zukünftige Erweiterung in
  [docs/TIMEZONE_AUDIT.md](docs/TIMEZONE_AUDIT.md) beschrieben.
- **A2 — Rechtstexte:** `legal/`-Vorlagen enthalten `[PLATZHALTER]` und sind vor
  Veröffentlichung anwaltlich zu prüfen (CO-05).
- **A3 — Compliance-Detailwerte:** Die in §11/§12 genannten SDK-Level
  (target/compile 35, min/ndk 24), die Permission-Whitelist und die
  Vitals-Schwellen sind aus dem aktuellen Stand abgeleitet; die laufend
  gepflegte SDK-Inventar-Liste bleibt in
  [docs/android/04_PRIVACY_PERMISSIONS.md](docs/android/04_PRIVACY_PERMISSIONS.md)
  maßgeblich (bei jeder Dependency-Änderung aktualisieren).
- **A4 — Crash-/Analytics-SDK:** Sentry/Crashlytics ist nur **geplant** und
  opt-in. Wird es aktiviert, MÜSSEN Data-Safety-Form und Datenschutzerklärung
  entsprechend nachgezogen werden (App-activity → Crash logs).
- **O1 — Offene Geräte-Verifikationen** (operativ, nicht im Repo lösbar):
  SQLCipher-/ML-Kit-/Icon-Verifikation auf echtem Gerät, signierter AAB-Build,
  Play-Console-Anlage, echte Screenshots, Closed-Test-Nachweis — vollständige
  Liste in [release/GO_LIVE_TODO.md](release/GO_LIVE_TODO.md).

---

*Dieses Dokument ist die konsolidierte Anforderungsübersicht. Bei Abweichungen
zwischen diesem Dokument und der jeweils verlinkten Detailquelle (Code,
`docs/android/`, `legal/`) gilt die Detailquelle; Diskrepanzen sind als Fehler zu
melden und hier nachzuziehen.*
