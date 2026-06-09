#!/usr/bin/env bash
# Erzeugt einen Upload-Keystore fuer Play-Store-Releases.
# WICHTIG: Passwort und .keystore sicher aufbewahren — Verlust = kein Update moeglich.
#
# Nutzung:
#   ./scripts/generate-upload-keystore.sh [pfad.zum.keystore]
#
# Danach Secrets in GitHub setzen (siehe docs/android/KEYSTORE_SETUP.md):
#   base64 -w0 upload.keystore  # oder base64 upload.keystore auf macOS
set -euo pipefail

OUT="${1:-upload.keystore}"
ALIAS="${KEY_ALIAS:-zunarodo-upload}"

if [[ -f "$OUT" ]]; then
  echo "FEHLER: $OUT existiert bereits."
  exit 1
fi

echo "Erzeuge Upload-Keystore: $OUT (Alias: $ALIAS)"
keytool -genkeypair -v \
  -keystore "$OUT" \
  -alias "$ALIAS" \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -storetype PKCS12

echo ""
echo "Naechste Schritte:"
echo "  1. Keystore sichern (Backup!)"
echo "  2. GitHub Secrets setzen (ANDROID_KEYSTORE_BASE64, *_PASSWORD, *_ALIAS)"
echo "  3. Workflow 'Android Release (AAB)' ausfuehren"
echo "  4. Play App Signing in der Play Console aktivieren"
