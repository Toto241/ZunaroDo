"""
Erststart-Dialog: Datenschutz-Hinweis und Zustimmung (persistiert in Settings).
"""
from __future__ import annotations

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel

from mobile.ui_text import t as _t
from services.identity import privacy_url
from services.privacy_consent import (consent_accepted, mark_consent_accepted)


def maybe_show_privacy_onboarding(app, on_done=None) -> None:
    """Zeigt den Dialog einmalig, wenn noch keine Zustimmung gespeichert ist."""
    settings = getattr(app, "settings", None)
    if consent_accepted(settings):
        if on_done:
            on_done()
        return

    def _open(_dt):
        body = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=dp(12),
            spacing=dp(8),
        )
        intro = MDLabel(
            text=_t(
                "privacy.onboarding.intro",
                "ZunaroDo speichert Daten lokal auf Ihrem Geraet. "
                "Optionale Online-Funktionen (KI, Sync) nur mit Ihrer Einwilligung.",
            ),
            halign="left",
            size_hint_y=None,
        )
        intro.bind(texture_size=lambda inst, val: setattr(
            inst, "height", val[1] + dp(8)))
        body.add_widget(intro)

        link = MDLabel(
            text=_t("privacy.onboarding.link", "Datenschutzerklaerung:") + "\n"
                 + privacy_url(),
            halign="left",
            size_hint_y=None,
            theme_text_color="Custom",
        )
        link.bind(texture_size=lambda inst, val: setattr(
            inst, "height", val[1] + dp(8)))
        body.add_widget(link)

        dlg = MDDialog(
            title=_t("privacy.onboarding.title", "Datenschutz"),
            type="custom",
            content_cls=body,
            buttons=[
                MDFlatButton(
                    text=_t("privacy.onboarding.decline", "Beenden"),
                    on_release=lambda *_: _decline(dlg, app),
                ),
                MDRaisedButton(
                    text=_t("privacy.onboarding.accept", "Akzeptieren"),
                    on_release=lambda *_: _accept(dlg, settings, on_done),
                ),
            ],
        )
        dlg.open()

    Clock.schedule_once(_open, 0.3)


def _accept(dlg: MDDialog, settings, on_done) -> None:
    mark_consent_accepted(settings)
    dlg.dismiss()
    if on_done:
        on_done()


def _decline(dlg: MDDialog, app) -> None:
    dlg.dismiss()
    if hasattr(app, "stop"):
        app.stop()
