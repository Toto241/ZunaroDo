"""
Finanzen-Screen: Ausgabenliste + Schnell-Erfassung.

Phone-Design:
- Oben Monatssumme als Hero
- Liste der letzten 30 Tage, gruppiert nach Tag
- FAB '+' fuer Schnellerfassung (Betrag, Kategorie, Beschreibung)
"""
from __future__ import annotations

from datetime import date, timedelta

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


class FinanceScreen(MDScreen):

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
            title="Finanzen",
            right_action_items=[["refresh", lambda *_: self._refresh()]],
        ))

        self.summary_label = MDLabel(
            text="...",
            font_style="H6",
            halign="center",
            size_hint=(1, None),
            height=dp(48),
        )
        root.add_widget(self.summary_label)

        self.scroll = ScrollView()
        self.container = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=dp(8),
            spacing=dp(4),
        )
        self.scroll.add_widget(self.container)
        root.add_widget(self.scroll)
        self.add_widget(root)

        fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={"right": 0.97, "y": 0.02},
            on_release=lambda *_: self._open_add_dialog(),
        )
        self.add_widget(fab)

    def _refresh(self) -> None:
        result = self.registry.dispatch("finance.list_expenses", {})
        expenses = result.get("expenses", [])
        # Letzte 30 Tage
        cutoff = date.today() - timedelta(days=30)
        recent = []
        total = 0.0
        for e in expenses:
            spent = e.get("spent_on")
            try:
                d = date.fromisoformat(spent) if spent else date.today()
            except ValueError:
                d = date.today()
            if d >= cutoff:
                recent.append((d, e))
                total += float(e.get("amount", 0) or 0)
        recent.sort(key=lambda kv: kv[0], reverse=True)

        self.summary_label.text = (f"Letzte 30 Tage: "
                                     f"{format_currency(total)}")
        self.container.clear_widgets()

        last_day = None
        for d, e in recent:
            if d != last_day:
                last_day = d
                self.container.add_widget(MDLabel(
                    text=d.strftime("%a, %d.%m."),
                    font_style="Subtitle2",
                    theme_text_color="Secondary",
                    size_hint=(1, None),
                    height=dp(28),
                    padding=(dp(8), 0),
                ))
            self.container.add_widget(self._build_card(e))

        if not recent:
            self.container.add_widget(MDLabel(
                text="Noch keine Ausgaben in den letzten 30 Tagen.",
                halign="center",
                size_hint=(1, None),
                height=dp(48)))

    def _build_card(self, expense: dict):
        card = MDCard(
            size_hint=(1, None),
            height=dp(56),
            padding=dp(10),
            radius=[dp(8)] * 4,
            elevation=0,
        )
        row = MDBoxLayout(orientation="horizontal")
        row.add_widget(MDLabel(
            text=truncate(expense.get("description", "?"), 28)))
        row.add_widget(MDLabel(
            text=format_currency(expense.get("amount", 0)),
            halign="right",
            theme_text_color="Primary"))
        card.add_widget(row)
        return card

    def _dismiss(self) -> None:
        if self._dialog is not None:
            self._dialog.dismiss()
            self._dialog = None

    def _open_add_dialog(self) -> None:
        body = MDBoxLayout(orientation="vertical",
                             spacing=dp(8),
                             adaptive_height=True,
                             padding=dp(8))
        desc = MDTextField(hint_text="Beschreibung")
        amount = MDTextField(hint_text="Betrag (EUR)",
                              input_filter="float")
        category = MDTextField(hint_text="Kategorie (optional)")
        for w in (desc, amount, category):
            body.add_widget(w)
        self._dialog = MDDialog(
            title="Neue Ausgabe",
            type="custom",
            content_cls=body,
            buttons=[
                MDFlatButton(text="Abbrechen",
                              on_release=lambda *_: self._dismiss()),
                MDFlatButton(
                    text="Speichern",
                    on_release=lambda *_: self._submit(
                        desc.text, amount.text, category.text)),
            ],
        )
        self._dialog.open()

    def _submit(self, description: str, amount: str, category: str) -> None:
        try:
            amt = float(amount)
        except ValueError:
            return
        args = {
            "description": description.strip() or "Ausgabe",
            "amount": amt,
        }
        if category.strip():
            args["category"] = category.strip()
        self.registry.dispatch("finance.add_expense", args)
        self._dismiss()
        self._refresh()
