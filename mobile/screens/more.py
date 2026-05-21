"""
"Mehr"-Screen: sammelt die Funktionen, die nicht in die Bottom-Nav passen.

Phone-Design:
- Einfache Liste mit Icons als Einstiegspunkte
- Beim Tap wird ein Sub-Screen geoeffnet, der die jeweilige Capability
  abbildet (Liste anzeigen, einfache Aktionen).
"""
from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar

from mobile.helpers import language_menu_items
from services import config as app_config
from services.data_deletion import delete_all_user_data, sandbox_data_dirs


class _SimpleListPage(MDScreen):
    """Generische Folge-Seite: ruft eine Capability auf und listet Ergebnisse."""

    def __init__(self, title: str, capability: str,
                 result_key: str, label_fn, registry, **kwargs):
        super().__init__(**kwargs)
        self.title_text = title
        self.capability = capability
        self.result_key = result_key
        self.label_fn = label_fn
        self.registry = registry
        self._build()
        self._refresh()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=self.title_text,
            left_action_items=[
                ["arrow-left", lambda *_: self._go_back()]],
            right_action_items=[
                ["refresh", lambda *_: self._refresh()]],
        ))
        scroll = ScrollView()
        self.list = MDList()
        scroll.add_widget(self.list)
        root.add_widget(scroll)
        self.add_widget(root)

    def _refresh(self) -> None:
        try:
            result = self.registry.dispatch(self.capability, {})
        except Exception as exc:
            result = {self.result_key: [], "_err": str(exc)}
        self.list.clear_widgets()
        items = result.get(self.result_key, [])
        if not items:
            self.list.add_widget(OneLineIconListItem(
                IconLeftWidget(icon="information-outline"),
                text="Noch keine Eintraege.",
            ))
            return
        for item in items:
            self.list.add_widget(OneLineIconListItem(
                IconLeftWidget(icon="chevron-right"),
                text=self.label_fn(item),
            ))

    def _go_back(self) -> None:
        parent = self.parent
        if parent is not None and hasattr(parent, "remove_widget"):
            parent.remove_widget(self)


class _LanguagePage(MDScreen):
    """Sprachumschalter: schreibt 'i18n.language' und bittet um Neustart."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()
        self._refresh()

    def _build(self) -> None:
        app = MDApp.get_running_app()
        title = app.i18n.t("tab.settings") if app is not None else "Sprache"
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=title,
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
        ))
        # Hinweiszeile (Neustart noetig) - anfangs leer.
        self.hint = MDLabel(
            text="", halign="center", size_hint_y=None, height=dp(28),
            theme_text_color="Custom",
        )
        root.add_widget(self.hint)
        scroll = ScrollView()
        self.list = MDList()
        scroll.add_widget(self.list)
        root.add_widget(scroll)
        self.add_widget(root)

    def _current_setting(self) -> str:
        app = MDApp.get_running_app()
        if app is not None and getattr(app, "settings", None) is not None:
            return app.settings.get("i18n.language", "de") or "de"
        return "de"

    def _refresh(self) -> None:
        self.list.clear_widgets()
        for entry in language_menu_items(self._current_setting()):
            icon = "check-circle" if entry["selected"] else "circle-outline"
            item = OneLineIconListItem(
                IconLeftWidget(icon=icon),
                text=entry["label"],
            )
            item.bind(on_release=self._make_handler(entry["code"]))
            self.list.add_widget(item)

    def _make_handler(self, code: str):
        def handler(_widget):
            app = MDApp.get_running_app()
            if app is None or getattr(app, "settings", None) is None:
                return
            app_config.save_value(app.settings, "i18n.language", code)
            self._refresh()
            # 'settings.save' enthaelt bereits den Neustart-Hinweis.
            self.hint.text = app.i18n.t("settings.save")
        return handler

    def _go_back(self) -> None:
        parent = self.parent
        if parent is not None and hasattr(parent, "remove_widget"):
            parent.remove_widget(self)


class _DataDeletionPage(MDScreen):
    """Voll-Loeschung aller Nutzerdaten mit ausdruecklicher Bestaetigung."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._done = False
        self._build()

    def _t(self, key: str, default: str = "") -> str:
        app = MDApp.get_running_app()
        return app.i18n.t(key, default) if app is not None else (default or key)

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=self._t("data.delete_section", "Daten loeschen"),
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
        ))
        # Warnhinweis (mehrzeilig).
        self.warning = MDLabel(
            text=self._t("data.delete_warning"),
            halign="center", valign="top",
            padding=(dp(16), dp(16)),
        )
        root.add_widget(self.warning)

        scroll = ScrollView()
        self.list = MDList()
        # Bewusst zweistufig: Eintrag im MoreScreen -> diese Seite ->
        # dieser explizite, destruktiv beschriftete Bestaetigungsknopf.
        self.confirm_item = OneLineIconListItem(
            IconLeftWidget(icon="delete-alert"),
            text=self._t("data.delete_confirm_action", "Endgueltig loeschen"),
        )
        self.confirm_item.bind(on_release=lambda *_: self._perform())
        self.list.add_widget(self.confirm_item)
        scroll.add_widget(self.list)
        root.add_widget(scroll)
        self.add_widget(root)

    def _perform(self) -> None:
        if self._done:
            return
        app = MDApp.get_running_app()
        db = getattr(app, "_db", None) if app is not None else None
        if db is None:
            return
        data_dirs = (sandbox_data_dirs(app.user_data_dir)
                     if hasattr(app, "user_data_dir") else [])
        delete_all_user_data(db, data_dirs=data_dirs, include_settings=True)
        self._done = True
        # Bestaetigungsknopf entfernen, Done-Hinweis anzeigen.
        self.list.clear_widgets()
        self.warning.text = self._t(
            "data.delete_done", "Alle Daten geloescht. Bitte App neu starten.")

    def _go_back(self) -> None:
        parent = self.parent
        if parent is not None and hasattr(parent, "remove_widget"):
            parent.remove_widget(self)


class MoreScreen(MDScreen):

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self._build()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(title="Mehr"))
        scroll = ScrollView()
        self.list = MDList()
        scroll.add_widget(self.list)
        root.add_widget(scroll)
        self.add_widget(root)

        # Eintraege definieren
        self._entries = [
            ("account-multiple", "Familie / Haushalt",
             "family.members", "members",
             lambda m: f"{m.get('name','?')} ({m.get('role','-')})"),
            ("account-heart", "Kontakte",
             "social.list_contacts", "contacts",
             lambda c: c.get("name", "?")),
            ("note", "Notizen",
             "notes.list", "notes",
             lambda n: n.get("title", "?")),
            ("clipboard-list", "Vorschlaege (Inbox)",
             "inbox.list", "proposals",
             lambda p: p.get("summary", "?")),
            ("magnify", "Suche (Sammeluebersicht)",
             "search.dashboard_summary", "items",
             lambda i: i.get("title", str(i))),
        ]
        for icon, label, _cap, _key, _fn in self._entries:
            item = OneLineIconListItem(
                IconLeftWidget(icon=icon),
                text=label,
            )
            item.bind(on_release=self._make_handler(label))
            self.list.add_widget(item)

        # Sprachumschalter
        app = MDApp.get_running_app()
        lang_label = (app.i18n.t("tab.settings") + " · Sprache / Language"
                      if app is not None else "Sprache / Language")
        lang_item = OneLineIconListItem(
            IconLeftWidget(icon="translate"),
            text=lang_label,
        )
        lang_item.bind(on_release=lambda *_: self._open_language_page())
        self.list.add_widget(lang_item)

        # Daten loeschen (DSGVO Art. 17 / Play Data-Deletion)
        del_label = (app.i18n.t("data.delete_button")
                     if app is not None else "Alle Daten loeschen")
        del_item = OneLineIconListItem(
            IconLeftWidget(icon="delete-forever"),
            text=del_label,
        )
        del_item.bind(on_release=lambda *_: self._open_data_deletion_page())
        self.list.add_widget(del_item)

        # Footer mit App-Info
        self.list.add_widget(OneLineIconListItem(
            IconLeftWidget(icon="information"),
            text="Version 0.9 (Android)",
        ))

    def _open_language_page(self) -> None:
        self.add_widget(_LanguagePage())

    def _open_data_deletion_page(self) -> None:
        self.add_widget(_DataDeletionPage())

    def _make_handler(self, label_text: str):
        def handler(_widget):
            for icon, lbl, cap, key, fn in self._entries:
                if lbl == label_text:
                    page = _SimpleListPage(
                        title=lbl, capability=cap, result_key=key,
                        label_fn=fn, registry=self.registry)
                    self.add_widget(page)
                    return
        return handler
