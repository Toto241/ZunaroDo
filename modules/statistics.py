"""
Modul Statistiken & Trends.

Liefert einfache Aggregate auf Basis der vorhandenen Daten - bewusst
ohne Diagramme, damit das Modul keine GUI-Library benoetigt. Die GUI
kann die Daten selbst rendern.

Capabilities:
  - stats.expenses_per_month     Letzte N Monate, Summe pro Monat
  - stats.expenses_per_category  Aggregat pro Kategorie (Default: aktuelles Jahr)
  - stats.contracts_overview     Anzahl Vertraege, Summe, hoechster Kostentreiber
  - stats.yearly_summary         Gesamtsicht fuer ein Jahr
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from core.interface import Capability, ModuleInterface
from database import ContractRepository, ExpenseRepository


def _add_months(d: date, months: int) -> date:
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    leap = (year % 4 == 0 and year % 100 != 0) or year % 400 == 0
    days_in_month = [31, 29 if leap else 28, 31, 30, 31, 30,
                     31, 31, 30, 31, 30, 31]
    day = min(d.day, days_in_month[month - 1])
    return date(year, month, day)


class StatisticsModule(ModuleInterface):
    """Aggregate ueber Ausgaben + Vertraege."""

    def __init__(self, expenses: ExpenseRepository,
                 contracts: ContractRepository):
        self.expenses = expenses
        self.contracts = contracts

    @property
    def module_id(self) -> str:
        return "statistics"

    @property
    def display_name(self) -> str:
        return "Statistiken & Trends"

    def get_context_summary(self) -> str:
        contracts = self.contracts.list_all(only_active=True)
        total = sum(c.monthly_cost for c in contracts)
        return (f"{len(contracts)} aktive Vertraege - "
                f"{total:.2f} EUR/Monat. Trends via 'stats.*'.")

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="stats.expenses_per_month",
                description="Summiert Ausgaben pro Monat fuer die letzten N "
                            "Monate (Default 12) inkl. dem laufenden Monat.",
                parameters={
                    "months": {"type": "integer",
                                "description": "Anzahl Monate "
                                               "(Default: 12)"},
                },
                handler=self._cap_expenses_per_month,
            ),
            Capability(
                name="stats.expenses_per_category",
                description="Aggregiert Ausgaben pro Kategorie (Default: "
                            "aktuelles Jahr).",
                parameters={
                    "year": {"type": "integer",
                              "description": "Zieljahr (Default: aktuell)"},
                },
                handler=self._cap_expenses_per_category,
            ),
            Capability(
                name="stats.contracts_overview",
                description="Liefert Ueberblick ueber Anzahl aktiver Vertraege, "
                            "monatliche Gesamtsumme und die teuersten 3 "
                            "Posten.",
                parameters={},
                handler=self._cap_contracts_overview,
            ),
            Capability(
                name="stats.yearly_summary",
                description="Gesamtsicht fuer ein Jahr: Summe aller Ausgaben, "
                            "Top-Kategorien, monatlicher Schnitt.",
                parameters={
                    "year": {"type": "integer",
                              "description": "Zieljahr (Default: aktuell)"},
                },
                handler=self._cap_yearly_summary,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_expenses_per_month(self, months: int = 12) -> dict:
        if months <= 0:
            return {"error": "months muss positiv sein"}
        today = date.today()
        start = _add_months(today.replace(day=1), -(months - 1))
        # Bucket-Initialisierung in chronologischer Reihenfolge
        buckets: dict[str, float] = {}
        cursor = start
        while cursor <= today:
            buckets[cursor.strftime("%Y-%m")] = 0.0
            cursor = _add_months(cursor, 1)
        # Aufsummieren
        for e in self.expenses.list_all():
            if e.spent_on is None:
                continue
            key = e.spent_on.strftime("%Y-%m")
            if key in buckets:
                buckets[key] += e.amount
        return {
            "months": months,
            "from": start.isoformat(),
            "buckets": [{"month": m, "total": round(v, 2)}
                         for m, v in buckets.items()],
        }

    def _cap_expenses_per_category(self, year: int | None = None) -> dict:
        target_year = year or date.today().year
        sums: dict[str, float] = defaultdict(float)
        for e in self.expenses.list_all():
            if e.spent_on is None or e.spent_on.year != target_year:
                continue
            sums[e.category] += e.amount
        sorted_cats = sorted(sums.items(), key=lambda kv: -kv[1])
        return {
            "year": target_year,
            "categories": [{"category": k, "total": round(v, 2)}
                            for k, v in sorted_cats],
        }

    def _cap_contracts_overview(self) -> dict:
        contracts = self.contracts.list_all(only_active=True)
        total = sum(c.monthly_cost for c in contracts)
        top = sorted(contracts, key=lambda c: -c.monthly_cost)[:3]
        return {
            "count": len(contracts),
            "monthly_total": round(total, 2),
            "yearly_total": round(total * 12, 2),
            "top_3": [{"name": c.name,
                        "monthly_cost": round(c.monthly_cost, 2),
                        "provider": c.provider}
                       for c in top],
        }

    def _cap_yearly_summary(self, year: int | None = None) -> dict:
        target_year = year or date.today().year
        relevant = [e for e in self.expenses.list_all()
                     if e.spent_on is not None
                     and e.spent_on.year == target_year]
        total = sum(e.amount for e in relevant)
        by_category: dict[str, float] = defaultdict(float)
        for e in relevant:
            by_category[e.category] += e.amount
        top = sorted(by_category.items(), key=lambda kv: -kv[1])[:5]
        # Monatlicher Schnitt: durch die bisher abgelaufenen Monate teilen
        elapsed = (date.today().month if target_year == date.today().year
                    else 12)
        elapsed = max(1, elapsed)
        return {
            "year": target_year,
            "expense_total": round(total, 2),
            "expense_count": len(relevant),
            "average_per_month": round(total / elapsed, 2),
            "elapsed_months": elapsed,
            "top_categories": [{"category": k, "total": round(v, 2)}
                                for k, v in top],
        }
