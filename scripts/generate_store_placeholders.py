#!/usr/bin/env python3
"""
Erzeugt minimale PNG-Platzhalter fuer Play-Store-Assets (stdlib only).

Aufruf:
    python scripts/generate_store_placeholders.py

Ersetzt die Platzhalter vor Production durch echte Screenshots/Branding.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "assets" / "store"

# RGBA: ZunaroDo-nahe Teal (#2d6a6a)
COLOR = (45, 106, 106, 255)


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_png(path: Path, width: int, height: int) -> None:
    """Schreibt ein einfarbiges RGBA-PNG."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b""
    row = bytes(COLOR) * width
    for _ in range(height):
        raw += b"\x00" + row
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    data = _png_chunk(b"IHDR", ihdr) + _png_chunk(
        b"IDAT", zlib.compress(raw, 9)
    ) + _png_chunk(b"IEND", b"")
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + data)


def main() -> None:
    specs = {
        "icon-512.png": (512, 512),
        "feature.png": (1024, 500),
        "phone-1.png": (1080, 1920),
        "phone-2.png": (1080, 1920),
        "phone-3.png": (1080, 1920),
    }
    for name, (w, h) in specs.items():
        target = OUT_DIR / name
        write_png(target, w, h)
        print(f"OK {target} ({w}x{h})")


if __name__ == "__main__":
    main()
