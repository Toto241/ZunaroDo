"""
Verifikation von SQLCipher und ML-Kit-OCR auf einem angeschlossenen Android-Geraet.

Voraussetzungen:
  - adb im PATH
  - Debug- oder Release-APK installiert (Package de.alltagshelfer.alltagshelfer)
  - Fuer OCR-Test: Kamera-Berechtigung + Testbild auf Geraet

Aufruf:
    python -m tools.verify_android_device
    python -m tools.verify_android_device --apk path/to/app.apk
    python -m tools.verify_android_device --skip-ocr
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PACKAGE = "de.alltagshelfer.alltagshelfer"
DB_FILENAME = "alltagshelfer.db"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _adb_devices() -> list[str]:
    out = _run(["adb", "devices"]).stdout.strip().splitlines()[1:]
    serials = []
    for line in out:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def _adb_shell(serial: str, command: str) -> str:
    return _run(["adb", "-s", serial, "shell", command]).stdout.strip()


def _find_db_on_device(serial: str) -> str | None:
    """Sucht die App-DB in der Sandbox."""
    candidates = [
        f"/data/data/{PACKAGE}/files/{DB_FILENAME}",
        f"/data/user/0/{PACKAGE}/files/{DB_FILENAME}",
    ]
    for path in candidates:
        if _adb_shell(serial, f"test -f {path} && echo ok") == "ok":
            return path
    found = _run(
        ["adb", "-s", serial, "shell",
         f"run-as {PACKAGE} find . -name {DB_FILENAME} -type f"],
        check=False).stdout.strip()
    if found and DB_FILENAME in found:
        for line in found.splitlines():
            if DB_FILENAME in line:
                return f"/data/data/{PACKAGE}/{line.lstrip('./')}"
    return None


def verify_sqlcipher(serial: str, db_path: str) -> tuple[bool, str]:
    """
    Prueft verschluesselten DB-Header via adb pull + lokalem sqlcipher3 oder
    Hex-Header ('SQLite format 3' vs verschluesselt).
    """
    with tempfile.TemporaryDirectory(prefix="ah_verify_") as tmp:
        local = Path(tmp) / DB_FILENAME
        _run(["adb", "-s", serial, "pull", db_path, str(local)], check=False)
        if not local.is_file() or local.stat().st_size < 16:
            return False, "DB konnte nicht vom Geraet gelesen werden (adb pull)."
        header = local.read_bytes()[:16]
        if header.startswith(b"SQLite format 3"):
            return False, "DB-Header ist Klartext-SQLite — SQLCipher aktiv?"
        try:
            import sqlcipher3  # type: ignore
            conn = sqlcipher3.connect(str(local))
            conn.execute("PRAGMA key = 'wrong-key-should-fail';")
            conn.execute("SELECT count(*) FROM sqlite_master;")
            conn.close()
        except ImportError:
            pass
        except Exception:
            return True, "Header verschluesselt; falscher Key wird abgewiesen (sqlcipher3)."
        return True, f"Header verschluesselt ({header[:8]!r}...) — kein Klartext-SQLite."


def verify_mlkit(serial: str) -> tuple[bool, str]:
    """
    OCR auf Geraet: startet die App und prueft Logcat auf ML-Kit-Hinweise.
    Vollstaendiger Test erfordert manuelles Beleg-Scannen in der App.
    """
    _run(["adb", "-s", serial, "shell", "am", "start", "-n",
          f"{PACKAGE}/org.kivy.android.PythonActivity"], check=False)
    logs = _run(["adb", "-s", serial, "logcat", "-d", "-t", "200"],
                check=False).stdout.lower()
    hints = ("mlkit", "ml kit", "textrecognition", "ocr_android")
    if any(h in logs for h in hints):
        return True, "Logcat enthaelt ML-Kit/OCR-Hinweise."
    return False, (
        "Kein ML-Kit in Logcat — Beleg in der App scannen und erneut pruefen, "
        "oder services/ocr_android.py manuell testen.")


def verify_package(serial: str) -> tuple[bool, str]:
    out = _adb_shell(serial, f"pm list packages {PACKAGE}")
    if PACKAGE in out:
        return True, f"Package {PACKAGE} installiert."
    return False, f"Package {PACKAGE} nicht installiert."


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SQLCipher + ML-Kit auf Android-Geraet verifizieren")
    parser.add_argument("--serial", help="adb-Serial (Default: erstes Geraet)")
    parser.add_argument("--skip-ocr", action="store_true",
                        help="ML-Kit-Pruefung ueberspringen")
    parser.add_argument("--json", action="store_true", help="JSON-Ausgabe")
    args = parser.parse_args()

    devices = _adb_devices()
    if not devices:
        msg = "Kein adb-Geraet verbunden (adb devices leer)."
        if args.json:
            print(json.dumps({"ok": False, "error": msg}))
        else:
            print(f"FEHLER: {msg}", file=sys.stderr)
        sys.exit(1)

    serial = args.serial or devices[0]
    results: dict[str, dict] = {}

    ok_pkg, msg_pkg = verify_package(serial)
    results["package"] = {"ok": ok_pkg, "message": msg_pkg}

    ok_cipher = False
    msg_cipher = "Package nicht installiert — SQLCipher-Check uebersprungen."
    if ok_pkg:
        db_path = _find_db_on_device(serial)
        if db_path:
            ok_cipher, msg_cipher = verify_sqlcipher(serial, db_path)
        else:
            msg_cipher = "DB nicht gefunden — App einmal starten und Daten anlegen."
    results["sqlcipher"] = {"ok": ok_cipher, "message": msg_cipher}

    ok_ocr = True
    msg_ocr = "uebersprungen"
    if not args.skip_ocr and ok_pkg:
        ok_ocr, msg_ocr = verify_mlkit(serial)
    results["mlkit_ocr"] = {"ok": ok_ocr, "message": msg_ocr}

    all_ok = ok_pkg and ok_cipher and ok_ocr

    if args.json:
        print(json.dumps({"serial": serial, "ok": all_ok, "checks": results},
                         indent=2))
    else:
        print(f"Geraet: {serial}\n")
        for name, r in results.items():
            status = "OK" if r["ok"] else "FAIL"
            print(f"  [{status}] {name}: {r['message']}")
        print()
        if all_ok:
            print("Alle Checks bestanden.")
        else:
            print("Mindestens ein Check fehlgeschlagen — siehe GO_LIVE_TODO.md §1.1.")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
