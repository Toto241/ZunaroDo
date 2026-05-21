"""
Headless-App: eine UI-freie, vollautomatisch testbare Variante der App.

Sie baut **dieselbe Registry** wie die echten Clients (über
``main.build_registry``) und stellt das Verhalten aller Screens über die
Presenter (``mobile.presenters``) bereit - ganz ohne Toolkit, Display,
Kivy oder Emulator. So lassen sich Navigations- und Screen-Flows
end-to-end automatisiert testen (siehe tests/test_headless_app.py).

    app = HeadlessApp()                 # eigene Temp-DB
    app.navigate("contracts")
    app.contracts.add(name="Strom", category="strom", monthly_cost=30)
    view = app.contracts.list(category="strom")
    app.close()
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional

from database import Database
from services.output import OutputService

from mobile.presenters import (CalendarPresenter, ContactsPresenter,
                               ContractsPresenter, DashboardPresenter,
                               FinancePresenter, OrdersPresenter,
                               SearchPresenter)


class HeadlessApp:
    """Toolkit-freie App-Fassade über Registry + Presentern."""

    TABS = ("dashboard", "contracts", "finance", "calendar", "more")

    def __init__(self, registry=None, *, db_path: Optional[str] = None,
                 output=None) -> None:
        self._owns_db = False
        self._db = None
        self._tmp_db: Optional[str] = None
        if registry is None:
            from main import build_registry
            if db_path is None:
                fd, db_path = tempfile.mkstemp(suffix=".db")
                os.close(fd)
                self._tmp_db = db_path
            self._db = Database(db_path)
            self._owns_db = True
            output = output or OutputService(
                tempfile.mkdtemp(prefix="ah_headless_"))
            registry = build_registry(self._db, output)

        self.registry = registry
        self.dispatch = registry.dispatch
        self.dashboard = DashboardPresenter(self.dispatch)
        self.contracts = ContractsPresenter(self.dispatch)
        self.orders = OrdersPresenter(self.dispatch)
        self.contacts = ContactsPresenter(self.dispatch)
        self.search = SearchPresenter(self.dispatch)
        self.calendar = CalendarPresenter(self.dispatch)
        self.finance = FinancePresenter(self.dispatch)
        self._tab = "dashboard"

    # ---- Navigation ---------------------------------------------------
    def navigate(self, tab: str) -> str:
        if tab not in self.TABS:
            raise ValueError(f"Unbekannter Tab: {tab!r}")
        self._tab = tab
        return tab

    @property
    def current_tab(self) -> str:
        return self._tab

    # ---- Lebenszyklus -------------------------------------------------
    def close(self) -> None:
        if self._owns_db and self._db is not None:
            try:
                self._db.close()
            finally:
                self._db = None
                if self._tmp_db and os.path.exists(self._tmp_db):
                    try:
                        os.unlink(self._tmp_db)
                    except OSError:
                        pass

    def __enter__(self) -> "HeadlessApp":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
