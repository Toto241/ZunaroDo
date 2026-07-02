"""
Anzeige der Rechtstexte (Datenschutz, Impressum, AGB, Widerruf) in der
Mobile-App.

Play-Store-Anforderung: Datenschutzerklaerung & Co. muessen aus der App
heraus erreichbar sein, nicht nur ueber die Store-/Web-Seite. Die Texte
kommen aus legal/ (im APK enthalten via buildozer source.include_patterns)
und werden ueber services/legal.py sprachaufgeloest (Deutsch-Fallback).
"""
from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar

from mobile.ui_text import t as _t
from services.legal import resolve_legal


def legal_menu_entries() -> list[tuple[str, str, str, str]]:
    """(icon, i18n_key, deutscher Fallback, LEGAL_DOC) fuer den Mehr-Screen."""
    return [
        ("shield-account", "legal.privacy", "Datenschutzerklaerung",
         "DATENSCHUTZ"),
        ("information", "legal.imprint", "Impressum", "IMPRESSUM"),
        ("file-document", "legal.terms", "AGB", "AGB"),
        ("undo", "legal.withdrawal", "Widerrufsbelehrung", "WIDERRUF"),
    ]


class LegalDocScreen(MDScreen):
    """Scrollbare Anzeige eines Rechtstextes aus legal/."""

    def __init__(self, doc: str, title: str = "", **kwargs):
        super().__init__(**kwargs)
        self.doc = doc.upper()
        self.title_text = title or self.doc
        self._build()

    def _lang(self) -> str:
        app = MDApp.get_running_app()
        i18n = getattr(app, "i18n", None) if app is not None else None
        if i18n is not None and getattr(i18n, "language", None):
            return i18n.language
        return "de"

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=self.title_text,
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
        ))
        scroll = ScrollView()
        body = BoxLayout(orientation="vertical", size_hint_y=None,
                         padding=dp(16), spacing=dp(8))
        body.bind(minimum_height=body.setter("height"))

        resolved = resolve_legal(self.doc, self._lang())
        if resolved is None:
            text = _t("legal.missing", "Dokument nicht gefunden.")
        else:
            text, _effective_lang = resolved
        label = MDLabel(
            text=text,
            halign="left",
            valign="top",
            size_hint_y=None,
            theme_text_color="Primary",
        )
        label.bind(texture_size=lambda inst, val: setattr(
            inst, "height", max(val[1], dp(200))))
        body.add_widget(label)
        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    def _go_back(self) -> None:
        parent = self.parent
        if parent is not None and hasattr(parent, "remove_widget"):
            parent.remove_widget(self)
