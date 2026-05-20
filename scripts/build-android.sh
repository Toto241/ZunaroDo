#!/usr/bin/env bash
# ============================================================
#  Android-Build (Linux / macOS) - Buildozer
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."

echo
echo "=== Alltagshelfer  -  Android-Build (Buildozer) ==="
echo

if ! command -v buildozer >/dev/null 2>&1; then
    echo "Buildozer fehlt - wird installiert ..."
    python3 -m pip install --user buildozer cython==0.29.36
    if ! command -v buildozer >/dev/null 2>&1; then
        echo "[FEHLER] Buildozer auch nach Installation nicht im PATH." >&2
        echo "        Pfad pruefen: ~/.local/bin in PATH?" >&2
        exit 1
    fi
fi

if ! command -v java >/dev/null 2>&1; then
    echo "[FEHLER] Java fehlt. Installation:" >&2
    echo "  sudo apt install openjdk-17-jdk" >&2
    exit 1
fi

echo
echo "--- buildozer android debug ---"
buildozer android debug

echo
echo "=== Build fertig ==="
ls -la bin/ dist/ 2>/dev/null | grep -E "\.(apk|aab)$" || true
