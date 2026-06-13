# Sicherheit

ZunaroDo ist ein **lokal-first** Alltagsassistent: Nutzdaten bleiben auf dem
Geraet, Netz-/Cloud-Funktionen sind optional und standardmaessig deaktiviert.
Diese Datei beschreibt das Sicherheitsmodell und den Meldeweg fuer
Schwachstellen. Rechtliche Texte (Datenschutz, AGB, Impressum, Widerruf) liegen
unter [`legal/`](legal/); die technische Datenfluss-Beschreibung in
[`PRIVACY.md`](PRIVACY.md).

## Schwachstellen melden

Bitte **keine** Sicherheitsluecken ueber oeffentliche GitHub-Issues melden.
Stattdessen vertraulich per E-Mail an **alltagshelfer@zunarodo.github.io**
(siehe `legal/IMPRESSUM.md`). Hilfreich sind: betroffene Version/Commit,
Reproduktionsschritte und – falls vorhanden – ein minimaler Nachweis.
Wir bestaetigen den Eingang und koordinieren eine verantwortungsvolle
Offenlegung nach Behebung.

## Sicherheitsmodell

### Lokale Datenhaltung
- Alle Nutzdaten liegen in einer lokalen **SQLite**-Datenbank auf dem Geraet.
- Optionale **SQLCipher-Verschluesselung** der gesamten DB ueber
  `ALLTAGSHELFER_DB_KEY`. Backups koennen mit einem **separaten** Schluessel
  (`ALLTAGSHELFER_BACKUP_KEY`) verschluesselt werden, z. B. zur Weitergabe an
  einen anderen Personenkreis.
- Ohne Konfiguration verlaesst **nichts** das Geraet (Offline-Modus).

### Secret-Handling
- Geheime Werte (`SECRET_KEYS` in `services/config.py`: Gemini-Key, IMAP-/
  SMTP-Passwort, DB-Key, Backup-Key) werden **nie in der Datenbank persistiert**.
  Sie kommen ausschliesslich aus **Umgebungsvariablen** oder dem
  **OS-Schluesselspeicher** (Keyring).
- `.env` ist ueber `.gitignore` ausgeschlossen; nur [`.env.example`](.env.example)
  (leere Werte) wird versioniert. Secret-Scanning ist ueber
  [`.gitleaks.toml`](.gitleaks.toml) konfiguriert.
- Keine echten Keys/Tokens in Code, Commits, Logs oder generierten Artefakten.

### KI-Assistent (Google Gemini) – optional, datensparsam
- Nur aktiv, wenn `GOOGLE_API_KEY` (oder `GEMINI_API_KEY`) gesetzt ist; sonst
  laeuft ein regelbasierter Offline-Router.
- An Google gehen ausschliesslich die konkrete Chat-Anfrage und ggf. ein
  **zusammengefasster** Kontext – **nie die gesamte Datenbank**.
- Das LLM sieht nur die ueber die **Capability-Schnittstelle** freigegebenen
  Funktionen (kein direkter Datenbankzugriff). Destruktive Capabilities sind als
  solche markiert und im Audit-Log nachvollziehbar.

### Synchronisation
- Optional via geteiltem Ordner (`ALLTAGSHELFER_SYNC_DIR`) oder HTTP/HTTPS-
  Sync-Server (`ALLTAGSHELFER_SYNC_URL`).
- Fuer Netz-Sync **dringend empfohlen**: TLS (`--cert`/`--key`) **und** ein
  Auth-Token (`ALLTAGSHELFER_SYNC_TOKEN`). Den Sync-Server nicht ungeschuetzt
  ins offene Netz stellen.
- Konfliktaufloesung ist Lamport-Clock-basiert (last-writer-wins) und im
  Audit-Log nachvollziehbar.

### Lizenz & Pairing
- Pro-Lizenz-Tokens sind **Ed25519-signiert** (`services/license_token.py`) –
  Manipulation wird bei der Verifikation erkannt.
- Pairing-Geheimnisse werden im OS-Keyring gehalten
  (`ALLTAGSHELFER_PAIRING_BACKEND=keyring`; `memory` ist nur fuer Tests/CI).

### Schutz vor Datenverlust
- Kritische, gebuendelte/irreversible Aktionen (Purge, gesammeltes Loeschen
  archivierter Vorschlaege, endgueltiges Loeschen von Notizen/Vorlagen)
  erfordern eine ausdrueckliche Bestaetigung; der KI-Assistent verlangt dafuer
  eine explizite Freigabe. Normale CRUD-Aktionen sind per Soft-Delete
  reversibel (Papierkorb -> `restore`/`purge`).

## Empfehlungen fuer den Betrieb
- DB-Verschluesselung aktivieren, wenn das Geraet geteilt/mobil ist
  (`ALLTAGSHELFER_DB_KEY`).
- Sync-Server nur mit TLS + Token betreiben und das `/data`-Volume schuetzen
  (siehe `Dockerfile`).
- Den Gemini-Key nur setzen, wenn Cloud-KI gewuenscht ist; sonst Offline-Modus.

## Unterstuetzte Versionen
Sicherheitsfixes erfolgen auf dem `main`-Branch / der jeweils aktuellen
Veroeffentlichung. Aeltere Staende werden nicht separat gepflegt.
