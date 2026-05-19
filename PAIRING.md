# Sichere Geraetekopplung - Konzept

Dieses Dokument beschreibt das Konzept zur sicheren Kopplung zwischen
einer Windows-Desktop-App, der Android-App und der iOS-App des
Alltagshelfers. Es ist die Grundlage fuer die Ablouml;sung des heute
verwendeten gemeinsamen `--token` in `services/sync_server.py` durch ein
echtes, geraetegebundenes Schluesselmaterial.

Das Dokument legt fest **was** gebaut wird und **warum** - die
konkrete Implementierung erfolgt in einem separaten Schritt
(Schnittstellen, Code-Pfade, Tests).

## 1. Ziele und Nicht-Ziele

### Ziele

1. **Geraetegebundene Identitaeten.** Jedes Geraet besitzt ein eigenes,
   nur lokal erzeugtes Langzeit-Schluesselpaar. Es verlaesst das
   Geraet nie im Klartext.
2. **Gegenseitige Authentisierung.** Nach der Kopplung kann jedes
   Geraet kryptographisch beweisen, mit welchen Partnern es vertraut
   - ohne Server, ohne Benutzerkonto.
3. **Drei gleichwertige Kopplungswege:** QR-Code, USB-Kabel, SMS-Link.
   Alle drei muenden in dasselbe Schluesselmaterial; die Sicherheit
   haengt nicht vom gewaehlten Weg ab.
4. **Begrenzte Gueltigkeit** der Kopplungs-Tokens (QR, SMS-Link)
   einstellbar; abgelaufene Codes sind kryptographisch wertlos.
5. **Sichere Speicherung** des Schluesselmaterials in den
   plattformeigenen Secure-Stores - **nicht** in der SQLite/SQLCipher-
   Datenbank.
6. **Stand der Technik** im Sinne von NIST SP 800-56A/57, RFC 7748
   (X25519), RFC 8032 (Ed25519), RFC 8439 (ChaCha20-Poly1305) und
   den OWASP MASVS L2 / ASVS L2 Anforderungen an Schluesselablage.

### Nicht-Ziele

- Keine Cloud-Identitaet, keine PKI mit externer CA. Vertrauen wird
  Geraet-zu-Geraet hergestellt (TOFU-Prinzip, Trust-On-First-Use, nach
  Out-of-Band-Bestaetigung).
- Kein Login-System. Die Kopplung ist ein einmaliger Vorgang pro
  Geraetepaar; der Benutzer authentisiert sich nicht laufend.
- Keine Wiederherstellung verlorener Geraete ueber das Netz. Geht ein
  Geraet verloren, wird es von den verbleibenden Partnern widerrufen.

## 2. Bedrohungsmodell

| Bedrohung                                | Schutz durch                                |
|------------------------------------------|---------------------------------------------|
| Passiver Lauscher im WLAN/Mobilnetz      | TLS 1.3 + Pinning auf Geraete-Public-Key    |
| Aktiver MITM beim Pairing                | PAKE mit kurzem Out-of-Band-Geheimnis       |
| Mitlesen eines QR-Codes vom Bildschirm   | Einmal-Code, kurze Gueltigkeit, PAKE         |
| Mitlesen einer SMS                        | Link enthaelt nur Einwegnonce, nicht den Key |
| Verlust/Diebstahl Geraet                 | Secure-Store + OS-Lockscreen + Widerruf      |
| Kompromittierter Server / Backup-Ordner  | Vertraulichkeit aus Ende-zu-Ende-Schluesseln |
| Replay einer alten Kopplungsnachricht    | Nonce + Ablaufzeitstempel + One-Time-Token  |

Annahmen:

- Der Benutzer kontrolliert beide an der Kopplung beteiligten
  Geraete physisch im Moment des Pairings.
- Das Betriebssystem ist nicht gerootet/jailbroken und der
  Lockscreen ist aktiv (Pruefung in der App; Warnung bei Verstoss).
- SMS gilt als **unsicherer Kanal**. Der Link transportiert deshalb
  nur ein One-Time-Nonce, niemals Schluesselmaterial.

## 3. Krypto-Bausteine

Alle drei Pairing-Wege benutzen denselben Krypto-Stack:

| Zweck                            | Verfahren                  | Quelle              |
|----------------------------------|----------------------------|---------------------|
| Geraete-Langzeit-Signatur        | **Ed25519**                | RFC 8032            |
| ECDH-Schluesselaustausch         | **X25519**                 | RFC 7748            |
| Passwort/Kurzcode-Austausch      | **SPAKE2** (PAKE)          | RFC 9382            |
| Schluesselableitung              | **HKDF-SHA-256**           | RFC 5869            |
| Symmetrische Vertraulichkeit     | **ChaCha20-Poly1305**      | RFC 8439            |
| Transport im Sync                | **TLS 1.3 (PSK-Mode)**     | RFC 8446            |
| Fingerprint-Anzeige (Backup-Check)| SHA-256, Base32 in 5x4 Gruppen | NIST SP 800-107 |

Keine RSA-Schluessel, kein CBC, kein SHA-1, keine selbstgebastelten
Konstruktionen. Verwendet werden ausschliesslich die
plattformnativen Bibliotheken: `cryptography` (Desktop, Mobile via
Python-for-Android), `CryptoKit` (iOS-Native-Bridge),
`androidx.security.crypto` + Tink (Android-Native-Bridge).

## 4. Geraete-Identitaet

Beim allerersten Start einer App auf einem Geraet:

1. Erzeuge ein Ed25519-Langzeit-Schluesselpaar `(IK_priv, IK_pub)`.
2. Erzeuge eine zufaellige `device_id` (UUIDv4) und einen
   menschenlesbaren `device_name` (Default: Hostname / Modellname,
   editierbar).
3. Speichere `IK_priv` im plattformeigenen Secure-Store
   (siehe Kapitel 7). `IK_pub`, `device_id`, `device_name` liegen
   unverschluesselt in der App-DB - es sind oeffentliche Werte.
4. Berechne den **Fingerprint** als `SHA-256(IK_pub)`, abgekuerzt auf
   die ersten 100 Bit, ausgegeben als 5 Gruppen zu 4 Zeichen Base32
   (Beispiel: `K7QH-3M2N-5T8X-PVR4-A9BC`). Dieser Fingerprint ist die
   einzige sicherheitsrelevante Zeichenkette, die der Benutzer je zu
   Gesicht bekommt.

Die Existenz und Form von `IK` ist unabhaengig vom Pairing-Weg. Alle
drei Wege beweisen am Ende nur eines: *welche `IK_pub` zu welchem
Geraet gehoert*.

## 5. Allgemeines Pairing-Protokoll

Egal ueber welchen der drei Wege - das eigentliche Handshake ist
identisch und laeuft so:

```
Initiator I  (= Geraet, das einlaedt)        Responder R (= Geraet, das beitritt)
--------------------------------------       -----------------------------------
1. erzeugt Pairing-Sitzung:
     sid       = 128-bit zufaellig
     ot_secret = 256-bit zufaellig
     exp       = jetzt + ttl  (siehe je Methode)
     ablage    = Pairing-Cache (RAM + verschluesselt auf Platte)
     -> "Einladung" enthaelt: sid, ot_secret-Material (kanal-spezifisch),
        IK_pub_I, fingerprint_I, exp, methode

                Einladung -- (Kanal: QR / USB / SMS) -->

                                                  2. parst Einladung
                                                  3. prueft exp > jetzt
                                                  4. zeigt fingerprint_I an,
                                                     fordert Bestaetigung
                                                     (bei QR/USB: implizit;
                                                      bei SMS: explizit)

5./6. SPAKE2-Handshake ueber TLS-1.3-PSK (PSK=ot_secret)
      -> liefert beidseitig: MS (master secret)
      -> erzwingt: Angreifer ohne ot_secret kann MS nicht ableiten

7. HKDF(MS, salt=sid, info="pair/v1") -> session_key (32 Byte)

8. Beidseitiger Identitaetsnachweis:
      I sendet: sign(IK_priv_I, transcript)
      R sendet: sign(IK_priv_R, transcript)
   transcript = sid || IK_pub_I || IK_pub_R || methode || exp

9. Beidseitige Pruefung der Signaturen + Pruefung dass
   fingerprint(IK_pub) zum erwarteten Fingerprint passt.

10. Beide Seiten speichern den Partner-Eintrag:
       (device_id, device_name, IK_pub, gekoppelt_seit, methode,
        letzter_kontakt, status=active)
    plus einen abgeleiteten Long-Term-PSK fuer den Sync:
       sync_psk = HKDF(MS, salt="sync-psk", info=sortiert(IK_pub_I,IK_pub_R))

11. Sitzung wird verworfen: ot_secret, sid, MS aus RAM geloescht.
    Der Einladende invalidiert den Einmal-Code (Wiederverwendung
    unmoeglich).
```

Wichtige Eigenschaften:

- **MITM-resistent** durch PAKE: ein Angreifer ohne `ot_secret`
  bekommt keine ableitbare Sitzung. Ein Angreifer *mit* `ot_secret`
  scheitert spaetestens an der Ed25519-Signatur ueber das Transcript -
  und an der Fingerprint-Anzeige beim Benutzer.
- **Forward Secrecy** fuer den Pairing-Akt durch SPAKE2 + ephemeres
  X25519 im TLS-Handshake.
- **Replay-Schutz** durch frische `sid`, `ot_secret`, `exp`.
- **Kein Server noetig**: alles laeuft direkt zwischen den beiden
  Geraeten ueber LAN/USB/Internet-Sync-Endpunkt.

## 6. Die drei Kopplungswege

### 6.1 QR-Code

Anwendungsfall: Beide Geraete liegen vor dem Benutzer, eines hat eine
Kamera.

**Ablauf:**

1. Auf dem Initiator-Geraet (typischerweise PC):
   *Einstellungen -> Geraete -> Neues Geraet koppeln -> QR-Code*.
2. Der Benutzer waehlt die **Gueltigkeitsdauer** des QR-Codes:
   `30 s | 1 min | 5 min | 10 min` (Default 1 min).
3. Die App erzeugt die Pairing-Sitzung (Kap. 5) und rendert einen
   QR-Code mit Inhalt:
   ```
   alltagshelfer://pair?v=1&sid=<base64url>
                         &m=qr
                         &ep=<endpoint>
                         &otp=<base64url(ot_secret)>
                         &fp=<fingerprint_I>
                         &exp=<unix-ts>
   ```
   Der `endpoint` ist die LAN-Adresse + Port des Initiator-Geraets
   (bei Sync ueber `HttpSyncProvider`) bzw. eine
   mDNS-Service-Adresse, kein Klartext-DNS-Hostname.
4. Mobile-App liest QR mit der Kamera, prueft `exp`, verbindet zum
   `endpoint`, fuehrt das Protokoll aus Kap. 5 aus.
5. Nach Erfolg: Bestaetigungstoast auf beiden Geraeten plus Anzeige
   des Partner-Fingerprints. Bei Abweichung -> Abbruch und Logging.

**Sicherheitshinweise:**

- `ot_secret` ist Teil der URL und damit *im QR sichtbar*. Das ist
  vertretbar, weil (a) die Sitzung nur einmal nutzbar ist, (b) die
  TTL kurz ist, (c) der Initiator den Code nach Ablauf hart loescht.
- Der QR-Code darf **nicht** dauerhaft als Bild gespeichert werden -
  auch nicht im App-Cache. Er existiert nur als gerenderte Bitmap im
  Fenster.

### 6.2 USB-Kabel

Anwendungsfall: Maximales Sicherheitsniveau, oder kein Funkkontakt
moeglich (z.B. wegen Hotel-WLAN).

**Ablauf:**

1. Mobile-Geraet ueber USB an den PC anschliessen.
2. PC-App erkennt das Geraet entweder:
   - via **ADB** (Android, Debug-Bruecke aktiviert) - bevorzugt fuer
     Power-User,
   - via **USB-Bulk-Transfer** ueber `libusb` und ein im Mobile
     registriertes USB-Vendor-Class-Interface,
   - via **iOS-USB-Mux** (`usbmuxd`/`libimobiledevice`) fuer iOS.
3. Der Initiator erzeugt eine Pairing-Sitzung mit *kurzer* TTL
   (Default 60 s; nicht laenger noetig, da Kanal physisch).
4. Die Einladung (gleicher Inhalt wie 6.1, ohne sichtbaren QR-Code)
   wird ueber den USB-Kanal an die App geschickt. Auf dem Mobile
   erscheint eine Dialogbox **"PC '<name>' moechte koppeln, Fingerprint
   <fp>. Annehmen?"** - der Benutzer bestaetigt physisch.
5. Das Protokoll aus Kap. 5 laeuft ueber den USB-Kanal als Transport
   ab; **kein** WLAN, kein Mobilfunk noetig.
6. Nach Erfolg merken sich beide Geraete den `sync_psk`. Ab da kann
   der Sync auch wieder ueber Funk laufen - USB war nur fuer den
   Pairing-Akt noetig.

**Plattform-Hinweis:** iOS erlaubt eigenen USB-Datenverkehr nur ueber
das offizielle MFi-Programm oder ueber das Apple-USB-Mux-Protokoll
(z.B. via `peertalk`). Wer das MFi-Programm nicht durchlaeuft,
implementiert den iOS-USB-Pfad ueber `usbmuxd` auf der PC-Seite und
ein TCP-Loopback auf der iOS-Seite. Aus Benutzersicht bleibt das
identisch.

### 6.3 SMS-Link

Anwendungsfall: Geraete sind nicht am selben Ort, der Initiator hat
nur die Mobilnummer des Ziels.

**Ablauf:**

1. Initiator gibt die Mobilnummer ein und waehlt die Gueltigkeit:
   `5 min | 15 min | 1 h | 6 h | 24 h` (Default 15 min).
2. Initiator erzeugt eine Pairing-Sitzung; statt das `ot_secret` in
   die URL zu legen, wird die URL **nur ein Lookup-Token** enthalten:
   ```
   https://pair.alltagshelfer.local/p/<lookup_token>
   ```
   Der `lookup_token` ist 128 Bit zufaellig, URL-safe Base64.
3. Initiator-Geraet stellt unter diesem Lookup-Token (auf einem vom
   Benutzer betriebenen, kleinen Relay-Endpunkt - siehe Kasten unten)
   die eigentliche Pairing-Einladung zur Abholung bereit. Die
   Einladung enthaelt zusaetzlich:
   - ein **zweites, dem Benutzer angezeigtes Bestaetigungs-PIN**
     (6 Ziffern), das *nicht* per SMS verschickt wird.
4. SMS wird via lokalem SMS-Gateway oder dem
   System-`Intent.ACTION_SENDTO` (Android) bzw.
   `MFMessageComposeViewController` (iOS) verschickt - die SMS-API
   ist niemals eine Cloud-API mit Datenabfluss.
5. Empfaenger oeffnet den Link. Die Ziel-App (per Deep-Link
   `alltagshelfer://pair?...`) zeigt:
   *"PC '<name>' moechte koppeln, gib die 6-stellige PIN ein, die auf
   dem PC angezeigt wird."*
6. Die PIN wird als `ot_secret` (nach SPAKE2-Konvention: gehasht,
   gesalzen) in den PAKE-Handshake aus Kap. 5 eingespeist.
7. Falsche PIN -> SPAKE2 schlaegt fehl, *keine* Information leakt,
   nach 3 Fehlversuchen wird der Lookup-Token verbrannt.

**Warum so?** Eine SMS ist nicht vertraulich. Sie darf daher kein
Schluesselmaterial enthalten. Was sie enthaelt, ist ein Zeiger auf
eine Sitzung; das eigentliche Geheimnis (die PIN) reist Out-of-Band -
mindestens muendlich, oder per Anzeige auf dem PC, den der Empfaenger
ohnehin sehen wird, wenn er physisch dort ist. So gewinnt der Angreifer
nichts, selbst wenn er die SMS mitliest.

> **Relay-Endpunkt:** Der "Briefkasten" fuer den Lookup ist bewusst
> klein gehalten. Er kann sein:
> 1. der lokal laufende `HttpSyncProvider` des Initiators
>    (LAN-erreichbar, mit Reverse-Tunnel ueber das Heimrouter-NAT
>    via UPnP/STUN), **oder**
> 2. ein vom Benutzer selbst gehosteter Mini-Service. Er speichert
>    nichts dauerhaft, kennt das `ot_secret` (=PIN) **nicht** und
>    haelt die Einladung nur bis `exp` vor.
> Es gibt bewusst keinen zentralen Hersteller-Server.

## 7. Sichere Speicherung des Schluesselmaterials

Nichts von dem, was unten gelistet ist, landet je in `database.py`
oder einer SQLite/SQLCipher-Datei. Diese Daten gehoeren in den
**plattformeigenen Secure-Store**:

| Plattform | Store                                              | Mechanismus                                  |
|-----------|----------------------------------------------------|----------------------------------------------|
| Windows   | Windows Credential Manager (Vault)                 | DPAPI (`CryptProtectData`) je Benutzer; Schluessel an Benutzeranmeldung gebunden |
| Android   | Android Keystore                                   | Hardware-Backed Keymaster/StrongBox falls vorhanden; `BiometricPrompt`-Gate optional |
| iOS       | Keychain Services, `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` | Secure Enclave fuer ECC-Schluessel (P-256-Schattenkopie der Ed25519-Identitaet via Curve-Transform, oder Secure-Enclave-gebundener Wrap-Key) |

**Was wird wo abgelegt:**

```
Secure-Store-Eintrag "alltagshelfer.identity"
  - IK_priv                   (Ed25519, 32 Byte)
  - device_id                 (UUID, Klartext erlaubt, aber zusammen lagern)
  - device_name               (optional, Klartext erlaubt)

Secure-Store-Eintrag je Partner "alltagshelfer.peer.<device_id>"
  - sync_psk                  (32 Byte, PSK fuer TLS-1.3 mit dem Partner)
  - IK_pub_peer               (32 Byte, Ed25519-Public-Key des Partners)
  - fingerprint_peer          (abgeleitet, redundant - fuer schnellen UI-Check)
  - methode, gekoppelt_seit   (Audit)
  - status                    (active | suspended | revoked)
```

Was in der normalen App-DB liegen darf:

- `device_name`, `device_id`, `IK_pub_peer`, `fingerprint_peer`,
  `gekoppelt_seit`, `letzter_kontakt`, `status`, `methode`.

Was **nicht** in der App-DB liegen darf - **nie**:

- `IK_priv`, `sync_psk`, jegliches `ot_secret`/PIN/Lookup-Token nach
  Abschluss der Sitzung.

**Zugriffskontrolle:**

- Android/iOS: Zugriff auf `IK_priv` und `sync_psk` darf optional an
  Biometrie (`BiometricPrompt`, `LAContext`) gebunden werden -
  einstellbar in den App-Einstellungen.
- Windows: Eintrag wird mit `CRYPTPROTECT_LOCAL_MACHINE = 0` (also
  benutzergebunden) abgelegt, sodass ein anderer Windows-Benutzer
  am selben PC nicht auf das Material zugreift.

## 8. Pairing-Sitzungs-Cache

Waehrend eine Einladung gueltig ist (zwischen Erzeugen des QR/SMS und
Eintreffen der Antwort), muss der Initiator drei Werte vorhalten:

- `sid`, `ot_secret`, `exp`.

Diese liegen:

- primaer im RAM des Initiators (verschwindet beim App-Beenden),
- redundant in einem **mit `sync_psk_bootstrap`-Schluessel
  AEAD-verschluesselten** kleinen JSON unter dem App-Profil-Ordner,
  damit ein App-Neustart waehrend der TTL den Vorgang nicht
  zerstoert. Der `sync_psk_bootstrap`-Schluessel liegt seinerseits im
  Secure-Store.

Wenn `exp` ueberschritten wird:

1. Eintrag aus RAM und Cache loeschen,
2. zugehoeriger QR-Code in der UI invalidieren (Anzeige "abgelaufen"),
3. eintreffende Verbindungen mit derselben `sid` mit
   `410 Gone` abweisen.

## 9. Integration in den bestehenden Sync

Heute (siehe `services/sync_server.py:51-110`) benutzt der
HTTP-Sync-Server einen statischen `--token`. Das wird ersetzt durch:

1. **TLS 1.3 PSK-Mode** auf der Transportebene. Der PSK ist der pro
   Geraetepaar gespeicherte `sync_psk`. Damit gibt es keinen
   gemeinsamen "alle-duerfen"-Token mehr - jede Verbindung
   identifiziert ihren Absender eindeutig.
2. Pro eingehender Verbindung wird die Peer-`device_id` aus dem
   PSK-Identity-Feld bestimmt und gegen die Liste der gekoppelten
   Peers gehalten. Unbekannte Peers -> `401`.
3. Das bestehende Event-Format (`event_id`, `device_id`,
   `timestamp`, `capability`, ...) bleibt unveraendert. Neu ist nur,
   dass jedes Event zusaetzlich mit `Ed25519(IK_priv, event_payload)`
   signiert wird. Empfaenger pruefen Signatur gegen den `IK_pub` des
   Absenders, *bevor* sie das Event in den Log uebernehmen. Damit ist
   das Sync-Log Ende-zu-Ende verifizierbar, auch wenn es ueber einen
   geteilten Ordner (Dropbox, OneDrive) laeuft.
4. Migration: Ein Geraet, das ein altes Token-basiertes Setup
   vorfindet, fuehrt beim Update einen einmaligen **"Geraet erneut
   koppeln"**-Flow durch (analog Kap. 6.1). Bis dahin laeuft der Sync
   read-only.

## 10. Lebenszyklus eines Peers

```
            +---------- pair via QR/USB/SMS ----------+
            |                                         v
  [unknown] --+                                 [active]
            |                                         |
            |   Benutzer in den Einstellungen waehlt  |
            |    "Geraet vorruebergehend pausieren"    |
            |                                         v
            |                                   [suspended]
            |                                         |
            |     "Geraet entfernen"                  |
            +-----------------------------------> [revoked]
```

- **suspended:** Schluesselmaterial bleibt, Sync wird aber
  abgewiesen. Reaktivierung ohne erneutes Pairing.
- **revoked:** Schluesselmaterial wird aus dem Secure-Store
  geloescht. Reaktivierung nur ueber neues Pairing. Alle anderen
  gekoppelten Geraete bekommen einen signierten **Revocation-Event**
  in den Sync-Log; sie loeschen den `sync_psk` zum widerrufenen Peer.

## 11. Benutzererlebnis (UI/UX-Regeln)

- Fingerprints werden konsistent in **5 Gruppen zu 4 Zeichen Base32**
  angezeigt - auf Desktop, Android und iOS gleich. Keine kuerzeren
  Varianten in irgendeinem Screen.
- Beim Pairing-Erfolg zeigt jede Seite den Fingerprint der Gegenseite
  und fragt: **"Stimmt diese Zeichenfolge mit dem ueberein, was du auf
  dem anderen Geraet siehst?"**. Erst nach "Ja" wird der Peer auf
  `active` gesetzt. Bei QR/USB ist das ein Fingerzeig-Vergleich, bei
  SMS-Link ein Telefonat oder persoenliches Treffen.
- Abgelaufene QR-Codes/SMS-Links erzeugen klare Fehlermeldungen
  ("Code ist seit X Sekunden abgelaufen, bitte neu erzeugen") - keine
  generischen Crypto-Fehler.
- Die App listet unter *Einstellungen -> Gekoppelte Geraete* alle
  Peers mit Fingerprint, Kopplungsdatum, letztem Kontakt und
  Methode. Aktionen: *Pausieren*, *Entfernen*, *Fingerprint anzeigen*.

## 12. Logging und Auditierbarkeit

- Jeder Pairing-Versuch (Erfolg/Misserfolg) wird lokal in
  `services/logging_setup.py` mit Zeitstempel, Methode, Ergebnis
  protokolliert. **Nicht** geloggt: `ot_secret`, PIN, `sync_psk`,
  `IK_priv` (auch nicht in Stacktraces).
- Erfolgreiche Pairings erzeugen einen signierten Audit-Event:
  `pair.completed (peer_id, method, fingerprint, ts)`. Dieser laeuft
  durch den normalen Audit-Hook der `ModuleRegistry`.
- Revocations dito: `pair.revoked (peer_id, reason, ts)`.

## 13. Risiken und Restrisiken

| Restrisiko                                    | Bewertung / Gegenmittel                        |
|-----------------------------------------------|-----------------------------------------------|
| Benutzer ignoriert Fingerprint-Vergleich      | UI macht Vergleich blockierend, Tooltip erklaert den Sinn |
| Verlorenes Geraet vor Widerruf missbraucht    | Lockscreen + Biometric-Gate fuer Sync-Zugriff |
| SMS-Provider sieht den Link-Inhalt            | Link enthaelt nur Lookup-Token; ohne PIN nutzlos |
| Relay-Endpunkt nicht erreichbar               | Fallback auf QR / USB; klare UI-Meldung       |
| Downgrade-Angriff auf TLS                     | TLS 1.3 erzwungen, keine Cipher-Verhandlung   |
| Schluesselverlust nach OS-Reinstall (Windows) | DPAPI-Migration ueber Microsoft-Konto, oder erneutes Pairing |

## 14. Offene Punkte fuer die Implementierung

Diese Punkte werden im Implementierungs-PR entschieden, sind hier
nur dokumentiert:

- Wahl der konkreten SPAKE2-Bibliothek (Kandidaten: `spake2`-PyPI
  fuer Desktop, `tink` fuer Android, `CryptoKit`-eigene KAS fuer iOS
  mit angepasstem PAKE-Wrapper).
- Ablage-Schema im jeweiligen Secure-Store
  (Schluesselnamen, Versionsfeld, Migration auf v2).
- Genauer USB-Bulk-Transfer-Protokoll-Header (Vendor-ID,
  Endpoint-Layout) - der Pairing-Flow ist davon unabhaengig.
- UPnP/STUN-Fallback fuer den SMS-Relay-Endpunkt - Konfiguration und
  Diagnose-Tools.
- Mapping der Pairing-Capabilities (`pair.start`, `pair.complete`,
  `pair.revoke`) auf `core.interface.Capability`.

## 15. Quellen / weiterfuehrend

- NIST SP 800-56A Rev. 3 - Pair-Wise Key Establishment
- NIST SP 800-57 Part 1 Rev. 5 - Key Management Recommendations
- NIST SP 800-63B - Authenticator Lifecycle / OOB
- RFC 7748 (X25519), RFC 8032 (Ed25519), RFC 8439 (ChaCha20-Poly1305)
- RFC 8446 (TLS 1.3), RFC 9258 (External PSK in TLS 1.3)
- RFC 9382 (SPAKE2)
- RFC 5869 (HKDF)
- OWASP MASVS v2 - Kapitel "Cryptography" und "Storage"
- OWASP ASVS 4.0 - Kapitel V6 (Stored Cryptography), V9 (Communications)
- Signal-Protokoll Whitepaper (X3DH) - als Inspiration fuer den
  Out-of-Band-Identitaetsbeweis
