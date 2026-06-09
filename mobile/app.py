"""
Mobile-App-Einstiegspunkt (KivyMD).

Start auf dem Desktop (zum Entwickeln):
    python -m mobile.app

Build als Android-APK:
    siehe MOBILE.md (buildozer)

Die App nutzt die selbe `build_registry(db, output)` aus main.py wie
die Desktop-GUI. Wird die DB-Konfiguration nicht ueberschrieben, landet
sie auf Android im 'user_data_dir' der App (sandboxed) - das ist
absichtlich, damit ein App-Update keine Daten verliert.
"""
from __future__ import annotations

import os
from pathlib import Path

# Kivy/KivyMD sind nur auf Android und in einer dev-Umgebung mit
# 'pip install kivy kivymd' verfuegbar. Wenn nicht installiert, geben
# wir eine hilfreiche Meldung - so kann die Datei trotzdem importiert
# werden (z.B. von Tests, die nur Helper-Logik pruefen).
try:
    from kivymd.app import MDApp
    from kivy.uix.screenmanager import ScreenManager
    HAS_KIVYMD = True
except ImportError:                              # pragma: no cover
    MDApp = object                               # type: ignore[misc,assignment]
    ScreenManager = object                       # type: ignore[misc,assignment]
    HAS_KIVYMD = False

from database import Database, SettingsRepository
from services.config import load_config
from services.i18n import I18n
from services.output import OutputService

try:
    from main import build_registry
except ImportError:                              # pragma: no cover
    build_registry = None                        # type: ignore[assignment]


def _default_db_path() -> Path:
    """
    Speicherort der DB:
      - Android: App-Sandbox via App.user_data_dir
      - Desktop: alltagshelfer.db neben dem Projekt
    """
    if HAS_KIVYMD:
        try:
            app = MDApp.get_running_app()
            if app is not None and getattr(app, "user_data_dir", ""):
                return Path(app.user_data_dir) / "alltagshelfer.db"
        except Exception:
            pass
    return Path("alltagshelfer.db")


if HAS_KIVYMD:

    from mobile.screens.dashboard import DashboardScreen
    from mobile.screens.contracts import ContractsScreen
    from mobile.screens.finance import FinanceScreen
    from mobile.screens.calendar import CalendarScreen
    from mobile.screens.more import MoreScreen

    from kivymd.uix.bottomnavigation import (
        MDBottomNavigation, MDBottomNavigationItem)
    from kivymd.uix.screen import MDScreen


    class _RootShell(MDScreen):
        """Tragender Container mit Bottom-Navigation."""

        def __init__(self, registry, i18n: I18n, **kwargs):
            super().__init__(**kwargs)
            self.registry = registry
            self.i18n = i18n
            nav = MDBottomNavigation()

            # 5 Bereiche - bewusst kompakt fuer Phones. Labels kommen aus
            # dem i18n-Lookup; fehlt eine Uebersetzung, faellt I18n auf
            # Deutsch zurueck.
            t = i18n.t
            for icon, title, key, ScreenCls in [
                ("view-dashboard", t("tab.dashboard"), "dashboard", DashboardScreen),
                ("file-document", t("tab.contracts"), "contracts", ContractsScreen),
                ("cash-multiple", t("tab.finance"), "finance", FinanceScreen),
                ("calendar", t("tab.calendar"), "calendar", CalendarScreen),
                ("dots-horizontal", t("tab.more"), "more", MoreScreen),
            ]:
                item = MDBottomNavigationItem(
                    name=key, text=title, icon=icon)
                screen_widget = ScreenCls(registry=registry)
                item.add_widget(screen_widget)
                nav.add_widget(item)

            self.add_widget(nav)


    class AlltagshelferMobile(MDApp):
        """KivyMD-App; haelt Registry + DB-Lebenszyklus."""

        def build(self):
            self.title = "ZunaroDo"
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_palette = "Blue"
            self.theme_cls.material_style = "M3"

            db_path = _default_db_path()
            # DB-Schluessel plattformabhaengig ableiten (Android Keystore /
            # Env). Liefert None, solange keine SQLCipher-Engine im Build
            # ist - dann laeuft die DB wie bisher unverschluesselt weiter.
            from services.db_key import resolve_db_key
            self._db = Database(str(db_path), encryption_key=resolve_db_key())
            # Settings-Repo oeffentlich halten - der Sprachumschalter im
            # "Mehr"-Screen persistiert hierueber.
            self.settings = SettingsRepository(self._db)
            config = load_config(self.settings)
            # Sprache aufloesen (inkl. Sonderwert "auto" = Geraetesprache).
            self.i18n = I18n(config.effective_language())

            self._output = OutputService(
                str(Path(self.user_data_dir) / "ausgaben")
                if hasattr(self, "user_data_dir")
                else "ausgaben")
            if build_registry is None:
                raise RuntimeError(
                    "build_registry konnte nicht importiert werden")
            self._registry = build_registry(self._db, self._output)
            from services.license_gate import install_gate
            from services.licensing import (apply_grandfathering_if_needed,
                                               load_license)
            install_gate(self._registry,
                         lambda: load_license(self.settings))

            def _has_any_data() -> bool:
                try:
                    if self._registry.dispatch(
                            "contracts.list", {}).get("count", 0):
                        return True
                    if self._registry.dispatch(
                            "family.members", {}).get("count", 0):
                        return True
                except Exception:
                    pass
                return False

            apply_grandfathering_if_needed(self.settings, _has_any_data)
            self._license = load_license(self.settings)
            shell = _RootShell(self._registry, self.i18n)
            from mobile.privacy_onboarding import maybe_show_privacy_onboarding
            maybe_show_privacy_onboarding(self)
            return shell

        def on_stop(self):
            try:
                self._db.close()
            except Exception:
                pass


    def main() -> None:
        AlltagshelferMobile().run()


else:                                            # pragma: no cover

    def main() -> None:
        raise SystemExit(
            "KivyMD ist nicht installiert. "
            "pip install kivy kivymd  (Desktop-Test) "
            "oder buildozer android debug  (Android-APK).")


if __name__ == "__main__":                       # pragma: no cover
    main()
