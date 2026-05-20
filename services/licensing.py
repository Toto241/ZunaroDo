"""
Lizenz- und Pricing-Modell des Alltagshelfers.

Drei Tiers:

  FREE         lokal, 1 Person, 2 Module, kein KI, kein Sync.
               Dient als Akquise-Pfad ohne die Privacy-Positionierung
               (Datenschutzfreundlich, keine Cloud-Pflicht) zu schwaechen.

  PRO_MONTHLY  Variante B - 6,99 EUR/Monat fuer bis zu zwei Personen,
               jede weitere Person 1,99 EUR/Monat. Alle acht Module,
               KI, Sync, SQLCipher, OCR.

  PRO_ANNUAL   Gleicher Funktionsumfang wie PRO_MONTHLY, 20 % Rabatt
               auf den effektiven Monatspreis (Industrie-Standard,
               Cashflow-Vorteil + niedrigere Churn).

Bewusst NICHT enthalten: ein werbefinanzierter Tier. Die App haelt
sensible Daten (Finanzen, Vertraege, Familie, Mails); Display-Ads
oder Tracking-basierte Werbung kollidieren frontal mit der Privacy-
Positionierung im README und sind unter DSGVO juristisch heikel.
Stattdessen sind Affiliate-Empfehlungen im Vertragsmodul vorgesehen
(siehe AFFILIATE_PARTNERS) - keine Display-Ads, kein Tracking.

Die Klassen hier *berechnen* und *deklarieren* den Funktionsumfang.
Die Durchsetzung (z.B. Sperren des KI-Tabs in der GUI) ist Sache
der jeweiligen Aufrufer - dieses Modul liefert nur die Wahrheit
darueber, was erlaubt ist. Das passt zum bestehenden Muster im
Alltagshelfer (vergl. Modul-Enable/Disable in ModuleRegistry).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from database import SettingsRepository


# ---- Preis-Konstanten (Variante B, brutto, inkl. 19 % USt.) ----------
PRICE_BASE_MONTHLY_EUR = 6.99
PRICE_PER_EXTRA_PERSON_MONTHLY_EUR = 1.99
BASE_PERSONS = 2
ANNUAL_DISCOUNT_RATE = 0.20

# ---- Free-Tier-Grenzen ----------------------------------------------
FREE_MAX_PERSONS = 1
FREE_MODULE_LIMIT = 2
# Kern-Module fuer den Einstieg: Vertraege + Familie. Bewusst nicht
# Finanzen - das ist das staerkste Upgrade-Argument.
FREE_MODULES_DEFAULT: tuple[str, ...] = ("contracts", "family")

# ---- Setting-Keys ----------------------------------------------------
KEY_TIER = "license.tier"
KEY_PERSONS = "license.persons"
KEY_MODULES = "license.enabled_modules"

# ---- Affiliate-Stub (kein Tracking, nur statische Empfehlungen) -----
# Wird vom Vertragsmodul abgefragt, wenn ein Vertrag gekuendigt
# oder gewechselt wird. Display-Ads bleiben bewusst aussen vor.
AFFILIATE_PARTNERS: dict[str, str] = {
    "verbraucherzentrale": "https://www.verbraucherzentrale.de/",
    "stiftung_warentest": "https://www.test.de/",
}


class Tier(str, enum.Enum):
    FREE = "free"
    PRO_MONTHLY = "pro_monthly"
    PRO_ANNUAL = "pro_annual"


@dataclass(frozen=True)
class PriceQuote:
    """Berechnete Preisangabe fuer eine Kombination aus Personen/Tier."""
    persons: int
    tier: Tier
    monthly_eur: float       # effektiver Monatspreis (nach Rabatt)
    total_eur: float          # was beim Abschluss anfaellt (Monat/Jahr)
    period: str               # "monthly" | "annual" | "forever"
    list_monthly_eur: float   # Listenpreis pro Monat (vor Rabatt)
    discount_rate: float

    def savings_eur(self) -> float:
        """Ersparnis gegenueber dem Monatsabo ueber denselben Zeitraum."""
        if self.tier != Tier.PRO_ANNUAL:
            return 0.0
        return round(self.list_monthly_eur * 12 - self.total_eur, 2)


def calculate_price(persons: int, tier: Tier) -> PriceQuote:
    """Berechnet den Preis fuer 'persons' Personen im gegebenen Tier."""
    if persons < 1:
        raise ValueError("persons muss >= 1 sein")
    if tier == Tier.FREE:
        return PriceQuote(persons=persons, tier=tier, monthly_eur=0.0,
                          total_eur=0.0, period="forever",
                          list_monthly_eur=0.0, discount_rate=0.0)
    extra = max(0, persons - BASE_PERSONS)
    list_monthly = (PRICE_BASE_MONTHLY_EUR
                    + extra * PRICE_PER_EXTRA_PERSON_MONTHLY_EUR)
    if tier == Tier.PRO_ANNUAL:
        # Erst den Jahresbetrag berechnen und runden, dann den
        # informativen Monatspreis ableiten - sonst akkumuliert die
        # Cent-Rundung im Monatspreis ueber 12 Monate eine sichtbare
        # Differenz (z.B. 105,36 statt 105,31 fuer eine 4-Personen-Familie).
        total_annual = round(list_monthly * 12 * (1 - ANNUAL_DISCOUNT_RATE), 2)
        effective_monthly = round(total_annual / 12, 2)
        return PriceQuote(persons=persons, tier=tier,
                          monthly_eur=effective_monthly,
                          total_eur=total_annual,
                          period="annual",
                          list_monthly_eur=round(list_monthly, 2),
                          discount_rate=ANNUAL_DISCOUNT_RATE)
    return PriceQuote(persons=persons, tier=tier,
                      monthly_eur=round(list_monthly, 2),
                      total_eur=round(list_monthly, 2),
                      period="monthly",
                      list_monthly_eur=round(list_monthly, 2),
                      discount_rate=0.0)


def all_quotes(persons: int) -> dict[Tier, PriceQuote]:
    """Alle drei Tiers fuer eine Personenanzahl - fuer Vergleichstabellen."""
    return {t: calculate_price(persons, t) for t in Tier}


@dataclass
class License:
    """Aktive Lizenz - aus Settings geladen."""
    tier: Tier = Tier.FREE
    persons: int = 1
    # Im Free-Tier: welche Module der Nutzer freigeschaltet hat.
    # Im Pro-Tier: ignoriert, alles ist offen.
    enabled_modules: tuple[str, ...] = FREE_MODULES_DEFAULT

    def is_pro(self) -> bool:
        return self.tier in (Tier.PRO_MONTHLY, Tier.PRO_ANNUAL)

    def allows_module(self, module_id: str) -> bool:
        if self.is_pro():
            return True
        return module_id in self.enabled_modules

    def allows_ai(self) -> bool:
        return self.is_pro()

    def allows_sync(self) -> bool:
        return self.is_pro()

    def max_persons(self) -> int:
        if self.tier == Tier.FREE:
            return FREE_MAX_PERSONS
        return self.persons


def _parse_modules(raw: str) -> tuple[str, ...]:
    return tuple(m.strip() for m in raw.split(",") if m.strip())


def load_license(repo: Optional[SettingsRepository]) -> License:
    """Lizenz aus Settings laden - Defaults: FREE-Tier."""
    if repo is None:
        return License()
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
    return License(tier=tier, persons=persons, enabled_modules=modules)


def save_license(repo: SettingsRepository, lic: License) -> None:
    """Lizenz in Settings persistieren."""
    repo.set(KEY_TIER, lic.tier.value)
    repo.set(KEY_PERSONS, str(lic.persons))
    repo.set(KEY_MODULES, ",".join(lic.enabled_modules))


def format_quote_de(quote: PriceQuote) -> str:
    """Lesbare Darstellung fuer GUI/CLI in deutscher Sprache."""
    if quote.tier == Tier.FREE:
        return f"Kostenlos - {FREE_MAX_PERSONS} Person, {FREE_MODULE_LIMIT} Module"
    if quote.tier == Tier.PRO_ANNUAL:
        return (f"{quote.total_eur:.2f} EUR/Jahr "
                f"(entspricht {quote.monthly_eur:.2f} EUR/Monat, "
                f"{round(quote.discount_rate * 100)} % Rabatt, "
                f"Ersparnis {quote.savings_eur():.2f} EUR)")
    return f"{quote.monthly_eur:.2f} EUR/Monat"
