# Anforderungs-Abdeckung & Lückenanalyse (ZunaroDo)

> Erzeugt im Rahmen der QA-/Release-Bewertung. Ergänzt die maschinelle
> Traceability-Matrix im Dashboard (`tests/concept/reports/dashboard.html`,
> Abschnitt **Anforderungen R1–R10**) um eine inhaltliche Bewertung und
> konkrete, noch fehlende Testfälle. Google-Play-Anforderungen sind je
> Punkt markiert mit 🟦 **PLAY**.

## 1. Bewertung je Anforderung

| ID | Anforderung | Status | Bewertung |
|----|-------------|--------|-----------|
| R1 | Aufgaben- & Tagesplanung (Familie, Rotation, Catch-Up, Kalender) | ✅ gut | Rotation inkl. Mehrfach-Catch-Up (`test_overdue_task_advances_rotation_multiple_times`, `test_bulk_complete_overdue_*`), Mitglieder-Szenarien, Pairwise-Matrix. **Lücke:** Tages-/Wochenübersicht nicht explizit getestet. |
| R2 | Erinnerungen & Benachrichtigungen | ✅ geschlossen | `tests/test_scheduler_reminders.py` (Auslösen, Fälligkeits-Wording, Dedup) + **neu** Persistenz-Klasse: „gesehen"-Marker werden atomar nach `reminder_seen.json` im State-Ordner persistiert und beim Start geladen (kein Doppelmelden nach Neustart); Marker sind datumsfrei → DST-/Zeitsprung löst keine erneute Meldung aus; defekte State-Datei wird ignoriert. |
| R3 | Kategorien & Prioritäten | ✅ geschlossen | `test_expenses_per_category_aggregates`, `test_calendar_unknown_category_normalizes` + **neu** `tests/test_priority_category.py`. **Geschlossen:** Kategorie-Filter für Verträge (`contracts.list`), Kontakte (`social.contacts`, nach Beziehung) und Aufträge (`family.orders`); Prioritäts-Vergabe (`family.add_order`) + stabile Sortierung; additive Migration v2→v3. |
| R4 | Suche & Filter | ✅ geschlossen | `test_search_finds_multiple_sources`, `test_search_finds_notes` + **neu** `tests/test_search_filters.py`. **Geschlossen:** `system.search` akzeptiert jetzt `date_from`/`date_to`, `status`, `category`; Filter ohne Suchwort funktioniert, ein gesetzter Filter schliesst Quellen ohne das Feld aus. |
| R5 | Datenpersistenz & Mehrgeräte-Sync | ✅ stark | LWW-Konfliktauflösung, Re-Entry-Schutz (`test_synced_outer_suppresses_synced_nested`), Kompaktierung, HTTP-Provider, TLS-Handshake, Pairing. |
| R6 | Import/Export (CSV, ICS, VCF, PDF) | ✅ gut | Export/Import-Roundtrips für alle Entitäten, ICS/VCF-Validierung & Negativfälle, PDF-Report (`test_pdf_report_produced`). |
| R7 | Datenschutz & Sicherheit | ✅ sehr stark | 270+ Privacy-Scan-Tests, Data-Safety-Konsistenz, Datenrechte/Löschung, Consent-Gating (IMAP/Gemini via Env), Secret-Scan, Legal. |
| R8 | Stabilität & Tests | ✅ stark | Smoke/Integration, GUI-Boot (free + default Lizenz), Property/Fuzz, Negativ-Inputs/Netzwerk/Security. |
| R9 | Play-Store-Release | ✅ stark | Target-SDK-Mindestversion, Permission-Whitelist/Deny, Versionierung, Store-Listing, Release-Gate (160+ Kriterien), Build-Status. |
| R10 | QA / Testübersicht | ✅ gut | Protokoll-, Dashboard-, Control-Panel-, MD→HTML-Generatoren getestet. |

## 2. Konkret fehlende Testfälle (priorisiert)

### Hoch — funktionale Kernanforderungen

1. **R4 — Such-Filter (Implementierung + Test).** ✅ **ERLEDIGT** 🟦 PLAY (Datensparsamkeit/Nutzbarkeit)
   `system.search` um optionale Parameter `date_from`/`date_to`, `status`,
   `category` erweitert ([modules/search.py](../modules/search.py)). Tests in
   [tests/test_search_filters.py](test_search_filters.py):
   - `test_search_filters_by_category` — nur Treffer der gewählten Kategorie.
   - `test_search_filters_by_date_range` — Termine außerhalb des Zeitraums fehlen.
   - `test_search_filters_by_status` — z. B. nur offene Vorschläge.
   - `test_search_empty_query_with_filter_lists_filtered` — Filter ohne Suchwort.

2. **R2 — Erinnerungs-Persistenz über Neustart.** ✅ **ERLEDIGT**
   Umgesetzt in [services/scheduler.py](../services/scheduler.py)
   (`state_path` + atomare `reminder_seen.json`), Tests in
   [tests/test_scheduler_reminders.py](test_scheduler_reminders.py):
   - `test_seen_markers_survive_restart` — Marker werden persistiert/geladen,
     keine Doppelmeldung nach Neustart.
   - `test_clock_change_does_not_resend` — datumsfreie Marker → Zeit-/DST-Sprung
     löst keine erneute Meldung aus.

3. **R3 — Prioritäten & Kategorie-Filter.** ✅ **ERLEDIGT**
   Umgesetzt in [tests/test_priority_category.py](test_priority_category.py):
   - `test_orders_filter_by_category`, `test_contracts_filter_by_category`,
     `test_contacts_filter_by_relation`.
   - `test_order_priority_sort_order` — Sortierung nach Priorität stabil.
   - `test_migration_adds_columns_and_keeps_rows` — Schema v2→v3.

### Mittel — Robustheit & UX

4. **R1 — Tages-/Wochenübersicht.**
   - `test_day_view_groups_due_items`, `test_week_view_spans_seven_days`.

5. **R6 — Import-Robustheit.**
   - `test_csv_import_rejects_malformed_row` (teilweise vorhanden — auf alle
     Entitäten ausweiten).
   - `test_ics_import_with_dst_recurrence` (Zeitzonen in Wiederholungen).

6. **R5 — Sync-Konflikt-Determinismus.**
   - `test_concurrent_edit_same_record_resolves_deterministically` (zwei Geräte,
     gleicher Datensatz, gleicher Lamport-Wert → Tie-Break über device_id).

### Play-Store-spezifisch 🟦 PLAY

7. **POST_NOTIFICATIONS (Android 13+).** Laufzeitberechtigung für
   Benachrichtigungen.
   - `test_manifest_declares_post_notifications` — buildozer.spec/Manifest
     deklariert die Permission.
   - `test_app_degrades_without_notification_permission` — App bleibt nutzbar,
     wenn die Berechtigung verweigert wird (Erinnerungen werden in-App
     angezeigt statt als System-Notification).

8. **Konto-/Datenlöschung (Google Account Deletion Policy).**
   - `test_data_deletion_reachable_from_ui` — In-App-Pfad zur vollständigen
     Löschung vorhanden (ergänzt `services/data_deletion.py`-Tests um die
     UI-Erreichbarkeit).
   - `test_privacy_policy_contains_deletion_url` — Datenschutzerklärung nennt
     die Web-Lösch-URL (Play verlangt erreichbaren Lösch-Pfad).

9. **Data-Safety-Konsistenz bei optionalen Features.**
   - `test_data_safety_reflects_gemini_optin` — wird Gemini/IMAP aktiviert,
     müssen die Data-Safety-Angaben „Daten geteilt/verarbeitet" konsistent
     bleiben (aktuell nur „clean app shares nothing" geprüft).

10. **Foreground-/Background-Verhalten.**
    - `test_no_undeclared_background_location_or_sensitive_permission` — keine
      sensiblen Berechtigungen ohne Deklaration/Begründung.

11. **Closed-Testing-Nachweis (≥12 Tester / 14 Tage).** 🟦 PLAY
    - `test_release_gate_requires_closed_test_evidence` — Release-Gate prüft das
      Vorhandensein der 14-Tage-Nachweisdokumente (Anhang F/13.2) vor „GO".

## 3. Hinweis zur Traceability

Die Zuordnung Test→Anforderung steckt in
[`tools/test_protocol.py`](../tools/test_protocol.py) (`FILE_REQUIREMENTS`).
Neue Testdateien dort eintragen, damit sie in der Dashboard-Matrix
(R1–R10) erscheinen. Die Matrix markiert Bereiche mit Fehlschlägen oder
0 Tests **rot** und Bereiche mit < 5 Tests **gelb**.
