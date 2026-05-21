"""
Tests fuer die Benachrichtigungs-Berechtigung (Play-Store-Compliance,
Android 13+).

Deckt ab:
  - das Manifest (buildozer.spec) deklariert POST_NOTIFICATIONS,
  - playstore.yml deklariert sie konsistent,
  - der Notifier bleibt nutzbar, wenn das Backend (bzw. die Berechtigung)
    fehlt -> Graceful Degradation statt Absturz,
  - es ist keine sensible/verbotene Permission deklariert.
"""
from __future__ import annotations

from pathlib import Path

import unittest

from services.notifier import Notifier
from tools import playstore_check as pc
from tools.playstore_sync import _load_yaml

_REPO = Path(__file__).resolve().parents[1]


def _declared_permissions() -> set[str]:
    spec = pc.parse_buildozer_spec(_REPO / "buildozer.spec")
    raw = spec.get("android.permissions", "")
    normed = set()
    for p in (x.strip() for x in raw.split(",") if x.strip()):
        normed.add(p if "." in p else f"android.permission.{p}")
    return normed


class TestPostNotificationsPermission(unittest.TestCase):

    def test_manifest_declares_post_notifications(self) -> None:
        self.assertIn("android.permission.POST_NOTIFICATIONS",
                      _declared_permissions())

    def test_playstore_yml_declares_post_notifications(self) -> None:
        cfg = _load_yaml(_REPO / "playstore.yml")
        declared = cfg.get("permissions", {}).get("declared", [])
        self.assertIn("android.permission.POST_NOTIFICATIONS", declared)

    def test_no_denied_sensitive_permission_in_manifest(self) -> None:
        declared = _declared_permissions()
        self.assertEqual(declared & pc.DENIED_PERMISSIONS, set())

    def test_only_whitelisted_permissions_declared(self) -> None:
        declared = _declared_permissions()
        self.assertTrue(declared.issubset(pc.ALLOWED_PERMISSIONS),
                        f"Nicht-whitelisted: {declared - pc.ALLOWED_PERMISSIONS}")


class _BoomNotifier(Notifier):
    """Notifier, dessen Backend immer wirft - simuliert eine fehlende
    Berechtigung / kein verfuegbares Notification-Backend."""

    def __init__(self) -> None:
        super().__init__()

        def _boom(_title: str, _message: str) -> None:
            raise RuntimeError("keine Notification-Berechtigung")

        self._send = _boom


class TestNotifierGracefulDegradation(unittest.TestCase):

    def test_notify_does_not_raise_without_permission(self) -> None:
        # App muss nutzbar bleiben, wenn die Berechtigung verweigert wird:
        # notify() darf die Ausnahme nicht nach aussen durchreichen.
        notifier = _BoomNotifier()
        try:
            notifier.notify("Erinnerung", "Termin heute faellig")
        except Exception as exc:                       # pragma: no cover
            self.fail(f"notify() hat eine Ausnahme propagiert: {exc!r}")


if __name__ == "__main__":
    unittest.main()
