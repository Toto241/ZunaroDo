"""
Finanzen-Screen: Ausgabenliste + Schnell-Erfassung.

Phone-Design:
- Oben Monatssumme als Hero
- Liste der letzten 30 Tage, gruppiert nach Tag
- FAB '+' fuer Schnellerfassung (Betrag, Kategorie, Beschreibung)
"""
from __future__ import annotations

from datetime import date

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
from mobile.presenters import FinancePresenter
from mobile.ui_text import t as _t


class FinanceScreen(MDScreen):

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self.presenter = FinancePresenter(registry.dispatch)
        self._dialog = None
        self._build()

    def on_pre_enter(self, *_args):
        self._refresh()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=_t("tab.finance", "Finanzen"),
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
        view = self.presenter.recent(days=30)
        recent = [(date.fromisoformat(e["spent_on"]) if e.get("spent_on")
                   else date.today(), e) for e in view["items"]]

        self.summary_label.text = (f"Letzte 30 Tage: "
                                     f"{format_currency(view['total'])}")
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
                text=_t(view["empty_text_key"], view["empty_text"]).format(
                    **view.get("empty_text_params", {})),
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
        desc = MDTextField(hint_text=_t("form.note", "Beschreibung"))
        amount = MDTextField(hint_text=_t("form.amount", "Betrag (EUR)"),
                              input_filter="float")
        category = MDTextField(hint_text=_t("form.category", "Kategorie")
                               + " (" + _t("form.optional", "optional") + ")")
        for w in (desc, amount, category):
            body.add_widget(w)
        self._dialog = MDDialog(
            title=_t("action.add_expense", "Neue Ausgabe"),
            type="custom",
            content_cls=body,
            buttons=[
                MDFlatButton(text=_t("action.cancel", "Abbrechen"),
                              on_release=lambda *_: self._dismiss()),
                MDFlatButton(
                    text=_t("action.save", "Speichern"),
                    on_release=lambda *_: self._submit(
                        desc.text, amount.text, category.text)),
            ],
        )
        self._dialog.open()

    def _submit(self, description: str, amount: str, category: str) -> None:
        result = self.presenter.add(description, amount, category)
        if "error" in result:
            return
        self._dismiss()
        self._refresh()
