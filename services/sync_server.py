"""
Kleiner HTTP-Sync-Server fuer den Alltagshelfer.

Alternative zu FileSyncProvider, wenn kein geteilter Ordner verfuegbar
ist. Bewusst Minimal-Implementierung mit dem Python-stdlib http.server.

Endpoints (alle JSON):
  GET  /events            -> liefert alle Events (chronologisch)
  GET  /events?since=N    -> Events ab Index N
  POST /events            -> haengt ein Event an, Body = SyncEvent-Dict
  GET  /health            -> { "ok": true }

Auth: Optional ein gemeinsames Bearer-Token via Header 'X-Sync-Token'.
Wird per Umgebungsvariable ALLTAGSHELFER_SYNC_TOKEN gesetzt; im Client
ebenfalls.

Bewusst out of scope:
  - HTTPS (sollte hinter einem Reverse-Proxy laufen)
  - Mehr-Mandanten / Familien-Trennung (ein Server, ein Haushalt)

So startest du den Server:

    python -m services.sync_server --host 0.0.0.0 --port 5151

und im Client:

    ALLTAGSHELFER_SYNC_URL=http://server:5151 python gui.py
"""
from __future__ import annotations

import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional


class _State:
    """Gemeinsamer Zustand zwischen allen Requests."""

    def __init__(self, log_path: Path, token: Optional[str]):
        self.log_path = log_path
        self.token = token
        self.lock = threading.Lock()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("", encoding="utf-8")


class _Handler(BaseHTTPRequestHandler):
    state: _State                        # wird vor dem Start gesetzt

    # ---- Hilfsfunktionen ---------------------------------------------
    def _check_token(self) -> bool:
        if not self.state.token:
            return True
        provided = self.headers.get("X-Sync-Token", "")
        return provided == self.state.token

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- GET ----------------------------------------------------------
    def do_GET(self) -> None:                            # noqa: N802
        if not self._check_token():
            return self._send_json(401, {"error": "unauthorized"})
        if self.path.startswith("/health"):
            return self._send_json(200, {"ok": True})
        if self.path.startswith("/events"):
            since = 0
            if "since=" in self.path:
                try:
                    since = int(self.path.split("since=", 1)[1].split("&")[0])
                except ValueError:
                    since = 0
            with self.state.lock:
                lines = self.state.log_path.read_text(
                    encoding="utf-8").splitlines()
            events = []
            for line in lines[since:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return self._send_json(200, {"total": len(lines), "events": events})
        return self._send_json(404, {"error": "not found"})

    # ---- POST ---------------------------------------------------------
    def do_POST(self) -> None:                           # noqa: N802
        if not self._check_token():
            return self._send_json(401, {"error": "unauthorized"})
        if self.path != "/events":
            return self._send_json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return self._send_json(400, {"error": "invalid json"})
        required = {"event_id", "device_id", "timestamp", "capability"}
        if not required.issubset(payload.keys()):
            return self._send_json(400, {"error": "missing fields"})
        with self.state.lock:
            with self.state.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return self._send_json(201, {"status": "accepted"})

    # log-Meldungen unterdruecken
    def log_message(self, format, *args):                # noqa: A002, ANN001
        pass


def serve(log_path: Path, host: str, port: int,
          token: Optional[str]) -> ThreadingHTTPServer:
    _Handler.state = _State(log_path, token)
    server = ThreadingHTTPServer((host, port), _Handler)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Alltagshelfer-Sync-Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5151)
    parser.add_argument("--log", default="sync_events.jsonl",
                         help="Pfad zur Log-Datei auf dem Server")
    parser.add_argument("--token",
                         default=os.environ.get("ALLTAGSHELFER_SYNC_TOKEN"),
                         help="Optionales Bearer-Token (Header X-Sync-Token)")
    args = parser.parse_args()

    server = serve(Path(args.log), args.host, args.port, args.token)
    print(f"Sync-Server laeuft auf http://{args.host}:{args.port}")
    print(f"Log:    {args.log}")
    print(f"Token:  {'gesetzt' if args.token else '(keiner)'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server beendet.")
        server.shutdown()


if __name__ == "__main__":
    main()
