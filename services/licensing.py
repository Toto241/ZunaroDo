"""
Lizenz- und Pricing-Modell des Alltagshelfers.

Tiers:

  FREE          lokal, 1 Person, 2 Module, kein KI, kein Sync.
                Akquise-Pfad ohne die Privacy-Positionierung zu schwaechen.

  TRIAL         14 Tage voller Pro-Funktionsumfang, danach automatischer
                Downgrade auf FREE (bzw. GRANDFATHERED, siehe unten).

  PRO_MONTHLY   Variante B - 6,99 EUR/Monat fuer bis zu zwei Personen,
                jede weitere Person 1,99 EUR/Monat.

  PRO_ANNUAL    Gleicher Funktionsumfang wie PRO_MONTHLY, 20 % Rabatt.

  PRO_FAMILY    Flat-Tarif 12,99 EUR/Monat (bzw. 124,70 EUR/Jahr mit
                Jahresabo) fuer bis zu 5 Personen. Verhindert, dass
                Grossfamilien beim Per-Person-Modell abspringen.

Special-Flags:
  - 'grandfathered': True wenn beim Pricing-Launch bereits Daten vorlagen.
    Diese Nutzer behalten Lese-Zugriff auf alle Module unbefristet,
    duerfen aber keine neuen Pro-Features (KI, Sync) nutzen.
  - 'expires_at' (UTC-ISO): Ablauf des Abos. Pro_-Tier wird nach
    7 Tagen Grace-Period auf FREE/GRANDFATHERED gedowngradet.

Bewusst NICHT enthalten: ein werbefinanzierter Tier. Die App haelt
sensible Daten (Finanzen, Vertraege, Familie, Mails); Display-Ads
oder Tracking-basierte Werbung kollidieren frontal mit der Privacy-
Positionierung im README und sind unter DSGVO juristisch heikel.

Die Klassen hier *berechnen* und *deklarieren* den Funktionsumfang.
Die Durchsetzung erfolgt zentral in services/license_gate.py - das
liefert nur die Wahrheit darueber, was erlaubt ist.
"""
from __future__ import annotations

import enum
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from database import SettingsRepository

log = logging.getLogger(__name__)


# ---- Preis-Konstanten (Variante B, brutto, inkl. 19 % USt.) ----------
PRICE_BASE_MONTHLY_EUR = 6.99
PRICE_PER_EXTRA_PERSON_MONTHLY_EUR = 1.99
PRICE_FAMILY_FLAT_MONTHLY_EUR = 12.99
FAMILY_PERSONS_CAP = 5
BASE_PERSONS = 2
ANNUAL_DISCOUNT_RATE = 0.20

# ---- Mobile-Markup (App-Store/Play-Store Cut, 30 % typisch) ---------
# Wer in den Stores verkaufen will, gibt 15-30 % ab. 25 % Markup deckt
# den 30%-Cut nicht ganz - der Rest geht zu Lasten der Marge, weil
# die Nutzer-Akquise im Store den Aufpreis trotzdem rechtfertigt.
MOBILE_PRICE_MARKUP = 0.25

# ---- Schweizer Franken (Stand 2026 ungefaehr 1.00 EUR = 0.94 CHF) ----
EUR_TO_CHF_RATE = 0.94
CH_VAT_RATE = 0.081  # MwSt. CH ab 2024

# ---- Free-Tier-Grenzen ----------------------------------------------
FREE_MAX_PERSONS = 1
FREE_MODULE_LIMIT = 2
FREE_MODULES_DEFAULT: tuple[str, ...] = ("contracts", "family")

# ---- Trial-Konfiguration --------------------------------------------
TRIAL_DAYS = 14
GRACE_PERIOD_DAYS = 7

# ---- Setting-Keys ----------------------------------------------------
KEY_TIER = "license.tier"
KEY_PERSONS = "license.persons"
KEY_MODULES = "license.enabled_modules"
KEY_PURCHASED_AT = "license.purchased_at"
KEY_EXPIRES_AT = "license.expires_at"
KEY_TRIAL_STARTED_AT = "license.trial_started_at"
KEY_GRANDFATHERED = "license.grandfathered"
KEY_TOKEN = "license.token"
KEY_WITHDRAWAL_WAIVED = "license.withdrawal_waived"
KEY_PLATFORM = "license.platform"        # desktop | ios | android | web

# ---- Affiliate-Stub (kein Tracking, nur statische Empfehlungen) -----
AFFILIATE_PARTNERS: dict[str, str] = {
    "verbraucherzentrale": "https://www.verbraucherzentrale.de/",
    "stiftung_warentest": "https://www.test.de/",
}


class Tier(str, enum.Enum):
    FREE = "free"
    TRIAL = "trial"
    PRO_MONTHLY = "pro_monthly"
    PRO_ANNUAL = "pro_annual"
    PRO_FAMILY = "pro_family"


class Platform(str, enum.Enum):
    DESKTOP = "desktop"
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class Currency(str, enum.Enum):
    EUR = "EUR"
    CHF = "CHF"


# ---------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class PriceQuote:
    """Berechnete Preisangabe fuer eine Kombination aus Personen/Tier."""
    persons: int
    tier: Tier
    monthly_eur: float       # effektiver Monatspreis (nach Rabatt/Markup)
    total_eur: float          # was beim Abschluss anfaellt
    period: str               # "monthly" | "annual" | "forever"
    list_monthly_eur: float
    discount_rate: float
    currency: Currency = Currency.EUR
    platform: Platform = Platform.DESKTOP

    def savings_eur(self) -> float:
        """Ersparnis gegenueber dem Monatsabo ueber denselben Zeitraum."""
        if self.tier != Tier.PRO_ANNUAL:
            return 0.0
        return round(self.list_monthly_eur * 12 - self.total_eur, 2)


def _list_monthly_price_eur(persons: int, tier: Tier) -> float:
    """Listenpreis Monat (vor Rabatt, vor Markup, in EUR)."""
    if tier == Tier.PRO_FAMILY:
        return PRICE_FAMILY_FLAT_MONTHLY_EUR
    extra = max(0, persons - BASE_PERSONS)
    return (PRICE_BASE_MONTHLY_EUR
            + extra * PRICE_PER_EXTRA_PERSON_MONTHLY_EUR)


def calculate_price(persons: int,
                    tier: Tier,
                    platform: Platform = Platform.DESKTOP) -> PriceQuote:
    """Berechnet den Preis fuer 'persons' Personen im gegebenen Tier."""
    if persons < 1:
        raise ValueError("persons muss >= 1 sein")
    if tier == Tier.PRO_FAMILY and persons > FAMILY_PERSONS_CAP:
        raise ValueError(
            f"PRO_FAMILY ist auf {FAMILY_PERSONS_CAP} Personen begrenzt")
    if tier in (Tier.FREE, Tier.TRIAL):
        return PriceQuote(persons=persons, tier=tier,
                          monthly_eur=0.0, total_eur=0.0,
                          period="forever" if tier == Tier.FREE else "trial",
                          list_monthly_eur=0.0, discount_rate=0.0,
                          platform=platform)

    list_monthly = _list_monthly_price_eur(persons, tier)

    # Mobile-Markup multiplikativ auf den Listenpreis.
    if platform in (Platform.IOS, Platform.ANDROID):
        list_monthly = list_monthly * (1 + MOBILE_PRICE_MARKUP)

    if tier == Tier.PRO_ANNUAL:
        # Jahresbetrag zuerst runden, dann Monatspreis ableiten - sonst
        # akkumuliert Cent-Rundung ueber 12 Monate.
        total_annual = round(list_monthly * 12 * (1 - ANNUAL_DISCOUNT_RATE), 2)
        effective_monthly = round(total_annual / 12, 2)
        return PriceQuote(persons=persons, tier=tier,
                          monthly_eur=effective_monthly,
                          total_eur=total_annual,
                          period="annual",
                          list_monthly_eur=round(list_monthly, 2),
                          discount_rate=ANNUAL_DISCOUNT_RATE,
                          platform=platform)

    # PRO_MONTHLY oder PRO_FAMILY
    return PriceQuote(persons=persons, tier=tier,
                      monthly_eur=round(list_monthly, 2),
                      total_eur=round(list_monthly, 2),
                      period="monthly",
                      list_monthly_eur=round(list_monthly, 2),
                      discount_rate=0.0,
                      platform=platform)


def convert_to_chf(quote: PriceQuote) -> PriceQuote:
    """Wandelt eine EUR-Preisangabe in CHF um (mit CH-MwSt.-Aufschlag)."""
    if quote.currency == Currency.CHF:
        return quote
    factor = EUR_TO_CHF_RATE * (1 + CH_VAT_RATE) / (1 + 0.19)  # DE 19 % -> CH 8.1 %
    return PriceQuote(
        persons=quote.persons,
        tier=quote.tier,
        monthly_eur=round(quote.monthly_eur * factor, 2),
        total_eur=round(quote.total_eur * factor, 2),
        period=quote.period,
        list_monthly_eur=round(quote.list_monthly_eur * factor, 2),
        discount_rate=quote.discount_rate,
        currency=Currency.CHF,
        platform=quote.platform,
    )


def all_quotes(persons: int,
                platform: Platform = Platform.DESKTOP) -> dict[Tier, PriceQuote]:
    """Alle vergleichbaren Tiers fuer eine Personenanzahl."""
    result: dict[Tier, PriceQuote] = {}
    for t in (Tier.FREE, Tier.PRO_MONTHLY, Tier.PRO_ANNUAL):
        result[t] = calculate_price(persons, t, platform)
    # PRO_FAMILY nur sinnvoll, wenn persons <= Cap
    if persons <= FAMILY_PERSONS_CAP:
        result[Tier.PRO_FAMILY] = calculate_price(persons, Tier.PRO_FAMILY,
                                                    platform)
    return result


def recommended_tier(persons: int) -> Tier:
    """Empfiehlt den guenstigsten Pro-Tier fuer eine Personenanzahl."""
    if persons <= BASE_PERSONS:
        return Tier.PRO_ANNUAL
    monthly_per_person = calculate_price(persons, Tier.PRO_MONTHLY).monthly_eur
    if (persons <= FAMILY_PERSONS_CAP
            and PRICE_FAMILY_FLAT_MONTHLY_EUR < monthly_per_person):
        return Tier.PRO_FAMILY
    return Tier.PRO_ANNUAL


# ---------------------------------------------------------------------
# License-Objekt + Zeitlogik
# ---------------------------------------------------------------------
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        # Akzeptiert sowohl '+00:00' als auch 'Z'
        cleaned = s.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


@dataclass
class License:
    """Aktive Lizenz - aus Settings geladen."""
    tier: Tier = Tier.FREE
    persons: int = 1
    enabled_modules: tuple[str, ...] = FREE_MODULES_DEFAULT
    purchased_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    trial_started_at: Optional[datetime] = None
    grandfathered: bool = False
    withdrawal_waived: bool = False
    platform: Platform = Platform.DESKTOP

    def effective_tier(self, now: Optional[datetime] = None) -> Tier:
        """
        Aktueller Tier nach Anwendung von Ablauf/Trial-Logik.

        - TRIAL abgelaufen -> FREE
        - PRO_* abgelaufen + Grace-Period vorbei -> FREE (bzw.
          GRANDFATHERED hat eigenen Lese-Modus, der nicht ueber den
          Tier laeuft).
        """
        now = now or _utcnow()
        if self.tier == Tier.TRIAL:
            if self.trial_started_at is None:
                return Tier.FREE
            if now > self.trial_started_at + timedelta(days=TRIAL_DAYS):
                return Tier.FREE
            return Tier.TRIAL
        if self.tier in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL, Tier.PRO_FAMILY):
            if self.expires_at is None:
                return self.tier  # noch nie aktiviert? -> behalten
            grace_end = self.expires_at + timedelta(days=GRACE_PERIOD_DAYS)
            if now > grace_end:
                return Tier.FREE
            return self.tier
        return self.tier

    def is_pro(self, now: Optional[datetime] = None) -> bool:
        eff = self.effective_tier(now)
        return eff in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL,
                       Tier.PRO_FAMILY, Tier.TRIAL)

    def is_in_grace_period(self, now: Optional[datetime] = None) -> bool:
        now = now or _utcnow()
        if self.expires_at is None:
            return False
        return self.expires_at < now <= self.expires_at + timedelta(
            days=GRACE_PERIOD_DAYS)

    def trial_days_left(self, now: Optional[datetime] = None) -> int:
        if self.tier != Tier.TRIAL or self.trial_started_at is None:
            return 0
        now = now or _utcnow()
        end = self.trial_started_at + timedelta(days=TRIAL_DAYS)
        return max(0, (end - now).days)

    def allows_module(self,
                       module_id: str,
                       *,
                       writing: bool = False,
                       now: Optional[datetime] = None) -> bool:
        if self.is_pro(now):
            return True
        # Grandfathered: Lesezugriff auf alles, Schreiben nur in den
        # urspruenglich freigeschalteten Modulen.
        if self.grandfathered and not writing:
            return True
        return module_id in self.enabled_modules

    def allows_ai(self, now: Optional[datetime] = None) -> bool:
        return self.is_pro(now)

    def allows_sync(self, now: Optional[datetime] = None) -> bool:
        return self.is_pro(now)

    def max_persons(self) -> int:
        if self.tier == Tier.FREE:
            return FREE_MAX_PERSONS
        if self.tier == Tier.PRO_FAMILY:
            return FAMILY_PERSONS_CAP
        return self.persons


# ---------------------------------------------------------------------
# Persistenz
# ---------------------------------------------------------------------
def _parse_modules(raw: str) -> tuple[str, ...]:
    return tuple(m.strip() for m in raw.split(",") if m.strip())


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _bool_from_raw(raw: Optional[str]) -> bool:
    return (raw or "").strip().lower() in ("1", "true", "yes", "on")


def detect_platform() -> Platform:
    """Plattform-Erkennung fuer Mobile-Markup. Buildozer setzt P4A_*."""
    if os.environ.get("ALLTAGSHELFER_PLATFORM"):
        try:
            return Platform(os.environ["ALLTAGSHELFER_PLATFORM"].lower())
        except ValueError:
            pass
    if "ANDROID_ARGUMENT" in os.environ or "P4A_RELEASE_KEYSTORE" in os.environ:
        return Platform.ANDROID
    if os.environ.get("KIVY_BUILD") == "ios":
        return Platform.IOS
    return Platform.DESKTOP


def load_license(repo: Optional[SettingsRepository]) -> License:
    """Lizenz aus Settings laden - Defaults: FREE-Tier.

    Wenn ein Lizenz-Token (KEY_TOKEN) hinterlegt ist, wird der Pro-
    Tier aus dem Token rekonstruiert - das blockiert Manipulation
    der einzelnen Settings-Felder (jemand setzt 'license.tier=pro_annual'
    per SQL-Editor, hat aber kein passendes Token).
    """
    if repo is None:
        return License(platform=detect_platform())
    # Token-basierte Re-Verifikation (Tamper-Schutz). Wichtig:
    # - Gueltiges Token -> Pro mit Token-Daten
    # - Abgelaufenes Token (Signatur OK) -> Pro mit Token-Daten,
    #   Grace-Period entscheidet im effective_tier(), ob der Tier
    #   noch greift. Token NICHT loeschen, sonst geht expires_at
    #   verloren und die Grace-Period waere nie anwendbar.
    # - Manipuliertes / kaputtes Token -> Token loeschen, Fallback
    #   auf Settings (die ohne gueltiges Token nichts wert sind -
    #   die Tier-Felder werden im Falle eines Tampering-Versuchs
    #   einfach mit FREE als Default ueberschrieben werden, weil
    #   keine Pro-Aktivierung ohne Token entstehen kann).
    token_str = repo.get(KEY_TOKEN)
    if token_str:
        from services.license_token import (TokenError, TokenExpired,
                                              verify_token)
        try:
            tok = verify_token(token_str)
        except TokenExpired as exc:
            # Signatur stimmt, nur expires_at vorbei. Token behalten,
            # damit Grace-Period in effective_tier() greifen kann.
            tok = exc.token
        except TokenError:
            # Signatur falsch oder Payload kaputt -> sicher loeschen.
            # In diesem Fall ist die Lizenz nicht mehr glaubhaft;
            # weiter mit Settings-Fallback (typischerweise FREE).
            repo.set(KEY_TOKEN, None)
            tok = None
        if tok is not None:
            return License(
                tier=tok.tier,
                persons=tok.persons,
                purchased_at=tok.purchased_at,
                expires_at=tok.expires_at,
                platform=tok.platform,
                enabled_modules=_parse_modules(repo.get(KEY_MODULES) or "")
                                or FREE_MODULES_DEFAULT,
                trial_started_at=_parse_iso(repo.get(KEY_TRIAL_STARTED_AT)),
                grandfathered=_bool_from_raw(repo.get(KEY_GRANDFATHERED)),
                withdrawal_waived=_bool_from_raw(
                    repo.get(KEY_WITHDRAWAL_WAIVED)),
            )

    try:
        tier = Tier((repo.get(KEY_TIER) or Tier.FREE.value).lower())
    except ValueError:
        tier = Tier.FREE
    try:
        persons = max(1, int(repo.get(KEY_PERSONS) or "1"))
    except ValueError:
        persons = 1
    modules_raw = (repo.get(KEY_MODULES) or "").strip()
    modules = _parse_modules(modules_raw) if modules_raw else FREE_MODULES_DEFAULT
    if tier == Tier.FREE and len(modules) > FREE_MODULE_LIMIT:
        modules = modules[:FREE_MODULE_LIMIT]
    try:
        platform = Platform((repo.get(KEY_PLATFORM)
                              or detect_platform().value).lower())
    except ValueError:
        platform = detect_platform()
    return License(
        tier=tier,
        persons=persons,
        enabled_modules=modules,
        purchased_at=_parse_iso(repo.get(KEY_PURCHASED_AT)),
        expires_at=_parse_iso(repo.get(KEY_EXPIRES_AT)),
        trial_started_at=_parse_iso(repo.get(KEY_TRIAL_STARTED_AT)),
        grandfathered=_bool_from_raw(repo.get(KEY_GRANDFATHERED)),
        withdrawal_waived=_bool_from_raw(repo.get(KEY_WITHDRAWAL_WAIVED)),
        platform=platform,
    )


def save_license(repo: SettingsRepository, lic: License) -> None:
    """Lizenz in Settings persistieren."""
    repo.set(KEY_TIER, lic.tier.value)
    repo.set(KEY_PERSONS, str(lic.persons))
    repo.set(KEY_MODULES, ",".join(lic.enabled_modules))
    repo.set(KEY_PURCHASED_AT, _to_iso(lic.purchased_at))
    repo.set(KEY_EXPIRES_AT, _to_iso(lic.expires_at))
    repo.set(KEY_TRIAL_STARTED_AT, _to_iso(lic.trial_started_at))
    repo.set(KEY_GRANDFATHERED, "true" if lic.grandfathered else None)
    repo.set(KEY_WITHDRAWAL_WAIVED, "true" if lic.withdrawal_waived else None)
    repo.set(KEY_PLATFORM, lic.platform.value)


def start_trial(repo: SettingsRepository,
                now: Optional[datetime] = None) -> License:
    """
    Startet die 14-Tage-Trial. Idempotent: laeuft eine Trial bereits
    (auch wenn abgelaufen), wird der Start NICHT zurueckgesetzt -
    so kann der Trial nicht durch Neuinstallation erneuert werden.
    """
    lic = load_license(repo)
    if lic.trial_started_at is not None:
        return lic  # bereits benutzt
    now = now or _utcnow()
    lic.tier = Tier.TRIAL
    lic.trial_started_at = now
    save_license(repo, lic)
    return lic


def activate_pro(repo: SettingsRepository,
                  tier: Tier,
                  persons: int,
                  *,
                  now: Optional[datetime] = None,
                  expires_at: Optional[datetime] = None) -> License:
    """
    Aktiviert ein Pro-Abo. Falls 'expires_at' fehlt, wird je nach
    Tier ein passendes Ablaufdatum gesetzt (Monat oder Jahr).
    """
    if tier not in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL, Tier.PRO_FAMILY):
        raise ValueError(f"{tier} ist kein Pro-Tier")
    now = now or _utcnow()
    if expires_at is None:
        if tier == Tier.PRO_ANNUAL:
            expires_at = now + timedelta(days=365)
        else:
            expires_at = now + timedelta(days=30)
    lic = load_license(repo)
    lic.tier = tier
    lic.persons = persons
    lic.purchased_at = now
    lic.expires_at = expires_at
    save_license(repo, lic)
    return lic


def mark_grandfathered(repo: SettingsRepository,
                        existing_modules: tuple[str, ...]) -> License:
    """
    Markiert Bestandsdaten als grandfathered (Migration beim
    Pricing-Launch). Lese-Zugriff auf existing_modules bleibt
    unbefristet, Pro-Features brauchen aber weiterhin ein Abo.
    """
    lic = load_license(repo)
    lic.grandfathered = True
    lic.enabled_modules = tuple(existing_modules)
    save_license(repo, lic)
    return lic


# Sentinel-Setting: einmal pro DB gesetzt, sobald die Grandfathering-
# Migration gelaufen ist. Verhindert, dass neue Free-Nutzer, die ihre
# DB spaeter mit Daten fuellen, faelschlich grandfathered werden.
KEY_GRANDFATHER_MIGRATION_DONE = "license.grandfather_migration_done"


def apply_grandfathering_if_needed(repo: SettingsRepository,
                                    has_data_fn) -> Optional[License]:
    """
    Startup-Migration: wenn die App zum ersten Mal mit dem neuen
    Pricing-System startet UND Bestandsdaten vorhanden sind, wird
    die Lizenz grandfathered markiert.

    'has_data_fn' ist ein 0-arg-Callable, das True liefert, wenn
    irgendein Modul Daten enthaelt - bei den Tests kann das einfach
    'lambda: True' sein.

    Idempotent: nach dem ersten Lauf wird KEY_GRANDFATHER_MIGRATION_DONE
    gesetzt und die Migration laeuft nie wieder.
    """
    if repo.get(KEY_GRANDFATHER_MIGRATION_DONE):
        return None
    repo.set(KEY_GRANDFATHER_MIGRATION_DONE, "true")
    lic = load_license(repo)
    if lic.tier != Tier.FREE or lic.purchased_at is not None:
        # Schon ein Abo aktiv - kein Grandfathering noetig
        return None
    try:
        has_data = bool(has_data_fn())
    except Exception as exc:                            # noqa: BLE001
        log.warning("Pruefung auf Bestandsdaten fuer Grandfathering "
                    "fehlgeschlagen: %s", exc)
        has_data = False
    if not has_data:
        return None
    # Alle bekannten Module als "darf weiter schreiben" markieren -
    # so dass der Nutzer seine bisherigen Daten ohne Reibung
    # weiterbearbeiten kann. KI/Sync bleibt Pro-only.
    all_modules = ("contracts", "finance", "family", "calendar",
                   "social", "inbox", "statistics", "daystructure",
                   "notes")
    return mark_grandfathered(repo, all_modules)


# ---------------------------------------------------------------------
# Anzeige
# ---------------------------------------------------------------------
def format_quote_de(quote: PriceQuote) -> str:
    """Lesbare Darstellung fuer GUI/CLI in deutscher Sprache."""
    unit = "EUR" if quote.currency == Currency.EUR else "CHF"
    if quote.tier == Tier.FREE:
        return f"Kostenlos - {FREE_MAX_PERSONS} Person, {FREE_MODULE_LIMIT} Module"
    if quote.tier == Tier.TRIAL:
        return f"Kostenlos {TRIAL_DAYS} Tage testen - kein Abo, kein Bezahlen"
    if quote.tier == Tier.PRO_FAMILY:
        return (f"{quote.monthly_eur:.2f} {unit}/Monat fuer bis zu "
                f"{FAMILY_PERSONS_CAP} Personen (Flat)")
    if quote.tier == Tier.PRO_ANNUAL:
        return (f"{quote.total_eur:.2f} {unit}/Jahr "
                f"(entspricht {quote.monthly_eur:.2f} {unit}/Monat, "
                f"{round(quote.discount_rate * 100)} % Rabatt, "
                f"Ersparnis {quote.savings_eur():.2f} {unit})")
    return f"{quote.monthly_eur:.2f} {unit}/Monat"
