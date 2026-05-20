"""
Lizenz-Ereignisse fuer den proaktiven Scheduler.

Damit der Nutzer rechtzeitig vor Trial-Ende oder Abo-Ablauf gewarnt
wird, liefert dieses Modul Event-Objekte im selben Format wie die
Fachmodule (models.Event). Der ProactiveScheduler bekommt diese
Events ueber einen optionalen 'extra_event_sources'-Hook eingespeist
und meldet sie ueber den Notifier - die bestehende Dedup-Logik
(self._seen) verhindert Spam.

Ausgeloeste Ereignisse:

  - Trial-Ende rueckt naeher    (sobald innerhalb warn_within_days)
  - Pro-Abo-Ablauf rueckt naeher (sobald innerhalb warn_within_days)
  - Karenzzeit gestartet         (sobald Ablauf gerade ueberschritten)
  - Karenzzeit endet bald        (sobald nur noch 2 Tage)

Keine Events fuer FREE / unbefristete Lizenzen.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from models import Event
from services.licensing import (GRACE_PERIOD_DAYS, License, Tier,
                                  TRIAL_DAYS)


LICENSE_MODULE_ID = "license"
LICENSE_MODULE_NAME = "Lizenz"


def compute_renewal_events(license: License,
                            warn_within_days: int,
                            now: Optional[datetime] = None
                            ) -> list[Event]:
    """Liefert Renewal-/Grace-Events fuer den Scheduler."""
    now = now or datetime.now(timezone.utc)
    events: list[Event] = []

    # ----- Trial -----
    if license.tier == Tier.TRIAL and license.trial_started_at is not None:
        end = license.trial_started_at + timedelta(days=TRIAL_DAYS)
        days = (end - now).days
        if 0 <= days <= warn_within_days:
            events.append(Event(
                title="Trial laeuft bald ab",
                due_date=end.date(),
                module_id=LICENSE_MODULE_ID,
                module_name=LICENSE_MODULE_NAME,
                category="lizenz",
                detail=(f"Deine 14-Tage-Trial endet in {days} Tag(en). "
                        "Danach werden Pro-Funktionen gesperrt - "
                        "im Settings-Tab kannst du jetzt upgraden."),
                days_remaining=days,
            ))

    # ----- Pro-Abo (alle drei Pro-Tiers) -----
    if license.tier in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL, Tier.PRO_FAMILY):
        exp = license.expires_at
        if exp is None:
            return events  # unbefristet (Ed25519-Token sollte das nie liefern)
        days = (exp - now).days

        # Renewal-Warnung: innerhalb des Warnfensters und noch nicht abgelaufen
        if 0 <= days <= warn_within_days:
            events.append(Event(
                title="Pro-Abo verlaengert sich bald nicht automatisch",
                due_date=exp.date(),
                module_id=LICENSE_MODULE_ID,
                module_name=LICENSE_MODULE_NAME,
                category="lizenz",
                detail=(f"Dein Abo laeuft in {days} Tag(en) ab. "
                        "Falls du verlaengern willst, kannst du im "
                        "Settings-Tab den neuen Token einfuegen."),
                days_remaining=days,
            ))

        # Karenzzeit gestartet: gerade abgelaufen, noch innerhalb Grace
        if license.is_in_grace_period(now):
            grace_end = exp + timedelta(days=GRACE_PERIOD_DAYS)
            days_left_in_grace = (grace_end - now).days
            events.append(Event(
                title="Karenzzeit aktiv - Pro-Zugriff endet bald",
                due_date=grace_end.date(),
                module_id=LICENSE_MODULE_ID,
                module_name=LICENSE_MODULE_NAME,
                category="lizenz",
                detail=(f"Dein Abo ist abgelaufen. Du hast noch "
                        f"{days_left_in_grace} Tag(e) Karenzzeit, danach "
                        "wird automatisch auf Free zurueckgestuft."),
                days_remaining=days_left_in_grace,
            ))

    return events


def license_event_source(license_provider):
    """
    Erzeugt eine Closure, die der Scheduler aufrufen kann.

    `license_provider` muss eine 0-arg-Funktion sein, die die aktuelle
    Lizenz liefert (typischerweise lambda: load_license(settings_repo)).
    """
    def _source(warn_within_days: int) -> list[Event]:
        try:
            lic = license_provider()
        except Exception:
            return []
        return compute_renewal_events(lic, warn_within_days)
    return _source
