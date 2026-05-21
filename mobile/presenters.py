"""
Presenter-/Headless-Schicht der App (toolkit-unabhängig).

Hier liegt das **Verhalten** der Screens als reines Python: welche
Capability mit welchen Argumenten aufgerufen wird und wie das Ergebnis zu
einem Anzeige-Modell (inkl. Leer-/Fehlerzuständen) wird. Die echten
Kivy-/customtkinter-Screens sind nur noch dünne Adapter, die diese
Presenter aufrufen und das zurückgegebene Modell rendern.

Vorteil: Das komplette UI-Verhalten ist damit **ohne Display, Kivy oder
Emulator vollautomatisch testbar** (siehe tests/test_presenters.py,
tests/test_headless_app.py) - genau die Tests, die sich mit der reinen
Widget-UI nicht einfach automatisieren lassen.
"""
from __future__ import annotations

from typing import Any, Callable

from mobile.helpers import (build_order_payload, build_search_args,
                            dashboard_summary, distinct_values,
                            search_args_valid, week_agenda)

Dispatch = Callable[[str, dict], dict]


class DashboardPresenter:
    def __init__(self, dispatch: Dispatch) -> None:
        self.dispatch = dispatch

    def summary(self) -> dict[str, Any]:
        return dashboard_summary(self.dispatch)

    def week(self, horizon_days: int = 7) -> dict[str, Any]:
        return week_agenda(self.dispatch, horizon_days)


class ContractsPresenter:
    def __init__(self, dispatch: Dispatch) -> None:
        self.dispatch = dispatch

    def list(self, category: str | None = None) -> dict[str, Any]:
        args: dict[str, Any] = {}
        chosen = (category or "").strip()
        if chosen:
            args["category"] = chosen
        result = self.dispatch("contracts.list", args) or {}
        contracts = result.get("contracts", [])
        return {
            "items": contracts,
            "count": len(contracts),
            "total_monthly_cost": result.get("total_monthly_cost", 0.0),
            "empty": not contracts,
            "empty_text": "Noch keine Vertraege. Tipp auf +.",
            "filter": chosen,
        }

    def detail(self, contract_id: Any) -> dict | None:
        if contract_id is None:
            return None
        contracts = (self.dispatch("contracts.list", {}) or {}).get(
            "contracts", [])
        return next((c for c in contracts
                     if c.get("id") == contract_id), None)

    def add(self, name: str, category: str = "", provider: str = "",
            monthly_cost: float = 0.0) -> dict:
        try:
            cost = float(monthly_cost)
        except (TypeError, ValueError):
            cost = 0.0
        return self.dispatch("contracts.add", {
            "name": (name or "").strip() or "Unbenannt",
            "category": (category or "").strip() or "sonstiges",
            "provider": (provider or "").strip(),
            "monthly_cost": cost,
        })

    def delete(self, contract_id: Any) -> dict:
        return self.dispatch("contracts.delete", {"contract_id": contract_id})


class OrdersPresenter:
    def __init__(self, dispatch: Dispatch) -> None:
        self.dispatch = dispatch

    def list(self) -> dict[str, Any]:
        result = self.dispatch("family.orders", {}) or {}
        orders = result.get("orders", [])
        return {
            "items": orders,
            "count": len(orders),
            "empty": not orders,
            "empty_text": "Keine Auftraege. Tipp auf +.",
        }

    def add(self, title: str, assignee: str = "", due_date: str = "",
            description: str = "", priority: str = "normal",
            category: str = "") -> dict:
        payload = build_order_payload(
            title, assignee=assignee, due_date=due_date,
            description=description, priority=priority, category=category)
        if payload is None:
            return {"error": "Titel fehlt"}
        return self.dispatch("family.add_order", payload)

    def complete(self, order_id: Any) -> dict:
        return self.dispatch("family.complete_order", {"order_id": order_id})


class ContactsPresenter:
    def __init__(self, dispatch: Dispatch) -> None:
        self.dispatch = dispatch

    def list(self, relation: str | None = None) -> dict[str, Any]:
        all_contacts = (self.dispatch("social.contacts", {}) or {}).get(
            "contacts", [])
        relations = distinct_values(all_contacts, "relation")
        chosen = (relation or "").strip()
        if chosen:
            contacts = (self.dispatch(
                "social.contacts", {"relation": chosen}) or {}).get(
                "contacts", [])
        else:
            contacts = all_contacts
        return {
            "items": contacts,
            "count": len(contacts),
            "empty": not contacts,
            "empty_text": "Keine Kontakte.",
            "relations": relations,
            "filter": chosen,
        }


class SearchPresenter:
    def __init__(self, dispatch: Dispatch) -> None:
        self.dispatch = dispatch

    def search(self, query: str, *, category: str | None = None,
               status: str | None = None, date_from: str | None = None,
               date_to: str | None = None) -> dict[str, Any]:
        args = build_search_args(query, category=category, status=status,
                                 date_from=date_from, date_to=date_to)
        if not search_args_valid(args):
            return {"status": "too_short", "hits": [], "count": 0,
                    "message": "Mind. 2 Zeichen oder einen Filter angeben."}
        result = self.dispatch("system.search", args) or {}
        if "error" in result:
            return {"status": "error", "hits": [], "count": 0,
                    "message": str(result["error"])}
        hits = result.get("hits", [])
        return {
            "status": "ok" if hits else "empty",
            "hits": hits,
            "count": result.get("count", len(hits)),
            "message": "" if hits else "Keine Treffer.",
        }


class CalendarPresenter:
    def __init__(self, dispatch: Dispatch) -> None:
        self.dispatch = dispatch

    def list(self, horizon_days: int = 30) -> dict[str, Any]:
        result = self.dispatch(
            "calendar.upcoming", {"horizon_days": horizon_days}) or {}
        events = result.get("events", [])
        return {
            "items": events,
            "count": len(events),
            "empty": not events,
            "empty_text": f"Keine Termine in den naechsten "
                          f"{horizon_days} Tagen.",
        }

    def add(self, title: str, due_date: str, category: str = "") -> dict:
        from datetime import date
        args: dict[str, Any] = {
            "title": (title or "").strip() or "Termin",
            "due_date": (due_date or "").strip() or date.today().isoformat(),
        }
        if (category or "").strip():
            args["category"] = category.strip()
        return self.dispatch("calendar.add_event", args)


class FinancePresenter:
    def __init__(self, dispatch: Dispatch) -> None:
        self.dispatch = dispatch

    def list(self) -> dict[str, Any]:
        result = self.dispatch("finance.list_expenses", {}) or {}
        expenses = result.get("expenses", [])
        return {
            "items": expenses,
            "count": len(expenses),
            "empty": not expenses,
            "empty_text": "Noch keine Ausgaben erfasst.",
        }
