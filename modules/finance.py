"""
Modul B - Finanz-Cockpit.

Bewusste Abgrenzung: KEIN Buchhaltungstool. Modul B liefert einen
einfachen, aber ehrlichen Ueberblick ueber die monatliche Belastung,
indem es ZWEI Quellen zusammenfuehrt:

  - eigene Daten:        einmalige Ausgaben dieses Monats
  - Daten von Modul A:   wiederkehrende Vertragskosten

Genau hier kommt Schnittstelle 2 ins Spiel: ueber den ModuleContext
ruft dieses Modul 'contracts.list' auf, OHNE Modul A direkt zu kennen.
Fehlt Modul A, faellt nur dieser Teil weg - Modul B laeuft trotzdem
(lose Kopplung via has_capability).
"""
from __future__ import annotations

from datetime import date

from core.interface import Capability, ModuleContext, ModuleInterface
from database import ExpenseRepository
from models import Event, Expense

_MONTHS_DE = ["Januar", "Februar", "Maerz", "April", "Mai", "Juni",
              "Juli", "August", "September", "Oktober", "November", "Dezember"]


class FinanceModule(ModuleInterface):
    """Modul B als steckbares Fachmodul."""

    def __init__(self, repo: ExpenseRepository):
        self.repo = repo
        self._ctx: ModuleContext | None = None

    # ---- Pflichtangaben des Interface ---------------------------------
    @property
    def module_id(self) -> str:
        return "finance"

    @property
    def display_name(self) -> str:
        return "Finanz-Cockpit"

    def on_register(self, context: ModuleContext) -> None:
        """Context merken - dadurch kann Modul B Modul A abfragen."""
        self._ctx = context

    def get_context_summary(self) -> str:
        today = date.today()
        ausgaben = self.repo.list_in_month(today.year, today.month)
        einmal = sum(e.amount for e in ausgaben)
        recurring, _src = self._recurring_from_contracts()
        gesamt = recurring + einmal
        return (f"Monatliche Belastung {today.strftime('%m/%Y')}: "
                f"{gesamt:.2f} EUR "
                f"(Vertraege {recurring:.2f} + einmalig {einmal:.2f}).")

    def get_events(self, horizon_days: int = 90) -> list[Event]:
        """
        Ein wiederkehrendes Ereignis: Monatsabschluss/Ausgaben pruefen.
        Faelligkeit ist der Letzte des laufenden Monats.
        """
        today = date.today()
        if today.month == 12:
            month_end = date(today.year, 12, 31)
        else:
            month_end = date(today.year, today.month + 1, 1).fromordinal(
                date(today.year, today.month + 1, 1).toordinal() - 1)
        days = (month_end - today).days
        if days < 0 or days > horizon_days:
            return []
        monat = _MONTHS_DE[today.month - 1]
        return [Event(
            title=f"Monatsabschluss {monat}: Ausgaben pruefen",
            due_date=month_end,
            module_id=self.module_id,
            module_name=self.display_name,
            category="review",
            detail="Belege erfassen, monatliche Belastung kontrollieren.",
            days_remaining=days,
        )]

    # ---- Faehigkeiten --------------------------------------------------
    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="finance.add_expense",
                description="Erfasst eine einmalige Ausgabe.",
                parameters={
                    "description": {"type": "string", "_required": True,
                                    "description": "Wofuer wurde Geld ausgegeben"},
                    "amount": {"type": "number", "_required": True,
                               "description": "Betrag in EUR"},
                    "category": {"type": "string",
                                 "description": "lebensmittel, freizeit, "
                                                "mobilitaet, sonstiges ..."},
                    "spent_on": {"type": "string",
                                 "description": "Datum ISO (YYYY-MM-DD), "
                                                "Standard: heute"},
                },
                handler=self._cap_add_expense,
            ),
            Capability(
                name="finance.list_expenses",
                description="Listet alle erfassten Ausgaben mit Summe auf.",
                parameters={},
                handler=self._cap_list_expenses,
            ),
            Capability(
                name="finance.monthly_overview",
                description="Berechnet die monatliche Belastung: einmalige "
                            "Ausgaben dieses Monats kombiniert mit den "
                            "wiederkehrenden Vertragskosten aus Modul A.",
                parameters={},
                handler=self._cap_monthly_overview,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_add_expense(self, description: str, amount: float,
                         category: str = "sonstiges",
                         spent_on: str | None = None) -> dict:
        e = Expense(
            description=description,
            amount=amount,
            category=category,
            spent_on=date.fromisoformat(spent_on) if spent_on else date.today(),
        )
        saved = self.repo.add(e)
        return {"status": "erfasst", "expense": saved.to_dict()}

    def _cap_list_expenses(self) -> dict:
        ausgaben = self.repo.list_all()
        return {
            "count": len(ausgaben),
            "total": round(sum(e.amount for e in ausgaben), 2),
            "expenses": [e.to_dict() for e in ausgaben],
        }

    def _cap_monthly_overview(self) -> dict:
        today = date.today()
        ausgaben_monat = self.repo.list_in_month(today.year, today.month)
        einmal = round(sum(e.amount for e in ausgaben_monat), 2)
        recurring, source = self._recurring_from_contracts()
        contract_count = 0
        if source == "modul_a":
            data = self._ctx.call("contracts.list") if self._ctx else {}
            contract_count = data.get("count", 0)
        return {
            "month": today.strftime("%m/%Y"),
            "recurring_contracts": round(recurring, 2),
            "contract_count": contract_count,
            "contract_costs_source": source,
            "one_time_this_month": einmal,
            "expense_count": len(ausgaben_monat),
            "total_monthly": round(recurring + einmal, 2),
        }

    # ---- Modul-zu-Modul-Aufruf ueber den Context ----------------------
    def _recurring_from_contracts(self) -> tuple[float, str]:
        """
        Holt die Vertragskosten von Modul A - ueber den ModuleContext.
        Fehlt Modul A, liefern wir 0 und kennzeichnen das transparent.
        """
        if self._ctx is None or not self._ctx.has_capability("contracts.list"):
            return 0.0, "nicht verfuegbar"
        data = self._ctx.call("contracts.list")
        if "error" in data:
            return 0.0, f"Fehler: {data['error']}"
        return float(data.get("total_monthly_cost", 0.0)), "modul_a"
