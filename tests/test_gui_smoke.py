"""
Headless GUI-Smoke-Tests.

Diese Tests starten KEIN echtes Tkinter-Fenster (es ist auf CI-Maschinen
oft nicht verfuegbar). Sie pruefen stattdessen:
  - das gui-Modul ist importierbar
  - reine Hilfsfunktionen (Validierung, Parsing) tun das Richtige
  - die App-Klasse hat die erwarteten oeffentlichen Hooks

Damit faellt ein Import-Bruch oder eine kaputte Signatur sofort auf,
ohne dass eine grafische Umgebung gebraucht wird.
"""
from __future__ import annotations

import unittest


class TestGuiImports(unittest.TestCase):

    def test_gui_module_imports(self) -> None:
        import gui
        self.assertTrue(hasattr(gui, "_is_valid_geometry"))

    def test_geometry_helpers(self) -> None:
        from gui import _is_valid_geometry
        self.assertTrue(_is_valid_geometry("1080x720"))
        self.assertTrue(_is_valid_geometry("1024x768+100+50"))
        self.assertFalse(_is_valid_geometry(""))
        self.assertFalse(_is_valid_geometry("abc"))
        self.assertFalse(_is_valid_geometry("10x10"))   # zu klein

    def test_main_app_class_exists(self) -> None:
        import gui
        # Eine zentrale GUI-Klasse muss existieren, sonst startet
        # nichts. Wir erlauben verschiedene Namen ('App', 'GUI', ...).
        gui_classes = [name for name in dir(gui)
                        if (name.endswith("App") or name.endswith("GUI"))
                        and isinstance(getattr(gui, name), type)]
        self.assertTrue(gui_classes,
                          "Keine GUI-Hauptklasse in gui.py gefunden")

    def test_license_ui_helpers_callable_headless(self) -> None:
        """Lizenz-UI-Helfer muessen ohne Tk-Display funktionieren."""
        from services.license_ui import (build_pricing_rows,
                                            make_tier_status,
                                            sidebar_indicator)
        from services.licensing import License, Tier
        st = make_tier_status(License())
        self.assertEqual(st.tier, Tier.FREE)
        self.assertEqual(sidebar_indicator(License()), "Tier: Free")
        rows = build_pricing_rows(2)
        self.assertGreater(len(rows), 0)

    def test_gui_has_license_section_methods(self) -> None:
        """Sicherstellen, dass die Aktivierungs-UI-Methoden existieren -
        verhindert dass die Bindings in __init__ ins Leere zeigen."""
        import gui
        for cls_name in dir(gui):
            cls = getattr(gui, cls_name)
            if not isinstance(cls, type):
                continue
            if not (cls_name.endswith("App") or cls_name.endswith("GUI")):
                continue
            for method in ("_build_license_section",
                            "_on_start_trial",
                            "_on_apply_token",
                            "_refresh_license_state",
                            "_build_upgrade_panel",
                            "_is_tab_locked",
                            "_tab_display_label"):
                self.assertTrue(hasattr(cls, method),
                                  f"{cls_name}.{method} fehlt")
            return
        self.fail("Keine GUI-Hauptklasse gefunden, um Hooks zu pruefen")


class TestMainImports(unittest.TestCase):

    def test_main_module_imports(self) -> None:
        import main
        self.assertTrue(hasattr(main, "main"))

    def test_build_registry_signature(self) -> None:
        import inspect
        from main import build_registry
        sig = inspect.signature(build_registry)
        # build_registry darf keine Argumente brauchen
        # (oder nur Defaults haben) - sonst kaputt
        required = [p for p in sig.parameters.values()
                     if p.default is inspect.Parameter.empty
                     and p.kind not in (inspect.Parameter.VAR_POSITIONAL,
                                          inspect.Parameter.VAR_KEYWORD)]
        # db + output sind Pflicht; llm hat Default None
        self.assertEqual(len(required), 2,
                          f"build_registry erwartet {len(required)} "
                          "Pflicht-Args; db und output muessen reichen")
        names = {p.name for p in required}
        self.assertIn("db", names)
        self.assertIn("output", names)


if __name__ == "__main__":                       # pragma: no cover
    unittest.main()
