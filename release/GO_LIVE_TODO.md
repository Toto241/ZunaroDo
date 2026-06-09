# ZunaroDo - Go-Live-TODO (Play Store)

Stand: 2026-06-09. Konsolidierte, abhakbare Liste der **verbleibenden** Schritte
bis zur Produktions-Veroeffentlichung. Code- und Compliance-Stand sind weit;
die offenen Punkte sind ueberwiegend **operativ/extern** (Build auf WSL2,
Play Console, Schluessel, Gerätetests) und koennen nicht im Windows-Repo erledigt
werden.

Legende: [x] erledigt im Repo · [ ] offen (Du/extern)

---

## 0. Bereits im Repo erledigt (diese Sitzung)

- [x] Gebrandetes App-Icon statt einfarbigem Platzhalter
      (`assets/icons/`, `assets/store/icon-512.png`) - reproduzierbar via
      `python -m tools.gen_assets`.
- [x] Adaptive-Icon-Set (Vordergrund/Hintergrund) + Presplash erzeugt.
- [x] Feature-Graphic (1024x500) gebrandet statt Platzhalter
      (`assets/store/feature.png`).
- [x] `buildozer.spec`: Icon/Adaptive-Icon/Presplash verdrahtet, SQLCipher
      (`sqlcipher3`) in `requirements` aktiviert.
- [x] Keystore-Helfer `release/create_upload_keystore.ps1` + `.gitignore`
      um Keystore-/Service-Account-Geheimnisse erweitert.

---

## 1. BLOCKER - vor Produktion zwingend

### 1.1 Android-Build auf WSL2/Linux erzeugen (Basis fuer alles Weitere)
> Buildozer laeuft NICHT nativ unter Windows. Ubuntu 22.04 in WSL2 verwenden.

- [ ] WSL2 + Abhaengigkeiten einrichten (siehe `buildozer.spec` Kommentar Pkt. 2
      und `docs/android/07_CICD.md`).
- [ ] Debug-Build: `buildozer android debug`
- [ ] **SQLCipher verifizieren** (jetzt aktiv): Baut `recipes/sqlcipher3/`?
      Ggf. `version`/`url`/OpenSSL-Pfad anpassen. Auf Geraet pruefen, dass
      `Database.encryption_mode == "sqlcipher"`. Falls der Build daran
      scheitert: `sqlcipher3` temporaer aus `requirements` nehmen (App laeuft
      dann mit Klartext-SQLite) und Recipe nachziehen.
- [ ] **ML-Kit-OCR verifizieren**: Beleg scannen -> `scan_receipt()` liefert
      `engine == "mlkit"` (Modell laedt beim 1. Aufruf nach).
- [ ] **Icon/Adaptive-Icon** auf echtem Launcher pruefen (kein weisser Default).
- [ ] Release-Bundle: `buildozer android release` -> `dist/*.aab`.

### 1.2 Upload-Keystore erstellen & sichern
- [ ] `pwsh ./release/create_upload_keystore.ps1` ausfuehren.
- [ ] Passwoerter im Passwort-Manager sichern (Verlust = App-Linie verloren).
- [ ] `P4A_RELEASE_*`-Env-Vars (lokal) bzw. GitHub-Secrets (CI) setzen.
- [ ] Sicherstellen: `.jks` ist NICHT im Git (ist bereits gitignored).

### 1.3 Play Console - App anlegen
- [ ] Play-Developer-Konto (25 USD einmalig) + Identitaetspruefung
      (2-4 Tage; bei Personenkonten Pflicht).
- [ ] Neue App: Name "ZunaroDo", Standardsprache de-DE, Kategorie PRODUCTIVITY,
      kostenlos (Pro via IAP). Package `de.alltagshelfer.alltagshelfer`
      (NICHT mehr aenderbar nach Release).
- [ ] Data-Safety-Formular gemaess `release/DATA_SAFETY_CONSOLE_ANSWERS.md`
      und `playstore.yml` ausfuellen.
- [ ] Datenschutz-URL eintragen (siehe `playstore.yml` privacy_policy_url) -
      sicherstellen, dass die GitHub-Pages-Seite live ist.
- [ ] IARC-Fragebogen (Content Rating) ausfuellen.

### 1.4 Play Billing scharf schalten (nur wenn Pro/Abos zum Launch verkauft werden)
> Java-Bridge + Python-Wrapper sind fertig; ungetestet auf Geraet.

- [ ] In der Console die drei Abos anlegen - IDs MUESSEN exakt zu
      `DEFAULT_SKUS` in `services/play_billing_android.py` passen:
      `zunarodo_pro_monthly`, `zunarodo_pro_yearly`, `zunarodo_pro_family`.
- [ ] Service-Account anlegen, Berechtigung `purchases.subscriptionsv2.get`,
      JSON-Key herunterladen (gitignored: `**/service-account*.json`).
- [ ] Payment-Server deployen (`tools/payment_server.py`,
      `release/deploy-payment-server.md`), Endpoint `/verify/play` mit
      Service-Account testen.
- [ ] Echten Kaufflow auf Geraet (Lizenz-Tester-Konto) testen: Kauf ->
      `purchaseToken` -> Server-Verifikation -> signiertes Ed25519-Token ->
      Tier flippt auf Pro.
- [ ] **Erst nach erfolgreichem Test**: `playstore.yml` -> `in_app_purchases: true`
      setzen und Listing erneut synchronisieren.

> Alternative: Launch OHNE IAP (nur Free), Billing in 1.1 nachreichen.
> Dann `in_app_purchases: false` belassen und 1.4 ueberspringen.

### 1.5 Echte Screenshots erstellen (Platzhalter ersetzen)
> `assets/store/phone-1..3.png` sind aktuell einfarbige Platzhalter. Google
> verlangt echte In-App-Screenshots; faken ist nicht zulaessig.

- [ ] App auf Geraet/Emulator starten, 3-8 aussagekraeftige Screenshots der
      echten Module (Vertraege, Finanzen, Kalender, Familie ...) aufnehmen.
- [ ] Nach `assets/store/` legen; falls mehr als 3, `playstore.yml`
      (`phone_screenshots`) erweitern.

### 1.6 Closed Testing (Pflicht-Gate fuer neue Personenkonten)
- [ ] Internal Testing: AAB hochladen, Pre-Launch-Report auf Crashes pruefen.
- [ ] Closed Test: >= 12 Tester, >= 14 Tage (siehe `playstore.yml` tracks.closed,
      `release/closed-test-2026-05-30.md`).
- [ ] Nachweise sammeln, dann Produktionszugang anfordern.

---

## 2. Optional / Qualitaet (nicht launch-blockierend)

- [ ] Finales Logo statt typografischem Lettermark (dann
      `assets/icons/*` + `assets/store/icon-512.png` ersetzen).
- [ ] Tablet-Screenshots fuer bessere Auffindbarkeit
      (`playstore.yml` tablet_screenshots).
- [ ] Promo-Video.
- [ ] `tools/playstore_check.py` haerten: aktuell prueft `check_store_assets`
      nur Existenz/Groesse (>=64 B), nicht Maße/Einfarbigkeit - dadurch sind
      Platzhalter durchgerutscht. Optional: PNG-Dimensionen + Farbvielfalt
      validieren, damit so etwas auffaellt.

---

## 3. Finaler Pre-Submit-Check (vor jedem Upload)

```bash
python -m tools.playstore_check --strict   # muss 0 FAIL liefern
python -m tools.data_safety --check
python -m tools.privacy_policy --list-placeholders
python -m unittest discover -s tests        # bzw. das Projekt-Testkommando
```

- [ ] versionCode in `buildozer.spec` und `playstore.yml` fuer jedes Update
      erhoehen (aktuell 2 / 1.0.0).
- [ ] Gestaffelter Rollout (5% -> 20% -> 50% -> 100%) + Monitoring der
      Crash-/ANR-Schwellen aus `playstore.yml` (monitoring).
