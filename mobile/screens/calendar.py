"""
Kalender-Screen: anstehende Termine.

Phone-Design:
- Liste der naechsten 30 Tage, gruppiert nach Tag
- FAB '+' fuer Schnellanlage
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

from mobile.helpers import relative_when, truncate, urgency_color
from mobile.presenters import CalendarPresenter


_URGENCY_HEX = {
    "error": (0.83, 0.18, 0.18, 1),
    "warning": (0.96, 0.49, 0.0, 1),
    "normal": (0.01, 0.53, 0.82, 1),
}


class CalendarScreen(MDScreen):

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self.presenter = CalendarPresenter(registry.dispatch)
        self._dialog = None
        self._build()

    def on_pre_enter(self, *_args):
        self._refresh()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title="Termine",
            right_action_items=[["refresh", lambda *_: self._refresh()]],
        ))
        scroll = ScrollView()
        self.container = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=dp(8),
            spacing=dp(6),
        )
        scroll.add_widget(self.container)
        root.add_widget(scroll)
        self.add_widget(root)

        fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={"right": 0.97, "y": 0.02},
            on_release=lambda *_: self._open_add_dialog(),
        )
        self.add_widget(fab)

    def _refresh(self) -> None:
        events = self.presenter.list(horizon_days=30)["items"]
        self.container.clear_widgets()
        if not events:
            self.container.add_widget(MDLabel(
                text="Keine Termine in den naechsten 30 Tagen.",
                halign="center",
                size_hint=(1, None),
                height=dp(48)))
            return
        for ev in events:
            self.container.add_widget(self._build_card(ev))

    def _build_card(self, event: dict):
        days = event.get("days_remaining")
        color = _URGENCY_HEX[urgency_color(days)]
        card = MDCard(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(72),
            padding=dp(12),
            radius=[dp(8)] * 4,
            elevation=1,
        )
        side = MDBoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=dp(56),
            md_bg_color=color,
            padding=dp(4),
            radius=[dp(8), 0, 0, dp(8)],
        )
        side.add_widget(MDLabel(
            text=relative_when(event.get("due_date") or ""),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign="center",
            font_style="Caption"))
        card.add_widget(side)
        body = MDBoxLayout(orientation="vertical", padding=(dp(8), 0))
        body.add_widget(MDLabel(
            text=truncate(event.get("title", "Termin"), 36),
            font_style="Subtitle1"))
        body.add_widget(MDLabel(
            text=event.get("due_date", ""),
            font_style="Caption",
            theme_text_color="Secondary"))
        card.add_widget(body)
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
        title = MDTextField(hint_text="Titel")
        due = MDTextField(hint_text="Datum (YYYY-MM-DD)",
                           text=date.today().isoformat())
        category = MDTextField(hint_text="Kategorie (optional)")
        for w in (title, due, category):
            body.add_widget(w)
        self._dialog = MDDialog(
            title="Neuer Termin",
            type="custom",
            content_cls=body,
            buttons=[
                MDFlatButton(text="Abbrechen",
                              on_release=lambda *_: self._dismiss()),
                MDFlatButton(
                    text="Speichern",
                    on_release=lambda *_: self._submit(
                        title.text, due.text, category.text)),
            ],
        )
        self._dialog.open()

    def _submit(self, title: str, due: str, category: str) -> None:
        self.presenter.add(title, due_date=due, category=category)
        self._dismiss()
        self._refresh()
