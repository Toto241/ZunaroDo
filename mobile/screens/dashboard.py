"""
Dashboard-Screen: Schnellueberblick + naechste Fristen/Termine.

Phone-Design:
- Hero-Card oben (Anzahl aktive Vertraege, monatl. Gesamtkosten)
- Scrollbare Liste 'Anstehend' (Vertraege + Termine zusammen)
- Pull-to-Refresh
"""
from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (MDList, OneLineAvatarIconListItem,
                              ThreeLineAvatarIconListItem,
                              IconLeftWidget)
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar

from mobile.helpers import format_currency, relative_when, urgency_color
from mobile.presenters import DashboardPresenter
from mobile.ui_text import t as _t


_URGENCY_HEX = {
    "error": "#D32F2F",
    "warning": "#F57C00",
    "normal": "#0288D1",
}


class DashboardScreen(MDScreen):

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self.presenter = DashboardPresenter(registry.dispatch)
        self._mode = "upcoming"            # "upcoming" | "week"
        self._build()

    def on_pre_enter(self, *_args):
        self._refresh()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=_t("app.title", "Alltagshelfer"),
            right_action_items=[
                ["calendar-week", lambda *_: self._toggle_mode()],
                ["refresh", lambda *_: self._refresh()],
            ],
        ))

        # Hero-Card mit Kennzahlen
        self.hero = MDCard(
            orientation="vertical",
            padding=dp(16),
            size_hint=(1, None),
            height=dp(110),
            radius=[dp(12)] * 4,
            md_bg_color=(0.18, 0.46, 0.89, 1),
            elevation=2,
        )
        self.hero_top = MDLabel(
            text="...",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6",
        )
        self.hero_sub = MDLabel(
            text="...",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.85),
        )
        self.hero.add_widget(self.hero_top)
        self.hero.add_widget(self.hero_sub)

        hero_wrap = BoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(12), dp(12), dp(4)),
            size_hint=(1, None),
            height=dp(128),
        )
        hero_wrap.add_widget(self.hero)
        root.add_widget(hero_wrap)

        # Listen-Sektion 'Anstehend'
        section_label = MDLabel(
            text=_t("dashboard.upcoming", "Anstehend"),
            font_style="Subtitle1",
            size_hint=(1, None),
            height=dp(32),
            padding=(dp(16), 0),
        )
        root.add_widget(section_label)

        scroll = ScrollView()
        self.list = MDList()
        scroll.add_widget(self.list)
        root.add_widget(scroll)

        self.add_widget(root)

    def _toggle_mode(self) -> None:
        self._mode = "week" if self._mode == "upcoming" else "upcoming"
        self._refresh()

    def _refresh(self) -> None:
        data = self.presenter.summary()
        n = data["contracts_count"]
        total = data["monthly_total"]
        self.hero_top.text = f"{n} aktive Vertraege"
        self.hero_sub.text = (f"Monatlich gesamt: "
                              f"{format_currency(total)}")

        self.list.clear_widgets()

        if self._mode == "week":
            self._render_week()
            return

        # Kuendigungsfristen zuerst
        for d in data.get("upcoming_deadlines", []):
            days = d.get("days_remaining")
            color = _URGENCY_HEX[urgency_color(days)]
            self.list.add_widget(ThreeLineAvatarIconListItem(
                IconLeftWidget(icon="alert-circle",
                                 theme_icon_color="Custom",
                                 icon_color=color),
                text=f"Kuendigungsfrist: {d.get('contract_name','?')}",
                secondary_text=relative_when(d.get("due_date")),
                tertiary_text=f"{d.get('due_date','')}",
            ))

        # Termine danach
        for ev in data.get("upcoming_events", []):
            days = None
            try:
                from mobile.helpers import days_until
                days = days_until(ev.get("due_date"))
            except Exception:
                pass
            color = _URGENCY_HEX[urgency_color(days)]
            self.list.add_widget(OneLineAvatarIconListItem(
                IconLeftWidget(icon="calendar",
                                 theme_icon_color="Custom",
                                 icon_color=color),
                text=(f"{ev.get('title','Termin')} – "
                      f"{relative_when(ev.get('due_date'))}"),
            ))

        if not self.list.children:
            self.list.add_widget(OneLineAvatarIconListItem(
                IconLeftWidget(icon="check-circle"),
                text="Keine offenen Punkte. Schoenes Leben!",
            ))

    def _render_week(self) -> None:
        """Tages-/Wochenuebersicht (system.agenda), nach Tag gruppiert."""
        agenda = self.presenter.week(horizon_days=7)
        if agenda["overdue_count"]:
            self.list.add_widget(OneLineAvatarIconListItem(
                IconLeftWidget(icon="alert-circle",
                                 theme_icon_color="Custom",
                                 icon_color=_URGENCY_HEX["error"]),
                text=f"{_t('dashboard.overdue', 'Ueberfaellig')} "
                     f"({agenda['overdue_count']})",
            ))
            for ev in agenda["overdue"]:
                self.list.add_widget(OneLineAvatarIconListItem(
                    IconLeftWidget(icon="chevron-right"),
                    text=ev.get("title", ""),
                ))
        for day in agenda["days"]:
            self.list.add_widget(OneLineAvatarIconListItem(
                IconLeftWidget(icon="calendar"),
                text=f"{day.get('weekday','')}, {day.get('date','')}"
                     f"  ({day.get('count', 0)})",
            ))
            for ev in day.get("events", []):
                self.list.add_widget(OneLineAvatarIconListItem(
                    IconLeftWidget(icon="chevron-right"),
                    text=ev.get("title", ""),
                ))
        if not self.list.children:
            self.list.add_widget(OneLineAvatarIconListItem(
                IconLeftWidget(icon="check-circle"),
                text="Diese Woche nichts faellig.",
            ))
