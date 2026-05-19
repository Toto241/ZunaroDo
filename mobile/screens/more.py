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
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar


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

        # Footer mit App-Info
        self.list.add_widget(OneLineIconListItem(
            IconLeftWidget(icon="information"),
            text="Version 0.9 (Android)",
        ))

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
