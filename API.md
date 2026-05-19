# API-Referenz (Capabilities)

Automatisch aus den geladenen Modulen erzeugt. Regenerieren mit:

```pwsh
python tools/gen_api_doc.py > API.md
```

Gesamtzahl: **88** Capabilities in **11** Modulen.

## Modul `calendar`

### `calendar.add_event`

Legt einen Termin an (einmalig oder wiederkehrend).

**Parameter:**

- `title` (string) **(erforderlich)** - Bezeichnung des Termins
- `due_date` (string) **(erforderlich)** - Datum ISO (YYYY-MM-DD)
- `category` (string) - termin, garantie, tuev, steuer, geburtstag, sonstiges
- `description` (string) - Details
- `recurrence_days` (integer) - Wiederholung in Tagen (z.B. 365 = jaehrlich)
- `person_id` (integer) - Optional: betroffene Person (siehe family.members)

### `calendar.delete_event` *(destruktiv)*

Verschiebt einen Termin in den Papierkorb. Restore via calendar.restore_event; endgueltig erst via calendar.purge_event.

**Parameter:**

- `event_id` (integer) **(erforderlich)** - ID des Termins

### `calendar.export_ical`

Exportiert alle Termine als iCalendar-Datei (.ics), die in jeden gaengigen Kalender importiert werden kann.

**Parameter:**

- `path` (string) **(erforderlich)** - Zielpfad (sollte auf .ics enden)

### `calendar.import_ical` *(destruktiv, intern)*

Liest eine iCalendar-Datei (.ics) und legt die enthaltenen Termine an. Bestehende Termine werden NICHT veraendert - es entstehen neue Eintraege.

**Parameter:**

- `path` (string) **(erforderlich)** - Pfad zur .ics-Datei

### `calendar.list_deleted`

Listet Termine im Papierkorb.

### `calendar.list_events`

Listet alle erfassten Termine auf.

### `calendar.purge_event` *(destruktiv)*

Loescht einen Termin endgueltig.

**Parameter:**

- `event_id` (integer) **(erforderlich)** - ID des Termins

### `calendar.restore_event` *(destruktiv)*

Stellt einen geloeschten Termin wieder her.

**Parameter:**

- `event_id` (integer) **(erforderlich)** - ID des Termins

### `calendar.upcoming`

Liefert anstehende Termine innerhalb eines Horizonts.

**Parameter:**

- `horizon_days` (integer) - Bis wie viele Tage in der Zukunft (Standard: 90)


## Modul `contracts`

### `contracts.add`

Legt einen neuen Vertrag an.

**Parameter:**

- `name` (string) **(erforderlich)** - Name des Vertrags
- `category` (string) **(erforderlich)** - versicherung, mobilfunk, streaming, strom oder sonstiges
- `provider` (string) - Anbieter
- `customer_number` (string) - Kunden- oder Vertragsnummer
- `start_date` (string) - Startdatum ISO (YYYY-MM-DD)
- `minimum_term_months` (integer) - Mindestlaufzeit in Monaten
- `notice_period_months` (integer) - Kuendigungsfrist in Monaten
- `auto_renew_months` (integer) - Verlaengerung in Monaten, falls nicht gekuendigt wird (z.B. 1 = monatlich kuendbar)
- `monthly_cost` (number) - Monatliche Kosten in EUR
- `owner_id` (integer) - Optional: ID des Haushaltsmitglieds, dem der Vertrag gehoert (siehe family.members)

### `contracts.delete` *(destruktiv)*

Verschiebt einen Vertrag in den Papierkorb (Soft-Delete). Mit 'contracts.restore' wiederherstellbar; endgueltig erst durch 'contracts.purge'.

**Parameter:**

- `contract_id` (integer) **(erforderlich)** - ID des Vertrags

### `contracts.generate_cancellation`

Erstellt ein fristgerechtes Kuendigungsschreiben fuer einen Vertrag - als druckbares PDF und/oder Mail-Entwurf.

**Parameter:**

- `contract_id` (integer) **(erforderlich)** - ID des zu kuendigenden Vertrags
- `sender_name` (string) - Name des Absenders
- `sender_address` (string) - Anschrift des Absenders
- `sender_city` (string) - Ort fuer die Datumszeile
- `recipient_email` (string) - Mailadresse des Anbieters (fuer den Mail-Entwurf)
- `channel` (string) - pdf, email oder both (Standard: both)

### `contracts.list`

Listet alle aktiven Vertraege mit Kosten auf.

### `contracts.list_deleted`

Listet die im Papierkorb liegenden Vertraege.

### `contracts.purge` *(destruktiv)*

Endgueltige Loeschung eines Vertrags (kein Restore mehr moeglich).

**Parameter:**

- `contract_id` (integer) **(erforderlich)** - ID des Vertrags

### `contracts.report_price_change` *(destruktiv)*

Vermerkt eine Preisaenderung fuer einen Vertrag und speichert sie in der Preis-Historie.

**Parameter:**

- `contract_id` (integer) **(erforderlich)** - ID des Vertrags
- `new_cost` (number) **(erforderlich)** - Neuer Monatspreis in EUR

### `contracts.restore` *(destruktiv)*

Stellt einen geloeschten Vertrag wieder her.

**Parameter:**

- `contract_id` (integer) **(erforderlich)** - ID des Vertrags

### `contracts.set_owner` *(destruktiv)*

Ordnet einen Vertrag einer Person zu (oder loest die Zuordnung mit owner_id=0).

**Parameter:**

- `contract_id` (integer) **(erforderlich)** - ID des Vertrags
- `owner_id` (integer) - ID der Person (0 = keine)

### `contracts.upcoming_deadlines`

Liefert anstehende Kuendigungsfristen, optional begrenzt auf die naechsten N Tage.

**Parameter:**

- `within_days` (integer) - Nur Fristen innerhalb so vieler Tage (Standard: alle)


## Modul `day`

### `day.log_energy`

Bewertet den heutigen Tag (1=ausgelaugt ... 5=top) und legt einen Eintrag an oder ersetzt den heutigen.

**Parameter:**

- `level` (integer) **(erforderlich)** - Skala 1-5
- `note` (string) - Kurzer Hinweis

### `day.recent_entries`

Listet die letzten Tageseintraege auf.

**Parameter:**

- `limit` (integer) - Maximal so viele (Standard: 30)

### `day.recommendation`

Liefert eine einfache Empfehlung auf Basis der letzten Eintraege.


## Modul `family`

### `family.add_member`

Fuegt ein Haushaltsmitglied hinzu, optional mit Geburtstag (Termin landet automatisch im Kalender-Modul).

**Parameter:**

- `name` (string) **(erforderlich)** - Name der Person
- `role` (string) - erwachsen, kind oder sonstiges
- `birthday` (string) - Geburtstag ISO (YYYY-MM-DD), optional

### `family.add_order`

Legt einen einmaligen Auftrag an, gezielt einer Person zugewiesen (mit Termin).

**Parameter:**

- `title` (string) **(erforderlich)** - Was ist zu erledigen
- `assignee` (string) - Name der zustaendigen Person
- `due_date` (string) - Faelligkeit ISO (YYYY-MM-DD)
- `description` (string) - Zusatzinfo zum Auftrag

### `family.add_task`

Legt eine wiederkehrende Haushaltsaufgabe mit Rotation zwischen Mitgliedern an.

**Parameter:**

- `title` (string) **(erforderlich)** - Bezeichnung der Aufgabe
- `interval_days` (integer) - Wiederholung in Tagen (z.B. 7 = woechentlich)
- `assignees` (array) **(erforderlich)** - Namen der Mitglieder in Rotationsreihenfolge
- `first_due` (string) - Erste Faelligkeit ISO (YYYY-MM-DD), Standard: heute

### `family.bulk_complete_overdue` *(destruktiv)*

Hakt alle Aufgaben ab, die heute oder davor faellig sind/waren. Die Rotation rueckt fuer jede Aufgabe um eine Person weiter.

### `family.complete_order` *(destruktiv)*

Markiert einen Auftrag als erledigt.

**Parameter:**

- `order_id` (integer) **(erforderlich)** - ID des Auftrags

### `family.complete_task` *(destruktiv)*

Hakt eine Aufgabe ab: die Rotation rueckt zur naechsten Person, die Aufgabe wird neu terminiert.

**Parameter:**

- `task_id` (integer) **(erforderlich)** - ID der Aufgabe

### `family.delete_member` *(destruktiv)*

Verschiebt ein Haushaltsmitglied in den Papierkorb (Soft-Delete). Restore via family.restore_member, endgueltig erst via family.purge_member.

**Parameter:**

- `member_id` (integer) **(erforderlich)** - ID des Mitglieds

### `family.list_deleted_members`

Listet Mitglieder im Papierkorb.

### `family.members`

Listet die Haushaltsmitglieder auf. Auch von anderen Modulen nutzbar, um Eintraege einer Person zuzuordnen.

### `family.orders`

Listet die einmaligen Auftraege mit Zustaendigkeit und Status auf.

### `family.purge_member` *(destruktiv)*

Loescht ein Mitglied endgueltig. Referenzen werden ueber ON DELETE SET NULL entkoppelt.

**Parameter:**

- `member_id` (integer) **(erforderlich)** - ID des Mitglieds

### `family.restore_member` *(destruktiv)*

Stellt ein geloeschtes Mitglied wieder her.

**Parameter:**

- `member_id` (integer) **(erforderlich)** - ID des Mitglieds

### `family.shopping_add`

Setzt einen Eintrag auf die gemeinsame Einkaufsliste.

**Parameter:**

- `name` (string) **(erforderlich)** - Was soll gekauft werden
- `quantity` (string) - Menge / Einheit
- `added_by` (string) - Name der Person, die den Eintrag setzt

### `family.shopping_list`

Listet die Eintraege der Einkaufsliste.

**Parameter:**

- `include_bought` (boolean) - Bereits gekaufte Eintraege einbeziehen

### `family.shopping_mark`

Hakt einen Eintrag auf der Einkaufsliste ab (oder setzt ihn zurueck).

**Parameter:**

- `item_id` (integer) **(erforderlich)** - ID des Eintrags
- `bought` (boolean) - True = gekauft (Standard), False = wieder offen

### `family.tasks`

Listet die Haushaltsaufgaben mit aktueller Zustaendigkeit und naechster Faelligkeit auf.


## Modul `finance`

### `finance.add_expense`

Erfasst eine einmalige Ausgabe.

**Parameter:**

- `description` (string) **(erforderlich)** - Wofuer wurde Geld ausgegeben
- `amount` (number) **(erforderlich)** - Betrag in EUR
- `category` (string) - lebensmittel, freizeit, mobilitaet, sonstiges ...
- `spent_on` (string) - Datum ISO (YYYY-MM-DD), Standard: heute
- `owner_id` (integer) - Optional: Person, der die Ausgabe zugeordnet wird (siehe family.members)

### `finance.delete_expense` *(destruktiv)*

Verschiebt eine Ausgabe in den Papierkorb. Restore via 'finance.restore_expense'; endgueltig erst via 'finance.purge_expense'.

**Parameter:**

- `expense_id` (integer) **(erforderlich)** - ID der Ausgabe

### `finance.expenses_by_category`

Aggregiert die Ausgaben pro Kategorie.

**Parameter:**

- `month` (string) - Optional: 'YYYY-MM', sonst alle

### `finance.expenses_by_person`

Aggregiert die Ausgaben pro Haushaltsmitglied (loest die owner_id ueber family.members auf).

**Parameter:**

- `month` (string) - Optional: 'YYYY-MM', sonst alle

### `finance.list_deleted`

Listet Ausgaben im Papierkorb.

### `finance.list_expenses`

Listet alle erfassten Ausgaben mit Summe auf.

### `finance.monthly_overview`

Berechnet die monatliche Belastung: einmalige Ausgaben dieses Monats kombiniert mit den wiederkehrenden Vertragskosten aus Modul A.

### `finance.price_memory`

Listet die gespeicherten Preise wiederkehrender Produkte auf.

### `finance.purge_expense` *(destruktiv)*

Loescht eine Ausgabe endgueltig.

**Parameter:**

- `expense_id` (integer) **(erforderlich)** - ID der Ausgabe

### `finance.remember_price`

Merkt sich den aktuellen Preis eines Produkts (Preis-Gedaechtnis fuer wiederkehrende Einkaeufe).

**Parameter:**

- `product` (string) **(erforderlich)** - Bezeichnung des Produkts
- `price` (number) **(erforderlich)** - Aktueller Preis in EUR
- `category` (string) - Kategorie, z.B. 'lebensmittel'

### `finance.restore_expense` *(destruktiv)*

Stellt eine geloeschte Ausgabe wieder her.

**Parameter:**

- `expense_id` (integer) **(erforderlich)** - ID der Ausgabe

### `finance.scan_receipt`

Liest einen Kassenbon per OCR ein und extrahiert Posten und Summe (erfordert pytesseract + Tesseract; ohne Installation gibt es einen klaren Hinweis).

**Parameter:**

- `image_path` (string) **(erforderlich)** - Pfad zur Bilddatei (jpg / png)


## Modul `inbox`

### `inbox.accept_proposal` *(destruktiv)*

Uebernimmt einen Vorschlag: ruft die Ziel-Capability auf, das zustaendige Modul traegt die Daten ein.

**Parameter:**

- `proposal_id` (integer) **(erforderlich)** - ID des Vorschlags

### `inbox.analyze_mail`

Analysiert den Text einer eingegangenen Mail und legt passende Vorschlaege in der Ablage an.

**Parameter:**

- `mail_text` (string) **(erforderlich)** - Der vollstaendige Mail-Text

### `inbox.bulk_delete_archived` *(destruktiv)*

Loescht alle Vorschlaege, die bereits uebernommen oder abgelehnt wurden, endgueltig aus der Ablage.

### `inbox.bulk_reject_open` *(destruktiv)*

Lehnt alle offenen Vorschlaege auf einen Schlag ab. Liefert die Anzahl der abgelehnten Vorschlaege.

### `inbox.fetch_imap`

Holt ungelesene Mails per IMAP und analysiert sie. Braucht ALLTAGSHELFER_IMAP_HOST/USER/PASS in der Umgebung; ohne diese wird uebersprungen.

**Parameter:**

- `folder` (string) - IMAP-Ordner (Standard: INBOX)
- `limit` (integer) - Max. Anzahl Mails

### `inbox.import_eml`

Liest eine .eml-Datei ein und analysiert sie.

**Parameter:**

- `path` (string) **(erforderlich)** - Pfad zur .eml-Datei

### `inbox.proposals`

Listet die offenen Vorschlaege in der Ablage auf.

### `inbox.reject_proposal` *(destruktiv)*

Lehnt einen Vorschlag ab (wird nicht uebernommen).

**Parameter:**

- `proposal_id` (integer) **(erforderlich)** - ID des Vorschlags

### `inbox.update_proposal` *(destruktiv)*

Bearbeitet einen offenen Vorschlag, bevor er uebernommen wird. Beruehrt nur Vorschlaege im Status 'offen'.

**Parameter:**

- `proposal_id` (integer) **(erforderlich)** - ID des Vorschlags
- `summary` (string) - Neue Kurzbeschreibung (optional)
- `payload` (object) - Vollstaendige neue Nutzlast fuer die Ziel-Capability


## Modul `notes`

### `notes.add`

Legt eine neue Notiz an. Optional an eine Entitaet angeheftet (entity_type, entity_id).

**Parameter:**

- `title` (string) **(erforderlich)** - Titel der Notiz
- `content` (string) - Notiz-Text
- `entity_type` (string) - Optional: contracts, expenses, calendar, social, family, orders
- `entity_id` (integer) - Optional: ID innerhalb der Entitaet

### `notes.add_attachment` *(destruktiv)*

Heftet eine Notiz zusaetzlich an eine weitere Entitaet (n:m). Die primaere Verknuepfung via notes.attach bleibt davon unberuehrt.

**Parameter:**

- `note_id` (integer) **(erforderlich)** - ID der Notiz
- `entity_type` (string) **(erforderlich)** - Entitaets-Typ
- `entity_id` (integer) **(erforderlich)** - ID der Entitaet

### `notes.attach` *(destruktiv)*

Heftet eine Notiz an eine Entitaet (oder loest sie mit entity_type=null).

**Parameter:**

- `note_id` (integer) **(erforderlich)** - ID der Notiz
- `entity_type` (string) - Entitaets-Typ (leer = nichts anheften)
- `entity_id` (integer) - ID der Entitaet

### `notes.cleanup_for_entity` *(destruktiv, intern)*

Loescht alle Notizen, die an die angegebene Entitaet geheftet sind. Wird intern von den Loesch-Capabilities anderer Module aufgerufen.

**Parameter:**

- `entity_type` (string) **(erforderlich)** - Entitaets-Typ
- `entity_id` (integer) **(erforderlich)** - ID der Entitaet

### `notes.delete` *(destruktiv)*

Loescht eine Notiz endgueltig.

**Parameter:**

- `note_id` (integer) **(erforderlich)** - ID der Notiz

### `notes.get`

Liefert eine konkrete Notiz.

**Parameter:**

- `note_id` (integer) **(erforderlich)** - ID der Notiz

### `notes.list`

Listet Notizen auf. Optional nach Entitaet gefiltert.

**Parameter:**

- `entity_type` (string) - Filter auf Entitaet
- `entity_id` (integer) - Filter auf konkrete ID

### `notes.list_attachments`

Listet alle Anhaenge einer Notiz auf.

**Parameter:**

- `note_id` (integer) **(erforderlich)** - ID der Notiz

### `notes.update` *(destruktiv)*

Aktualisiert Titel und/oder Inhalt einer Notiz.

**Parameter:**

- `note_id` (integer) **(erforderlich)** - ID der Notiz
- `title` (string) - Neuer Titel (optional)
- `content` (string) - Neuer Inhalt (optional)


## Modul `social`

### `social.add_contact`

Legt einen Kontakt fuer die soziale Pflege an.

**Parameter:**

- `name` (string) **(erforderlich)** - Name der Person
- `relation` (string) - Beziehung, z.B. Familie, Freund, Kollege
- `cadence_days` (integer) - Wunsch-Rhythmus in Tagen (Standard: 30)
- `notes` (string) - Notizen

### `social.contacts`

Listet alle Kontakte mit Resttagen bis zum naechsten Melden auf.

### `social.delete_contact` *(destruktiv)*

Verschiebt einen Kontakt in den Papierkorb. Restore via social.restore_contact; endgueltig erst via social.purge_contact.

**Parameter:**

- `contact_id` (integer) **(erforderlich)** - ID des Kontakts

### `social.draft_message`

Schlaegt eine kurze Nachricht fuer einen Kontakt vor (Offline-Vorlage; im API-Modus generiert das LLM eine persoenlichere).

**Parameter:**

- `contact_id` (integer) **(erforderlich)** - ID des Kontakts
- `template` (string) - kurz, treffen, geburtstag
- `anlass` (string) - Optional: konkreter Anlass, den das LLM aufgreifen soll

### `social.export_vcard`

Exportiert alle Kontakte als vCard-Datei (.vcf), importierbar in jedes gaengige Adressbuch.

**Parameter:**

- `path` (string) **(erforderlich)** - Zielpfad (sollte auf .vcf enden)

### `social.import_vcard` *(destruktiv, intern)*

Liest eine vCard-Datei (.vcf) und legt die enthaltenen Kontakte an. Bestehende Kontakte bleiben unveraendert - es entstehen neue Eintraege.

**Parameter:**

- `path` (string) **(erforderlich)** - Pfad zur .vcf-Datei

### `social.list_deleted`

Listet Kontakte im Papierkorb.

### `social.mark_contacted`

Markiert einen Kontakt als gerade kontaktiert (setzt last_contacted = heute).

**Parameter:**

- `contact_id` (integer) **(erforderlich)** - ID des Kontakts

### `social.purge_contact` *(destruktiv)*

Loescht einen Kontakt endgueltig.

**Parameter:**

- `contact_id` (integer) **(erforderlich)** - ID des Kontakts

### `social.restore_contact` *(destruktiv)*

Stellt einen geloeschten Kontakt wieder her.

**Parameter:**

- `contact_id` (integer) **(erforderlich)** - ID des Kontakts


## Modul `stats`

### `stats.contracts_overview`

Liefert Ueberblick ueber Anzahl aktiver Vertraege, monatliche Gesamtsumme und die teuersten 3 Posten.

### `stats.expenses_per_category`

Aggregiert Ausgaben pro Kategorie (Default: aktuelles Jahr).

**Parameter:**

- `year` (integer) - Zieljahr (Default: aktuell)

### `stats.expenses_per_month`

Summiert Ausgaben pro Monat fuer die letzten N Monate (Default 12) inkl. dem laufenden Monat.

**Parameter:**

- `months` (integer) - Anzahl Monate (Default: 12)

### `stats.export_yearly_pdf`

Erzeugt einen druckbaren PDF-Jahresbericht mit Ausgaben-Summe, Top-Kategorien und Vertraege-Uebersicht.

**Parameter:**

- `path` (string) **(erforderlich)** - Zielpfad (PDF)
- `year` (integer) - Zieljahr (Default: aktuell)

### `stats.yearly_summary`

Gesamtsicht fuer ein Jahr: Summe aller Ausgaben, Top-Kategorien, monatlicher Schnitt.

**Parameter:**

- `year` (integer) - Zieljahr (Default: aktuell)


## Modul `system`

### `system.search`

Sucht querbeet in Vertraegen, Ausgaben, Terminen, Familienmitgliedern, Kontakten und Vorschlaegen. Eingabe ist ein Stichwort - Treffer kommen vereinheitlicht zurueck.

**Parameter:**

- `query` (string) **(erforderlich)** - Suchbegriff (mindestens 2 Zeichen)
- `limit` (integer) - Maximale Treffer (Standard: 50)


## Modul `templates`

### `templates.add`

Legt eine neue Aufgaben-Vorlage an.

**Parameter:**

- `title` (string) **(erforderlich)** - Titel der Aufgabe
- `interval_days` (integer) - Tages-Intervall (Standard 7)
- `description` (string) - Notiz zur Vorlage

### `templates.apply` *(destruktiv)*

Erzeugt aus einer Vorlage eine konkrete Haushaltsaufgabe - die Rotation muss zusaetzlich angegeben werden.

**Parameter:**

- `template_id` (integer) **(erforderlich)** - ID der Vorlage
- `assignees` (array) **(erforderlich)** - Namen der Rotationsmitglieder
- `first_due` (string) - Erste Faelligkeit (YYYY-MM-DD); Standard: heute

### `templates.delete` *(destruktiv)*

Loescht eine Vorlage endgueltig.

**Parameter:**

- `template_id` (integer) **(erforderlich)** - ID der Vorlage

### `templates.list`

Listet alle vorhandenen Aufgaben-Vorlagen auf.

