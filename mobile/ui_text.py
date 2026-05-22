"""
i18n-Helfer für die Mobile-Screens.

Die KivyMD-Screens bekommen ihre Übersetzung über die laufende App
(``MDApp.get_running_app().i18n``). Dieser Helfer kapselt das robust: ohne
laufende App / ohne Kivy liefert er den mitgegebenen Default zurück - so
gibt es nie einen Crash und nie einen rohen Key, und der bisherige
deutsche Text bleibt als Fallback erhalten.
"""
from __future__ import annotations


def t(key: str, default: str = "") -> str:
    """Übersetzt ``key`` über die laufende MDApp; Fallback = ``default``."""
    try:
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        i18n = getattr(app, "i18n", None) if app is not None else None
        if i18n is not None:
            return i18n.t(key, default or key)
    except Exception:
        pass
    return default or key
