[app]

# Anzeigename auf dem Geraet
title = ZunaroDo
package.name = alltagshelfer
package.domain = de.alltagshelfer

source.dir = .
source.include_exts = py,png,jpg,kv,json,otf,ttf,xml
source.include_patterns = locales/*.json,ARCHITECTURE.md,legal/*.md
# Demo-DBs, SQLite-Dateien und Logs duerfen NIE ins APK/AAB.
# Der Play-Store-Compliance-Checker erzwingt 'db' und 'sqlite' in dieser Liste.
source.exclude_dirs = tests,htmlcov,backups,logs,dist,build,.venv,venv,.git,docs,.buildozer
source.exclude_exts = spec,db,sqlite,log,pyc

version = 1.0.0

# Pflicht-Requirements
# - python3, kivy, kivymd: das Frontend selbst
# - sqlite3: built-in im python-for-android-Recipe
# - certifi, requests: TLS-Validierung + Gemini-REST-Client
#   (services/gemini_rest.py spricht Gemini ueber requests an, damit der
#   KI-Assistent OHNE das nicht-baubare 'google-generativeai'-SDK laeuft).
# - pyjnius: Java-Bruecken (Play Billing, DB-Keystore, ML-Kit-OCR).
# DB-Verschluesselung (SQLCipher) ist AKTIV: 'sqlcipher3' greift ueber die
# lokale Recipe unter ./recipes (siehe p4a.local_recipes weiter unten).
# Python-Seite: database.py + services/db_key.py.
#   ACHTUNG: Die Recipe (recipes/sqlcipher3/) ist noch NICHT auf einem
#   echten WSL2/Linux-Build verifiziert - siehe release/GO_LIVE_TODO.md.
#   Falls der erste Build daran scheitert, 'sqlcipher3' temporaer entfernen
#   (App laeuft dann mit unverschluesseltem SQLite) und Recipe nachziehen.
requirements = python3,kivy==2.3.0,kivymd==1.2.0,certifi,requests,pyjnius,sqlcipher3

# Welcher Screen-Orientierungs-Default
orientation = portrait
fullscreen = 0

# Berechtigungen - bewusst minimal.
# Vorgabe: jede Permission ist in docs/android/04_PRIVACY_PERMISSIONS.md
# begruendet und durch tools/playstore_check.py whitelisted.
# INTERNET nur, weil Gemini/Sync online gehen koennen.
# POST_NOTIFICATIONS (Android 13+/API 33): Laufzeitberechtigung fuer die
# Erinnerungs-Benachrichtigungen des Schedulers. Wird sie verweigert,
# bleibt die App nutzbar - Erinnerungen erscheinen dann nur in-App.
# Kein FOREGROUND-/Calendar-/Contacts-/Location-Provider, weil Daten lokal bleiben.
android.permissions = INTERNET, POST_NOTIFICATIONS

# API-Level und Architektur.
# - android.api: Target-SDK. Play Store verlangt aktuell mind. 35 fuer neue
#   Apps und App-Updates. Anhebung mit Tests verbinden (Edge-to-Edge,
#   Foreground-Service-Restrictions, Predictive-Back).
# - android.minapi: 24 (Android 7.0) deckt >98 % aktiver Geraete ab.
# - android.ndk_api: 24, MUSS mit minapi konsistent sein.
android.api = 35
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a

# ---------------------------------------------------------------------
# Native-Integrationen (Java-Bruecken + Gradle-Abhaengigkeiten)
# ---------------------------------------------------------------------
# Java-Quellwurzel mit korrekter Paketstruktur:
#   de/alltagshelfer/billing/PlayBillingBridge.java   (Play Billing)
#   de/alltagshelfer/dbkey/DbKeyProvider.java         (SQLCipher-Key)
#   de/alltagshelfer/ocr/MlKitOcrBridge.java          (On-Device-OCR)
android.add_src = src/android/java

# AndroidX wird von security-crypto und ML Kit benoetigt.
android.enable_androidx = True

# Gradle-Abhaengigkeiten der Bruecken:
#   - billing:        In-App-Abos (Play Billing Library)
#   - security-crypto: Keystore-gestuetzte EncryptedSharedPreferences
#   - text-recognition: lokale OCR (kein Cloud-Call)
android.gradle_dependencies = com.android.billingclient:billing:6.2.1, androidx.security:security-crypto:1.1.0-alpha06, com.google.mlkit:text-recognition:16.0.1

# Lokale p4a-Recipes (aktuell: sqlcipher3). Wird nur gebaut, wenn das
# Paket auch in 'requirements' steht.
p4a.local_recipes = ./recipes

# Release-Artefakt: Google Play verlangt ein App Bundle (.aab), kein APK.
# 'buildozer android release' erzeugt damit bin/*.aab. Die Signierung
# uebernimmt python-for-android ueber die P4A_RELEASE_*-Umgebungsvariablen
# (im Release-Workflow aus GitHub-Secrets gesetzt) bzw. Play App Signing.
android.release_artifact = aab

# Release-Build packt nur das hier definierte; debug-only Strings via
# Build-Time-Env-Var (siehe docs/android/01_ARCHITECTURE.md#6).
# Cleartext-Traffic ist im generierten Manifest standardmaessig aus
# (usesCleartextTraffic == false). Bei Aenderungen Manifest pruefen
# (tools/playstore_check.py erkennt es).
android.allow_backup = False

# Entry-Point (Modul, das die Kivy-App-Klasse haelt)
entrypoint = mobile/app.py

# App-Icon, Adaptive-Icon (Android 8+) und Splashscreen.
# Diese Assets werden reproduzierbar erzeugt mit:  python -m tools.gen_assets
# (gebrandetes "Z"-Lettermark; ersetzbar durch ein finales Logo).
icon.filename = assets/icons/icon-512.png
icon.adaptive_foreground.filename = assets/icons/adaptive-foreground.png
icon.adaptive_background.filename = assets/icons/adaptive-background.png
presplash.filename = assets/icons/presplash.png
android.presplash_color = #245858

# Logleveldetails fuer Buildozer
log_level = 2
warn_on_root = 1


[buildozer]

# Wo Builds landen
build_dir = .buildozer
bin_dir = dist


# ---------------------------------------------------------------------
# Compliance- und Sicherheits-Hinweise
# (siehe docs/android/ fuer das vollstaendige Regelwerk)
# ---------------------------------------------------------------------
# 1) Vor JEDEM Push laeuft 'python -m tools.playstore_check --strict'
#    in der CI - lokal koennt ihr ihn manuell aufrufen.
#
# 2) Buildozer laeuft auf Linux/macOS und in WSL2 - NICHT direkt unter
#    Windows. Empfohlen: WSL2 mit Ubuntu 22.04.
#       pip install buildozer cython==0.29.36
#       sudo apt install -y python3-pip openjdk-17-jdk \
#           autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
#           libtinfo5 cmake unzip libffi-dev libssl-dev
#       buildozer android debug
#
# 3) Erster Build laed Android-SDK/NDK; das dauert (>1 GB Download).
#    Folge-Builds sind schnell.
#
# 4) APK landet unter dist/. Installieren via adb:
#       adb install dist/alltagshelfer-0.9.0-arm64-v8a-debug.apk
#
# 5) Release-Signierung erfolgt ueber Env-Vars:
#       P4A_RELEASE_KEYSTORE             - Pfad zum Upload-Keystore
#       P4A_RELEASE_KEYSTORE_PASSWD      - Keystore-Passwort
#       P4A_RELEASE_KEYALIAS             - Alias
#       P4A_RELEASE_KEYALIAS_PASSWD      - Alias-Passwort
#    Diese Werte NIEMALS ins Repo commiten; im CI als GitHub-Secrets.
#
# 6) SQLCipher ist aktiviert (sqlcipher3 in requirements + recipes/sqlcipher3).
#    Beim ERSTEN WSL2-Build verifizieren, dass die Recipe baut und die DB
#    auf dem Geraet wirklich verschluesselt ist (Database.encryption_mode
#    == "sqlcipher"). Details: release/GO_LIVE_TODO.md, docs/android/03_SECURITY.md.
#
# 7) Fuer den Play Store sollte ein AAB statt fat-APK erzeugt werden.
#    Buildozer >=1.5: 'buildozer -v android release --aab'.
# ---------------------------------------------------------------------
