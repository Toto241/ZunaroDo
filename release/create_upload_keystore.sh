#!/usr/bin/env bash
# Erstellt den Upload-Keystore fuer die Play-Store-Signierung von ZunaroDo.
#
# Linux/macOS-Aequivalent zu release/create_upload_keystore.ps1.
# Benoetigt keytool (Teil des JDK, z. B. Temurin 17).
#
# Aufruf:
#   ./release/create_upload_keystore.sh
#
# WICHTIG:
#   - Passwoerter werden NICHT gespeichert — im Passwort-Manager ablegen.
#   - Die .jks-Datei NIEMALS committen (ist in .gitignore).
#   - Fuer CI: Base64-kodieren und als GitHub-Secrets hinterlegen
#     (siehe docs/android/07_CICD.md und release/PLAY_CONSOLE_SETUP.md).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEYSTORE_PATH="${KEYSTORE_PATH:-$SCRIPT_DIR/keystore/alltagshelfer-upload.jks}"
ALIAS="${ALIAS:-alltagshelfer-upload}"
VALIDITY_DAYS="${VALIDITY_DAYS:-10000}"

keytool_cmd=""
if command -v keytool >/dev/null 2>&1; then
  keytool_cmd="keytool"
elif [[ -n "${JAVA_HOME:-}" && -x "$JAVA_HOME/bin/keytool" ]]; then
  keytool_cmd="$JAVA_HOME/bin/keytool"
fi

if [[ -z "$keytool_cmd" ]]; then
  echo "FEHLER: keytool nicht gefunden. JDK 17 installieren und JAVA_HOME setzen." >&2
  exit 1
fi

mkdir -p "$(dirname "$KEYSTORE_PATH")"

if [[ -f "$KEYSTORE_PATH" ]]; then
  echo "FEHLER: Keystore existiert bereits: $KEYSTORE_PATH — Abbruch." >&2
  exit 1
fi

echo "Erzeuge Upload-Keystore:"
echo "  Datei : $KEYSTORE_PATH"
echo "  Alias : $ALIAS"
echo "  Gueltig: $VALIDITY_DAYS Tage"
echo "keytool fragt gleich nach Keystore- und Key-Passwort (merken!)."

"$keytool_cmd" -genkeypair -v \
  -keystore "$KEYSTORE_PATH" \
  -alias "$ALIAS" \
  -keyalg RSA -keysize 2048 \
  -validity "$VALIDITY_DAYS" \
  -storetype JKS

echo ""
echo "Fertig. Naechste Schritte:"
echo "  1. Passwoerter im Passwort-Manager sichern."
echo "  2. Fuer lokalen Release-Build:"
echo "       export P4A_RELEASE_KEYSTORE=\"$KEYSTORE_PATH\""
echo "       export P4A_RELEASE_KEYSTORE_PASSWD=\"<keystore-passwort>\""
echo "       export P4A_RELEASE_KEYALIAS=\"$ALIAS\""
echo "       export P4A_RELEASE_KEYALIAS_PASSWD=\"<key-passwort>\""
echo "  3. Fuer GitHub Actions (.github/workflows/android-release.yml) vier Secrets:"
echo "       ANDROID_KEYSTORE_BASE64     = base64 der .jks"
echo "       ANDROID_KEYSTORE_PASSWORD   = <keystore-passwort>"
echo "       ANDROID_KEY_ALIAS           = $ALIAS"
echo "       ANDROID_KEY_ALIAS_PASSWORD  = <key-passwort>"
echo "     Base64 erzeugen: base64 -w0 \"$KEYSTORE_PATH\""
echo "  4. .jks NIEMALS committen."
