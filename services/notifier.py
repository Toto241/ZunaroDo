"""
Desktop-Notifikationen.

Versucht in dieser Reihenfolge:
  1. plyer.notification        (cross-platform, falls installiert)
  2. winsound + print           (Windows-Fallback mit Pieps)
  3. nur print                  (letzte Reissleine)

So bleibt der Notifier ohne harte Abhaengigkeit lauffaehig.
"""
from __future__ import annotations

from typing import Callable


def _try_plyer() -> Callable[[str, str], None] | None:
    try:
        from plyer import notification
    except Exception:
        return None

    def _send(title: str, message: str) -> None:
        notification.notify(title=title, message=message,
                            app_name="Alltagshelfer", timeout=10)
    return _send


def _try_winsound() -> Callable[[str, str], None]:
    def _send(title: str, message: str) -> None:
        try:                                           # nur Windows
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
        print(f"[NOTIFICATION] {title}: {message}")
    return _send


class Notifier:
    """Sendet Desktop-Notifikationen, mit sanftem Fallback."""

    def __init__(self) -> None:
        self._send = _try_plyer() or _try_winsound()
        self._permission_asked = False

    def notify(self, title: str, message: str) -> None:
        if not self._ensure_notification_permission():
            return
        try:
            self._send(title, message)
        except Exception:                              # pragma: no cover
            print(f"[NOTIFICATION] {title}: {message}")

    def _ensure_notification_permission(self) -> bool:
        """Android 13+: POST_NOTIFICATIONS einmalig anfragen."""
        try:
            from services.android_permissions import (has_post_notifications,
                                                      request_post_notifications)
        except ImportError:
            return True
        if has_post_notifications():
            return True
        if self._permission_asked:
            return False
        self._permission_asked = True
        request_post_notifications()
        return has_post_notifications()
