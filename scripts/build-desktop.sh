#!/usr/bin/env bash
# ============================================================
#  Desktop-Build (Linux / macOS) - PyInstaller
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."

echo
echo "=== Alltagshelfer  -  PC-Build (PyInstaller) ==="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "[FEHLER] python3 fehlt." >&2
    exit 1
fi

if ! python3 -c "import PyInstaller" >/dev/null 2>&1; then
    echo "PyInstaller wird installiert ..."
    python3 -m pip install --upgrade pyinstaller
fi

echo
echo "--- Build laeuft (1-3 min) ---"
python3 -m PyInstaller --noconfirm alltagshelfer.spec

echo
echo "=== Build fertig ==="
ls -la dist/Alltagshelfer/ 2>/dev/null | head -10 || true
echo
echo "Bundle in dist/Alltagshelfer/"
