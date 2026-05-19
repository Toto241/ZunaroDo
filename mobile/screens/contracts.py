"""
Verträge-Screen: scrollbare Liste + FAB zum Hinzufügen.

Phone-Design:
- Jeder Eintrag ist eine MDCard mit Name, Anbieter, monatl. Kosten
- Tap auf Karte oeffnet Detail-Bottom-Sheet
- FAB unten rechts -> Dialog 'Neuer Vertrag'
"""
from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

from mobile.helpers import format_currency, truncate


class ContractsScreen(MDScreen):

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self._dialog = None
        self._build()

    def on_pre_enter(self, *_args):
        self._refresh()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title="Vertraege",
            right_action_items=[["refresh", lambda *_: self._refresh()]],
        ))

        self.scroll = ScrollView()
        self.container = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=dp(8),
            spacing=dp(8),
        )
        self.scroll.add_widget(self.container)
        root.add_widget(self.scroll)

        fab_anchor = BoxLayout(size_hint=(1, None), height=dp(0))
        fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={"right": 0.97, "y": 0.02},
            on_release=lambda *_: self._open_add_dialog(),
        )
        # FAB direkt an Screen statt Box - bleibt fixiert unten rechts
        self.add_widget(root)
        self.add_widget(fab)

    def _refresh(self) -> None:
        result = self.registry.dispatch("contracts.list", {})
        self.container.clear_widgets()
        contracts = result.get("contracts", [])
        total = result.get("total_monthly_cost", 0.0)

        # Header-Card mit Summe
        if contracts:
            header = MDCard(
                size_hint=(1, None),
                height=dp(56),
                padding=dp(12),
                radius=[dp(8)] * 4,
                elevation=0,
                md_bg_color=(0.93, 0.96, 1.0, 1),
            )
            header.add_widget(MDLabel(
                text=f"{len(contracts)} aktiv – "
                     f"monatlich {format_currency(total)}",
                font_style="Subtitle1"))
            self.container.add_widget(header)
        else:
            self.container.add_widget(MDLabel(
                text="Noch keine Vertraege. Tipp auf +.",
                halign="center",
                size_hint=(1, None),
                height=dp(48)))

        for c in contracts:
            self.container.add_widget(self._build_card(c))

    def _build_card(self, contract: dict):
        card = MDCard(
            orientation="vertical",
            padding=dp(12),
            size_hint=(1, None),
            height=dp(100),
            radius=[dp(10)] * 4,
            elevation=1,
            ripple_behavior=True,
        )
        title_row = MDBoxLayout(orientation="horizontal",
                                adaptive_height=True)
        title_row.add_widget(MDLabel(
            text=truncate(contract.get("name", ""), 32),
            font_style="Subtitle1"))
        title_row.add_widget(MDLabel(
            text=format_currency(contract.get("monthly_cost", 0)),
            halign="right",
            font_style="Subtitle1"))
        card.add_widget(title_row)

        sub = MDLabel(
            text=f"{contract.get('provider','')} · "
                 f"{contract.get('category','')}",
            font_style="Caption",
            theme_text_color="Secondary",
        )
        card.add_widget(sub)

        cid = contract.get("id")
        card.bind(on_release=lambda *_: self._open_detail(cid))
        return card

    def _open_detail(self, cid):
        if cid is None:
            return
        result = self.registry.dispatch("contracts.list", {})
        contract = next(
            (c for c in result.get("contracts", []) if c.get("id") == cid),
            None)
        if contract is None:
            return
        text = (f"Anbieter: {contract.get('provider','-')}\n"
                f"Kategorie: {contract.get('category','-')}\n"
                f"Start: {contract.get('start_date','-')}\n"
                f"Kuendigungsfrist: "
                f"{contract.get('notice_period_months','-')} Monate\n"
                f"Kosten: {format_currency(contract.get('monthly_cost',0))}")
        self._dialog = MDDialog(
            title=contract.get("name", "Vertrag"),
            text=text,
            buttons=[
                MDFlatButton(text="Loeschen",
                              on_release=lambda *_: self._delete(cid)),
                MDFlatButton(text="Schliessen",
                              on_release=lambda *_: self._dismiss()),
            ],
        )
        self._dialog.open()

    def _delete(self, cid: int) -> None:
        self.registry.dispatch("contracts.delete", {"contract_id": cid})
        self._dismiss()
        self._refresh()

    def _dismiss(self) -> None:
        if self._dialog is not None:
            self._dialog.dismiss()
            self._dialog = None

    def _open_add_dialog(self) -> None:
        body = MDBoxLayout(orientation="vertical",
                             spacing=dp(8),
                             adaptive_height=True,
                             padding=dp(8))
        name = MDTextField(hint_text="Name")
        category = MDTextField(hint_text="Kategorie "
                                 "(streaming/mobilfunk/...)")
        provider = MDTextField(hint_text="Anbieter")
        cost = MDTextField(hint_text="Monatlich (EUR)",
                            input_filter="float")
        for w in (name, category, provider, cost):
            body.add_widget(w)
        self._dialog = MDDialog(
            title="Neuer Vertrag",
            type="custom",
            content_cls=body,
            buttons=[
                MDFlatButton(text="Abbrechen",
                              on_release=lambda *_: self._dismiss()),
                MDFlatButton(
                    text="Speichern",
                    on_release=lambda *_: self._submit_add(
                        name.text, category.text, provider.text,
                        cost.text)),
            ],
        )
        self._dialog.open()

    def _submit_add(self, name: str, category: str, provider: str,
                     cost: str) -> None:
        try:
            cost_val = float(cost) if cost else 0.0
        except ValueError:
            cost_val = 0.0
        self.registry.dispatch("contracts.add", {
            "name": name.strip() or "Unbenannt",
            "category": (category.strip() or "sonstiges"),
            "provider": provider.strip(),
            "monthly_cost": cost_val,
        })
        self._dismiss()
        self._refresh()
