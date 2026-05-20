"""
Pairing-Session - die State-Machine fuer den eigentlichen Handshake.

Das ist der gemeinsame Krypto-Kern, ueber den alle drei Wege (QR, USB,
SMS) am Ende laufen (siehe PAIRING.md Kapitel 5). Diese Schicht ist
absichtlich kanal-unabhaengig: sie erzeugt und konsumiert Bytes, der
Transport (HTTP, USB-Bulk, Stdin/Stdout im Test) ist anderswo.

Ablauf:

    Initiator                                          Responder
    ---------                                          ---------
    init(role=INITIATOR, ot_secret, sid, method,
         exp, peer_ik_pub=eigener_ik_pub_initiator)
                                                       init(role=RESPONDER, ot_secret, sid,
                                                            method, exp,
                                                            peer_ik_pub=ik_pub_initiator_aus_einladung)
    msg1 = pake_start()
        ---- msg1 ---->                                m = ingest_peer_pake(msg1)
                                                       msg2 = ingest_peer_pake_returns_proof(msg1)
                       <---- msg2 ----                 (msg2 = mb || ik_pub_r || sig_r)
    res = finalize(msg2)
                                                       res = finalize(msg3)
    msg3 = sig_i ----- msg3 ---->

Drei Nachrichten, beide Seiten haben am Ende:
  - peer_public_key (verifiziert via Signatur ueber Transcript)
  - sync_psk = HKDF(MS, salt='sync-psk',
                    info=sorted(ik_pub_initiator, ik_pub_responder))
  - transcript_hash zum Anzeigen/Loggen

Beide MUESSEN ihren `our_private_key`-Eintrag aus dem SecureStore
holen - das passiert *ausserhalb* dieser Klasse, damit der Private-Key
nur am Ort der Signatur kurz auf den Stack kommt.
"""
from __future__ import annotations

import enum
import hashlib
from dataclasses import dataclass
from typing import Optional

from spake2 import SPAKE2_A, SPAKE2_B

from services.pairing.identity import sign, verify
from services.pairing.kdf import hkdf_sha256
from services.pairing.transcript import make_transcript, transcript_hash


class PairingRole(enum.Enum):
    INITIATOR = "initiator"
    RESPONDER = "responder"


class PairingMethod(str, enum.Enum):
    QR = "qr"
    USB = "usb"
    SMS = "sms"


class PairingError(RuntimeError):
    """Handshake-Abbruch - falsche Reihenfolge, ungueltige Signatur,
    fehlgeschlagene PAKE-Pruefung. Aufrufer muessen die Sitzung verwerfen."""


@dataclass(frozen=True)
class PairingResult:
    """Ergebnis nach erfolgreichem Handshake.

    `sync_psk` ist der Pre-Shared-Key fuer den TLS-1.3-PSK-Modus mit
    diesem Peer; gehoert sofort in den SecureStore unter
    `alltagshelfer.peer.<peer_device_id>`.
    """

    peer_public_key: bytes
    sync_psk: bytes
    transcript_hash: bytes


class PairingSession:
    """Zustandsmaschine fuer eine Pairing-Sitzung.

    Eine Instanz pro Sitzung. Nicht thread-safe; Aufrufer
    serialisieren die Methodenaufrufe.
    """

    def __init__(
        self,
        *,
        role: PairingRole,
        our_private_key: bytes,
        our_public_key: bytes,
        peer_public_key_initiator: bytes,
        sid: bytes,
        ot_secret: bytes,
        method: PairingMethod,
        exp: int,
    ) -> None:
        """Erstellt eine Sitzung.

        Argumente:
          role: INITIATOR oder RESPONDER.
          our_private_key: 32-Byte-Ed25519. Nur fuer `make_proof()`
            benutzt, danach geht die Referenz aus dem Scope.
          our_public_key: 32-Byte-Ed25519, eigener Public-Key.
          peer_public_key_initiator: Public-Key des *Initiators*. Beim
            Initiator selbst ist das = `our_public_key`. Beim Responder
            ist das der Wert aus der Einladung.
          sid: Sitzungs-ID (>=16 Byte zufaellig empfohlen).
          ot_secret: Out-of-Band-Geheimnis aus der Einladung (QR-otp,
            USB-otp, SMS-PIN). Wird in SPAKE2 eingespeist.
          method: Pairing-Weg (qr|usb|sms) - geht ins Transcript ein.
          exp: Unix-Sekunden, Ablaufzeitpunkt der Einladung -
            informativ, geht ins Transcript ein.
        """
        if len(our_private_key) != 32 or len(our_public_key) != 32:
            raise ValueError("Ed25519-Schluessel muessen 32 Byte sein")
        if len(peer_public_key_initiator) != 32:
            raise ValueError("ik_pub_initiator muss 32 Byte sein")
        if not sid or not ot_secret:
            raise ValueError("sid und ot_secret duerfen nicht leer sein")

        self._role = role
        self._our_priv = bytes(our_private_key)
        self._our_pub = bytes(our_public_key)
        self._ik_pub_initiator = bytes(peer_public_key_initiator)
        self._ik_pub_responder: Optional[bytes] = (
            bytes(our_public_key) if role is PairingRole.RESPONDER else None
        )
        self._sid = bytes(sid)
        self._method = method
        self._exp = exp

        # SPAKE2: A startet beim Initiator, B beim Responder.
        cls = SPAKE2_A if role is PairingRole.INITIATOR else SPAKE2_B
        self._spake = cls(bytes(ot_secret))
        self._pake_message_out: Optional[bytes] = None
        self._master_secret: Optional[bytes] = None
        self._state = "created"

    # ---- Phase 1: PAKE ----

    def pake_start(self) -> bytes:
        """Erzeugt die eigene PAKE-Nachricht (msg1 bzw. msg2-Anteil)."""
        if self._state != "created":
            raise PairingError(f"pake_start() in falschem Zustand: {self._state}")
        self._pake_message_out = self._spake.start()
        self._state = "pake_started"
        return self._pake_message_out

    def pake_finish(self, peer_pake_message: bytes) -> None:
        """Verarbeitet die PAKE-Nachricht der Gegenseite, leitet MS ab."""
        if self._state != "pake_started":
            raise PairingError(f"pake_finish() in falschem Zustand: {self._state}")
        try:
            self._master_secret = self._spake.finish(peer_pake_message)
        except Exception as exc:  # SPAKE2-Bibliothek wirft verschiedene Typen
            raise PairingError(
                "PAKE-Verifikation fehlgeschlagen - ot_secret falsch "
                "oder Nachricht manipuliert"
            ) from exc
        self._state = "pake_finished"

    # ---- Phase 2: Identitaetsnachweis ----

    def _proof_payload(self, ik_pub_responder: bytes) -> bytes:
        """Bytes, ueber die signiert wird.

        = Transcript ueber sid, IK_pub_I, IK_pub_R, method, exp
          (siehe transcript.make_transcript)
        || session_key = HKDF(MS, salt=sid, info='pair/v1')

        Der angehaengte session_key ist die *Bindung an PAKE*: ohne
        denselben MS auf beiden Seiten ergibt die Signatur ueber dieses
        Payload auf der Gegenseite einen anderen Hash, und Ed25519-
        Verify schlaegt fehl. Damit wird ein nicht-uebereinstimmendes
        ot_secret zur Abbruch-Bedingung des Handshakes, wie es das
        PAKE-Modell vorsieht.
        """
        assert self._master_secret is not None
        transcript = make_transcript(
            sid=self._sid,
            ik_pub_initiator=self._ik_pub_initiator,
            ik_pub_responder=ik_pub_responder,
            method=self._method.value,
            exp=self._exp,
        )
        session_key = hkdf_sha256(
            secret=self._master_secret,
            salt=self._sid,
            info=b"pair/v1",
            length=32,
        )
        return transcript + session_key

    def make_proof(self) -> bytes:
        """Erzeugt die Signatur ueber Transcript+session_key.

        Der Aufrufer schickt zusammen mit der Signatur auch den eigenen
        Public-Key an die Gegenseite (der ist dort noch nicht
        unbedingt bekannt - der Initiator lernt den Responder-Public-
        Key erst aus ingest_proof()).
        """
        expected = (
            "proof_verified_initiator"
            if self._role is PairingRole.INITIATOR
            else "pake_finished"
        )
        if self._state != expected:
            raise PairingError(f"make_proof() in falschem Zustand: {self._state}")

        ik_pub_r = (
            self._ik_pub_responder
            if self._ik_pub_responder is not None
            else self._our_pub
        )
        payload = self._proof_payload(ik_pub_r)
        sig = sign(self._our_priv, payload)
        self._state = "proof_made"
        return sig

    def ingest_proof(self, peer_public_key: bytes, peer_signature: bytes) -> None:
        """Verarbeitet Public-Key + Signatur der Gegenseite.

        Beim Initiator: Responder schickt zuerst seinen Proof. Hier
        wird `ik_pub_responder` gesetzt.
        Beim Responder: Initiator schickt seinen Proof als letzte
        Nachricht.
        """
        if self._role is PairingRole.INITIATOR:
            valid_states = ("pake_finished",)
        else:
            valid_states = ("proof_made",)
        if self._state not in valid_states:
            raise PairingError(
                f"ingest_proof() in falschem Zustand: {self._state}"
            )
        if len(peer_public_key) != 32:
            raise PairingError("peer_public_key muss 32 Byte sein")
        if len(peer_signature) != 64:
            raise PairingError("peer_signature muss 64 Byte sein (Ed25519)")

        if self._role is PairingRole.INITIATOR:
            self._ik_pub_responder = bytes(peer_public_key)
            expected_pub = self._ik_pub_responder
        else:
            expected_pub = self._ik_pub_initiator
            if bytes(peer_public_key) != expected_pub:
                raise PairingError(
                    "Initiator-Public-Key weicht von dem in der Einladung ab"
                )

        payload = self._proof_payload(
            self._ik_pub_responder or self._our_pub
        )
        if not verify(expected_pub, payload, peer_signature):
            raise PairingError(
                "Peer-Signatur ueber Transcript+session_key ungueltig "
                "(ot_secret falsch, Transcript manipuliert oder "
                "Identitaet stimmt nicht)"
            )

        self._state = (
            "proof_verified_initiator"
            if self._role is PairingRole.INITIATOR
            else "completed"
        )

    # ---- Phase 3: Abschluss ----

    def finalize(self) -> PairingResult:
        """Leitet den sync_psk ab und liefert das Ergebnis.

        Voraussetzung: PAKE und Proof sind durch. Auf Initiator-Seite
        bedeutet das, dass nach `ingest_proof()` noch einmal
        `make_proof()` gerufen wurde (damit der Responder auch
        verifizieren kann).
        """
        if self._role is PairingRole.INITIATOR:
            if self._state != "proof_made":
                raise PairingError(
                    f"finalize() (Initiator) in falschem Zustand: {self._state}"
                )
        else:
            if self._state != "completed":
                raise PairingError(
                    f"finalize() (Responder) in falschem Zustand: {self._state}"
                )

        assert self._master_secret is not None
        assert self._ik_pub_responder is not None

        ik_pub_initiator = self._ik_pub_initiator
        ik_pub_responder = self._ik_pub_responder

        # Info-Feld der HKDF ist die sortierte Konkatenation der beiden
        # Public-Keys - damit ergibt sich auf beiden Seiten *exakt*
        # derselbe sync_psk, unabhaengig davon, welche Seite "I" oder
        # "R" war.
        sorted_pub = b"".join(sorted([ik_pub_initiator, ik_pub_responder]))

        sync_psk = hkdf_sha256(
            secret=self._master_secret,
            salt=b"sync-psk",
            info=sorted_pub,
            length=32,
        )

        transcript = make_transcript(
            sid=self._sid,
            ik_pub_initiator=ik_pub_initiator,
            ik_pub_responder=ik_pub_responder,
            method=self._method.value,
            exp=self._exp,
        )
        th = transcript_hash(transcript)

        peer_pub = (
            ik_pub_responder
            if self._role is PairingRole.INITIATOR
            else ik_pub_initiator
        )
        self._state = "done"
        return PairingResult(
            peer_public_key=peer_pub,
            sync_psk=sync_psk,
            transcript_hash=th,
        )

    # ---- Diagnostik ----

    @property
    def state(self) -> str:
        return self._state


def run_pairing_in_memory(
    *,
    initiator_priv: bytes,
    initiator_pub: bytes,
    responder_priv: bytes,
    responder_pub: bytes,
    sid: bytes,
    ot_secret: bytes,
    method: PairingMethod = PairingMethod.QR,
    exp: int = 0,
) -> tuple[PairingResult, PairingResult]:
    """Hilfsfunktion fuer Tests / lokale Demos: spielt das volle
    Drei-Nachrichten-Protokoll zwischen zwei In-Memory-Sessions ab.

    Returns:
        (initiator_result, responder_result) - beide enthalten denselben
        sync_psk und transcript_hash, und jeweils den Public-Key der
        Gegenseite.
    """
    init = PairingSession(
        role=PairingRole.INITIATOR,
        our_private_key=initiator_priv,
        our_public_key=initiator_pub,
        peer_public_key_initiator=initiator_pub,
        sid=sid,
        ot_secret=ot_secret,
        method=method,
        exp=exp,
    )
    resp = PairingSession(
        role=PairingRole.RESPONDER,
        our_private_key=responder_priv,
        our_public_key=responder_pub,
        peer_public_key_initiator=initiator_pub,
        sid=sid,
        ot_secret=ot_secret,
        method=method,
        exp=exp,
    )

    msg1 = init.pake_start()        # I -> R: PAKE-Nachricht A
    msg2_pake = resp.pake_start()   # R: PAKE-Nachricht B vorbereiten
    init.pake_finish(msg2_pake)     # I: MS ableiten
    resp.pake_finish(msg1)          # R: MS ableiten

    # Responder schickt zuerst seinen Proof.
    sig_r = resp.make_proof()
    init.ingest_proof(responder_pub, sig_r)

    # Initiator antwortet mit seinem Proof.
    sig_i = init.make_proof()
    resp.ingest_proof(initiator_pub, sig_i)

    return init.finalize(), resp.finalize()
