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


DEFAULT_MAX_LOG_LINES = 5000


class _State:
    """Gemeinsamer Zustand zwischen allen Requests."""

    def __init__(self, log_path: Path, token: Optional[str],
                 max_log_lines: int = DEFAULT_MAX_LOG_LINES):
        self.log_path = log_path
        self.token = token
        self.max_log_lines = max_log_lines
        self.lock = threading.Lock()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("", encoding="utf-8")

    def compact_if_needed(self) -> int:
        """
        Wirft die aeltesten Eintraege weg, sobald der Log ueber
        max_log_lines Zeilen waechst. Liefert die Anzahl der entfernten
        Zeilen zurueck.
        """
        # Lock-Aufrufer haelt den Lock bereits - kein erneutes Acquire.
        text = self.log_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) <= self.max_log_lines:
            return 0
        keep = lines[-self.max_log_lines:]
        tmp = self.log_path.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(keep) + "\n", encoding="utf-8")
        tmp.replace(self.log_path)
        return len(lines) - len(keep)


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
            # Periodische Kompaktierung - mindestens einmal pro 100 Events
            # nachschauen, ob die weiche Obergrenze erreicht ist.
            try:
                self.state.compact_if_needed()
            except Exception:                              # pragma: no cover
                pass
        return self._send_json(201, {"status": "accepted"})

    # log-Meldungen unterdruecken
    def log_message(self, format, *args):                # noqa: A002, ANN001
        pass


def serve(log_path: Path, host: str, port: int,
          token: Optional[str],
          max_log_lines: int = DEFAULT_MAX_LOG_LINES) -> ThreadingHTTPServer:
    _Handler.state = _State(log_path, token, max_log_lines=max_log_lines)
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
    parser.add_argument("--max-log-lines", type=int,
                         default=DEFAULT_MAX_LOG_LINES,
                         help=("Weiche Obergrenze fuer Eintraege im Log; "
                                "danach wird automatisch kompaktiert."))
    args = parser.parse_args()

    server = serve(Path(args.log), args.host, args.port, args.token,
                    max_log_lines=args.max_log_lines)
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
