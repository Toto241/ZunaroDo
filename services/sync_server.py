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
# Rate-Limit: maximal so viele POST-Requests pro IP innerhalb des
# Sliding-Window von DEFAULT_RATE_WINDOW_SEC Sekunden. Konservativ
# gewaehlt - ein normales Geraet erzeugt vielleicht 1 Event pro Minute.
DEFAULT_RATE_LIMIT = 60
DEFAULT_RATE_WINDOW_SEC = 60


class _State:
    """Gemeinsamer Zustand zwischen allen Requests."""

    def __init__(self, log_path: Path, token: Optional[str],
                 max_log_lines: int = DEFAULT_MAX_LOG_LINES,
                 rate_limit: int = DEFAULT_RATE_LIMIT,
                 rate_window_sec: int = DEFAULT_RATE_WINDOW_SEC):
        self.log_path = log_path
        self.token = token
        self.max_log_lines = max_log_lines
        self.rate_limit = max(1, rate_limit)
        self.rate_window_sec = max(1, rate_window_sec)
        self.lock = threading.Lock()
        # Pro Client-IP eine Liste von Timestamps der letzten POSTs.
        # Sliding-Window: alles aelter als rate_window_sec wird verworfen.
        self._request_log: dict[str, list[float]] = {}
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("", encoding="utf-8")

    def check_rate(self, client_ip: str) -> bool:
        """True = unter dem Limit, False = abgelehnt."""
        import time as _time
        now = _time.time()
        cutoff = now - self.rate_window_sec
        with self.lock:
            timestamps = self._request_log.setdefault(client_ip, [])
            # Alte Eintraege wegwerfen
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)
            if len(timestamps) >= self.rate_limit:
                return False
            timestamps.append(now)
            return True

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
        # Rate-Limit pro Client-IP: schuetzt auch vor einem
        # kompromittierten Geraet, das den Log mit Muell fluten will (B).
        client_ip = self.client_address[0] if self.client_address else "?"
        if not self.state.check_rate(client_ip):
            return self._send_json(429, {"error": "rate limit exceeded"})
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
          max_log_lines: int = DEFAULT_MAX_LOG_LINES,
          certfile: Optional[str] = None,
          keyfile: Optional[str] = None,
          rate_limit: int = DEFAULT_RATE_LIMIT,
          rate_window_sec: int = DEFAULT_RATE_WINDOW_SEC) -> ThreadingHTTPServer:
    """
    Startet den Sync-Server (ungebunden, der Aufrufer muss
    serve_forever() ausfuehren).

    Wenn 'certfile' UND 'keyfile' gesetzt sind, wird das Listening-
    Socket per TLS verschluesselt. Ohne diese Parameter laeuft der
    Server unverschluesselt - dann auf 127.0.0.1 binden ODER Token
    setzen ODER beides.

    Rate-Limit: max 'rate_limit' POSTs pro Client-IP im Sliding-Window
    'rate_window_sec' Sekunden. Schuetzt vor einem kompromittierten
    Geraet, das den Log voll spammen will.
    """
    _Handler.state = _State(log_path, token, max_log_lines=max_log_lines,
                              rate_limit=rate_limit,
                              rate_window_sec=rate_window_sec)
    server = ThreadingHTTPServer((host, port), _Handler)
    if certfile and keyfile:
        import ssl
        try:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
            server.socket = ctx.wrap_socket(server.socket, server_side=True)
        except BaseException:
            # Bei jedem Fehler im TLS-Setup (fehlende Datei, falsches
            # Passwort etc.) muss das frisch geoeffnete Listening-Socket
            # wieder geschlossen werden - sonst leakt es bis zum
            # naechsten GC.
            server.server_close()
            raise
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
    parser.add_argument("--cert", default=None,
                         help="Pfad zum TLS-Zertifikat (PEM)")
    parser.add_argument("--key", default=None,
                         help="Pfad zum privaten TLS-Schluessel (PEM)")
    parser.add_argument("--self-signed", action="store_true",
                         help="Erzeugt bei Bedarf ein selbstsigniertes "
                              "Zertifikat unter --cert/--key (Default: "
                              "./sync-cert.pem / ./sync-key.pem) und nutzt es.")
    args = parser.parse_args()

    if args.self_signed:
        # Default-Pfade, falls nicht angegeben; dann Cert bei Bedarf erzeugen.
        args.cert = args.cert or "sync-cert.pem"
        args.key = args.key or "sync-key.pem"
        from services.tls_certs import generate_self_signed_cert
        generate_self_signed_cert(args.cert, args.key, common_name=args.host)

    if bool(args.cert) != bool(args.key):
        parser.error("--cert UND --key muessen gemeinsam gesetzt sein")

    server = serve(Path(args.log), args.host, args.port, args.token,
                    max_log_lines=args.max_log_lines,
                    certfile=args.cert, keyfile=args.key)
    scheme = "https" if args.cert else "http"
    print(f"Sync-Server laeuft auf {scheme}://{args.host}:{args.port}")
    print(f"Log:    {args.log}")
    print(f"Token:  {'gesetzt' if args.token else '(keiner)'}")
    print(f"TLS:    {'aktiv' if args.cert else 'aus'}")
    if not args.token:
        # Auf nicht-lokale Bind-Adressen ist das ein echtes Sicherheits-
        # problem - der Endpunkt akzeptiert sonst beliebige Schreibzugriffe
        # auf den geteilten Log. Auf 127.0.0.1 nur ein Hinweis.
        is_local_only = args.host in ("127.0.0.1", "localhost", "::1")
        if is_local_only:
            print("Hinweis: Ohne Token nur fuer Tests auf 127.0.0.1 nutzen.")
        else:
            print("WARNUNG: Server bindet auf eine OEFFENTLICHE Adresse "
                  f"({args.host}) OHNE Token. Jeder, der den Port erreicht, "
                  "kann Events einspeisen. Entweder --token setzen oder "
                  "auf 127.0.0.1 binden.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server beendet.")
        server.shutdown()


if __name__ == "__main__":
    main()
