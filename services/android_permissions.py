"""
Android-Laufzeitberechtigungen (API 33+: POST_NOTIFICATIONS).

Seit Android 13 (API 33) reicht die Manifest-Deklaration in
buildozer.spec nicht mehr: POST_NOTIFICATIONS muss zusaetzlich zur
Laufzeit angefragt werden, sonst bleiben System-Benachrichtigungen
(Erinnerungen) stumm. Dieses Modul kapselt die Anfrage defensiv:

- Auf Desktop / ohne python-for-android ist alles ein No-Op und
  liefert True ("nicht noetig") - es wird nie eine Exception geworfen.
- Wird die Berechtigung verweigert, degradiert services/notifier.py
  bereits auf In-App-/Print-Ausgabe (getestet in
  tests/test_notifications_permission.py).
"""
from __future__ import annotations

import os
import sys

#: Voll qualifizierter Permission-Name als Fallback, falls das
#: p4a-Permission-Enum die Konstante (noch) nicht kennt.
POST_NOTIFICATIONS = "android.permission.POST_NOTIFICATIONS"


def _is_android() -> bool:
    """True nur im python-for-android-Bootstrap (nie auf Desktop)."""
    return "ANDROID_ARGUMENT" in os.environ or sys.platform == "android"


def _sdk_int() -> int:
    """Android-API-Level; 0, wenn nicht ermittelbar."""
    try:
        from jnius import autoclass  # type: ignore[import-not-found]
        return int(autoclass("android.os.Build$VERSION").SDK_INT)
    except Exception:
        return 0


def ensure_post_notifications() -> bool:
    """
    Fordert POST_NOTIFICATIONS an, falls noetig (Android 13+).

    Rueckgabe: True, wenn die Berechtigung erteilt ist oder gar nicht
    gebraucht wird (Desktop, API < 33). False, wenn die Anfrage gerade
    gestellt wurde - das Ergebnis kommt asynchron; der naechste
    notify()-Aufruf prueft dann erneut.
    """
    if not _is_android():
        return True
    if 0 < _sdk_int() < 33:
        return True
    try:
        from android.permissions import (  # type: ignore[import-not-found]
            Permission, check_permission, request_permissions)
    except Exception:
        # Kein p4a-Permission-Modul (z.B. Desktop-Test mit gesetztem
        # ANDROID_ARGUMENT) -> nichts anzufragen.
        return True
    try:
        perm = getattr(Permission, "POST_NOTIFICATIONS", POST_NOTIFICATIONS)
        if check_permission(perm):
            return True
        request_permissions([perm])
        return False
    except Exception:
        # Anfrage darf den App-Start niemals reissen.
        return True


def has_post_notifications() -> bool:
    """True, wenn System-Benachrichtigungen gesendet werden duerfen."""
    if not _is_android():
        return True
    if 0 < _sdk_int() < 33:
        return True
    try:
        from android.permissions import (  # type: ignore[import-not-found]
            Permission, check_permission)
    except Exception:
        return True
    try:
        perm = getattr(Permission, "POST_NOTIFICATIONS", POST_NOTIFICATIONS)
        return bool(check_permission(perm))
    except Exception:
        return True
