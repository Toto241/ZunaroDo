"""
Negativtests Block B - Netzwerk- und Synchronisationsfehler
(TESTING.md Abschnitt 11.3 B).

Wir testen den HttpSyncProvider und das FileSyncProvider-Pendant gegen:

  N-B-01  kein Internet           (HTTP-URL nicht erreichbar)
  N-B-04  Server-Fehler 500       (Provider darf nicht crashen)
  N-B-06  Offline-Edit + Sync     (Datei-Replay ohne Datenverlust)
  N-B-07  Konflikt LWW            (LWW ueber Lamport+real_time+device)

Die Tests benutzen einen synthetischen In-Memory-HTTP-Server bzw.
einen geteilten Dateipfad als Sync-Ort. Es findet KEINE echte
Netzkommunikation statt.
"""
from __future__ import annotations

import http.server
import socket
import socketserver
import threading
from pathlib import Path

import pytest

from services.sync import (FileSyncProvider, HttpSyncProvider, LamportClock,
                            SyncEvent)


pytestmark = [pytest.mark.concept, pytest.mark.negative]


# ---------------------------------------------------------------------------
# Hilfsklassen
# ---------------------------------------------------------------------------
class _FailingHandler(http.server.BaseHTTPRequestHandler):
    """Antwortet immer mit 500."""
    def log_message(self, *args, **kwargs): pass     # quiet
    def do_GET(self):
        self.send_response(500); self.end_headers()
        self.wfile.write(b"boom")
    def do_POST(self):
        self.send_response(500); self.end_headers()
        self.wfile.write(b"boom")


class _GarbageHandler(http.server.BaseHTTPRequestHandler):
    """Antwortet mit 200, aber komplett kaputtem Body (HTML statt JSON)."""
    def log_message(self, *args, **kwargs): pass
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"<html>nope</html>")
    def do_POST(self):
        self.send_response(200); self.end_headers()


def _start_server(handler_cls) -> tuple[socketserver.TCPServer, str]:
    sock = socket.socket(); sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]; sock.close()
    server = socketserver.TCPServer(("127.0.0.1", port), handler_cls)
    server.timeout = 1
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, f"http://127.0.0.1:{port}"


def _event(ev_id: str = "ev-1") -> SyncEvent:
    return SyncEvent(event_id=ev_id, device_id="dev-A",
                      lamport=1, timestamp="2026-05-20T10:00:00Z",
                      capability="family.add_member",
                      args={"name": "Anna"})


# ---------------------------------------------------------------------------
# N-B-01: Server nicht erreichbar
# ---------------------------------------------------------------------------
def test_NB01_unreachable_server_does_not_corrupt_state(tmp_path: Path):
    """Provider gegen Port 1 (immer unreachable). append darf eine
    URLError werfen, MUSS aber das lokale State-File konsistent lassen
    und unseen_events() darf keine falschen Events liefern."""
    provider = HttpSyncProvider(
        base_url="http://127.0.0.1:1",
        device_id="dev-X",
        local_state_path=tmp_path / "sync_seen.json")
    with pytest.raises(Exception):
        provider.append(_event())
    # State-File ist entweder noch nicht da (Default) oder leer/sauber
    seen_file = tmp_path / "sync_seen.json"
    if seen_file.exists():
        text = seen_file.read_text(encoding="utf-8")
        assert "ev-1" not in text, (
            "Fehlgeschlagenes append darf das Event nicht als 'seen' "
            "markieren")


# ---------------------------------------------------------------------------
# N-B-04 Server 500
# ---------------------------------------------------------------------------
def test_NB04_server_500_does_not_silently_succeed(tmp_path: Path):
    server, base = _start_server(_FailingHandler)
    try:
        provider = HttpSyncProvider(
            base_url=base, device_id="dev-X",
            local_state_path=tmp_path / "sync_seen.json")
        with pytest.raises(Exception):
            provider.append(_event("ev-500"))
    finally:
        server.shutdown()


def test_NB04_garbage_response_is_handled(tmp_path: Path):
    """Server liefert HTML statt JSON -> Aufrufer muss das als Fehler
    erkennen, nicht stillschweigend leere Liste produzieren."""
    server, base = _start_server(_GarbageHandler)
    try:
        provider = HttpSyncProvider(
            base_url=base, device_id="dev-X",
            local_state_path=tmp_path / "sync_seen.json")
        with pytest.raises(Exception):
            provider.unseen_events()
    finally:
        server.shutdown()


# ---------------------------------------------------------------------------
# N-B-06 Offline-Edit + Datei-Sync (FileProvider als Stand-in)
# ---------------------------------------------------------------------------
def test_NB06_offline_then_sync_round_trips_events(tmp_path: Path):
    sync_dir = tmp_path / "sync"; sync_dir.mkdir()
    a = FileSyncProvider(
        sync_dir=str(sync_dir), device_id="A",
        local_seen_path=tmp_path / "sa.json")
    b = FileSyncProvider(
        sync_dir=str(sync_dir), device_id="B",
        local_seen_path=tmp_path / "sb.json")

    # B schreibt ein Event, A sieht es noch nicht
    b.append(SyncEvent(event_id="e1", device_id="B", lamport=1,
                        timestamp="2026-05-20T10:00:00Z",
                        capability="family.add_member",
                        args={"name": "Bobo"}))
    unseen = a.unseen_events()
    assert any(e.event_id == "e1" for e in unseen)
    a.mark_seen("e1")
    assert all(e.event_id != "e1" for e in a.unseen_events())


def test_NB06_corrupt_log_lines_are_skipped(tmp_path: Path):
    """Eine kaputte Zeile im JSONL-Log darf den gesamten Sync nicht
    sprengen - die fehlerhafte Zeile wird uebersprungen."""
    sync_dir = tmp_path / "sync"; sync_dir.mkdir()
    log = sync_dir / "sync_events.jsonl"
    log.write_text(
        '{"event_id":"good","device_id":"A","lamport":1,'
        '"timestamp":"2026-05-20T10:00:00Z","capability":"x","args":{}}\n'
        'NICHT_JSON_KAPUTT_KAPUTT_KAPUTT\n'
        '{"event_id":"good2","device_id":"A","lamport":2,'
        '"timestamp":"2026-05-20T10:00:02Z","capability":"x","args":{}}\n',
        encoding="utf-8")
    provider = FileSyncProvider(
        sync_dir=str(sync_dir), device_id="B",
        local_seen_path=tmp_path / "s.json")
    events = provider.read_all()
    assert {e.event_id for e in events} == {"good", "good2"}


# ---------------------------------------------------------------------------
# N-B-07 Last-Write-Wins-Konflikt
# ---------------------------------------------------------------------------
def test_NB07_lww_orders_by_lamport_then_time(tmp_path: Path):
    sync_dir = tmp_path / "sync"; sync_dir.mkdir()
    a = FileSyncProvider(sync_dir=str(sync_dir), device_id="A",
                          local_seen_path=tmp_path / "sa.json")
    b = FileSyncProvider(sync_dir=str(sync_dir), device_id="B",
                          local_seen_path=tmp_path / "sb.json")
    e1 = SyncEvent(event_id="x", device_id="A", lamport=1,
                    timestamp="2026-05-20T10:00:00Z",
                    capability="contracts.update_cost",
                    args={"contract_id": 1, "new_cost": 9.99})
    e2 = SyncEvent(event_id="y", device_id="B", lamport=2,
                    timestamp="2026-05-20T10:00:01Z",
                    capability="contracts.update_cost",
                    args={"contract_id": 1, "new_cost": 12.50})
    a.append(e1)
    b.append(e2)

    everyone = sorted(a.read_all(), key=lambda e: e.order_key())
    assert everyone[-1].args["new_cost"] == 12.50, (
        "Letzter Schreibvorgang (LWW) muss gewinnen")


# ---------------------------------------------------------------------------
# LamportClock-Negativtests
# ---------------------------------------------------------------------------
def test_lamport_observe_clamps_negative_input():
    clock = LamportClock(initial=5)
    # Negative oder None-aehnliche Werte sind reale Inputs aus kaputten
    # Events. Sie duerfen den Lokal-Wert nicht zurueckdrehen.
    clock.observe(-100)
    assert clock.value >= 5
    clock.observe(0)
    assert clock.value >= 6
    clock.observe(999_999)
    assert clock.value >= 1_000_000


def test_sync_event_from_dict_handles_missing_fields():
    """SyncEvent.from_dict mit unvollstaendigem Dict darf ohne Crash
    arbeiten ODER eine klar deklarierte Exception werfen."""
    try:
        SyncEvent.from_dict({"event_id": "x"})
    except (KeyError, TypeError, ValueError):
        pass  # explizit erkannter Fehler ist OK
