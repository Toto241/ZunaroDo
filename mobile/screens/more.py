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
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

from mobile.helpers import language_menu_items, truncate
from mobile.presenters import OrdersPresenter, SearchPresenter
from mobile.ui_text import t as _t
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


class _FilteredListPage(MDScreen):
    """Wie _SimpleListPage, aber mit einem Filterfeld, das als Argument an
    die Capability durchgereicht wird (z.B. Beziehung bei Kontakten)."""

    def __init__(self, title: str, capability: str, result_key: str,
                 label_fn, filter_key: str, filter_hint: str,
                 registry, **kwargs):
        super().__init__(**kwargs)
        self.title_text = title
        self.capability = capability
        self.result_key = result_key
        self.label_fn = label_fn
        self.filter_key = filter_key
        self.filter_hint = filter_hint
        self.registry = registry
        self._build()
        self._refresh()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=self.title_text,
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
            right_action_items=[["refresh", lambda *_: self._refresh()]],
        ))
        fbox = MDBoxLayout(orientation="horizontal", adaptive_height=True,
                           padding=dp(8), spacing=dp(8), size_hint=(1, None))
        self.filter_field = MDTextField(hint_text=self.filter_hint)
        self.filter_field.bind(on_text_validate=lambda *_: self._refresh())
        fbox.add_widget(self.filter_field)
        fbox.add_widget(MDFlatButton(text="Filtern",
                                     on_release=lambda *_: self._refresh()))
        root.add_widget(fbox)
        scroll = ScrollView()
        self.list = MDList()
        scroll.add_widget(self.list)
        root.add_widget(scroll)
        self.add_widget(root)

    def _refresh(self) -> None:
        args: dict = {}
        val = (self.filter_field.text or "").strip()
        if val:
            args[self.filter_key] = val
        try:
            result = self.registry.dispatch(self.capability, args)
        except Exception as exc:
            result = {self.result_key: [], "_err": str(exc)}
        self.list.clear_widgets()
        items = result.get(self.result_key, [])
        if not items:
            self.list.add_widget(OneLineIconListItem(
                IconLeftWidget(icon="information-outline"),
                text="Keine Eintraege."))
            return
        for item in items:
            self.list.add_widget(OneLineIconListItem(
                IconLeftWidget(icon="chevron-right"),
                text=self.label_fn(item)))

    def _go_back(self) -> None:
        parent = self.parent
        if parent is not None and hasattr(parent, "remove_widget"):
            parent.remove_widget(self)


class _SearchPage(MDScreen):
    """Volltextsuche (system.search) mit optionalen Filtern."""

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self.presenter = SearchPresenter(registry.dispatch)
        self._build()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title="Suche",
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
        ))
        form = MDBoxLayout(orientation="vertical", adaptive_height=True,
                           padding=dp(8), spacing=dp(4), size_hint=(1, None))
        self.q = MDTextField(hint_text="Suchbegriff")
        self.f_category = MDTextField(hint_text="Kategorie (optional)")
        self.f_status = MDTextField(hint_text="Status (optional)")
        self.f_from = MDTextField(hint_text="von JJJJ-MM-TT (optional)")
        self.f_to = MDTextField(hint_text="bis JJJJ-MM-TT (optional)")
        for w in (self.q, self.f_category, self.f_status,
                  self.f_from, self.f_to):
            form.add_widget(w)
        form.add_widget(MDRaisedButton(
            text="Suchen", on_release=lambda *_: self._run()))
        root.add_widget(form)
        scroll = ScrollView()
        self.list = MDList()
        scroll.add_widget(self.list)
        root.add_widget(scroll)
        self.add_widget(root)

    def _run(self) -> None:
        result = self.presenter.search(
            self.q.text, category=self.f_category.text,
            status=self.f_status.text, date_from=self.f_from.text,
            date_to=self.f_to.text)
        self.list.clear_widgets()
        if result["status"] != "ok":
            icon = {"too_short": "information-outline",
                    "error": "alert", "empty": "magnify"}.get(
                        result["status"], "information-outline")
            self.list.add_widget(OneLineIconListItem(
                IconLeftWidget(icon=icon), text=result["message"]))
            return
        for hit in result["hits"]:
            self.list.add_widget(OneLineIconListItem(
                IconLeftWidget(icon="chevron-right"),
                text=f"[{hit.get('source','?')}] "
                     f"{truncate(hit.get('title',''), 40)}"))

    def _go_back(self) -> None:
        parent = self.parent
        if parent is not None and hasattr(parent, "remove_widget"):
            parent.remove_widget(self)


class _OrdersPage(MDScreen):
    """Einmalige Auftraege: Liste + Anlegen mit Prioritaet/Kategorie."""

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self.presenter = OrdersPresenter(registry.dispatch)
        self._dialog = None
        self._build()
        self._refresh()

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title="Auftraege",
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
            right_action_items=[["plus", lambda *_: self._open_add()],
                                ["refresh", lambda *_: self._refresh()]],
        ))
        scroll = ScrollView()
        self.list = MDList()
        scroll.add_widget(self.list)
        root.add_widget(scroll)
        self.add_widget(root)

    def _refresh(self) -> None:
        view = self.presenter.list()
        self.list.clear_widgets()
        orders = view["items"]
        if view["empty"]:
            self.list.add_widget(OneLineIconListItem(
                IconLeftWidget(icon="information-outline"),
                text=view["empty_text"]))
            return
        for o in orders:
            done = o.get("status") == "erledigt"
            mark = {"hoch": "[!] ", "mittel": "[~] "}.get(
                o.get("priority", "normal"), "")
            kat = f" #{o['category']}" if o.get("category") else ""
            check = "✓ " if done else ""
            item = OneLineIconListItem(
                IconLeftWidget(icon="checkbox-marked-circle-outline" if done
                               else "checkbox-blank-circle-outline"),
                text=f"{check}{mark}{o.get('title','')}{kat}")
            oid = o.get("id")
            if not done and oid is not None:
                item.bind(on_release=self._make_complete(oid))
            self.list.add_widget(item)

    def _make_complete(self, oid: int):
        def handler(_w):
            self.presenter.complete(oid)
            self._refresh()
        return handler

    def _open_add(self) -> None:
        body = MDBoxLayout(orientation="vertical", spacing=dp(8),
                           adaptive_height=True, padding=dp(8))
        self._in_title = MDTextField(hint_text="Titel")
        self._in_assignee = MDTextField(hint_text="Zustaendig (optional)")
        self._in_due = MDTextField(hint_text="Faellig JJJJ-MM-TT (optional)")
        self._in_priority = MDTextField(
            hint_text="Prioritaet hoch/mittel/normal", text="normal")
        self._in_category = MDTextField(hint_text="Kategorie (optional)")
        for w in (self._in_title, self._in_assignee, self._in_due,
                  self._in_priority, self._in_category):
            body.add_widget(w)
        self._dialog = MDDialog(
            title=_t("action.add_order", "Neuer Auftrag"), type="custom",
            content_cls=body,
            buttons=[
                MDFlatButton(text=_t("action.cancel", "Abbrechen"),
                             on_release=lambda *_: self._dismiss()),
                MDFlatButton(text=_t("action.save", "Speichern"),
                             on_release=lambda *_: self._submit()),
            ])
        self._dialog.open()

    def _submit(self) -> None:
        result = self.presenter.add(
            self._in_title.text, assignee=self._in_assignee.text,
            due_date=self._in_due.text, priority=self._in_priority.text,
            category=self._in_category.text)
        if "error" in result:
            return                       # ohne Titel kein Auftrag
        self._dismiss()
        self._refresh()

    def _dismiss(self) -> None:
        if self._dialog is not None:
            self._dialog.dismiss()
            self._dialog = None

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
        root.add_widget(MDTopAppBar(title=_t("tab.more", "Mehr")))
        scroll = ScrollView()
        self.list = MDList()
        scroll.add_widget(self.list)
        root.add_widget(scroll)
        self.add_widget(root)

        # Generische Listen-Eintraege (ohne Filter)
        self._entries = [
            ("account-multiple", "Familie / Haushalt",
             "family.members", "members",
             lambda m: f"{m.get('name','?')} ({m.get('role','-')})"),
            ("note", "Notizen",
             "notes.list", "notes",
             lambda n: n.get("title", "?")),
            ("clipboard-list", "Vorschlaege (Inbox)",
             "inbox.proposals", "proposals",
             lambda p: p.get("summary", "?")),
        ]
        for icon, label, _cap, _key, _fn in self._entries:
            item = OneLineIconListItem(
                IconLeftWidget(icon=icon),
                text=label,
            )
            item.bind(on_release=self._make_handler(label))
            self.list.add_widget(item)

        # Dedizierte Seiten mit eigener Bedienung
        search_item = OneLineIconListItem(
            IconLeftWidget(icon="magnify"), text="Suche (mit Filtern)")
        search_item.bind(on_release=lambda *_: self._open_search())
        self.list.add_widget(search_item)

        orders_item = OneLineIconListItem(
            IconLeftWidget(icon="clipboard-check"),
            text="Auftraege (Prioritaet/Kategorie)")
        orders_item.bind(on_release=lambda *_: self._open_orders())
        self.list.add_widget(orders_item)

        contacts_item = OneLineIconListItem(
            IconLeftWidget(icon="account-heart"),
            text="Kontakte (nach Beziehung)")
        contacts_item.bind(on_release=lambda *_: self._open_contacts())
        self.list.add_widget(contacts_item)

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

    def _open_search(self) -> None:
        self.add_widget(_SearchPage(registry=self.registry))

    def _open_orders(self) -> None:
        self.add_widget(_OrdersPage(registry=self.registry))

    def _open_contacts(self) -> None:
        self.add_widget(_FilteredListPage(
            title="Kontakte", capability="social.contacts",
            result_key="contacts",
            label_fn=lambda c: f"{c.get('name','?')} "
                               f"({c.get('relation','-')})",
            filter_key="relation", filter_hint="Beziehung filtern (optional)",
            registry=self.registry))

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
