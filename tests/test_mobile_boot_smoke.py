"""
Mobile-Laufzeit-Smoke (KivyMD, headless).

Startet die echte KivyMD-App mit Mock-Window/-GL-Backend (kein Display
noetig), baut damit alle fuenf Bottom-Nav-Screens auf und beendet sich
selbst sofort wieder. Faengt Boot-/Render-Crashes des Phone-Clients, die
die reinen Helfer-/Capability-Tests nicht sehen.

Laeuft nur, wenn ``kivy``/``kivymd`` installiert sind - sonst ``skip``.
Auf CI deckt das der Job ``mobile-kivy-smoke`` in
``.github/workflows/ui-runtime.yml`` ab (dort werden die Pakete und die
SDL-Systembibliotheken installiert).
"""
from __future__ import annotations

import os

# Headless-Provider MUESSEN vor dem ersten Kivy-Import gesetzt werden.
os.environ.setdefault("KIVY_WINDOW", "mock")
os.environ.setdefault("KIVY_GL_BACKEND", "mock")
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

import tempfile
import unittest

try:
    import kivymd  # noqa: F401
    from kivy.clock import Clock
    _HAS_KIVYMD = True
except Exception:                                    # pragma: no cover
    _HAS_KIVYMD = False


@unittest.skipUnless(_HAS_KIVYMD, "kivy/kivymd nicht installiert")
class TestMobileBootSmoke(unittest.TestCase):

    def test_app_boots_and_builds_all_tabs(self) -> None:
        from mobile.app import AlltagshelferMobile, HAS_KIVYMD
        self.assertTrue(HAS_KIVYMD)

        workdir = tempfile.mkdtemp(prefix="ah_mobile_smoke_")
        prev = os.getcwd()
        os.chdir(workdir)               # Temp-DB landet hier, nicht im Repo
        try:
            app = AlltagshelferMobile()
            # Nach kurzem Lauf selbst beenden; ein Crash in build() bzw. in
            # einem Screen-Konstruktor propagiert aus run() heraus.
            Clock.schedule_once(lambda _dt: app.stop(), 1.0)
            app.run()
        finally:
            os.chdir(prev)


if __name__ == "__main__":
    unittest.main()
