"""
Datenexport (CSV + JSON) fuer Mobile — DSGVO Art. 20 / Play Data-Export.
"""
from __future__ import annotations

from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar

from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, SettingsRepository,
                      SocialRepository)
from mobile.ui_text import t as _t
from services.export import export_all, export_all_json


class ExportDataScreen(MDScreen):
    """Schreibt CSV + JSON in den App-Sandbox-Ordner."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _t(self, key: str, default: str = "") -> str:
        app = MDApp.get_running_app()
        if app is not None and getattr(app, "i18n", None) is not None:
            return app.i18n.t(key, default)
        return default or key

    def _build(self) -> None:
        root = BoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(
            title=self._t("export.title", "Daten exportieren"),
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
        ))
        self.status = MDLabel(
            text=self._t(
                "export.hint",
                "Exportiert Vertraege, Ausgaben, Termine, Kontakte und "
                "Haushalt als CSV und JSON in den App-Ordner."),
            halign="left", valign="top",
            padding=(dp(16), dp(16)),
        )
        root.add_widget(self.status)
        root.add_widget(MDRaisedButton(
            text=self._t("export.run", "Jetzt exportieren"),
            size_hint_y=None, height=dp(48),
            pos_hint={"center_x": 0.5},
            on_release=lambda *_: self._run_export(),
        ))
        self.add_widget(root)

    def _run_export(self) -> None:
        app = MDApp.get_running_app()
        db = getattr(app, "_db", None) if app is not None else None
        if db is None:
            return
        base = Path(app.user_data_dir) / "export" if hasattr(app, "user_data_dir") else Path("export")
        settings = SettingsRepository(db)
        try:
            csv_counts = export_all(
                base,
                ContractRepository(db), ExpenseRepository(db),
                CalendarRepository(db), SocialRepository(db),
                FamilyRepository(db),
            )
            json_path = export_all_json(
                base,
                ContractRepository(db), ExpenseRepository(db),
                CalendarRepository(db), SocialRepository(db),
                FamilyRepository(db),
                include_settings=True,
                settings_rows=settings.all(),
            )
            lines = [f"CSV: {sum(csv_counts.values())} Zeilen",
                     f"JSON: {json_path.name}"]
            self.status.text = self._t("export.done", "Export abgeschlossen.") + "\n" + "\n".join(lines)
        except Exception as exc:
            self.status.text = f"{self._t('export.error', 'Export fehlgeschlagen')}: {exc}"

    def _go_back(self) -> None:
        parent = self.parent
        if parent is not None and hasattr(parent, "remove_widget"):
            parent.remove_widget(self)
