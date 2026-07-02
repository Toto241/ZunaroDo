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
                            app_name="ZunaroDo", timeout=10)
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

    def notify(self, title: str, message: str) -> None:
        try:
            self._send(title, message)
        except Exception:                              # pragma: no cover
            print(f"[NOTIFICATION] {title}: {message}")
