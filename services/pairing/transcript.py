"""
Kanonische Serialisierung des Pairing-Transcripts.

Das Transcript ist der einzige Datenblock, ueber den am Ende beide
Geraete eine Ed25519-Signatur leisten - es bildet damit den Anker
des Out-of-Band-Identitaetsnachweises (siehe PAIRING.md Kapitel 5,
Schritt 8).

Format (alle Laengen big-endian):

    0x01                              1 Byte Version-Tag
    sid_len  (uint32) + sid_bytes
    ik_pub_i_len (uint32) + ik_pub_i  (Ed25519-Public-Key, immer 32 Byte)
    ik_pub_r_len (uint32) + ik_pub_r  (Ed25519-Public-Key, immer 32 Byte)
    method_len (uint32) + method_utf8 (typischerweise 'qr'|'usb'|'sms')
    exp        (uint64) Unix-Sekunden

Begruendung fuer das Laengen-Praefix bei jedem Feld: ohne dieses
Praefix koennte ein Angreifer zwei semantisch unterschiedliche
Eingaben so konstruieren, dass sie dieselbe Byte-Sequenz ergeben
(z.B. eine laengere `method` durch Verlust eines Trennzeichens). Das
Versions-Tag macht zukuenftige Protokoll-Aenderungen unmissverstaendlich.
"""
from __future__ import annotations

import hashlib
import struct
from typing import Final

TRANSCRIPT_VERSION: Final[int] = 1


def make_transcript(
    sid: bytes,
    ik_pub_initiator: bytes,
    ik_pub_responder: bytes,
    method: str,
    exp: int,
) -> bytes:
    """Erzeugt die kanonische Transcript-Bytestring-Repraesentation."""
    if not isinstance(sid, (bytes, bytearray)) or len(sid) == 0:
        raise ValueError("sid muss nicht-leere Bytes sein")
    if len(ik_pub_initiator) != 32:
        raise ValueError("ik_pub_initiator muss 32 Byte sein")
    if len(ik_pub_responder) != 32:
        raise ValueError("ik_pub_responder muss 32 Byte sein")
    if not isinstance(method, str) or not method:
        raise ValueError("method muss ein nicht-leerer String sein")
    if not isinstance(exp, int) or exp < 0 or exp >= 2 ** 64:
        raise ValueError("exp muss eine vorzeichenlose 64-Bit-Ganzzahl sein")

    method_bytes = method.encode("utf-8")
    parts = [
        bytes([TRANSCRIPT_VERSION]),
        struct.pack(">I", len(sid)) + bytes(sid),
        struct.pack(">I", 32) + bytes(ik_pub_initiator),
        struct.pack(">I", 32) + bytes(ik_pub_responder),
        struct.pack(">I", len(method_bytes)) + method_bytes,
        struct.pack(">Q", exp),
    ]
    return b"".join(parts)


def transcript_hash(transcript_bytes: bytes) -> bytes:
    """SHA-256 ueber das Transcript - 32 Byte. Hilfreich zum Loggen
    oder Anzeigen, niemals als Beweis-Ersatz fuer die Signatur."""
    return hashlib.sha256(transcript_bytes).digest()
