# 04 - Datenschutz, Berechtigungen, SDKs

## 1. Datenschutz-Prinzipien

1. **Datensparsamkeit** - nichts erheben, was nicht gebraucht wird.
2. **Lokal vor Cloud** - die App lebt lokal; Sync und LLM sind opt-in.
3. **Transparenz** - jede externe Datenübertragung ist im UI sichtbar
   (Sync-Status, LLM-Indikator).
4. **Löschbarkeit** - jede Entität ist löschbar (Soft-Delete + Purge,
   bereits umgesetzt in `database.py`).
5. **Portabilität** - Export aller Daten als JSON/CSV per Settings-Menü.
6. **Defaults sicher** - Sync aus, LLM aus, Analytics aus.

## 2. Personenbezogene Daten - vollständige Liste

| Datum | Erhebung | Speicherort | Empfänger | Rechtsgrundlage | Speicherdauer |
| ----- | -------- | ----------- | ---------- | ---------------- | ------------- |
| Familienmitglieder (Name, Geb-Datum, Rolle) | nur lokal | SQLite | keine | Art. 6 (1) b DSGVO (Vertrag) | bis Nutzer löscht |
| Kontakte (Name, Telefon, E-Mail) | nur lokal | SQLite | keine | Art. 6 (1) b DSGVO | bis Nutzer löscht |
| Verträge (Anbieter, Beträge, Daten) | nur lokal | SQLite | keine | Art. 6 (1) b DSGVO | bis Nutzer löscht |
| Ausgaben/Einnahmen | nur lokal | SQLite | keine | Art. 6 (1) b DSGVO | bis Nutzer löscht |
| Termine/Erinnerungen | nur lokal | SQLite | keine | Art. 6 (1) b DSGVO | bis Nutzer löscht |
| Notizen + Anhänge | nur lokal | SQLite + Sandbox-Files | keine | Art. 6 (1) b DSGVO | bis Nutzer löscht |
| Lizenz-Token (E-Mail-bound) | Server-Issuance | SQLite Settings | Anbieter (Issuance), Paddle/Lemon Squeezy (Payment) | Art. 6 (1) b DSGVO | bis Lizenzende + 6 Mon. Aufbewahrung |
| Sync-Logs (Lamport-Clock) | optional | SQLite + Sync-Server | eigener Server | Art. 6 (1) b DSGVO | 90 Tage rolling |
| Gemini-Prompts | opt-in | nicht persistiert | Google LLC (USA) - DPF | Art. 6 (1) a DSGVO (Einwilligung) | Google: bis 18 Mon. |
| Crash-Reports (geplant) | opt-in | Sentry/Crashlytics | Sentry / Google | Art. 6 (1) f DSGVO | 90 Tage |
| Geräte-ID/Werbe-ID | **nicht erhoben** | - | - | - | - |
| Standort | **nicht erhoben** | - | - | - | - |

**Wichtige Konsequenz:** Solange die App keine Crash-Reports und kein
Analytics-SDK enthält, ist sie aus DSGVO-Sicht "still" - im Play-Listing
Data-Safety-Form sind dann nahezu alle Felder mit "Es werden keine
Daten erhoben" beantwortbar.

## 3. Berechtigungsmatrix

| Permission | Aktiv? | Manifest | Runtime-Prompt? | Begründung | Alternative |
| ---------- | ------ | -------- | --------------- | ---------- | ----------- |
| `INTERNET` | ja | `buildozer.spec` | nein | Sync-Server + optional Gemini | - |
| `ACCESS_NETWORK_STATE` | aktuell **nein**, empfohlen | optional ergänzen | nein | Connectivity-Check vor Sync, sonst unnötige Fehlversuche | `requests`-Timeout |
| `POST_NOTIFICATIONS` | optional | bei Termin-Push aktivieren | ja (API 33+) | Termin-Erinnerungen | E-Mail-Versand |
| `CAMERA` | nein | nicht ergänzen | - | OCR wäre Anwendungsfall, aber Photo-Picker reicht | Photo-Picker |
| `READ_MEDIA_IMAGES` | nein | nicht ergänzen | - | Photo-Picker braucht keine Permission | Photo-Picker |
| `VIBRATE` | nein | nicht ergänzen | nein | aktuell ungenutzt | - |
| `WAKE_LOCK` | nein | nicht ergänzen | nein | WorkManager regelt das | - |
| `FOREGROUND_SERVICE` | nein | nur falls Sync-Worker im Vordergrund läuft | nein | aktuell WorkManager-Periodic ohne FG | - |
| `RECEIVE_BOOT_COMPLETED` | nein | nicht ergänzen | nein | WorkManager überlebt Reboot | - |
| `BLUETOOTH_*`, `NFC`, `BIOMETRIC` | nein | nicht ergänzen | - | nicht im Funktionsumfang | - |

### Begründungstexte (im Runtime-Prompt anzuzeigen)

Diese Strings landen in `strings.xml` (Native) bzw.
`mobile/i18n.py` (Kivy) und sind die **einzigen erlaubten Permission-
Rationale-Texte**:

```text
notifications:
  "Damit dich ZunaroDo an Termine und Fristen erinnern kann."
network_state:
  "Damit wir vor einem Sync prüfen können, ob du gerade online bist."
```

## 4. Data Safety Form (Play Console) - Antworten

Vorlage zum Ausfüllen in der Play Console:

```yaml
data_collection:
  collects_data: false                # solange kein Crashlytics/Analytics
  shares_data:    false
  encrypted_in_transit: true          # TLS aktiv
  user_can_request_deletion: true     # In-App-Export+Löschen
  committed_to_play_families_policy: true
  independent_security_review: false  # ehrliche Angabe, sonst Verstoß
data_types: []                        # leer; falls Crashlytics/Sentry aktiv:
                                      # - App activity > Crash logs
                                      # - App info & performance > Diagnostics
purposes:
  account_management: false
  advertising_or_marketing: false
  analytics: false
  app_functionality: true             # Sync-Server-Verbindung
  developer_communications: false
  fraud_prevention: false
  personalization: false
```

**Sobald Crash-Reports/Sentry aktiv werden:**

```yaml
data_collection:
  collects_data: true
data_types:
  - category: "App activity"
    type: "Crash logs"
    collected: true
    shared:    false
    optional:  true                    # Opt-in!
    purposes: ["Analytics", "App functionality"]
  - category: "App info & performance"
    type: "Diagnostics"
    collected: true
    shared:    false
    optional:  true
    purposes: ["Analytics", "App functionality"]
```

## 5. SDK-Inventar

Pflicht: bei jeder Dependency-Änderung diese Tabelle aktualisieren.
Der Checker vergleicht die Liste in `requirements.txt` / `gradle`
gegen diese Tabelle und schlägt bei Drift Alarm.

| SDK / Library | Version | Zweck | Erhobene Daten | Datenfluss | Alternative mit weniger Tracking |
| ------------- | ------- | ----- | --------------- | ---------- | -------------------------------- |
| `kivy` | 2.3.0 | UI-Framework | keine | lokal | n/a (Framework) |
| `kivymd` | 1.2.0 | Material-Widgets | keine | lokal | nativ Compose |
| `certifi` | latest | TLS-CA-Bundle | keine | lokal | OS-Trust-Store |
| `requests` | latest | HTTP-Client | URLs an Zielserver | nur an konfigurierte Hosts | `httpx` |
| `google-generativeai` | optional | Gemini-LLM | Prompt-Text, App-ID | Google LLC | offline LLM (llama.cpp) - bei Bedarf |
| `cryptography` (transitiv) | latest | Krypto-Primitives | keine | lokal | n/a |
| `keyring` | >=24 | OS-Keychain-Zugriff (sichere Geraete-Identitaet) | keine | nur OS-Keychain auf demselben Geraet | File-Fallback fuer Headless |
| `spake2` | >=0.8 | SPAKE2-Handshake (Geraetekopplung) | keine | nur lokal zwischen den koppelnden Geraeten | n/a (Standard-PAKE) |
| `Pillow` (falls genutzt) | latest | Bildverarbeitung | keine | lokal | n/a |
| `APScheduler` | latest | Termin-/Reminder-Scheduler (Desktop) | keine | lokal | nativ `WorkManager` (Android) |
| `customtkinter` | latest | Desktop-UI (Tk) | keine | lokal | nicht auf Android |
| `fpdf2` | latest | PDF-Export (Belege/Reports) | keine | lokal | Android-`PdfDocument` |
| `plyer` | latest | Plattform-API-Brücke (Benachrichtigung, Connectivity) | keine | lokal | nativ Android-SDK |
| **Geplant: Sentry / Crashlytics** | - | Crash-Reports | Crash-Stacktrace, Geräte-Modell, Android-Version | Sentry SaaS / Firebase | self-hosted Sentry, opt-in |

Bei Native-Build zusätzlich:

| SDK | Version | Zweck | Datenfluss |
| --- | ------- | ----- | ---------- |
| AndroidX Compose BOM | latest stable | UI | lokal |
| AndroidX Room | latest stable | DB | lokal |
| AndroidX WorkManager | latest stable | Hintergrund-Worker | lokal |
| OkHttp + Retrofit | latest stable | HTTP | konfig. Hosts |
| kotlinx-serialization | latest | JSON | lokal |
| Hilt | latest | DI | lokal |

## 6. Nutzer-Einwilligungen

Drei Stufen, alle **opt-in**:

1. **App-Funktionalität (default an)** - lokale Datenverarbeitung,
   keine Einwilligung nötig (Vertrag = Nutzung der App).
2. **Sync-Server** - Onboarding-Dialog mit Aufklärung, Häkchen
   "Sync aktivieren". Standard: aus.
3. **LLM-Assistent (Gemini)** - separater Toggle in Settings,
   Aufklärungstext über Datenfluss zu Google. Standard: aus.

Konkrete Texte sind in [legal/DATENSCHUTZ.md](../../legal/DATENSCHUTZ.md)
hinterlegt. In-App-Verlinkung: **Pflicht** im Settings-Screen.

## 7. Tracking-Disclosure

Aktuell: **kein** Tracking, keine Werbung, kein User-ID-Tracking,
keine Werbe-IDs. Damit:

- **Apple-Style Privacy Nutrition Labels**: leer.
- **Google Data Safety Form**: "Es werden keine Daten erhoben".
- **DSGVO TIA (Transfer Impact Assessment)**: nur für Gemini relevant
  (USA, DPF-Status), in [legal/DATENSCHUTZ.md](../../legal/DATENSCHUTZ.md)
  dokumentiert.

Sobald Tracking/Analytics geplant ist, vor dem Code-Merge:

- Update dieses Dokuments
- Update Data Safety Form
- Update Privacy Policy
- Opt-in-Dialog im UI
- TIA bei Drittland-Anbietern

## 8. Datenexport- und Löschfunktion (Pflicht)

Implementierungs-Status:

| Funktion | Status | Ort |
| -------- | ------ | --- |
| Soft-Delete pro Entität | ja | `database.py` |
| Hard-Delete (Purge) | ja | `database.py` |
| Komplett-Export aller Daten | ja (Mobile) | `services/export.py` (`export_all` + `export_all_json`); UI: „Mehr → Daten exportieren“ |
| Komplett-Löschung (Account-Reset) | ja | `services/data_deletion.py` + `Database.wipe_all_data()`; Mobile-UI: "Mehr" → "Alle Daten löschen" ([mobile/screens/more.py](../../mobile/screens/more.py)). Leert alle DB-Tabellen (inkl. VACUUM) + Sandbox-Verzeichnisse (ausgaben/backups/logs/attachments/cache) |
| Lizenz-Widerruf -> Pro-Daten unverändert lokal | ja | DB lokal, Lizenz-Token gibt nur Funktion frei |

**Sprint-Pflicht:** Komplett-Export- und Komplett-Lösch-Button vor dem
ersten Play-Store-Release implementieren (Google verlangt "User can
request that their data is deleted" - Web-Form reicht, aber In-App
ist Best Practice).

## 9. Datenfluss-Analyse

```text
[App lokal] ----lokal---->  SQLite (Sandbox)
   |
   +---> [opt-in: Sync-Server]
   |        TLS, JSON-Diffs, Lamport-Clock
   |        Endpoint: Eigener Container / VPS in EU
   |
   +---> [opt-in: Gemini API]
   |        TLS, Prompt-Strings (vom Nutzer freigegeben)
   |        Endpoint: generativelanguage.googleapis.com (USA, DPF)
   |
   +---> [Zahlung]
            Externe Browser-Weiterleitung zu Paddle / Lemon Squeezy
            App selbst sieht keine Zahlungsdaten
```

Erkenntnisse:

- Lokale Verarbeitung dominiert.
- Drittländer-Transfer **nur** bei explizit aktiviertem Gemini.
- Zahlung läuft **außerhalb** der App (kein PCI-Scope).

## 10. Berechtigungs-/Datenschutz-Audit-Rhythmus

- **Quartal:** Berechtigungsmatrix gegen Manifest vergleichen
  (automatischer Check via `tools/playstore_check.py`).
- **Bei jeder neuen Dependency:** SDK-Inventar erweitern, ggf.
  Data-Safety-Form aktualisieren.
- **Vor jedem Release:** Diff der `requirements.txt`/`gradle` lokal
  reviewen.
- **Jährlich:** Privacy Policy auf Aktualität prüfen.

## 11. Datenschutzauswirkungsabschätzung (DSFA)

Aktuell **nicht erforderlich**:

- Keine sensiblen Daten (Art. 9 DSGVO) verarbeitet.
- Kein Tracking.
- Kein Profiling.

Bei künftigen Features (Gesundheitsdaten, ML-basierte Empfehlungen,
Gesichtserkennung in Beleg-Bildern) -> DSFA gemäß Art. 35 DSGVO
durchführen.
