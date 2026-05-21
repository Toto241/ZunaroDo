[app]

# Anzeigename auf dem Geraet
title = Alltagshelfer
package.name = alltagshelfer
package.domain = de.alltagshelfer

source.dir = .
source.include_exts = py,png,jpg,kv,json,otf,ttf,xml
source.include_patterns = locales/*.json,ARCHITECTURE.md,legal/*.md
# Demo-DBs, SQLite-Dateien und Logs duerfen NIE ins APK/AAB.
# Der Play-Store-Compliance-Checker erzwingt 'db' und 'sqlite' in dieser Liste.
source.exclude_dirs = tests,htmlcov,backups,logs,dist,build,.venv,venv,.git,docs,.buildozer
source.exclude_exts = spec,db,sqlite,log,pyc

version = 0.9.0

# Pflicht-Requirements
# - python3, kivy, kivymd: das Frontend selbst
# - sqlite3: built-in im python-for-android-Recipe
# - certifi, requests: TLS-Validierung (z.B. fuer den Sync-Server)
# - google-generativeai: optional, wenn die App Online-Assistent nutzen darf
requirements = python3,kivy==2.3.0,kivymd==1.2.0,certifi,requests

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

# Release-Build packt nur das hier definierte; debug-only Strings via
# Build-Time-Env-Var (siehe docs/android/01_ARCHITECTURE.md#6).
# Cleartext-Traffic ist im generierten Manifest standardmaessig aus
# (usesCleartextTraffic == false). Bei Aenderungen Manifest pruefen
# (tools/playstore_check.py erkennt es).
android.allow_backup = False

# Entry-Point (Modul, das die Kivy-App-Klasse haelt)
entrypoint = mobile/app.py

# Icon und Splashscreen koennen unter assets/ liegen
# icon.filename = assets/app_icon.png
# presplash.filename = assets/splash.png

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
# 6) Falls SQLCipher gewuenscht: requirements um sqlcipher3 ergaenzen
#    und im python-for-android ein passendes Recipe einbinden. Dann auch
#    docs/android/03_SECURITY.md updaten.
#
# 7) Fuer den Play Store sollte ein AAB statt fat-APK erzeugt werden.
#    Buildozer >=1.5: 'buildozer -v android release --aab'.
# ---------------------------------------------------------------------
