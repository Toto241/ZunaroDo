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
from database import ExpenseRepository, PriceMemoryRepository
from models import Event, Expense

_MONTHS_DE = ["Januar", "Februar", "Maerz", "April", "Mai", "Juni",
              "Juli", "August", "September", "Oktober", "November", "Dezember"]


class FinanceModule(ModuleInterface):
    """Modul B als steckbares Fachmodul."""

    def __init__(self, repo: ExpenseRepository,
                 price_memory: PriceMemoryRepository | None = None):
        self.repo = repo
        self.price_memory = price_memory
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
                    "owner_id": {"type": "integer",
                                 "description": "Optional: Person, der die "
                                                "Ausgabe zugeordnet wird "
                                                "(siehe family.members)"},
                },
                handler=self._cap_add_expense,
            ),
            Capability(
                name="finance.expenses_by_category",
                description="Aggregiert die Ausgaben pro Kategorie.",
                parameters={
                    "month": {"type": "string",
                              "description": "Optional: 'YYYY-MM', sonst alle"},
                },
                handler=self._cap_by_category,
            ),
            Capability(
                name="finance.expenses_by_person",
                description="Aggregiert die Ausgaben pro Haushaltsmitglied "
                            "(loest die owner_id ueber family.members auf).",
                parameters={
                    "month": {"type": "string",
                              "description": "Optional: 'YYYY-MM', sonst alle"},
                },
                handler=self._cap_by_person,
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
            Capability(
                name="finance.remember_price",
                description="Merkt sich den aktuellen Preis eines Produkts "
                            "(Preis-Gedaechtnis fuer wiederkehrende Einkaeufe).",
                parameters={
                    "product": {"type": "string", "_required": True,
                                "description": "Bezeichnung des Produkts"},
                    "price": {"type": "number", "_required": True,
                              "description": "Aktueller Preis in EUR"},
                    "category": {"type": "string",
                                 "description": "Kategorie, z.B. 'lebensmittel'"},
                },
                handler=self._cap_remember_price,
            ),
            Capability(
                name="finance.price_memory",
                description="Listet die gespeicherten Preise wiederkehrender "
                            "Produkte auf.",
                parameters={},
                handler=self._cap_price_memory,
            ),
            Capability(
                name="finance.scan_receipt",
                description="Liest einen Kassenbon per OCR ein und extrahiert "
                            "Posten und Summe (erfordert pytesseract + Tesseract; "
                            "ohne Installation gibt es einen klaren Hinweis).",
                parameters={
                    "image_path": {"type": "string", "_required": True,
                                   "description": "Pfad zur Bilddatei "
                                                  "(jpg / png)"},
                },
                handler=self._cap_scan_receipt,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_add_expense(self, description: str, amount: float,
                         category: str = "sonstiges",
                         spent_on: str | None = None,
                         owner_id: int | None = None) -> dict:
        e = Expense(
            description=description,
            amount=amount,
            category=category,
            spent_on=date.fromisoformat(spent_on) if spent_on else date.today(),
            owner_id=owner_id if owner_id else None,
        )
        saved = self.repo.add(e)
        # owner_name nachladen (kommt aus dem JOIN bei list_all)
        for ex in self.repo.list_all():
            if ex.id == saved.id:
                saved = ex
                break
        return {"status": "erfasst", "expense": saved.to_dict()}

    def _cap_by_category(self, month: str | None = None) -> dict:
        ausgaben = self._select_expenses(month)
        sums: dict[str, float] = {}
        for e in ausgaben:
            sums[e.category] = sums.get(e.category, 0.0) + e.amount
        return {"month": month or "alle",
                "categories": [{"category": k, "total": round(v, 2)}
                                for k, v in sorted(sums.items(),
                                                    key=lambda kv: -kv[1])]}

    def _cap_by_person(self, month: str | None = None) -> dict:
        ausgaben = self._select_expenses(month)
        sums: dict[str, float] = {}
        for e in ausgaben:
            key = e.owner_name or "(keine Zuordnung)"
            sums[key] = sums.get(key, 0.0) + e.amount
        return {"month": month or "alle",
                "persons": [{"person": k, "total": round(v, 2)}
                             for k, v in sorted(sums.items(),
                                                 key=lambda kv: -kv[1])]}

    # ---- Preis-Gedaechtnis ---------------------------------------------
    def _cap_remember_price(self, product: str, price: float,
                            category: str = "sonstiges") -> dict:
        if self.price_memory is None:
            return {"error": "Preis-Gedaechtnis nicht verfuegbar"}
        previous = next((p for p in self.price_memory.list_all()
                          if p.product.lower() == product.lower()), None)
        saved = self.price_memory.remember(product, price, category)
        diff = None if previous is None else round(price - previous.last_price, 2)
        return {"status": "gemerkt",
                "product": saved.product,
                "price": saved.last_price,
                "previous_price": previous.last_price if previous else None,
                "difference": diff,
                "category": saved.category}

    def _cap_price_memory(self) -> dict:
        if self.price_memory is None:
            return {"count": 0, "products": []}
        eintraege = self.price_memory.list_all()
        return {"count": len(eintraege),
                "products": [p.to_dict() for p in eintraege]}

    # ---- OCR fuer Kassenbons -------------------------------------------
    def _cap_scan_receipt(self, image_path: str) -> dict:
        try:
            from services.ocr import scan_receipt
        except Exception as exc:                       # pragma: no cover
            return {"error": f"OCR-Dienst nicht geladen: {exc}"}
        return scan_receipt(image_path)

    def _select_expenses(self, month: str | None) -> list[Expense]:
        if month:
            try:
                year, mon = month.split("-")
                return self.repo.list_in_month(int(year), int(mon))
            except (ValueError, AttributeError):
                return []
        return self.repo.list_all()

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
