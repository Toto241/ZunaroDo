"""
Lizenz- und Pro-Aktivierung fuer die Mobile-App (Paritaet zu gui.py Settings).
"""
from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

from mobile.ui_text import t as _t
from services.license_ui import (action_apply_token, action_start_trial,
                                  make_tier_status)


class LicenseScreen(MDScreen):
    """Trial starten, Pro-Token einfuegen, Tier-Status anzeigen."""

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self._token_dialog = None
        self._build()
        self._refresh_status()

    def _settings_repo(self):
        app = MDApp.get_running_app()
        return getattr(app, "settings", None) if app is not None else None

    def _t(self, key: str, default: str = "") -> str:
        app = MDApp.get_running_app()
        if app is not None and getattr(app, "i18n", None) is not None:
            return app.i18n.t(key, default)
        return default or key

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=self._t("license.title", "Lizenz"),
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
        ))
        scroll = ScrollView()
        body = BoxLayout(orientation="vertical", size_hint_y=None,
                         padding=dp(16), spacing=dp(12))
        body.bind(minimum_height=body.setter("height"))

        self.status_label = MDLabel(
            text="", halign="left", valign="top",
            size_hint_y=None, theme_text_color="Primary",
        )
        self.status_label.bind(texture_size=self._resize_label)
        body.add_widget(self.status_label)

        self.hint_label = MDLabel(
            text=self._t(
                "license.hint",
                "Pro: alle Module, KI und Mehrgeraete-Sync. "
                "Token aus der Kauf-Mail einfuegen oder Trial starten."),
            halign="left", valign="top", size_hint_y=None,
            theme_text_color="Secondary",
        )
        self.hint_label.bind(texture_size=self._resize_label)
        body.add_widget(self.hint_label)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                            height=dp(48), spacing=dp(8))
        self.trial_btn = MDRaisedButton(
            text=self._t("license.start_trial", "14 Tage Trial"),
            on_release=lambda *_: self._on_trial(),
        )
        btn_row.add_widget(self.trial_btn)
        btn_row.add_widget(MDRaisedButton(
            text=self._t("license.activate_token", "Pro-Token"),
            on_release=lambda *_: self._open_token_dialog(),
        ))
        body.add_widget(btn_row)

        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    def _resize_label(self, widget, _size) -> None:
        widget.height = max(dp(48), widget.texture_size[1] + dp(8))

    def _refresh_status(self) -> None:
        repo = self._settings_repo()
        if repo is None:
            return
        from services.licensing import load_license

        lic = load_license(repo)
        st = make_tier_status(lic)
        self.status_label.text = (
            f"{st.headline}\n{st.detail}")
        self.trial_btn.disabled = not st.can_start_trial
        if not st.can_start_trial:
            self.trial_btn.text = self._t(
                "license.trial_used", "Trial nicht verfuegbar")

    def _on_trial(self) -> None:
        repo = self._settings_repo()
        if repo is None:
            return
        result = action_start_trial(repo)
        self._show_message(result.message)
        self._refresh_status()

    def _open_token_dialog(self) -> None:
        field = MDTextField(
            hint_text=self._t(
                "license.token_hint", "Token <payload>.<signature>"),
            multiline=True,
        )
        self._token_dialog = MDDialog(
            title=self._t("license.activate_token", "Pro-Token"),
            type="custom",
            content_cls=field,
            buttons=[
                MDFlatButton(
                    text=self._t("action.cancel", "Abbrechen"),
                    on_release=lambda *_: self._dismiss_token()),
                MDRaisedButton(
                    text=self._t("license.activate", "Aktivieren"),
                    on_release=lambda *_: self._apply_token(field),
                ),
            ],
        )
        self._token_dialog.open()

    def _apply_token(self, field: MDTextField) -> None:
        repo = self._settings_repo()
        if repo is None:
            return
        result = action_apply_token(repo, field.text or "")
        self._dismiss_token()
        self._show_message(result.message)
        self._refresh_status()

    def _dismiss_token(self) -> None:
        if self._token_dialog is not None:
            self._token_dialog.dismiss()
            self._token_dialog = None

    def _show_message(self, message: str) -> None:
        if not message:
            return
        MDDialog(
            title=self._t("license.title", "Lizenz"),
            text=message,
            buttons=[MDFlatButton(
                text=self._t("common.close", "Schliessen"),
                on_release=lambda dlg: dlg.dismiss(),
            )],
        ).open()

    def _go_back(self) -> None:
        parent = self.parent
        if parent is not None and hasattr(parent, "remove_widget"):
            parent.remove_widget(self)
