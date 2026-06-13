# Datenschutz & Datenfluss (technisch)

Diese Datei beschreibt **technisch**, welche Daten ZunaroDo verarbeitet, wo sie
liegen und wann sie das Geraet verlassen – als Orientierung fuer Entwickler,
Audits und Handoffs. Die **rechtlich verbindliche** Datenschutzerklaerung (DSGVO,
Verantwortlicher, Betroffenenrechte, Speicherdauer) ist
[`legal/DATENSCHUTZ.md`](legal/DATENSCHUTZ.md); sie hat im Zweifel Vorrang.

## Grundsatz: lokal-first, offline per Default

ZunaroDo ist eine lokal laufende Anwendung. Ohne ausdrueckliche Konfiguration
findet **keine** Uebertragung an Server statt. Alle Netz-/Cloud-Funktionen sind
opt-in ueber Umgebungsvariablen (siehe [`.env.example`](.env.example)).

## Datenkategorien und Speicherort

| Datenart | Wo gespeichert | Verschluesselung |
| --- | --- | --- |
| Nutzdaten (Vertraege, Termine, Finanzen, Familie, Kontakte, Notizen) | lokale SQLite-DB | optional SQLCipher (`ALLTAGSHELFER_DB_KEY`) |
| Backups | lokal (`backups/`) | optional separater Key (`ALLTAGSHELFER_BACKUP_KEY`) |
| Logs/Audit | lokal (`logs/`) | – |
| Lizenz-Token (signiert) | lokal | Ed25519-signiert |
| Zahlungsdaten | beim Bezahldienstleister (Paddle/Lemon Squeezy) | – |

Daten- und Konfigverzeichnis lassen sich ueber `ALLTAGSHELFER_DATA_DIR` /
`ALLTAGSHELFER_CONFIG_DIR` umlenken; Profile (`ALLTAGSHELFER_PROFILE`) trennen
DB und State.

## Was das Geraet verlaesst – und nur wenn konfiguriert

| Funktion | Aktiv durch | Was uebertragen wird | Ziel |
| --- | --- | --- | --- |
| KI-Assistent | `GOOGLE_API_KEY` | konkrete Chat-Anfrage + ggf. **zusammengefasster** Kontext (nicht die DB) | Google Gemini |
| Mehrgeraete-Sync | `ALLTAGSHELFER_SYNC_DIR` **oder** `ALLTAGSHELFER_SYNC_URL` | replizierte Aenderungen | geteilter Ordner bzw. selbst gehosteter Sync-Server |
| Mail-Import | `ALLTAGSHELFER_IMAP_*` | Abruf von Mails (Anmeldedaten bleiben lokal) | konfigurierter IMAP-Server |
| Lizenz/Zahlung | Kauf einer Pro-Lizenz | Kunden-ID, Abo-Status, Ablaufdatum (vom Anbieter erhalten) | Bezahldienstleister |

Standardmaessig sind alle vier deaktiviert. Bleibt `GOOGLE_API_KEY` ungesetzt,
arbeitet der Assistent rein lokal/regelbasiert.

## Datensparsamkeit beim KI-Assistenten
- Es wird **nicht** automatisch uebertragen: die gesamte DB, Vertragsdetails
  ohne ausdrueckliche Anfrage, Mail-Klartext ausserhalb des Posteingangs-Moduls.
- Das LLM erhaelt nur die ueber die Capability-Schnittstelle freigegebenen
  Funktionen, keinen direkten Datenbankzugriff.

## Kein Tracking
Keine Cookies, keine Telemetrie, keine Werbung. Affiliate-Links sind statisch
und ohne Tracking-Parameter.

## Nutzerkontrolle / Loeschung
- In-App: **„Mehr" -> „Alle Daten loeschen"** leert lokale DB und App-
  Verzeichnisse unwiderruflich (es gibt kein Server-Konto).
- Export (Datenuebertragbarkeit): `python __main__.py --export` (CSV).
- Deinstallation entfernt alle lokalen Daten; Lizenz-/Zahlungsdaten loescht der
  Anbieter auf Anfrage (siehe `legal/DATENSCHUTZ.md`).

## Secret-Handling
Geheime Werte (API-Key, Passwoerter, DB-/Backup-Key, Sync-Token) liegen nie in
der DB, sondern nur in Umgebungsvariablen oder im OS-Keyring. Details:
[`SECURITY.md`](SECURITY.md).

Stand: synchron zu `legal/DATENSCHUTZ.md` (Stand dort: 2026-05-26).
