"""
HTTP-Webhook-Server fuer Paddle und Lemon Squeezy.

Endpoints:
  POST /webhook/paddle           Paddle-Billing
  POST /webhook/lemon_squeezy   Lemon Squeezy
  POST /verify/play              Google Play Billing (App schickt Token,
                                  Server verifiziert + gibt Lizenz zurueck)
  GET  /health                    Liveness-Probe (200 'ok')

Sicherheit:
  - HMAC-Verifikation pro Adapter (verifiziert mit dem jeweiligen
    Webhook-Secret des Anbieters).
  - Wir empfehlen, hinter einem Reverse-Proxy mit TLS zu betreiben
    (Nginx/Caddy) - der eingebaute Server kann TLS, das ist aber
    primaer fuer lokale Tests gedacht.

Antworten:
  - 200/201: Webhook akzeptiert (auch wenn 'ignoriert', damit der
    Anbieter den Webhook nicht retried).
  - 400:    Body kaputt oder unbekannte Preis-ID.
  - 401:    HMAC-Verifikation fehlgeschlagen.
  - 500:    Issuer-Fehler (Token konnte nicht signiert werden o.ae.).

Der Server ist absichtlich dünn - er routet, prueft Signaturen,
delegiert an Adapter + Issuer. Keine Persistenz, kein State.
"""
from __future__ import annotations

import json
import logging
import ssl
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from services.payment import (PriceMapping, SignatureError, UnknownPriceError,
                                WebhookContext, WebhookError)
from services.payment_adapter_play import (PlaySkuMapping, PlayVerifier,
                                           parse_play_purchase)
from services.payment_issuer import IssuerConfig, handle_event

log = logging.getLogger(__name__)


@dataclass
class WebhookServerConfig:
    """Konfiguration eines Webhook-Endpoints (pro Provider)."""

    secret: str               # Webhook-Signing-Secret beim Anbieter
    price_mapping: PriceMapping  # variant_id/price_id -> (tier, persons)
    parser: callable           # services.payment_adapter_*.parse_event


@dataclass
class PlayVerifyConfig:
    """Konfiguration des /verify/play-Endpoints (Google Play Billing)."""

    package_name: str
    sku_mapping: PlaySkuMapping
    verifier: PlayVerifier
    # Eigener Issuer (typischerweise mit send_mail=None) - die Lizenz
    # geht als HTTP-Antwort an die App zurueck, nicht per Mail.
    issuer: IssuerConfig


@dataclass
class _State:
    paddle: Optional[WebhookServerConfig]
    lemon: Optional[WebhookServerConfig]
    issuer: IssuerConfig
    play: Optional[PlayVerifyConfig] = None


class _Handler(BaseHTTPRequestHandler):
    state: _State                        # wird vor dem Start gesetzt

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(length) if length > 0 else b""

    def _gather_headers(self) -> dict[str, str]:
        # http.server liefert HTTPMessage - in einfaches dict packen
        return {k: v for k, v in self.headers.items()}

    def do_GET(self) -> None:                            # noqa: N802
        if self.path.startswith("/health"):
            return self._send_json(200, {"ok": True})
        return self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:                           # noqa: N802
        if self.path == "/verify/play":
            return self._handle_play()
        if self.path == "/webhook/paddle":
            cfg = self.state.paddle
        elif self.path == "/webhook/lemon_squeezy":
            cfg = self.state.lemon
        else:
            return self._send_json(404, {"error": "not found"})
        if cfg is None:
            return self._send_json(404,
                                     {"error": "provider not configured"})

        ctx = WebhookContext(
            raw_body=self._read_body(),
            headers=self._gather_headers(),
            signing_secret=cfg.secret,
            price_mapping=cfg.price_mapping,
        )
        try:
            event = cfg.parser(ctx)
        except SignatureError as exc:
            log.warning("Webhook %s signature rejected: %s", self.path, exc)
            return self._send_json(401, {"error": "unauthorized"})
        except UnknownPriceError as exc:
            log.warning("Webhook %s unknown price: %s", self.path, exc)
            return self._send_json(400, {"error": str(exc)})
        except WebhookError as exc:
            log.warning("Webhook %s parse error: %s", self.path, exc)
            return self._send_json(400, {"error": str(exc)})
        except Exception as exc:                        # noqa: BLE001
            log.exception("Webhook %s unhandled error", self.path)
            return self._send_json(500, {"error": "internal", "detail": str(exc)})

        if event is None:
            # Uninteressantes Event - 200, damit Provider nicht retried.
            return self._send_json(200, {"status": "ignored"})

        result = handle_event(event, self.state.issuer)
        if not result.success:
            return self._send_json(500, {"error": result.message})
        return self._send_json(201,
                                 {"status": "ok",
                                  "message": result.message,
                                  "mail_status": result.mail_status})

    def _handle_play(self) -> None:
        """Verifiziert einen Play-Purchase-Token und gibt die Lizenz zurueck.

        Im Gegensatz zu den Webhooks wird das signierte Token NICHT
        gemailt, sondern direkt im HTTP-Body an die App zurueckgegeben -
        die App wendet es dann lokal an (apply_token_to_repo).
        """
        cfg = self.state.play
        if cfg is None:
            return self._send_json(404, {"error": "play not configured"})
        try:
            payload = json.loads(self._read_body().decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._send_json(400, {"error": f"bad json: {exc}"})

        try:
            event = parse_play_purchase(
                payload,
                package_name=cfg.package_name,
                sku_mapping=cfg.sku_mapping,
                verifier=cfg.verifier,
            )
        except UnknownPriceError as exc:
            return self._send_json(400, {"error": str(exc)})
        except WebhookError as exc:
            return self._send_json(400, {"error": str(exc)})
        except Exception as exc:                          # noqa: BLE001
            log.exception("/verify/play unhandled error")
            return self._send_json(500, {"error": "internal", "detail": str(exc)})

        if event is None:
            # Token ungueltig/abgelaufen - kein false-positive ausstellen.
            return self._send_json(402, {"error": "purchase not valid"})

        result = handle_event(event, cfg.issuer)
        if not result.success:
            return self._send_json(500, {"error": result.message})
        return self._send_json(201, {"status": "ok", "token": result.token_str})

    # Default-Logger ist sehr gespraechig; auf Python-Logger umlenken
    def log_message(self, format, *args):                # noqa: A002, ANN001
        log.info("payment-server %s - %s",
                 self.client_address[0] if self.client_address else "?",
                 format % args)


def serve(host: str,
          port: int,
          *,
          paddle: Optional[WebhookServerConfig],
          lemon: Optional[WebhookServerConfig],
          issuer: IssuerConfig,
          play: Optional[PlayVerifyConfig] = None,
          certfile: Optional[str] = None,
          keyfile: Optional[str] = None) -> ThreadingHTTPServer:
    """Startet den Webhook-Server (Aufrufer muss serve_forever() rufen)."""
    if paddle is None and lemon is None and play is None:
        raise ValueError("Mindestens ein Provider muss konfiguriert sein")
    _Handler.state = _State(paddle=paddle, lemon=lemon, issuer=issuer,
                            play=play)
    server = ThreadingHTTPServer((host, port), _Handler)
    if certfile and keyfile:
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
    return server
