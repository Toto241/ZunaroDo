# Play-Console-Snapshot fuer `de.alltagshelfer.alltagshelfer`

Stand: 2026-05-20T16:47:12+00:00

## Identitaet

| Feld | Wert |
| --- | --- |
| App-Name | Alltagshelfer |
| Package | `de.alltagshelfer.alltagshelfer` |
| Version | 0.9.0 (code 1) |
| Standard-Sprache | de-DE |

## Kontakt / URLs

- Support-E-Mail: `support@example.org`
- Support-URL:    https://example.org/alltagshelfer
- Marketing-URL:  https://example.org/alltagshelfer/marketing
- Datenschutz:    https://example.org/alltagshelfer/privacy

## Lokalisierungen

### de-DE

- Titel: Alltagshelfer (13/30)
- Kurz:  Vertraege, Termine, Finanzen, Familie - alles lokal und ohne Cloud-Zwang. (73/80)
- Lang:  183/4000 Zeichen

### en-US

- Titel: Alltagshelfer (13/30)
- Kurz:  Privacy-friendly household helper. (34/80)
- Lang:  105/4000 Zeichen

## Store-Listing

- Kategorie: PRODUCTIVITY
- Tags: household, privacy, german
- Werbung: False
- In-App-Kaeufe: False

## Permissions

Deklariert:
  - android.permission.INTERNET

Blockiert (Datenschutz-Negativliste):
  - android.permission.MANAGE_EXTERNAL_STORAGE
  - android.permission.READ_PHONE_STATE
  - android.permission.ACCESS_BACKGROUND_LOCATION
  - android.permission.RECEIVE_BOOT_COMPLETED
  - android.permission.SYSTEM_ALERT_WINDOW

## Data Safety

- Daten gesammelt: True
- Daten geteilt:   False
- TLS in Transit:  True
- Loeschen moeglich: True

### Datentypen

| Typ | gesammelt | geteilt | Zweck | optional |
| --- | :---: | :---: | --- | :---: |
| email | x |  | APP_FUNCTIONALITY |  |
| name | x |  | APP_FUNCTIONALITY |  |
| user_content | x |  | APP_FUNCTIONALITY |  |
| app_interactions | x |  | ANALYTICS | x |
| crash_logs | x | x | APP_FUNCTIONALITY |  |

### SDK-Inventar

| SDK | Datentypen | Zweck |
| --- | --- | --- |
| Firebase Auth | email_hash | APP_FUNCTIONALITY |
| Firebase Firestore | user_content | APP_FUNCTIONALITY |
| Firebase Crashlytics | crash_logs | APP_FUNCTIONALITY |
| Firebase Analytics | app_interactions | ANALYTICS |

## Tracks

### internal

- 1 Release(s) konfiguriert
- Tester-Gruppen: internal-team@example.org
  - v0.9.0 (code 1, status completed, rollout 1.0)

### closed

- 0 Release(s) konfiguriert
- Tester-Gruppen: zunarodo-closed-testers@googlegroups.com

### production

- 0 Release(s) konfiguriert

---

*Generiert von `tools/playstore_sync.py`. Aenderungen bitte ausschliesslich in `playstore.yml` vornehmen und mit `python -m tools.playstore_sync push` in die Play Console schieben.*