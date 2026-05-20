"""
Pro-Aktivierungs-Flow mit Widerrufsverzicht (BGB §356 Abs. 5).

Funktionsweise:
  1. Der Nutzer waehlt einen Pro-Tier (z.B. PRO_ANNUAL).
  2. Vor der Aktivierung muss er **explizit zustimmen**, dass:
     - er die AGB und Datenschutzerklaerung gelesen hat
     - die Ausfuehrung des Vertrags vor Ablauf der 14-Tage-Frist
       beginnen soll
     - er weiss, dass er damit sein Widerrufsrecht verliert
  3. Ohne diese drei Bestaetigungen verweigert die App die Aktivierung.

Der Flow ist GUI-agnostisch - die GUI ruft 'request_activation()' mit
einer Confirm-Callback auf, die einen Bool zurueckgibt. So koennen
Headless-Tests dieselbe Logik durchlaufen wie das tatsaechliche
Dialog-Fenster.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from database import SettingsRepository
from services.licensing import (KEY_WITHDRAWAL_WAIVED, License, Tier,
                                  activate_pro, load_license)

log = logging.getLogger(__name__)


# Text der drei Bestaetigungen - die GUI rendert sie als Checkboxen,
# alle drei muessen aktiv sein, damit 'confirmed' True zurueckgibt.
CONFIRMATIONS_DE = (
    "Ich habe die AGB und die Datenschutzerklaerung gelesen und "
    "akzeptiere beide.",
    "Ich stimme zu, dass die Ausfuehrung des Vertrags sofort beginnt - "
    "noch vor Ablauf der 14-taegigen Widerrufsfrist.",
    "Ich habe verstanden, dass ich durch diese Zustimmung mein "
    "gesetzliches Widerrufsrecht (§356 Abs. 5 BGB) verliere.",
)


@dataclass
class ActivationRequest:
    tier: Tier
    persons: int
    customer_id: str = ""


@dataclass
class ActivationResult:
    success: bool
    license: Optional[License] = None
    error: Optional[str] = None


def request_activation(repo: SettingsRepository,
                        request: ActivationRequest,
                        confirm_callback: Callable[
                            [ActivationRequest, tuple[str, ...]], bool
                        ],
                        *,
                        now: Optional[datetime] = None) -> ActivationResult:
    """
    Fragt die drei Widerrufs-Bestaetigungen ab und aktiviert die
    Lizenz nur dann, wenn alle drei akzeptiert wurden.

    'confirm_callback' bekommt das Request-Objekt und die drei
    Texte und liefert True/False zurueck.
    """
    if request.tier not in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL,
                              Tier.PRO_FAMILY):
        return ActivationResult(
            success=False,
            error=f"{request.tier.value} ist kein zahlungspflichtiger Tier")

    try:
        confirmed = bool(confirm_callback(request, CONFIRMATIONS_DE))
    except Exception as exc:                            # noqa: BLE001
        log.exception("Confirm-Callback in request_activation hat eine "
                      "Ausnahme ausgeloest")
        return ActivationResult(success=False,
                                  error=f"Confirm-Callback hat geworfen: {exc}")

    if not confirmed:
        return ActivationResult(
            success=False,
            error="Aktivierung abgebrochen - Widerrufsverzicht nicht erklaert")

    # Widerruf wurde wirksam erklaert -> Activate
    lic = activate_pro(repo, request.tier, request.persons, now=now)
    # Verzicht im Setting markieren - so kann spaeter rechtlich
    # nachgewiesen werden, wann die App den Verzicht eingeholt hat.
    repo.set(KEY_WITHDRAWAL_WAIVED, "true")
    lic.withdrawal_waived = True
    return ActivationResult(success=True, license=lic)
