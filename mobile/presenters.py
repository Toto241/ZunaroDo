"""Kompatibilitäts-Shim: die Presenter liegen jetzt toolkit-neutral in
``app_core.presenters``. Dieses Modul re-exportiert sie für bestehende
``from mobile.presenters import ...``-Aufrufe.
"""
from app_core.presenters import *  # noqa: F401,F403
