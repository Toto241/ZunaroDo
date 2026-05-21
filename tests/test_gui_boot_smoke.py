"""
Desktop-GUI-Laufzeit-Smoke (customtkinter).

Im Gegensatz zu den AST-basierten Guard-Tests startet dieser Test die
echte App: er konstruiert das Hauptfenster mit echter Registry (Temp-DB),
laesst alle Tabs bauen, ruft ``_refresh_all`` (alle ``_refresh_*``) auf und
zerstoert das Fenster wieder. So werden Render-/Konstruktions-Crashes
gefangen, die statische Prüfungen nicht sehen koennen.

Laeuft nur, wenn ``customtkinter`` UND ein X-Display (z.B. via ``xvfb-run``)
verfuegbar sind - sonst ``skip``. Auf CI deckt das der Job
``desktop-gui-smoke`` in ``.github/workflows/ui-runtime.yml`` ab.
"""
from __future__ import annotations

import os
import tempfile
import unittest

try:
    import customtkinter  # noqa: F401
    _HAS_CTK = True
except Exception:                                    # pragma: no cover
    _HAS_CTK = False

_HAS_DISPLAY = bool(os.environ.get("DISPLAY"))


@unittest.skipUnless(_HAS_CTK and _HAS_DISPLAY,
                     "customtkinter oder X-Display nicht verfuegbar")
class TestGuiBootSmoke(unittest.TestCase):

    def test_app_boots_builds_and_refreshes(self) -> None:
        import gui
        workdir = tempfile.mkdtemp(prefix="ah_gui_smoke_")
        prev = os.getcwd()
        os.chdir(workdir)               # Temp-DB landet hier, nicht im Repo
        db = None
        app = None
        try:
            (db, registry, assistant, config, settings, module_states,
             synced, profile, auto_backup) = gui.bootstrap()
            app = gui.AlltagshelferGUI(
                registry, assistant, config, settings, module_states,
                synced, profile, auto_backup=auto_backup)
            # Ein Event-Zyklus baut die Widgets; _refresh_all uebt alle
            # _refresh_*-Methoden (Dashboard/Agenda, Vertraege, Auftraege,
            # Kontakte, Suche ...) der App durch.
            app.update()
            app._refresh_all()
            app.update()
        finally:
            if app is not None:
                try:
                    app.scheduler.stop()
                except Exception:
                    pass
                app.destroy()
            if db is not None:
                db.close()
            os.chdir(prev)


if __name__ == "__main__":
    unittest.main()
