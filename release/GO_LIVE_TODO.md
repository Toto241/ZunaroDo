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
- [x] Asset-Gate `python -m tools.gen_assets --check` (erkennt einfarbige
      Platzhalter + falsche Maße) in den Release-Workflow eingebaut
      (`.github/workflows/android-release.yml`) - blockiert Go-Live mit
      Platzhalter-Screenshots, ohne die main-CI rot zu machen.
- [x] versionCode gepinnt: `android.numeric_version = 2` in `buildozer.spec`.
      Der `versioning`-Check in `tools/playstore_check.py` erzwingt jetzt
      Konsistenz mit `playstore.yml` (`identity.version_code`/`version_name`) -
      vorher haette buildozer einen abweichenden versionCode abgeleitet.
- [x] Platzhalter-Testergruppe `internal-team@example.org` (Internal Track)
      durch die echte Google-Group ersetzt (`playstore.yml` +
      Mock-Vorlage in `tools/playstore_sync.py`).
- [x] `release/assets/` fuer Play-Console-Belege angelegt (dort erwartet
      `closed-test-2026-05-30.md` den echten Konsolen-Screenshot).

---

## 1. BLOCKER - vor Produktion zwingend

### 1.1 Android-Build erzeugen (Basis fuer alles Weitere)
> ERLEDIGT via CI (kein WSL2 noetig): Actions-Workflow `Android
> Robo/Monkey (Emulator)` baut das Debug-APK auf einem Linux-Runner.
> Lauf #10 (2026-06-10) war komplett gruen: Build -> APK-Artefakt ->
> Emulator-Installation -> Monkey-Stresstest (500 Events) ohne
> Crash/ANR. Lokales WSL2 bleibt als optionaler zweiter Weg.

- [x] Debug-Build: Robo-Workflow dispatchen (gruen, APK als Artefakt
      `debug-apk`; Workflow-Profil baut x86_64 fuer den Emulator,
      Produktions-Archs bleiben ARM).
- [x] **SQLCipher-Recipe baut** (beide ARM-Archs + x86_64): Die Recipe
      (`recipes/sqlcipher3/`) generiert die Amalgamation beim Build
      selbst (braucht `tcl`, in den CI-Workflows enthalten) und baut sie
      statisch; auf dem Host validiert (cipher_version 4.6.1, falscher
      Key abgewiesen, Datei-Header verschluesselt).
- [ ] **SQLCipher auf Geraet verifizieren**: APK-Artefakt installieren,
      pruefen dass `Database.encryption_mode == "sqlcipher"`.
- [ ] **ML-Kit-OCR verifizieren**: Beleg scannen -> `scan_receipt()` liefert
      `engine == "mlkit"` (Modell laedt beim 1. Aufruf nach).
- [ ] **Icon/Adaptive-Icon** auf echtem Launcher pruefen (kein weisser Default).
- [ ] Release-Bundle: Workflow `Android Release (AAB)` dispatchen ->
      Artefakt `dist/*.aab` (braucht die vier Keystore-Secrets aus 1.2).

### 1.2 Upload-Keystore erstellen & sichern
- [ ] `pwsh ./release/create_upload_keystore.ps1` ausfuehren.
- [ ] Passwoerter im Passwort-Manager sichern (Verlust = App-Linie verloren).
- [ ] Lokaler Build: `P4A_RELEASE_*`-Env-Vars setzen (das Skript zeigt sie an).
- [ ] CI-Build (`.github/workflows/android-release.yml`): vier Repo-Secrets
      setzen - `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`,
      `ANDROID_KEY_ALIAS`, `ANDROID_KEY_ALIAS_PASSWORD`.
- [ ] Sicherstellen: `.jks` ist NICHT im Git (ist bereits gitignored).

### 1.3 Play Console - App anlegen
- [ ] Play-Developer-Konto (25 USD einmalig) + Identitaetspruefung
      (2-4 Tage; bei Personenkonten Pflicht).
- [ ] Neue App: Name "ZunaroDo", Standardsprache de-DE, Kategorie PRODUCTIVITY,
      kostenlos (Pro via IAP). Package `de.alltagshelfer.alltagshelfer`
      (NICHT mehr aenderbar nach Release).
- [ ] Data-Safety-Formular gemaess `release/DATA_SAFETY_CONSOLE_ANSWERS.md`
      und `playstore.yml` ausfuellen.
- [ ] Datenschutz-URL eintragen (siehe `playstore.yml` privacy_policy_url).
      Pages-Deploy lief bereits erfolgreich (Actions-Workflow
      "Privacy-Policy Pages", zuletzt 2026-06-03) - nur noch kurz im
      Browser gegenpruefen, dass die URL HTTP 200 liefert.
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
- [ ] `python -m tools.gen_assets --check` muss danach gruen sein - der
      Release-Workflow bricht sonst beim Asset-Gate ab.

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
- [x] Asset-Platzhalter-Erkennung: erledigt via `tools/gen_assets.py --check`
      (Release-Gate). `tools/playstore_check.py check_store_assets` prueft
      weiterhin nur Existenz/Groesse - bewusst, damit die routinemaeßige
      main-CI nicht an den noch fehlenden echten Screenshots scheitert.

---

## 3. Finaler Pre-Submit-Check (vor jedem Upload)

```bash
python -m tools.playstore_check --strict   # muss 0 FAIL liefern
python -m tools.data_safety --check
python -m tools.privacy_policy --list-placeholders
python -m unittest discover -s tests        # bzw. das Projekt-Testkommando
```

- [ ] versionCode fuer jedes Update gemeinsam erhoehen:
      `android.numeric_version` in `buildozer.spec` UND
      `identity.version_code` in `playstore.yml` (aktuell 2 / 1.0.0).
      Ein Auseinanderlaufen macht `tools/playstore_check.py` zum FAIL.
- [ ] Gestaffelter Rollout (5% -> 20% -> 50% -> 100%) + Monitoring der
      Crash-/ANR-Schwellen aus `playstore.yml` (monitoring).
