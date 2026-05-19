[app]

# Anzeigename auf dem Geraet
title = Alltagshelfer
package.name = alltagshelfer
package.domain = de.alltagshelfer

source.dir = .
source.include_exts = py,png,jpg,kv,json,otf,ttf
source.include_patterns = locales/*.json,ARCHITECTURE.md
source.exclude_dirs = tests,htmlcov,backups,logs,dist,build,.venv,venv,.git
source.exclude_exts = spec,db,sqlite,log

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

# Berechtigungen - bewusst minimal
# INTERNET nur, weil Gemini/Sync online gehen koennen.
# Kein FOREGROUND-/Calendar-/Contacts-Provider, weil Daten lokal bleiben.
android.permissions = INTERNET

# Welcher API-Level und Architektur
android.api = 33
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a

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
# Hinweise:
# 1) Buildozer laeuft auf Linux/macOS und in WSL2 - NICHT direkt unter
#    Windows. Empfohlen: WSL2 mit Ubuntu 22.04.
#       pip install buildozer cython
#       sudo apt install -y python3-pip openjdk-17-jdk \
#           autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
#           libtinfo5 cmake unzip
#       buildozer android debug
#
# 2) Erster Build laed Android-SDK/NDK; das dauert (>1 GB Download).
#    Folge-Builds sind schnell.
#
# 3) APK landet unter dist/. Installieren via adb:
#       adb install dist/alltagshelfer-0.9.0-arm64-v8a-debug.apk
#
# 4) Falls SQLCipher gewuenscht: requirements um sqlcipher3 ergaenzen
#    und im python-for-android ein passendes Recipe einbinden.
# ---------------------------------------------------------------------
