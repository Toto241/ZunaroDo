# 11 - Play-Console-Einreichung (Hand-Schritte)

> Diese Schritte lassen sich **nicht** aus dem Repo automatisieren — sie
> passieren in der Google Play Console. Diese Datei bündelt sie mit den
> aus dem Code abgeleiteten Antworten, damit das Ausfüllen schnell und
> wahrheitsgemäß geht. Die Hard-Checks (SDK, Permissions, Privacy-Doku,
> Löschpfad, Closed-Test-Config) deckt bereits `android-compliance` ab;
> siehe auch [09_RELEASE_CHECKLIST.md](09_RELEASE_CHECKLIST.md).

## 1. Data-Safety-Formular

Antworten **aus dem Code generiert** mit
`python -m tools.data_safety --markdown` (bei Änderungen am Datenfluss neu
erzeugen und `python -m tools.data_safety --check` muss grün sein):

- Daten gesammelt: **Ja**
- Daten an Dritte weitergegeben: **Nein**
- Verschlüsselt bei Übertragung: **Ja**
- Nutzer können Löschung anfordern: **Ja** (In-App, siehe unten)

| Datentyp | gesammelt | geteilt | Zweck | optional |
| --- | --- | --- | --- | --- |
| E-Mail | Ja | Nein | App-Funktionalität | Ja (nur bei IMAP-Opt-in) |
| Name | Ja | Nein | App-Funktionalität | Nein |
| Nutzer­inhalte | Ja | Nein | App-Funktionalität | Nein |

- Kein Tracking-/Werbe-/Analytics-SDK (vom Compliance-Check verifiziert).
- Optionale Online-Features (Gemini-KI, IMAP) verarbeiten Inhalte nur auf
  ausdrückliches Opt-in und teilen nichts zu Werbe-/Analytics-Zwecken.

## 2. Datenlöschung (Account Deletion)

- Es gibt **kein Entwickler-Konto/Server** → keine serverseitige Löschung
  nötig. Maßgeblich ist der **In-App-Vollöschpfad**
  („Mehr → Alle Daten löschen", siehe `mobile/screens/more.py` /
  `services/data_deletion.py`), dokumentiert in `legal/DATENSCHUTZ.md`.
- Im Console-Formular „Datenlöschung": **In-App-Löschung** angeben; als
  URL die gehostete Datenschutzerklärung (Abschnitt Löschung) verlinken.

## 3. Content-Rating-Fragebogen

- Kategorie: **Dienstprogramm / Produktivität** (keine Gewalt, kein
  Glücksspiel, keine UGC-Sharing-Funktion).
- Nutzergenerierte Inhalte mit Veröffentlichung/Teilen: **Nein**.
- Erwartetes Rating: **USK 0 / PEGI 3** o. ä. (Console berechnet final).

## 4. Zielgruppe & App-Inhalt

- Zielgruppe: **≥ 13 Jahre** („Mixed audiences", nicht primär für Kinder).
- App-Zugriff: **Kein Login erforderlich** — alle Funktionen ohne
  Anmeldung erreichbar (Pro-Aktivierung optional, kein Konto).
- Werbung enthalten: **Nein**.
- Government-/Finanz-/Gesundheits-Sonderkategorien: **Nein**.

## 5. Store-Listing-Assets

Pflicht-Assets (aktuell, ohne Skeleton/Lorem-ipsum):

- App-Icon 512×512 PNG.
- Feature-Graphic 1024×500.
- Mindestens 2 Telefon-Screenshots (16:9 oder 9:16, ≥ 320 px).
- Kurz-/Vollbeschreibung + Release-Notes je Locale — Pflichtfelder und
  Längen prüft `python -m tools.store_listing --check`.

## 6. Signierung & Bundle

- AAB via Workflow „Android Release (AAB)" bauen
  ([07_CICD.md → Release-Build](07_CICD.md)).
- **Play App Signing** in der Console aktivieren; Upload-Key sicher sichern.

## 7. Konto- & Identitätsprüfung

- Personal-/Organisations-Verifizierung in der Console abschließen
  (Adresse, ggf. D-U-N-S für Organisationen, Telefon/E-Mail).
- **Closed Test** mit ≥ 12 Testern über ≥ 14 Tage durchführen und den
  Nachweis als `release/closed-test-JJJJ-MM.md` ablegen (Vorlage:
  `release/CLOSED_TEST_EVIDENCE_TEMPLATE.md`).

## 8. Reihenfolge

1. Identitäts-/Kontoverifizierung abschließen.
2. Internal Testing hochladen, Pre-Launch-Report prüfen.
3. Closed Test (≥ 12 / ≥ 14 Tage) → Nachweis ablegen.
4. Data-Safety, Content-Rating, Zielgruppe, Store-Listing ausfüllen.
5. Privacy-URL setzen (HTTP 200) und im Listing eintragen.
6. Production-Release mit Staged-Rollout (10 %).
