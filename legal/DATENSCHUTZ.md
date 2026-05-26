# Datenschutzerklaerung

Diese Erklaerung beschreibt die Datenverarbeitung der lokal-first App
ZunaroDo. Vor Veroeffentlichung im Store sollte die Fassung anwaltlich
gegen das konkrete Anbieter- und Payment-Setup geprueft werden.

---

## 1. Verantwortlicher

Verantwortlicher fuer die Datenverarbeitung im Sinne der DSGVO ist:

**ZunaroDo**
Open-Source-Projekt: <https://github.com/zunarodo/alltagshelfer>
E-Mail: zunarodo@users.noreply.github.com

## 2. Grundsatz - Lokale Datenhaltung

Alltagshelfer ist eine **lokal laufende Anwendung**. Alle Nutzdaten
(Vertraege, Termine, Familie, Finanzen, Notizen) werden ausschliesslich
auf dem Geraet des Nutzers in einer SQLite-Datenbank gespeichert -
optional verschluesselt mit SQLCipher (siehe README).

Eine Uebertragung an unsere Server findet **nicht** statt, soweit nicht
ausdruecklich konfiguriert (siehe Punkt 4 - optionale Cloud-Dienste).

## 3. Welche Daten verarbeitet werden

| Datenart | Wo | Zweck | Rechtsgrundlage |
| --- | --- | --- | --- |
| Vertraege, Termine, Finanzen, Familie, Kontakte | lokal | Kernfunktion der App | Art. 6 Abs. 1 lit. b DSGVO (Vertrag) |
| Crash-Logs (`logs/`) | lokal | Fehlersuche | Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse) |
| Lizenz-Token (signiert) | lokal | Pro-Aktivierung | Art. 6 Abs. 1 lit. b DSGVO |
| Zahlungsdaten | beim Bezahldienstleister | Abwicklung | Art. 6 Abs. 1 lit. b DSGVO |

## 4. Optionale Cloud-Dienste

Folgende Dienste sind standardmaessig **deaktiviert** und werden nur
nach ausdruecklicher Konfiguration durch den Nutzer aktiv:

### 4.1 Google Gemini (KI-Assistent)
Wenn `GOOGLE_API_KEY` gesetzt ist, werden die Nutzer-Eingaben an die
Chat-Funktion an Google ([Google Ireland Ltd., Dublin]) uebertragen.
Datenschutzerklaerung: <https://policies.google.com/privacy>.

### 4.2 Mehrgeraete-Sync
Sync-Daten werden entweder in einem geteilten Ordner (Dropbox/OneDrive
- jeweils eigener Datenschutzhinweis des Anbieters) oder zu einem
selbst gehosteten HTTP/HTTPS-Sync-Server gespiegelt. Ohne Konfiguration
findet keine Synchronisation statt.

### 4.3 IMAP-Mail-Import
Wenn `ALLTAGSHELFER_IMAP_*` konfiguriert ist, werden Mails vom
angegebenen Server abgerufen und lokal in Vorschlaege umgewandelt.
Anmeldedaten verbleiben auf dem Endgeraet.

### 4.4 Bezahldienstleister (Lizenz-Aktivierung)
Fuer den Erwerb einer Pro-Lizenz kann der Anbieter Paddle oder Lemon
Squeezy als Merchant of Record nutzen. Dort gilt deren jeweilige
Datenschutzerklaerung:
- Paddle: <https://www.paddle.com/legal/privacy>
- Lemon Squeezy: <https://www.lemonsqueezy.com/privacy>

Wir erhalten vom Bezahldienstleister: Kunden-ID, Abo-Status, Ablaufdatum.

## 5. KI-Verarbeitung (Gemini)

Bei aktivem Gemini werden folgende Daten an Google uebertragen:
- die konkrete Nutzer-Anfrage im Chat
- ggf. zusammengefasster Kontext aus der App (z.B. anstehende Termine)

Die App **uebertraegt nicht automatisch**:
- die gesamte DB
- Vertragsdetails ohne ausdrueckliche Anfrage
- Klartextfelder von Mails ausser im Posteingangs-Modul

Empfehlung: Wenn Sie keine Cloud-KI wollen, lassen Sie `GOOGLE_API_KEY`
ungesetzt - die App laeuft dann im Offline-Modus mit regelbasiertem
Router.

## 6. Cookies, Tracking, Werbung

Die App setzt **keine Cookies**, sendet **keine Telemetrie** und
zeigt **keine Werbung** an. Affiliate-Empfehlungen im Vertragsmodul
sind statische Links ohne Tracking-Parameter.

## 7. Ihre Rechte (Art. 15 - 22 DSGVO)

Sie haben das Recht auf:
- **Auskunft** (Art. 15): Was haben wir ueber Sie gespeichert?
- **Berichtigung** (Art. 16): Korrektur falscher Daten.
- **Loeschung** (Art. 17): Loeschung Ihrer Daten. Die App bietet einen
   vollstaendigen In-App-Loeschpfad: **"Mehr" -> "Alle Daten loeschen"**
   leert die lokale Datenbank und alle App-Verzeichnisse unwiderruflich
   (es gibt kein Server-Konto, daher ist keine serverseitige Loeschung
   noetig). Alternativ entfernt die Deinstallation alle lokalen Daten;
   Lizenz-/Zahlungsdaten loeschen wir auf Anfrage per Mail.
- **Einschraenkung** (Art. 18) und **Widerspruch** (Art. 21).
- **Datenuebertragbarkeit** (Art. 20): CSV-Export ist in der App
   eingebaut (`__main__.py --export`).
- **Beschwerde bei der Aufsichtsbehoerde** (Art. 77).

## 8. Speicherdauer

- Lokale Nutzdaten: bis zur Loeschung durch den Nutzer.
- Lizenz-/Zahlungsdaten: bis 10 Jahre nach Ablauf der Lizenz
  (handelsrechtliche Aufbewahrungsfrist).

## 9. Aenderungen dieser Erklaerung

Wir behalten uns vor, diese Datenschutzerklaerung anzupassen, um sie
an geaenderte Rechtslagen oder neue Funktionen anzupassen. Die
jeweils aktuelle Version finden Sie in der App unter
Einstellungen -> Datenschutz.

Stand: 2026-05-26
