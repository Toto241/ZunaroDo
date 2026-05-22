"""
Tests für den Mobile-i18n-Helfer (mobile.ui_text.t).

Ohne laufende App/ohne Kivy muss er den Default liefern (kein Crash,
kein roher Key) - genau das garantiert die Regressionsfreiheit der
i18n-Umstellung der Screens.
"""
from __future__ import annotations

import unittest

from mobile.ui_text import t


class TestUiText(unittest.TestCase):

    def test_returns_default_without_running_app(self) -> None:
        self.assertEqual(t("tab.contracts", "Vertraege"), "Vertraege")

    def test_falls_back_to_key_without_default(self) -> None:
        self.assertEqual(t("some.key"), "some.key")

    def test_uses_running_app_i18n_when_present(self) -> None:
        class _FakeI18n:
            def t(self, key, default=None):
                return {"tab.contracts": "Contracts"}.get(key, default or key)

        class _FakeApp:
            i18n = _FakeI18n()

        import mobile.ui_text as ui
        # MDApp.get_running_app() durch Fake ersetzen.
        import sys
        import types
        fake_mod = types.ModuleType("kivymd.app")
        fake_mod.MDApp = type("MDApp", (), {
            "get_running_app": staticmethod(lambda: _FakeApp())})
        sys.modules["kivymd"] = types.ModuleType("kivymd")
        sys.modules["kivymd.app"] = fake_mod
        try:
            self.assertEqual(ui.t("tab.contracts", "Vertraege"), "Contracts")
        finally:
            sys.modules.pop("kivymd.app", None)
            sys.modules.pop("kivymd", None)


if __name__ == "__main__":
    unittest.main()
