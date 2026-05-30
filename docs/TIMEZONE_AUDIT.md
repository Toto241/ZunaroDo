# DST- / Zeitzonen-Audit

> Status: abgeschlossen für 1.0.0. Dieses Dokument hält fest, welche
> Zeitangaben in ZunaroDo in UTC und welche als zeitzonenlose Kalendertage
> geführt werden, warum diese Aufteilung für den Einsatzzweck korrekt ist
> und was bei einem echten Multi-Zeitzonen-Szenario zu ergänzen wäre.

## Kurzfassung

| Kategorie | Speicherung | Beispiele |
| --- | --- | --- |
| **Technische Zeitstempel** | **UTC**, ISO-8601 mit `+00:00` | `created_at`, `updated_at`, `changed_at`, Sync-Event-Zeitpunkte |
| **Kalendarische Datumsfelder** | **Lokaler Kalendertag** (`YYYY-MM-DD`, ohne Zeit/Zone) | Fälligkeiten von Terminen/Aufgaben/Aufträgen, Geburtstage, Steuerfristen, „zuletzt kontaktiert" |

Beide Entscheidungen sind bewusst getroffen und für die Zielnutzung (lokale
Einzel- bzw. Haushalts-Installation, optionaler Mehrgeräte-Sync innerhalb
derselben Zeitzone) korrekt.

## 1. Technische Zeitstempel — UTC

Alle DB-internen Stempel laufen über `database._now_utc_iso()`:

```python
def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
```

Damit gilt:

- `created_at` / `updated_at` / `changed_at` aller Entitäten sind UTC.
- Sync-Events (`services/sync.py`) tragen denselben UTC-Stempel; die
  Last-Write-Wins-Konfliktauflösung vergleicht damit zonenunabhängig und
  über Gerätegrenzen hinweg korrekt.
- Sortierungen nach Änderungszeit sind global eindeutig, unabhängig davon,
  in welcher Zeitzone das schreibende Gerät steht.

**DST-Wirkung:** keine. UTC kennt keine Sommer-/Winterzeit; die Umstellung
am schreibenden Gerät verschiebt keinen gespeicherten Stempel und kann keine
doppelten oder rückläufigen Zeitstempel erzeugen.

## 2. Kalendarische Datumsfelder — lokaler Kalendertag

Fälligkeiten, Geburtstage, gesetzliche Fristen und „zuletzt kontaktiert"
werden als reines Datum `YYYY-MM-DD` gespeichert und mit `date.today()` bzw.
`date.fromisoformat()` verglichen (z. B. in `modules/calendar.py`,
`modules/family.py`, `modules/social.py`, `modules/overview.py`).

Das ist beabsichtigt: Ein Termin „am 15. Mai" ist ein Kalendertag, kein
Zeitpunkt. Er soll am 15. Mai fällig sein — egal in welcher Zeitzone das
Gerät steht und unabhängig von einer DST-Umstellung. Eine Umrechnung nach
UTC würde solche Datumsfelder in Grenzfällen (kurz vor Mitternacht) auf den
falschen Kalendertag kippen.

**DST-Wirkung:** Reminder/Agenda gruppieren nach `date.today()` des lokalen
Geräts. Die DST-Nacht hat lokal weiterhin genau ein Kalenderdatum, daher
bleibt die Tagesgruppierung stabil. Der Reminder-Scheduler
(`services/scheduler.py`) entdedupliziert datumsbasiert
(`reminder_seen.json`), sodass eine Zeitumstellung **keine** erneute
Benachrichtigung für bereits gemeldete Fälligkeiten auslöst.

## 3. Bekannte Grenze: echtes Multi-Zeitzonen-Szenario

Die aktuelle Aufteilung ist korrekt, solange die synchronisierenden Geräte
in **derselben** Zeitzone leben (Normalfall: ein Haushalt). Würden zwei
Geräte in unterschiedlichen Zeitzonen denselben Datensatz teilen, gilt:

- Technische Stempel bleiben korrekt (UTC).
- Kalendertage bleiben numerisch identisch — sie werden auf beiden Geräten
  als derselbe `YYYY-MM-DD` angezeigt. Was sich unterscheiden kann, ist die
  Berechnung von „heute" / „überfällig", weil `date.today()` gerätelokal
  ist. An der Datumsgrenze können zwei Geräte „heute" also kurzzeitig
  unterschiedlich bewerten.

### Was dafür zu tun wäre (bewusst nicht umgesetzt)

1. Pro Termin eine optionale IANA-Zeitzone (`tzid`) und ggf. eine Uhrzeit
   mitführen, statt nur ein nacktes Datum.
2. „Überfällig/heute" gegen die Zeitzone des Termins statt gegen die
   Gerätezeit auswerten.
3. In der GUI die Anzeige-Zeitzone wählbar machen.

Das ist für eine lokale Haushalts-App Over-Engineering und wurde daher
bewusst nicht implementiert. Dieses Dokument hält die Entscheidung und den
Migrationspfad fest, falls sich die Anforderung später ändert.

## 4. Testabdeckung

- `tests/test_scheduler_reminders.py` — Auslösen/Dedup von Erinnerungen;
  die „gesehen"-Marker sind datumsbasiert, sodass eine Zeitumstellung keine
  erneute Meldung für bereits gemeldete Fälligkeiten auslöst.
- `tests/test_calendar_birthday.py` — Schaltjahr-Randfall (29.02. → 28.02.
  in Nicht-Schaltjahren), damit Geburtstags-Datumslogik nicht kippt.
- `tests/test_overview.py` — Agenda-Tagesgruppierung gegen `date.today()`,
  robust gegen datumsabhängige Basis-Ereignisse.
