#!/usr/bin/env bash
# ============================================================
#  iOS-Build (nur macOS) - kivy-ios + Xcode
#
#  Erzeugt ein Xcode-Projekt unter ../Alltagshelfer-ios/ und
#  baut die Python-/Kivy-Runtime fuer ARM64. Code-Signing /
#  IPA-Export erfolgt anschliessend ueber Xcode oder fastlane.
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "$(uname)" != "Darwin" ]]; then
    echo "[FEHLER] iOS-Builds brauchen macOS. Du bist auf: $(uname)" >&2
    exit 1
fi

if ! command -v xcodebuild >/dev/null 2>&1; then
    echo "[FEHLER] Xcode (xcodebuild) fehlt." >&2
    echo "        Im App Store installieren + 'sudo xcode-select --install'." >&2
    exit 1
fi

if ! command -v toolchain >/dev/null 2>&1; then
    echo "kivy-ios fehlt - wird installiert ..."
    python3 -m pip install --upgrade kivy-ios
fi

echo
echo "=== Alltagshelfer  -  iOS-Build (kivy-ios) ==="
echo

# 1) Python + Kivy + OpenSSL fuer iOS bauen (einmalig, dauert lange)
if [[ ! -d "dist/root" ]]; then
    echo "--- Erste Toolchain-Builds (python3, kivy, openssl) ---"
    toolchain build python3 kivy openssl
fi

# 2) Xcode-Projekt erzeugen
APP_NAME="Alltagshelfer"
PROJECT_DIR="../${APP_NAME}-ios"
if [[ ! -d "${PROJECT_DIR}" ]]; then
    echo "--- Erzeuge Xcode-Projekt ${PROJECT_DIR} ---"
    toolchain create "${APP_NAME}" "$(pwd)"
fi

echo
echo "=== Build fertig ==="
echo "Xcode-Projekt: ${PROJECT_DIR}/${APP_NAME}-ios.xcodeproj"
echo "Naechster Schritt:"
echo "  open ${PROJECT_DIR}/${APP_NAME}-ios.xcodeproj"
echo "  (Signing-Team und Bundle-ID in Xcode setzen, dann 'Run')"
