"""
GUI-agnostische Helfer fuer die Lizenz-/Aktivierungs-UI.

Trennt Datenaufbereitung von Tk-Rendering, damit dieselbe Logik
ohne Tk-Display testbar ist (siehe tests/test_smoke.py:TestLicenseUI).

Verwendet von:
  - gui.py:_build_license_section (Settings-Tab)
  - gui.py:_build_upgrade_panel (Stand-In fuer gesperrte Tabs)
  - gui.py:_build_sidebar (kompakter Tier-Indikator)
  - mobile/ ... (spaeter, sobald die Mobile-UI Pro-Aktivierung anbietet)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from database import SettingsRepository
from services.licensing import (FAMILY_PERSONS_CAP, GRACE_PERIOD_DAYS,
                                  License, Platform, Tier, TRIAL_DAYS,
                                  all_quotes, calculate_price,
                                  format_quote_de, load_license,
                                  start_trial)


# ---------------------------------------------------------------------
# Status-Anzeigen
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class TierStatus:
    """Zustand der Lizenz - Vorlage fuer Sidebar/Settings-Block."""
    tier: Tier
    headline: str            # "Pro (jaehrlich)" / "Free" / "Trial - 7 Tage"
    detail: str               # ein Satz Erklaerung
    expires_in_days: Optional[int]   # negativ = abgelaufen, None = kein Ablauf
    in_grace_period: bool
    can_start_trial: bool


def make_tier_status(lic: License,
                      *,
                      now: Optional[datetime] = None) -> TierStatus:
    """Baut die Anzeigedaten aus einer License-Instanz."""
    now = now or datetime.now(timezone.utc)
    effective = lic.effective_tier(now)

    can_trial = (lic.trial_started_at is None
                  and effective == Tier.FREE
                  and not lic.is_pro(now))

    if effective == Tier.TRIAL:
        days_left = lic.trial_days_left(now)
        return TierStatus(
            tier=effective,
            headline=f"Trial - noch {days_left} Tag(e)",
            detail=("Voller Pro-Zugriff bis zum Ablauf. Danach automatischer "
                    "Wechsel auf Free."),
            expires_in_days=days_left,
            in_grace_period=False,
            can_start_trial=False,
        )

    if effective in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL, Tier.PRO_FAMILY):
        if lic.expires_at is None:
            return TierStatus(
                tier=effective, headline=_tier_label(effective),
                detail="Unbefristet aktiv.",
                expires_in_days=None,
                in_grace_period=False,
                can_start_trial=False,
            )
        delta_days = (lic.expires_at - now).days
        if lic.is_in_grace_period(now):
            return TierStatus(
                tier=effective,
                headline=f"{_tier_label(effective)} - in Karenzzeit",
                detail=(f"Abgelaufen, Karenzzeit endet in "
                        f"{delta_days + GRACE_PERIOD_DAYS} Tag(en). "
                        f"Bitte verlaengern."),
                expires_in_days=delta_days,
                in_grace_period=True,
                can_start_trial=False,
            )
        return TierStatus(
            tier=effective, headline=_tier_label(effective),
            detail=(f"Aktiv bis {lic.expires_at.date().isoformat()}"
                    f" ({delta_days} Tag(e))."),
            expires_in_days=delta_days,
            in_grace_period=False,
            can_start_trial=False,
        )

    # FREE (inkl. abgelaufene Pro-Tier nach Grace)
    return TierStatus(
        tier=Tier.FREE,
        headline="Free",
        detail=(f"Eingeschraenkter Funktionsumfang. "
                f"Du kannst {TRIAL_DAYS} Tage kostenlos testen."
                if can_trial else
                "Eingeschraenkter Funktionsumfang. Trial bereits aufgebraucht."),
        expires_in_days=None,
        in_grace_period=False,
        can_start_trial=can_trial,
    )


def sidebar_indicator(lic: License,
                       *,
                       now: Optional[datetime] = None) -> str:
    """Einzeiliger Tier-Indikator fuer die Sidebar."""
    st = make_tier_status(lic, now=now)
    if st.tier == Tier.TRIAL:
        return f"Tier: Trial ({st.expires_in_days}d)"
    if st.in_grace_period:
        return f"Tier: {_tier_label(st.tier)} (Karenz)"
    if st.tier in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL, Tier.PRO_FAMILY):
        if st.expires_in_days is not None:
            return f"Tier: {_tier_label(st.tier)} ({st.expires_in_days}d)"
        return f"Tier: {_tier_label(st.tier)}"
    return "Tier: Free"


def _tier_label(tier: Tier) -> str:
    return {
        Tier.FREE: "Free",
        Tier.TRIAL: "Trial",
        Tier.PRO_MONTHLY: "Pro (monatlich)",
        Tier.PRO_ANNUAL: "Pro (jaehrlich)",
        Tier.PRO_FAMILY: "Pro Familie",
    }.get(tier, tier.value)


# ---------------------------------------------------------------------
# Pricing-Tabelle
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class PricingRow:
    tier: Tier
    label: str
    price_text: str
    description: str
    is_recommended: bool


def build_pricing_rows(persons: int,
                        *,
                        platform: Platform = Platform.DESKTOP,
                        recommended: Optional[Tier] = None
                        ) -> list[PricingRow]:
    """Liefert die Zeilen fuer die Pricing-Tabelle in der GUI."""
    quotes = all_quotes(persons, platform=platform)
    rows: list[PricingRow] = []
    for tier in (Tier.FREE, Tier.PRO_MONTHLY, Tier.PRO_ANNUAL,
                  Tier.PRO_FAMILY):
        if tier not in quotes:
            continue
        q = quotes[tier]
        rows.append(PricingRow(
            tier=tier,
            label=_tier_label(tier),
            price_text=format_quote_de(q),
            description=_tier_description(tier, persons),
            is_recommended=(tier == recommended),
        ))
    return rows


def _tier_description(tier: Tier, persons: int) -> str:
    if tier == Tier.FREE:
        return "1 Person, 2 Module, kein KI, kein Sync."
    if tier == Tier.TRIAL:
        return f"{TRIAL_DAYS} Tage voller Funktionsumfang, einmalig."
    if tier == Tier.PRO_FAMILY:
        return f"Flat-Tarif fuer bis zu {FAMILY_PERSONS_CAP} Personen."
    if tier == Tier.PRO_ANNUAL:
        return "20 % Rabatt, jaehrliche Abrechnung."
    return "Monatliche Abrechnung, jederzeit kuendbar."


# ---------------------------------------------------------------------
# Aktionen (geben uniforme Result-Objekte zurueck)
# ---------------------------------------------------------------------
@dataclass
class ActionResult:
    success: bool
    message: str
    license: Optional[License] = None


def action_start_trial(repo: SettingsRepository,
                        *,
                        now: Optional[datetime] = None) -> ActionResult:
    """Startet die Trial - idempotent: zweiter Aufruf bleibt wirkungslos."""
    before = load_license(repo)
    if before.trial_started_at is not None:
        return ActionResult(
            success=False,
            message="Trial wurde fuer dieses Geraet bereits genutzt.",
            license=before,
        )
    lic = start_trial(repo, now=now)
    return ActionResult(
        success=True,
        message=(f"Trial gestartet - {TRIAL_DAYS} Tage voller Funktionsumfang. "
                 "Nach Ablauf wechselt die App automatisch zurueck auf Free."),
        license=lic,
    )


def action_apply_token(repo: SettingsRepository,
                        token_str: str,
                        *,
                        public_key_hex: Optional[str] = None,
                        now: Optional[datetime] = None) -> ActionResult:
    """Verifiziert ein eingegebenes Token und uebertraegt es in die Settings."""
    from services.license_token import (CRYPTO_AVAILABLE, TokenError,
                                          TokenExpired, apply_token_to_repo,
                                          verify_token)
    # Input-Validierung ZUERST - sonst sieht ein Nutzer, der nichts
    # eingibt, die kryptische 'Krypto-Bibliothek fehlt'-Meldung statt
    # des erwarteten 'Kein Token eingegeben'.
    token_str = (token_str or "").strip()
    if not token_str:
        return ActionResult(
            success=False,
            message="Kein Token eingegeben.",
        )
    if not CRYPTO_AVAILABLE:
        return ActionResult(
            success=False,
            message="Krypto-Bibliothek nicht installiert - "
                    "Token-Aktivierung nicht moeglich.",
        )
    try:
        token = verify_token(token_str, public_key_hex, now=now)
    except TokenExpired as exc:
        return ActionResult(
            success=False,
            message=(f"Token ist bereits am "
                     f"{exc.token.expires_at.date().isoformat()} abgelaufen."),
        )
    except TokenError as exc:
        return ActionResult(
            success=False,
            message=f"Token konnte nicht verifiziert werden: {exc}",
        )
    apply_token_to_repo(repo, token_str, token)
    return ActionResult(
        success=True,
        message=(f"Pro-Lizenz aktiviert: {_tier_label(token.tier)}, "
                 f"{token.persons} Person(en), aktiv bis "
                 f"{token.expires_at.date().isoformat()}."),
        license=load_license(repo),
    )
