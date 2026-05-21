"""Kompatibilitäts-Shim: ``HeadlessApp`` liegt jetzt toolkit-neutral in
``app_core.headless_app``. Re-Export für bestehende
``from mobile.headless_app import HeadlessApp``-Aufrufe.
"""
from app_core.headless_app import *  # noqa: F401,F403
from app_core.headless_app import HeadlessApp  # noqa: F401
