"""
Android-Laufzeitberechtigungen (API 33+: POST_NOTIFICATIONS).

Auf Desktop/no-pyjnius wird still uebersprungen; Erinnerungen bleiben
dann nur in-app sichtbar.
"""
from __future__ import annotations

import sys


def _is_android() -> bool:
    return "android" in sys.platform


def request_post_notifications(rationale: str = "") -> bool:
    """
    Fordert POST_NOTIFICATIONS an (Android 13+). Gibt True zurueck, wenn
    die Permission erteilt ist oder nicht noetig (API < 33 / Desktop).
    """
    if not _is_android():
        return True
    try:
        from jnius import autoclass, cast
        from android import mActivity  # type: ignore[import-untyped]
    except Exception:
        return True

    try:
        BuildVersion = autoclass("android.os.Build$VERSION")
        if BuildVersion.SDK_INT < 33:
            return True

        Manifest = autoclass("android.Manifest")
        permission = Manifest.permission.POST_NOTIFICATIONS

        ContextCompat = autoclass("androidx.core.content.ContextCompat")
        PackageManager = autoclass("android.content.pm.PackageManager")
        granted = ContextCompat.checkSelfPermission(
            mActivity, permission) == PackageManager.PERMISSION_GRANTED
        if granted:
            return True

        ActivityCompat = autoclass("androidx.core.app.ActivityCompat")
        ActivityCompat.requestPermissions(
            cast("android.app.Activity", mActivity),
            [permission],
            1001,
        )
        # Ergebnis kommt asynchron; naechster notify-Versuch prueft erneut.
        return False
    except Exception:
        return True


def has_post_notifications() -> bool:
    """True, wenn Erinnerungs-Benachrichtigungen gesendet werden duerfen."""
    if not _is_android():
        return True
    try:
        from jnius import autoclass
        from android import mActivity  # type: ignore[import-untyped]
    except Exception:
        return True

    try:
        BuildVersion = autoclass("android.os.Build$VERSION")
        if BuildVersion.SDK_INT < 33:
            return True
        Manifest = autoclass("android.Manifest")
        ContextCompat = autoclass("androidx.core.content.ContextCompat")
        PackageManager = autoclass("android.content.pm.PackageManager")
        return ContextCompat.checkSelfPermission(
            mActivity, Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
    except Exception:
        return True
