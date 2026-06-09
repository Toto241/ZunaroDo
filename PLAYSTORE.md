# Play-Store-Veroeffentlichung - vollstaendige Anleitung

Stand: 2026-05. Die Google-Play-Console aendert sich regelmaessig - bei
groesseren Differenzen zur offiziellen Doku gilt diese. Diese Datei
beschreibt **konkret** den Weg vom lokalen Build zum oeffentlichen
Release im Google Play Store.

Die App "ZunaroDo" baut mit Buildozer/python-for-android auf
einem KivyMD-Stack ([MOBILE.md](MOBILE.md)). Die Beispiele unten
beziehen sich auf dieses Setup; wer mit Android Studio / Gradle
arbeitet, findet die Aequivalente in Abschnitt C.

---

## Inhalt

1. [Voraussetzungen](#1-voraussetzungen)
2. [Technische Vorbereitung](#2-technische-vorbereitung)
3. [Recht und Datenschutz](#3-recht-und-datenschutz)
4. [Store-Listing](#4-store-listing)
5. [Play Console einrichten](#5-play-console-einrichten)
6. [Testphase](#6-testphase)
7. [Produktionsfreigabe](#7-produktionsfreigabe)
8. [Nach der Veroeffentlichung](#8-nach-der-veroeffentlichung)

**Liefer-Checklisten:**

- [A. Vollstaendige Checkliste](#a-vollstaendige-checkliste)
- [B. Chronologischer Ablaufplan](#b-chronologischer-ablaufplan)
- [C. Technische Release-Checkliste (Buildozer / Android Studio)](#c-technische-release-checkliste-buildozer--android-studio)
- [D. Play-Console-Checkliste](#d-play-console-checkliste)
- [E. Datenschutz- und Richtlinien-Checkliste](#e-datenschutz--und-richtlinien-checkliste)
- [F. Teststrategie vor Veroeffentlichung](#f-teststrategie-vor-veroeffentlichung)
- [G. Typische Ablehnungsgruende und Vermeidung](#g-typische-ablehnungsgruende-und-vermeidung)
- [H. Finale Go-Live-Checkliste](#h-finale-go-live-checkliste)

---

## 1. Voraussetzungen

### 1.1 Google Play Developer Account

- **Einmalige Gebuehr:** 25 USD (nicht-rueckerstattbar) ueber
  <https://play.google.com/console/signup>.
- Account-Typ entscheidet sich beim Anlegen - **nicht** spaeter
  aenderbar ohne Daten-/App-Migration.

### 1.2 Persoenliches Konto vs. Organisationskonto

| Aspekt | Persoenlich | Organisation |
| --- | --- | --- |
| Wer veroeffentlicht | Einzelperson, eigener Name | Firma, Verein, Behoerde |
| Verifikation | Ausweis (Reisepass/Personalausweis) | D-U-N-S-Nummer + Firmen-Dokumente |
| Adresse oeffentlich | ja (Privatadresse oder Postfach) | Firmenadresse |
| Closed-Testing-Pflicht (neue Accounts) | **ja, 12 Tester / 14 Tage** | nein |
| Steuerlich | Privatperson, ggf. Kleinunternehmer | je nach Rechtsform |

**Empfehlung:** Falls du ein Gewerbe / eine GmbH / einen Verein hast,
nutze ein Organisationskonto. Es ist seriöser, vermeidet die
Privatadresse-Veroeffentlichung und entgeht der 12-Tester-Huerde.

### 1.3 Identitaetspruefung

**Privatperson:**

- Pass oder Personalausweis hochladen
- Adressnachweis (z.B. Stromrechnung, nicht aelter als 1 Jahr)
- Vorname/Nachname muessen exakt dem Ausweis entsprechen
- Bearbeitungsdauer typischerweise 2-4 Tage

**Organisation:**

- D-U-N-S-Nummer (kostenlos bei Dun & Bradstreet beantragen,
  Dauer 5-30 Tage)
- Eintragungsnachweis (Handelsregisterauszug)
- Adressnachweis
- Verifikations-Mail kommt typischerweise binnen 1-3 Tagen

### 1.4 Zahlungsprofil

Auch fuer eine **kostenlose** App noetig, weil das Konto sonst nach
Identitaetspruefung in einen halb-blockierten Zustand kommt.

- Adressdaten (muessen mit Identitaet uebereinstimmen)
- Mehrwertsteuer-Identifikationsnummer (USt.-IdNr.) wenn Unternehmer
- IBAN/BIC fuer Auszahlungen (bei kostenpflichtigen Apps)

### 1.5 App-Name und Paketname

| Feld | Beispiel | Hinweis |
| --- | --- | --- |
| App-Titel (Store-Listing) | ZunaroDo | bis 30 Zeichen, **nach Release nicht aenderbar** |
| Paketname / Application ID | `de.alltagshelfer.alltagshelfer` | **nie wieder aenderbar nach erstem Upload** - sehr sorgfaeltig waehlen! |
| Reverse-Domain | `<tld>.<organisation>.<app>` | eigene Domain als Praefix nutzen |

**Falle:** Wer `com.example.alltagshelfer` hochlaedt und es spaeter auf
seine echte Domain umstellen will, muss eine komplett neue App anlegen
und verliert alle Bewertungen/Downloads.

### 1.6 Datenschutzerklaerung

- **Pflicht** seit 2022 fuer **alle** Apps, auch wenn die App keine
  Daten erhebt.
- Muss als oeffentlich zugaengliche URL hinterlegt werden (Vorlage in
  [legal/DATENSCHUTZ.md](legal/DATENSCHUTZ.md)).
- Empfehlung: eigene Domain mit `/datenschutz`-Pfad.
- Inhaltlich muss konsistent sein mit dem **Data-Safety-Formular** im
  Play Store - Diskrepanzen sind ein haeufiger Ablehnungsgrund (siehe G).

### 1.7 Support-E-Mail

- Wird im Store-Listing angezeigt.
- Privatpersonen koennen oft kein Postfach nutzen - ggf. eigene
  Domain einrichten (`support@deine-domain.de`).
- Muss aktiv geprueft werden - Google testet das gelegentlich.

### 1.8 Impressum / Anbieterangaben

- Bei kostenpflichtigen Apps **immer** Pflicht.
- Bei kostenlosen Apps mit deutschem Marktbezug (deutsche Beschreibung,
  deutsche Inhalte) ebenfalls Pflicht nach TMG / DDG.
- Vorlage in [legal/IMPRESSUM.md](legal/IMPRESSUM.md) - vor
  Veroeffentlichung anwaltlich pruefen lassen.
- Verlinkung sowohl im Store-Listing (Support-URL) als auch in der App
  selbst (Settings -> Impressum).

---

## 2. Technische Vorbereitung

### 2.1 Stabile Release-Version

- Aktuelles `main` muss durchlaufen
- Volle Test-Suite gruen
- Keine `TODO: vor Release fixen`-Marker offen
- CHANGELOG-Eintrag fuer die Version vorhanden

### 2.2 Android App Bundle (.aab)

- **Pflichtformat** seit August 2021 fuer neue Apps.
- Buildozer-Beispiel: `buildozer android release` (mit
  `android.release_artifact = aab` in `buildozer.spec`)
- Android-Studio: Build -> Generate Signed Bundle / APK -> Android
  App Bundle

### 2.3 Release-Signing / Play App Signing

Zwei Schluessel im Spiel:

1. **Upload-Key:** dein Key, mit dem du das AAB signierst.
2. **App-Signing-Key:** Googles Key, mit dem die fertigen APKs an die
   Geraete ausgeliefert werden.

**Play App Signing aktivieren** - Google haelt den App-Signing-Key
sicher, du brauchst nur den Upload-Key zu pflegen. Falls dieser
verloren geht, kannst du ihn ueber den Play Console-Support resetten.

Buildozer:

```ini
# buildozer.spec
[app]
android.release_artifact = aab

[buildozer]
android.keystore = ~/.keystores/alltagshelfer-upload.jks
android.keyalias = upload
# Passwoerter NIE committen - per Env-Var setzen:
#   export P4A_RELEASE_KEYSTORE_PASSWD=...
#   export P4A_RELEASE_KEYALIAS_PASSWD=...
```

Keystore erzeugen (einmalig):

```bash
keytool -genkey -v -keystore alltagshelfer-upload.jks \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -alias upload
```

**Keystore SOFORT sichern** - verlieren bedeutet, dass du kein Update
mehr ausspielen kannst (bei Play App Signing kann Google resetten;
ohne App Signing ist die App tot).

### 2.4 Versionierung

| Feld | Bedeutung | Beispiel |
| --- | --- | --- |
| `versionCode` | strikt monoton steigender Integer | 100, 101, 102 |
| `versionName` | menschenlesbare Version | 1.0.0, 1.0.1 |

Jeder Upload zu Google Play muss einen **groesseren** `versionCode**
haben als der vorherige - sonst Reject.

Buildozer:

```ini
[app]
version = 0.10.0
# versionCode wird aus dem Datum berechnet, wenn nicht gesetzt:
android.numeric_version = 100100   # 1.00.100 - eigene Konvention
```

Convention: `Major*10000 + Minor*100 + Patch`, also `1.10.2 -> 11002`.

### 2.5 Target SDK / API-Level

**Stand 2026:** Neue Apps und Updates muessen **Android 15 (API 35)**
oder hoeher targeten (mit Ausnahmen fuer Wear OS, Android TV,
Automotive - dort gelten je nach Kategorie eigene Min-Levels).

Buildozer:

```ini
[app]
android.api = 35
android.minapi = 24            # Android 7.0 als Minimum
android.ndk = 27c
```

Android Studio (`app/build.gradle`):

```gradle
android {
    compileSdk 35
    defaultConfig {
        targetSdk 35
        minSdk 24
    }
}
```

**Aktuelle Fristen** (siehe Google fuer das jeweils gueltige Datum):

- Neue Apps: bis 31.08.2025 mussten auf API 35 targeten
- Updates bestehender Apps: bis 01.11.2025 ebenfalls
- Nach Ablauf werden nicht-targetende Apps zurueckgehalten

Bei einer neuen App heute geht's also nicht ohne API 35.

### 2.6 Berechtigungen

- `AndroidManifest.xml` minimal halten - nur was wirklich gebraucht wird.
- Buildozer: `android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE`
- **Sensible Berechtigungen** (Standort, Kamera, Mikrofon, Kontakte,
  Telefonbuch, Hintergrund-Standort, alle "...Files" auf API 33+,
  Notifications) brauchen:
  - Runtime-Permission-Dialog im Code
  - Begruendung in der Privacy Policy
  - Eintrag im Data-Safety-Formular
- **MANAGE_EXTERNAL_STORAGE** (R/W auf alle Dateien) ist
  rechtfertigungspflichtig - nur erlaubt bei wenigen Use-Cases
  (Datei-Manager, Backup-Apps). Sonst -> Reject.

Pruefe `_alle_` Permissions vor Submit:

```bash
buildozer android debug
unzip -p .buildozer/.../app.apk AndroidManifest.xml | aapt2 dump xmltree --file -
```

Oder mit `apkanalyzer manifest permissions <app.aab>`.

### 2.7 Absturzfreiheit und Performance

- **Cold Start unter 5 Sekunden** auf Mittelklasse-Geraet.
- **Keine ANRs** (Application Not Responding) im Test - schwere Arbeit
  in Worker-Threads, nicht im UI-Thread.
- **Crash-Frei-Rate > 99 %** im internen/Closed-Test bevor Production.
- Speicherverbrauch < 200 MB auf 2-GB-Geraet.

### 2.8 Geraetekompatibilitaet

- Mindestens 3 Geraete testen:
  - **Klein:** 720x1280, API 24 (Android 7) - aelteste Minimal-Variante
  - **Mittel:** 1080x1920, API 33
  - **Gross:** Tablet 1600x2560 oder Foldable, API 35
- Hochformat **und** Querformat (sofern unterstuetzt)
- DPI: ldpi, mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi - jeweils einmal pruefen
- Dark Mode (Material Day/Night) muss funktionieren

### 2.9 Lokales Testing

- **Emulatoren:** Android Studio AVD Manager, mindestens drei
  unterschiedliche API/Form-Factor-Kombinationen.
- **Echte Geraete:** mindestens eines, idealerweise eines pro
  Hauptzielgruppe (Senior-Familie -> einfaches Geraet; Power-User ->
  Pixel/Samsung).
- **Firebase Test Lab** (kostenpflichtig, aber spart Hardware-Park):
  laesst die App auf einer Matrix echter Geraete in der Cloud laufen.

---

## 3. Recht und Datenschutz

### 3.1 Datenschutzerklaerung

- Vorlage: [legal/DATENSCHUTZ.md](legal/DATENSCHUTZ.md)
- Inhaltliche Pflicht-Bestandteile (DSGVO Art. 13, Google Play):
  - Verantwortlicher (Anbieter mit Adresse)
  - welche personenbezogenen Daten erhoben werden
  - Zweck der Verarbeitung
  - Rechtsgrundlage
  - Speicherdauer
  - Drittlandtransfer (z.B. wenn Google-Dienste genutzt werden)
  - Rechte der Nutzer (Auskunft, Loeschung, Widerspruch, ...)
  - Beschwerderecht bei der Aufsichtsbehoerde
- **Hosting:** muss auf einer **anderen** URL als der Store-Listing
  liegen (eigene Website oder GitHub Pages).
- **Konsistenz** mit Data-Safety-Formular ist Pflicht.

### 3.2 Drittanbieter-SDKs auditieren

Pruefe jeden Drittanbieter:

| SDK | Was sammelt es | Datentransfer | Privacy-Erklaerung |
| --- | --- | --- | --- |
| Firebase Analytics | Geraete-IDs, Events | USA (Google) | ja |
| Firebase Crashlytics | Stack-Traces, Geraete-Info | USA | ja |
| Google AdMob | Werbe-IDs, IP, Geraete-Info | USA | ja |
| Stripe SDK | Zahlungsdaten | USA (Stripe) | ja |
| Paddle / Lemon Squeezy | Zahlungsdaten | USA/UK | ja |
| KivyMD / python-for-android | nichts (lokal) | nein | nein |

**ZunaroDo aktuell:** nutzt nur python-for-android,
Gemini (optional, vom Nutzer aktivierbar) und SMTP/IMAP gegen
Nutzer-eigene Server. **Keine** Drittanbieter-Telemetrie.

### 3.3 Data-Safety-Formular

In der Play Console: App-Inhalte -> Datensicherheit. Pflichtangaben:

- Welche Datentypen werden gesammelt? (Standort, persoenliche Infos,
  Finanzdaten, App-Aktivitaet, ...)
- Werden Daten **gesammelt** oder nur **lokal verarbeitet**?
  - "gesammelt" = an externe Server uebertragen
  - "verarbeitet" = nur auf dem Geraet
- Werden Daten an Dritte weitergegeben?
- Sind Daten verschluesselt waehrend Uebertragung?
- Kann der Nutzer die Loeschung seiner Daten anfordern?
- Hat die App ein etabliertes Sicherheits-Audit?

**Fuer ZunaroDo:** Sehr stark "lokal verarbeitet, nicht
gesammelt" - das ist eines unserer Verkaufsargumente. Sauber so
deklarieren, Privacy-Story passt 1:1.

### 3.4 Verschluesselung, Loeschung, Nutzerrechte

- **At rest:** SQLCipher optional ueber `ALLTAGSHELFER_DB_KEY`
  (siehe README).
- **In transit:** falls Sync verwendet wird, TLS verpflichtend.
- **Loeschung:** App-Deinstallation loescht alle lokalen Daten;
  CSV-Export ueber `__main__.py --export` als Daten-Portabilitaet.

### 3.5 Altersfreigabe / Inhaltsbewertung (IARC)

Play Console -> App-Inhalte -> Inhaltsbewertung. Fragenkatalog
durchklicken (Gewalt, Sex, Drogen, ...). Fuer ZunaroDo:
typisch USK 0 / PEGI 3 / ESRB Everyone.

### 3.6 Werbung, In-App-Kaeufe, Abos

- **Werbung enthalten?** Bei ZunaroDo: nein -> "Diese App enthaelt
  keine Werbung".
- **In-App-Kaeufe?** Bei ZunaroDo aktuell: nein (Lizenz wird ueber
  externes Paddle/Lemon Squeezy ausgestellt - das ist KEIN IAP im
  Play-Sinn). Pruefe aber Google's externe-Zahlung-Politik (DMA-bedingt
  in EU jetzt erlaubt, sonst eingeschraenkt).
- **Abos:** wenn echte Play-Abos genutzt werden, muessen sie ueber
  Google Play Billing laufen (sonst Reject ausserhalb DMA-Raum).

### 3.7 Familien-/Kindgerichtete Inhalte

- Wenn Zielgruppe Kinder unter 13: Compliance mit "Designed for
  Families"-Programm (zusaetzliche Pruefung, COPPA-konform).
- ZunaroDo: Zielgruppe Erwachsene -> entsprechend deklarieren.

---

## 4. Store-Listing

### 4.1 Pflicht-Felder

| Feld | Limit | Best Practice |
| --- | --- | --- |
| App-Titel | 30 Zeichen | "ZunaroDo - Familien-Organizer" |
| Kurzbeschreibung | 80 Zeichen | "Vertraege, Termine, Familie - lokal, privat, ohne Werbung." |
| Vollstaendige Beschreibung | 4000 Zeichen | Fliesstext, kein Keyword-Spam |
| App-Icon | 512x512 PNG, kein Alpha | mit dem In-App-Icon konsistent |
| Feature Graphic | 1024x500 JPG/PNG | das erste, was Nutzer im Store sehen |
| Screenshots Telefon | 2-8, min 320 px Kante | echte App-Screens, keine Mockups |
| Screenshots Tablet | optional, empfohlen | 7'' und 10'' |
| Promo-Video | optional, YouTube-Link | 30 Sek max |

### 4.2 Beispiel-Beschreibung (Auszug)

```text
ZunaroDo haelt Vertraege, Termine, Familie und Finanzen sortiert -
komplett lokal auf deinem Geraet, ohne Werbung, ohne Tracking.

Was du erledigst:
* Vertraege verwalten, Kuendigungsfristen automatisch errechnen,
  Kuendigungsschreiben als PDF erzeugen
* Familien-Aufgaben mit Rotation
* Einkaufsliste, Termine, Geburtstage
* Optional: KI-Assistent ueber Google Gemini (du behaeltst die Kontrolle)

Datenschutz ist eingebaut:
* Alle Daten bleiben auf dem Geraet
* Optional verschluesselt mit SQLCipher
* Keine Telemetrie, kein Tracking
* Open Source: <https://github.com/Toto241/ZunaroDo>

Preise:
* Free: 1 Person, 2 Module - dauerhaft kostenlos
* Pro: 6,99 EUR/Monat oder 67,10 EUR/Jahr fuer 2 Personen
* Familie: 12,99 EUR/Monat fuer bis zu 5 Personen
* 14 Tage Trial inklusive

Fragen? support@deine-domain.de
```

### 4.3 ASO (App Store Optimization)

- **Keyword im Titel:** ein primaeres Keyword neben dem App-Namen
  ("ZunaroDo - Familien-Organizer" - "Familien-Organizer" ist
  ein gesuchter Begriff).
- **Kurzbeschreibung:** muss Wert versprechen, weil das Conversion-
  treiber ist.
- **Vollstaendige Beschreibung:** Keywords NATUERLICH einbauen
  (3-5 mal das Haupt-Keyword, 1-2 mal Nebenkeywords).
- **KEIN Keyword-Stuffing** - Google laesst Listings dafuer ablehnen.

### 4.4 Lokalisierungen

- Standardsprache: Deutsch (de-DE)
- Empfohlene zusaetzliche Sprachen (sofern App lokalisiert ist):
  - en-US (groesster App-Markt, ~$1 zusaetzliche Reichweite ja)
  - de-AT, de-CH (kleine Aufwand, gleiche Texte)
- Pro Sprache: eigenes Set Titel/Beschreibung/Screenshots

---

## 5. Play Console einrichten

### 5.1 Neue App anlegen

Play Console -> "App erstellen". Du wirst nach folgenden Angaben
gefragt - alle **nicht aenderbar** ausser den Beschreibungstexten:

- **App-Name** (max 30 Zeichen)
- **Standardsprache** (z.B. Deutsch (de-DE))
- **App oder Spiel** (App)
- **Kostenlos oder kostenpflichtig** (kostenlos - Lizenz wird
  extern verkauft, App-Download ist gratis)

### 5.2 Erklaerungen ("Deklarationen")

Mehrere Pflicht-Pflicht-Pflicht-Felder, bevor Production-Release moeglich ist:

| Erklaerung | Antwort fuer ZunaroDo |
| --- | --- |
| App-Zugriff | "Komplett zugaenglich - kein Login noetig" (alternativ Testkonto angeben, falls Login Pflicht ist) |
| Anzeigen | "Nein, meine App enthaelt keine Werbung" |
| Inhaltsbewertung | IARC-Fragebogen ausfuellen -> USK 0 |
| Zielgruppe und Inhalte | Alterskategorie: 18+ (Erwachsene); kindgerichtet: nein |
| Datensicherheit | siehe Abschnitt 3.3 |
| Datenverkauf an Dritte | nein |
| Staatliche App? | nein |
| Finanz-/Banken-/Krypto-App? | nein - nur Verwaltungs-App |
| COVID-19? | nein |
| News? | nein |

### 5.3 Hauptseite "App-Inhalte"

Klicke jede Sektion an, bis sie **gruen** ist. Erst dann darfst du
in Produktion releasen.

### 5.4 Laender / Regionen

- "Verfuegbar in: alle Laender" oder gezielt auswaehlen (DACH +
  EU + ggf. weltweit).
- Sanktionierte Laender (Iran, Syrien, Nordkorea, Krim) automatisch
  ausgeschlossen.

---

## 6. Testphase

### 6.1 Interner Test

- Schnellster Track, bis zu 100 Tester, keine Review.
- Tester werden ueber E-Mail-Adressen oder eine Google-Group eingeladen.
- Ideal fuer den eigenen Roundtrip + kleines Vertrauten-Team.

### 6.2 Geschlossener Test (Closed Testing)

- Bis zu 1000 Tester pro Liste, mehrere Listen moeglich.
- Tester muessen **explizit opt-in** klicken ueber einen Opt-In-Link.
- **WICHTIG bei neuen persoenlichen Accounts:** Google verlangt fuer
  Production-Zugriff:
  - mindestens **12 opt-in Tester** (Mailadressen, die den Opt-In
    geklickt haben)
  - mindestens **14 zusammenhaengende Tage** in dem Track
  - erst danach kann Production-Zugriff beantragt werden

  Diese Huerde existiert seit Nov 2023 fuer neue persoenliche Konten
  und ist bei Organisationskonten i.d.R. nicht aktiv.

### 6.3 Offener Test (Open Testing / Beta)

- Jeder kann ueber den Store-Link beitreten.
- Beta-Bewertungen fliessen NICHT in den oeffentlichen Score ein.
- Gut, um vor Production echtes Nutzer-Feedback zu sammeln.

### 6.4 Build hochladen

```bash
# Buildozer
buildozer android release   # erzeugt bin/<app>-<ver>-release.aab

# Hochladen ueber Play Console:
Production / Testing -> "Neuer Release" -> Bundle waehlen
```

Bei jedem Upload:

- `versionCode` muss hoeher sein als der letzte
- Release Notes pro unterstuetzter Sprache (max 500 Zeichen)
  - Beispiel: "Pricing-Modell + Pro-Lizenz-Aktivierung im Settings-Tab"

### 6.5 Tester verwalten

- E-Mail-Listen pflegen ueber "Testermanager"
- Bei Closed Testing: Opt-In-Link in der Mail mitschicken
- Feedback ueber Play-Console-Direktnachrichten + Bug-Reports

---

## 7. Produktionsfreigabe

### 7.1 Vorbereitung

- [ ] Alle "App-Inhalte"-Sektionen gruen
- [ ] Closed-Testing-Phase erfuellt (12 Tester / 14 Tage bei
      persoenlichem Konto)
- [ ] Mindestens ein Closed-Testing-Release ist publiziert (auch wenn
      identisch mit Production-Release)
- [ ] Production-Zugriff beantragt und genehmigt (nur fuer neue
      persoenliche Konten)

### 7.2 Release erstellen

- Production -> "Neuer Release"
- AAB hochladen
- Release Notes eintragen (DE als Standardsprache)
- Pruefung Pre-Launch-Reports - automatische Crawl-Tests auf
  echten Geraeten

### 7.3 Pre-Launch-Report

Google laeuft die App automatisch auf einer Matrix Test-Geraete:

- Crashes
- Performance-Probleme
- Sicherheits-Issues (z.B. Klartext-HTTP-Calls)
- Barrierefreiheits-Probleme

Vor Production-Release durchgehen und Issues fixen.

### 7.4 Review-Prozess

- Einreichung: Klick auf "Release zur Pruefung freigeben"
- Erste App-Review dauert typischerweise **3-7 Tage** (kann bis 14
  Tage sein bei sensiblen Apps)
- Nach erstem Release: Updates oft binnen Stunden, manchmal Minuten

### 7.5 Bei Ablehnung

- E-Mail mit konkretem Ablehnungsgrund kommt von Google
- Im Play Console -> Richtlinien-Center steht der detaillierte Befund
- **Nicht panisch werden** - meist sind die Fixes klein
- Liste typischer Gruende: siehe Abschnitt G
- Nach Fix: neuer Release-Upload mit hoeherem versionCode, dann
  erneut einreichen

---

## 8. Nach der Veroeffentlichung

### 8.1 Gestaffelter Rollout

Empfohlen: **5 % -> 20 % -> 50 % -> 100 %** ueber 3-7 Tage.

- Frueh-Adopter bekommen den Release, Bugs koennen gefangen werden
  bevor 100 % betroffen sind
- Rollback ist moeglich: niedrigere Prozentzahl setzen oder
  vorheriger Release zurueck

### 8.2 Monitoring

- **Crashes:** Play Console -> Statistiken -> ANRs und Abstuerze
- **Nutzerbewertungen:** Antworten - auch auf negative - innerhalb 24h
  ist Best Practice
- **Performance:** Cold-Start-Zeit, Memory, Battery
- **Vitals-Score:** Play priorisiert Apps mit gutem Vitals-Score in den
  Charts

### 8.3 Datenschutz- und Richtlinien-Anpassungen

- Google aendert Richtlinien quartalsweise - die "Was ist neu"-Sektion
  abonnieren
- Bei Aenderung: ggf. Data-Safety-Formular nachpflegen
- Neue Pflicht-Disclaimers nicht ignorieren - sonst App-Sperrung

### 8.4 Updates

- Mindestens **alle 6 Monate** ein Update releasen - sonst gilt die
  App als "abandoned" und faellt im Ranking
- Updates sollten echte Verbesserungen enthalten, keine Pseudo-Updates
- Versionierung disziplinieren - jede Production-Version bekommt einen
  Git-Tag (siehe [DEVELOPING.md](DEVELOPING.md))

### 8.5 Backup-Strategie

| Was | Wo | Wie oft |
| --- | --- | --- |
| Upload-Keystore | Offline-Datentraeger + Cloud (verschluesselt) | nach jeder Aenderung (selten) |
| Source-Code | Git-Remote (GitHub) + zweites Remote (GitLab/eigener Server) | bei jedem Push |
| Release-AAB | Cloud-Storage, mind. letzte 5 Releases | nach jedem Release |
| Play-Console-Backup | Screenshot von Store-Listing + Export der Config | bei jeder groesseren Aenderung |

---

# A. Vollstaendige Checkliste

## Voraussetzungen

- [ ] Google Play Developer Account angelegt (25 USD bezahlt)
- [ ] Account-Typ entschieden (Persoenlich vs. Organisation)
- [ ] Identitaetspruefung abgeschlossen (mit gueltigem Ausweis)
- [ ] Zahlungsprofil angelegt (mit Bankverbindung, USt.-IdNr.)
- [ ] App-Name finalisiert (max 30 Zeichen, im Store eindeutig)
- [ ] Paketname (Application ID) **endgueltig** entschieden
- [ ] Datenschutzerklaerung als oeffentliche URL gehostet
- [ ] Support-E-Mail-Adresse aktiv und beantwortet
- [ ] Impressum gehostet (eigene URL)

## Technik

- [ ] Aktueller `main`-Stand stabil und getestet
- [ ] AAB statt APK produziert (`buildozer android release`)
- [ ] Upload-Keystore erzeugt UND gesichert
- [ ] Play App Signing aktiviert
- [ ] `versionCode` monoton steigend, `versionName` semver
- [ ] `targetSdk 35` (Android 15)
- [ ] `minSdk 24` (Android 7) oder hoeher
- [ ] Berechtigungen auf Notwendiges reduziert
- [ ] Sensible Permissions in Privacy Policy + Data Safety dokumentiert
- [ ] App testet auf min. 3 Geraeten / Emulatoren
- [ ] Cold-Start-Zeit < 5 Sekunden
- [ ] Crash-Free-Rate > 99 % in Closed Testing

## Recht und Datenschutz

- [ ] Datenschutzerklaerung deckt alle erhobenen Datentypen ab
- [ ] Drittanbieter-SDKs aufgelistet
- [ ] Data-Safety-Formular ausgefuellt
- [ ] Inhaltsbewertung (IARC) ausgefuellt
- [ ] Zielgruppen-Erklaerung ausgefuellt
- [ ] Werbung-Erklaerung ausgefuellt
- [ ] Falls Kinder-Zielgruppe: COPPA / Designed-for-Families
- [ ] Falls Zahlungen: AGB + Widerrufsbelehrung verlinkt
- [ ] Falls externe Zahlungen: DMA-konform deklariert

## Store-Listing

- [ ] App-Titel 30 Zeichen
- [ ] Kurzbeschreibung 80 Zeichen
- [ ] Vollstaendige Beschreibung bis 4000 Zeichen
- [ ] App-Icon 512x512 ohne Alpha
- [ ] Feature Graphic 1024x500
- [ ] 4-8 Screenshots Smartphone (echte App-Screens)
- [ ] Tablet-Screenshots (sofern Tablet supported)
- [ ] Promo-Video (optional)
- [ ] App-Kategorie gewaehlt
- [ ] Kontakt-Mail im Listing

## Play Console

- [ ] Neue App angelegt
- [ ] Standardsprache: de-DE
- [ ] Frei vs. Kostenpflichtig (gewaehlt)
- [ ] Laender ausgewaehlt
- [ ] Alle "App-Inhalte"-Sektionen gruen

## Testphase

- [ ] Interner Test mit eigenem Team
- [ ] Closed Test mit min. 12 opt-in Testern (bei neuem Konto)
- [ ] Closed Test laeuft min. 14 Tage
- [ ] Pre-Launch-Report ohne Critical-Issues
- [ ] Production-Zugriff beantragt (bei neuem Konto)

## Production

- [ ] Production-AAB hochgeladen
- [ ] Release Notes auf Deutsch (+ Englisch)
- [ ] Rollout-Strategie definiert (gestaffelt empfohlen)
- [ ] Zur Pruefung eingereicht
- [ ] Pruefung bestanden

## Post-Release

- [ ] Crash-Monitoring aktiv (Console-Dashboard)
- [ ] Bewertungen werden beantwortet
- [ ] Keystore + Source-Code + AAB extern gesichert
- [ ] Update-Plan fuer naechste 6 Monate

---

# B. Chronologischer Ablaufplan

## Phase 0 - Vorbereitung (Woche -8 bis -4)

| Tag | Aufgabe |
| --- | --- |
| -56 | Play Developer Account anlegen, Identitaetspruefung starten |
| -55 | D-U-N-S beantragen (bei Organisation, dauert bis 30 Tage) |
| -50 | Paketname final festlegen, eigene Domain reservieren |
| -45 | Datenschutzerklaerung schreiben + anwaltlich pruefen lassen |
| -40 | Impressum + AGB + Widerrufsbelehrung anwaltlich pruefen |
| -35 | Hosting fuer Privacy/Impressum/AGB einrichten |
| -30 | Support-Mail-Adresse einrichten |

## Phase 1 - Technik (Woche -4 bis -2)

| Tag | Aufgabe |
| --- | --- |
| -28 | targetSdk auf 35 hochziehen, Tests durchlaufen lassen |
| -26 | Permissions audit, alle nicht-noetigen entfernen |
| -24 | Upload-Keystore generieren, sicher ablegen |
| -22 | Erstes Release-AAB bauen, signieren |
| -20 | Eigene Tests auf 3 Geraeten |
| -18 | Internes Testing in Play Console aktivieren, Build hochladen |

## Phase 2 - Closed Testing (Woche -2 bis 0)

| Tag | Aufgabe |
| --- | --- |
| -14 | Closed Test starten, mind. 12 Tester einladen |
| -14 bis 0 | Bug-Reports sammeln, fixen, neue Builds raushauen |
| -10 | Store-Listing vorbereiten (Texte, Screenshots) |
| -7 | Data-Safety-Formular ausfuellen |
| -5 | Inhaltsbewertung ausfuellen |
| -3 | Pre-Launch-Report pruefen und Critical-Issues fixen |
| -1 | Final-Build hochladen |

## Phase 3 - Production

| Tag | Aufgabe |
| --- | --- |
| 0 | Production-Zugriff beantragen (falls neues Konto) |
| 0+1 | Release zur Pruefung einreichen |
| +3 bis +7 | Auf Review warten, ggf. Nachfragen beantworten |
| +Tag X | App live - gestaffelter Rollout startet bei 5 % |
| +X+1 | Crash-Rate pruefen - 5 % -> 20 % |
| +X+3 | 20 % -> 50 % |
| +X+7 | 50 % -> 100 % |

## Phase 4 - Betrieb

- Woechentlich: Bewertungen + ANR/Crash-Statistiken
- Monatlich: Pre-Launch-Report fuer neue Builds, Vitals-Check
- Quartalsweise: Richtlinien-Update von Google reviewen
- Halbjaehrlich: mindestens ein Update releasen

---

# C. Technische Release-Checkliste (Buildozer / Android Studio)

## Buildozer (ZunaroDo)

```ini
# buildozer.spec - Schluessel-Felder fuer Release
[app]
title = ZunaroDo
package.name = alltagshelfer
package.domain = de.alltagshelfer
source.dir = mobile
source.include_exts = py,png,jpg,kv,atlas,json,ttf
version = 0.10.0
android.numeric_version = 11000     # 1.10.00 -> 11000

requirements = python3,kivy,kivymd,pillow,...

orientation = portrait
fullscreen = 0

# API-Level
android.api = 35
android.minapi = 24
android.ndk = 27c
android.archs = arm64-v8a,armeabi-v7a

# Permissions (minimal!)
android.permissions = INTERNET

# Release-Artifact: aab statt apk
android.release_artifact = aab

# Play App Signing - Upload-Key
[buildozer]
android.keystore = ~/.keystores/alltagshelfer-upload.jks
android.keyalias = upload
# Passwoerter NIE committen - per Env-Var setzen:
#   export P4A_RELEASE_KEYSTORE_PASSWD=...
#   export P4A_RELEASE_KEYALIAS_PASSWD=...
```

Build-Kommandos:

```bash
# Vor jedem Release: clean, sonst kommen Reste mit
buildozer android clean
buildozer android release

# Output: bin/alltagshelfer-0.10.0-arm64-v8a_armeabi-v7a-release.aab
```

Verifikation des AAB:

```bash
# Manifest pruefen
unzip -p bin/*.aab BundleConfig.pb | head
bundletool dump manifest --bundle bin/*.aab | head -50

# Permissions auflisten
bundletool dump manifest --bundle bin/*.aab \
    --xpath /manifest/uses-permission/@android:name

# Signatur pruefen
jarsigner -verify -verbose -certs bin/*.aab
```

## Android Studio / Gradle

```gradle
// app/build.gradle (Kotlin DSL: app/build.gradle.kts entsprechend)
android {
    namespace 'de.alltagshelfer.alltagshelfer'
    compileSdk 35

    defaultConfig {
        applicationId "de.alltagshelfer.alltagshelfer"
        minSdk 24
        targetSdk 35
        versionCode 11000
        versionName "0.10.0"
    }

    signingConfigs {
        release {
            keyAlias "upload"
            keyPassword System.getenv("KEYSTORE_PASSWORD")
            storeFile file(System.getenv("KEYSTORE_PATH") ?:
                "${System.getenv('HOME')}/.keystores/alltagshelfer-upload.jks")
            storePassword System.getenv("KEYSTORE_PASSWORD")
        }
    }

    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            signingConfig signingConfigs.release
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'),
                          'proguard-rules.pro'
        }
    }
}
```

Build:

```bash
./gradlew clean bundleRelease
# Output: app/build/outputs/bundle/release/app-release.aab
```

## Checkpoints vor Upload

- [ ] `versionCode` ist hoeher als zuletzt veroeffentlichter Wert
- [ ] `targetSdk = 35` (Android 15)
- [ ] `minSdk >= 24`
- [ ] AAB-Groesse vernuenftig (typ. 30-80 MB bei KivyMD-Apps)
- [ ] Keine Test-/Debug-Strings im Code (`TODO`, `XXX`, `DEBUG`)
- [ ] Keine hartcodierten API-Keys oder Passwoerter
- [ ] R8/ProGuard-Regeln pruefen (Android Studio) / `--release` (buildozer)
- [ ] `INTERNET`-Permission nur drin, wenn die App wirklich Netz nutzt
- [ ] Network-Security-Config: Klartext-HTTP blockiert ausser auf
      explizit erlaubten Domains
- [ ] App startet auf Emulator API 24 ohne Crash
- [ ] App startet auf Emulator API 35 ohne Crash

---

# D. Play-Console-Checkliste

Schritt-fuer-Schritt durch das Menue:

## App-Inhalte (alle Punkte gruen)

- [ ] App-Zugriff
- [ ] Anzeigen
- [ ] Inhaltsbewertung
- [ ] Zielgruppe
- [ ] Datensicherheit
- [ ] News-App
- [ ] COVID-19-Tracing
- [ ] Datenverkauf
- [ ] Staatliche App
- [ ] Finanzdienstleistungen
- [ ] Konto-Loeschung-Verlinkung (falls App Konten erlaubt)

## Hauptverkaufsangebote / Listing

- [ ] App-Symbol
- [ ] Feature Graphic
- [ ] Screenshots Telefon (min. 2, empfohlen 4-8)
- [ ] Screenshots 7-Zoll-Tablet (falls Tablet supported)
- [ ] Screenshots 10-Zoll-Tablet
- [ ] Kurzbeschreibung (80 Zeichen)
- [ ] Vollstaendige Beschreibung
- [ ] App-Kategorie
- [ ] Tags
- [ ] Kontaktdaten (E-Mail Pflicht, Telefon/Website optional)
- [ ] Datenschutzerklaerung-URL

## App-Einstellungen

- [ ] App-Verfuegbarkeit (Laender)
- [ ] Preise und Vertrieb
- [ ] In-App-Produkte (falls vorhanden)
- [ ] Translations

## Release-Management

- [ ] Internal Testing -> ein Build hochgeladen
- [ ] Closed Testing -> ein Build hochgeladen + Tester opt-in
- [ ] Pre-Launch-Report ohne Critical Issues
- [ ] Production -> Release vorbereitet, noch nicht eingereicht

## Final

- [ ] Production-Zugriff beantragt (bei neuem persoenlichem Konto)
- [ ] Release ausgerollt mit gestaffeltem Rollout 5 %

---

# E. Datenschutz- und Richtlinien-Checkliste

## Datenschutzerklaerung (eigene URL)

- [ ] Verantwortlicher mit Adresse + Kontakt
- [ ] Auflistung der erhobenen personenbezogenen Daten
- [ ] Zweck jeder Datenerhebung
- [ ] Rechtsgrundlage je Zweck (Art. 6 DSGVO)
- [ ] Speicherdauer pro Datenkategorie
- [ ] Empfaenger / Drittlandtransfer benannt
- [ ] Hinweis auf Auftragsverarbeiter (Google, Paddle, SMTP-Provider)
- [ ] Cookie-/Tracking-Verzicht ausdruecklich erklaert
- [ ] Rechte der Betroffenen (Auskunft, Berichtigung, Loeschung,
      Einschraenkung, Widerspruch, Datenportabilitaet,
      Beschwerderecht)
- [ ] Aktualisierungsdatum
- [ ] **Pruefung durch Anwalt mit DSGVO-Schwerpunkt** (~150-400 EUR)

## Data-Safety-Formular (Play Console)

Pro Datentyp die folgende Trinitaet pruefen:

| Datentyp | gesammelt? | weitergegeben? | optional? |
| --- | --- | --- | --- |
| Standort (genau) | ❌ | - | - |
| Standort (ungefaehr) | ❌ | - | - |
| Persoenliche Infos (Name, Mail) | ❌ lokal | ❌ | n/a |
| Finanzdaten | ❌ lokal | ❌ | n/a |
| Kontakte | ❌ | - | - |
| App-Aktivitaet | ❌ | - | - |
| Crashes | ❌ | - | - |
| Geraete-IDs | ❌ | - | - |

Anpassen je nach tatsaechlicher App.

- [ ] Verschluesselung in Uebertragung: ja, wo immer Uebertragung
      stattfindet
- [ ] Verschluesselung at-rest: optional via SQLCipher
- [ ] Loeschung auf Nutzeranfrage: ja, ueber Deinstallation +
      Mail-Anfrage fuer Lizenz-Daten

## Inhaltsbewertung (IARC)

- [ ] Fragenkatalog ausgefuellt
- [ ] Resultat plausibel (USK 0 / PEGI 3 / ESRB Everyone fuer
      ZunaroDo)

## Zielgruppe und Inhalte

- [ ] Alterskategorie korrekt (18+ fuer ZunaroDo mit
      Finanz-Inhalten)
- [ ] Apellation an Kinder: nein
- [ ] Kein "Designed for Families"-Anspruch

## Werbung

- [ ] Werbung enthalten: nein (ZunaroDo)
- [ ] Bei "ja": Werbe-Netzwerk benannt, AdMob-ID konfiguriert

## In-App-Kaeufe / Abos

- [ ] Vorhanden: nein (Lizenz extern ueber Paddle/Lemon)
- [ ] **Wichtig:** wenn extern, dann **kein Play-Billing-Wording** in
      der App ("In-App-Kauf", "Subscription"), sonst Konflikt mit
      Play-Policies

## DSGVO-Spezifika

- [ ] Datenschutzerklaerung in deutscher Sprache
- [ ] Auftragsverarbeitungs-Vertrag mit Google (Standard-DPA
      automatisch akzeptiert)
- [ ] Auftragsverarbeitungs-Vertrag mit Paddle/Lemon (Self-Service-DPA
      in deren Customer-Area)

---

# F. Teststrategie vor Veroeffentlichung

## Automatisierte Tests (lokal CI)

- [ ] Volle Smoke-Suite: `python -m unittest discover tests`
- [ ] GUI-Smoke: `python -m unittest tests.test_gui_smoke`
- [ ] Mobile-Helpers: `python -m unittest tests.test_mobile_helpers`
- [ ] Performance-Regression: `python -m unittest tests.test_performance`
- [ ] Property-Tests (optional): `python -m unittest tests.test_property`

## Manuelle Tests (Geraete-Matrix)

| Geraet | API | Form | Was testen |
| --- | --- | --- | --- |
| Pixel 4a Emulator | 35 | Phone | Hauptflow Free + Trial + Pro |
| Pixel 7 echt | 34 | Phone | Notifikation, Dark Mode |
| Samsung A22 echt | 33 | Phone | groesseres Display, einfacher Chip |
| Pixel Tablet Emulator | 35 | Tablet | Layout responsive |
| Galaxy Fold Emulator | 33 | Foldable | Aspect-Ratio-Wechsel |
| Generic Phone API 24 | 24 | Phone | Min-API erfuellt |

## Funktionale Test-Szenarien

Kern-Workflows je 1x manuell durchspielen:

- [ ] Frischer Install -> Onboarding (Pricing-Reveal + Demo-Daten)
- [ ] Free-Tier: Vertraege + Familie nutzen, alles andere gesperrt
- [ ] Trial starten: 14-Tage-Counter, voller Zugriff
- [ ] Token-Aktivierung (Test-Token vom Anbieter signiert)
- [ ] Pro: alle Module nutzbar, KI funktioniert (mit eigenem
      GOOGLE_API_KEY)
- [ ] Sync ueber HTTP-Server mit zwei Geraeten
- [ ] SQLCipher-DB mit Passwort
- [ ] OCR auf einem Kassenbon-Foto (falls Tesseract/easyocr installiert)
- [ ] Backup erstellen + restoren
- [ ] CSV-Export + Re-Import
- [ ] Kuendigungsschreiben PDF + Mail-Entwurf

## Pre-Launch-Report-Issues abarbeiten

- [ ] Alle Critical/High Severity Issues geloest
- [ ] Barrierefreiheits-Hinweise (Schriftgroessen, Kontraste)
- [ ] Performance-Hinweise (langer Cold-Start o.ae.)

## Beta-Testing (Closed Track)

- [ ] 12+ opt-in Tester ueber 14+ Tage
- [ ] Feedback gesammelt (Play Console Direktnachrichten, eigenes
      Tracker-Tool wie ein simples Issue-Repo)
- [ ] Mindestens 1 voller Release-Zyklus mit Tester-Feedback

---

# G. Typische Ablehnungsgruende und Vermeidung

## G1. Datenschutz-Mismatch

**Symptom:** "Eure Privacy-Policy und das Data-Safety-Formular sind
inkonsistent."

**Ursache:** Privacy-Policy sagt "wir verwenden Google Analytics",
das Data-Safety-Formular sagt "wir sammeln keine Daten".

**Fix:** Datenschutzerklaerung und Formular synchronisieren. Vor
Submit beide Texte nebeneinander legen.

## G2. Fehlende Datenschutzerklaerung

**Symptom:** "Privacy Policy URL missing or invalid."

**Fix:** URL ueberpruefen - muss `https://` sein, oeffentlich
abrufbar (kein Login-Wall), die Datenschutzerklaerung muss am Anfang
sichtbar sein.

## G3. Sensible Permissions ohne Begruendung

**Symptom:** "Your app declares permission X but does not use it in
its core functionality."

**Beispiele:** `READ_CONTACTS`, `READ_SMS`, `RECORD_AUDIO`,
`ACCESS_BACKGROUND_LOCATION`, `MANAGE_EXTERNAL_STORAGE`.

**Fix:** Permission ENTFERNEN, wenn nicht zwingend gebraucht.
Wenn doch: in Privacy Policy und in In-App-Erklaerung begruenden
und ueber den Permission-Use-Case-Fragebogen in der Play Console
deklarieren.

## G4. Falsche Inhaltsbewertung

**Symptom:** "Your content rating questionnaire is inaccurate."

**Fix:** Fragebogen ehrlich ausfuellen. Wenn die App
Erwachsenen-Themen behandelt (Finanzen, Kontakte, Personalisierung),
nicht "Alle Altersgruppen" angeben.

## G5. Spam / Keyword-Stuffing

**Symptom:** "Your store listing engages in spammy practices."

**Ursache:** Beschreibung wie "Beste App Beste 2026 Familie Termine
Kalender Vertraege Versicherung..." - Keyword-Salat.

**Fix:** Beschreibung in fluessigen Saetzen, Keywords NATUERLICH
einarbeiten.

## G6. Irrefuehrender Titel / Icon

**Symptom:** "Your app's metadata is misleading."

**Beispiel:** Icon zeigt Google-Logo, App heisst "Whatsapp Plus".

**Fix:** Eigene Marken, keine Verwechslung mit grossen Apps.

## G7. Werbe-/IAP-Probleme

**Symptom:** "Your app violates the Payments Policy."

**Ursache:** Digitale Inhalte werden ueber externe Zahlung verkauft
(ausserhalb DMA-Geltungsbereich) ODER Play-Billing-Tokens werden
falsch implementiert.

**Fix:** Fuer EU: DMA-konforme externe Zahlung mit
Alternative-Billing-API. Ausserhalb EU: Play-Billing nutzen oder
digitale Inhalte aus dem App-Scope nehmen.

## G8. Crashs / Hohe ANR-Rate

**Symptom:** Pre-Launch-Report meldet Crashes auf gaengigen Geraeten.

**Fix:** Crashes reproduzieren und fixen. Wenn nicht reproduzierbar:
Test-Lab in Firebase nutzen, dort laeuft die exakte Geraete-Matrix.

## G9. API-Level zu niedrig

**Symptom:** "Apps targeting Android XX or below cannot be published."

**Fix:** `targetSdk 35` setzen.

## G10. Versionscode-Konflikt

**Symptom:** "Upload an APK or App Bundle with a higher version code."

**Fix:** `versionCode` muss strikt hoeher sein als der bisher
hochgeladene Wert - auch wenn dieser nie released wurde.

## G11. Closed-Testing-Pflicht nicht erfuellt

**Symptom:** "You must complete closed testing before requesting
production access."

**Fix:** Mindestens 12 opt-in Tester (Mailadressen, die den Opt-In-
Link geklickt haben) ueber 14 zusammenhaengende Tage in einem Closed
Track. Dann kannst du Production-Zugriff anfragen.

## G12. Privacy-Policy nicht erreichbar

**Symptom:** "The privacy policy URL you provided is not accessible."

**Fix:** Eigene Domain, nicht in `robots.txt` blockieren, kein
Login-Wall, nicht 404, nicht 500. Vor Submit mit `curl -I` testen.

## G13. Nicht-funktionale Mail-Adresse

**Symptom:** "Could not contact developer at provided email."

**Fix:** Eigene Mail-Adresse einrichten und beantworten. Catchall-
Postfaecher manchmal problematisch.

## G14. Verstoss gegen Trademarks

**Symptom:** "Your app uses trademarks without permission."

**Fix:** Keine fremden Marken in Titel/Beschreibung/Icon. Eigene
Marke entwickeln und einheitlich verwenden.

## G15. Sicherheitsluecken

**Symptom:** "Your app has known security vulnerabilities (e.g., SSL
errors, exposed credentials)."

**Fix:**

- Network-Security-Config keine "trustUserCerts" ohne Grund
- Keine API-Keys im Code (auch nicht in resources/strings.xml)
- ProGuard/R8 aktiviert
- `android:allowBackup="false"` ausser bei expliziter Backup-Strategie

---

# H. Finale Go-Live-Checkliste

Eine Stunde vor Submit zur Pruefung:

## Code

- [ ] `git status` ist clean
- [ ] `git tag v0.10.0` setzt
- [ ] CHANGELOG-Eintrag fuer die Version vorhanden
- [ ] AAB ist die finale Version (aus dem getaggten Commit gebaut)
- [ ] AAB ist signiert mit dem **richtigen** Upload-Keystore
- [ ] AAB-Hash notiert (fuer spaetere Verifikation)

## Play Console - Listing

- [ ] App-Symbol ist aktuell
- [ ] Feature Graphic ist aktuell
- [ ] Screenshots zeigen den aktuellen UI-Stand (keine alten Versionen)
- [ ] Beschreibung enthaelt keine "Coming Soon"-Versprechen
- [ ] Kontakt-Mail funktioniert
- [ ] Privacy-Policy-URL ist erreichbar (`curl -I` testen)

## Play Console - App-Inhalte

- [ ] Alle Sektionen gruen
- [ ] Data-Safety-Formular passt zur Privacy-Policy
- [ ] Inhaltsbewertung ist aktuell
- [ ] Zielgruppen-Erklaerung ist aktuell

## Release

- [ ] AAB hochgeladen (Production)
- [ ] Release-Name gesetzt (z.B. `v0.10.0`)
- [ ] Release Notes auf Deutsch UND Englisch
- [ ] Rollout-Prozent gesetzt (empfohlen: 5 %)

## Backup

- [ ] Upload-Keystore in 2 voneinander unabhaengigen Speicherorten
- [ ] Letzte 5 Release-AABs gesichert
- [ ] Privacy-Policy-Backup gesichert (PDF + Markdown)
- [ ] Play-Console-Konfig als Screenshots dokumentiert

## Kommunikations-Vorbereitung

- [ ] Support-Mail vorbereitet auf erhoehtes Volumen
- [ ] FAQ fuer typische Fragen vorbereitet
- [ ] Release-Notes auch auf der eigenen Website / Social Media

## Nach Submit

- [ ] Bestaetigungs-Mail von Google in eigener Inbox
- [ ] Review-Status taeglich pruefen
- [ ] Bei Ablehnung: Sektion G durchgehen, fixen, neu einreichen
- [ ] Bei Annahme: Crash-Monitoring + Bewertungen taeglich pruefen

---

## Weitere Quellen

- Offizielle Play-Console-Doku: <https://support.google.com/googleplay/android-developer>
- Richtlinien-Center: <https://play.google.com/about/developer-content-policy/>
- Pre-Launch-Reports: Play Console -> Release -> Pre-launch reports
- API-Level-Deadlines: <https://support.google.com/googleplay/android-developer/answer/11926878>
- Designed-for-Families: <https://play.google.com/console/about/families/>
- DSGVO + Play-Store: <https://support.google.com/googleplay/android-developer/answer/9888076>

---

Dieser Leitfaden wird per Pull Request aktualisiert, wenn Google
Play-Richtlinien-Updates herausgibt, die uns betreffen. Letzte
Aktualisierung: 2026-05.
