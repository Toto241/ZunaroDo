"""
Token-Issuer: PaymentEvent -> signiertes Lizenz-Token -> Mail.

Verbindet:
  - services.payment (provider-neutrales Event)
  - services.license_token (Ed25519-Signatur)
  - services.output.OutputService (Mail-Versand per SMTP)

Schreibt ausserdem ein lokales JSONL-Audit-Log mit allen ausgestellten
Tokens. Bezahldienstleister haben Webhook-Retries (manchmal Stunden),
also brauchen wir Idempotenz: ein Event mit derselben transaction_id
darf nicht zwei Tokens erzeugen.

Mail-Versand:
  Wird einfach gehalten - Klartext mit Anleitung, Token im Body
  (kopiert sich gut in das Eingabefeld der App). Anhaenge (PDF mit
  Rechnung etc.) liefert der Bezahldienstleister selbst.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Callable, Optional

from services.license_token import LicenseToken, sign_token
from services.licensing import Tier
from services.payment import EventKind, PaymentEvent

log = logging.getLogger(__name__)


@dataclass
class IssueResult:
    success: bool
    message: str
    token_str: Optional[str] = None
    mail_status: Optional[dict] = None


@dataclass
class IssuerConfig:
    """Anbieter-Konfiguration fuer die Token-Ausstellung."""

    private_key_hex: str             # Ed25519-Private-Key des Anbieters
    audit_log_path: Path              # JSONL mit allen Ausstellungen
    # SMTP-Versender: Funktion(to_addr, subject, body) -> dict
    # Erlaubt Test ohne echten SMTP-Server.
    send_mail: Optional[Callable[..., dict]] = None
    mail_subject_template: str = "Ihre Pro-Lizenz fuer ZunaroDo"
    app_name: str = "ZunaroDo"


def handle_event(event: PaymentEvent,
                  config: IssuerConfig,
                  *,
                  dedupe: bool = True) -> IssueResult:
    """
    Verarbeitet ein PaymentEvent.

    - SUBSCRIPTION_CREATED, ONE_TIME_PURCHASE, SUBSCRIPTION_RENEWED:
      Token signieren + Mail
    - SUBSCRIPTION_CANCELED, REFUND: nichts ausstellen, nur Audit
    - Idempotenz (nur bei dedupe=True): bereits verarbeitete
      transaction_ids werden geloggt und uebersprungen (return
      success=True, damit der Provider den Webhook nicht ewig retried);
      parallele Retries werden ueber _inflight serialisiert.

    `dedupe`:
      True  (Default) fuer asynchrone Webhooks (Paddle/Lemon): das Token
            wird per Mail zugestellt, der HTTP-Response transportiert es
            NICHT. Doppelt-Ausstellen wuerde doppelte Mails/Lizenzen
            bedeuten -> Idempotenz + In-Flight-Claim.
      False fuer den synchronen Play-Pfad (/verify/play): das Token IST
            die HTTP-Antwort. Hier darf der De-Dup-Kurzschluss NICHT
            greifen - sonst bekaeme ein paralleler/erneuter Aufruf eine
            201-Erfolgsantwort OHNE Token und der Client koennte die Lizenz
            nie aktivieren. Erneutes Ausstellen ist hier unbedenklich, weil
            jeder Aufruf den Kauf zuvor frisch gegen Google verifiziert.
    """
    tx_key = (event.provider, event.transaction_id)
    claimed = False
    # Atomar gegen das Audit-Log UND gegen parallele Retries pruefen und
    # die Transaktion "claimen", bevor irgendetwas ausgestellt wird.
    if dedupe:
        with _audit_lock:
            try:
                if _already_processed(event, config.audit_log_path):
                    log.info("Webhook %s/%s bereits verarbeitet - skip",
                             event.provider, event.transaction_id)
                    return IssueResult(success=True,
                                       message="bereits verarbeitet")
            except OSError:
                log.warning("Audit-Log %s nicht lesbar - Event wird "
                            "abgelehnt, damit der Provider erneut zustellt",
                            config.audit_log_path)
                return IssueResult(
                    success=False,
                    message="Audit-Log nicht lesbar - bitte erneut zustellen")
            if event.transaction_id and tx_key in _inflight:
                # Paralleler Retry derselben Transaktion ist bereits in Arbeit.
                log.info("Webhook %s/%s wird bereits parallel verarbeitet "
                         "- skip", event.provider, event.transaction_id)
                return IssueResult(success=True,
                                   message="wird bereits verarbeitet")
            if event.transaction_id:
                _inflight.add(tx_key)
                claimed = True

    try:
        if event.kind in (EventKind.SUBSCRIPTION_CANCELED, EventKind.REFUND):
            _append_audit(config.audit_log_path,
                          event=event, token_str=None, mail_status=None,
                          note=f"Kein Token ausgestellt (kind={event.kind.value})")
            return IssueResult(success=True,
                                message=f"{event.kind.value} - kein Token")

        if event.tier not in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL,
                                Tier.PRO_FAMILY):
            return IssueResult(
                success=False,
                message=f"Tier {event.tier} ist nicht zahlpflichtig")

        now = datetime.now(timezone.utc)
        token = LicenseToken(
            tier=event.tier,
            persons=event.persons,
            purchased_at=now,
            expires_at=event.expires_at,
            customer_id=event.customer_email,  # bewusst Mail als Reference
            platform=event.platform,
        )
        try:
            token_str = sign_token(token, config.private_key_hex)
        except Exception as exc:                        # noqa: BLE001
            log.exception("Token-Signatur fehlgeschlagen")
            return IssueResult(
                success=False,
                message=f"Token konnte nicht signiert werden: {exc}")

        mail_status: Optional[dict] = None
        if config.send_mail is not None:
            subject = config.mail_subject_template
            body = _build_mail_body(event, token_str, app_name=config.app_name)
            try:
                mail_status = config.send_mail(event.customer_email,
                                                subject, body)
            except Exception as exc:                    # noqa: BLE001
                log.exception("Mail-Versand fehlgeschlagen")
                mail_status = {"status": "fehler", "error": str(exc)}

        _append_audit(config.audit_log_path,
                      event=event, token_str=token_str,
                      mail_status=mail_status, note="ok")
        return IssueResult(success=True,
                            message="Token ausgestellt",
                            token_str=token_str,
                            mail_status=mail_status)
    finally:
        if claimed:
            with _audit_lock:
                _inflight.discard(tx_key)


# ---------------------------------------------------------------------
# Mail-Template
# ---------------------------------------------------------------------
def _build_mail_body(event: PaymentEvent,
                      token_str: str,
                      *,
                      app_name: str) -> str:
    return f"""Hallo,

vielen Dank fuer den Kauf einer {_tier_text(event.tier)}-Lizenz fuer
{app_name}. Im Folgenden findest du deinen Aktivierungs-Token.

So aktivierst du:

  1. Oeffne {app_name}.
  2. Wechsle in den Tab 'Einstellungen'.
  3. Scrolle zu 'Lizenz' und fuege den Token unten ein.
  4. Klicke auf 'Aktivieren'.

Token (in einer Zeile, vollstaendig einfuegen):

{token_str}

Gueltig bis: {event.expires_at.date().isoformat()}
Personen:    {event.persons}

Bei Fragen einfach auf diese Mail antworten.

Viele Gruesse
{app_name}-Team
"""


def _tier_text(tier: Tier) -> str:
    return {
        Tier.PRO_MONTHLY: "Pro-Monats",
        Tier.PRO_ANNUAL: "Pro-Jahres",
        Tier.PRO_FAMILY: "Pro-Familien",
    }.get(tier, str(tier))


# ---------------------------------------------------------------------
# Audit-Log + Idempotenz
# ---------------------------------------------------------------------
_audit_lock = Lock()
# Transaktionen, die gerade (in diesem Prozess) verarbeitet werden, aber
# noch nicht im Audit-Log stehen. Schliesst das Zeitfenster zwischen
# Idempotenz-Pruefung und Audit-Append, in dem zwei parallele Webhook-
# Retries (ThreadingHTTPServer!) beide den Check passieren und doppelt
# ausstellen wuerden. Immer unter _audit_lock zugreifen.
_inflight: set[tuple[str, str]] = set()


def _already_processed(event: PaymentEvent, log_path: Path) -> bool:
    """True, wenn die transaction_id bereits im Audit-Log steht.

    Wirft OSError weiter (NICHT mehr fail-open): kann das Log nicht gelesen
    werden, darf der Aufrufer NICHT einfach ausstellen - sonst koennte ein
    voruebergehender Lesefehler (Datei gesperrt, Platte voll) Duplikate
    erzeugen. Der Aufrufer behandelt OSError als "kann nicht bestaetigen".
    """
    if not log_path.exists() or not event.transaction_id:
        return False
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (entry.get("provider") == event.provider
                    and entry.get("transaction_id")
                    == event.transaction_id):
                return True
    return False


def _append_audit(log_path: Path,
                   *,
                   event: PaymentEvent,
                   token_str: Optional[str],
                   mail_status: Optional[dict],
                   note: str) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "provider": event.provider,
        "transaction_id": event.transaction_id,
        "kind": event.kind.value,
        "customer_email": event.customer_email,
        "tier": event.tier.value,
        "persons": event.persons,
        "expires_at": event.expires_at.isoformat(),
        "token_issued": token_str is not None,
        "mail_status": mail_status,
        "note": note,
    }
    with _audit_lock:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
