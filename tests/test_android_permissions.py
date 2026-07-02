"""
Tests fuer services/android_permissions.py (POST_NOTIFICATIONS-Laufzeit-
anfrage, Android 13+).

Auf dem Desktop muss alles ein sicherer No-Op sein; die Android-Pfade
werden ueber gemockte p4a-Module (android.permissions) geprueft.
"""
from __future__ import annotations

import os
import sys
import types
import unittest
from unittest import mock

from services import android_permissions as ap


def _fake_android_modules(granted: bool, requested: list):
    """Baut android/android.permissions-Fakes wie im p4a-Bootstrap."""
    android_mod = types.ModuleType("android")
    perms_mod = types.ModuleType("android.permissions")

    class Permission:
        POST_NOTIFICATIONS = ap.POST_NOTIFICATIONS

    def check_permission(perm):
        return granted

    def request_permissions(perms):
        requested.extend(perms)

    perms_mod.Permission = Permission
    perms_mod.check_permission = check_permission
    perms_mod.request_permissions = request_permissions
    android_mod.permissions = perms_mod
    return {"android": android_mod, "android.permissions": perms_mod}


class TestDesktopNoOp(unittest.TestCase):
    """Ohne Android-Umgebung: True, keine Anfrage, kein Crash."""

    def test_ensure_is_true_on_desktop(self) -> None:
        self.assertNotIn("ANDROID_ARGUMENT", os.environ)
        self.assertTrue(ap.ensure_post_notifications())

    def test_has_is_true_on_desktop(self) -> None:
        self.assertTrue(ap.has_post_notifications())

    def test_app_start_hook_is_wired(self) -> None:
        # Der Mobile-Einstiegspunkt fragt die Permission beim Start an.
        from pathlib import Path
        app_py = (Path(__file__).resolve().parent.parent
                  / "mobile" / "app.py").read_text(encoding="utf-8")
        self.assertIn("ensure_post_notifications", app_py)
        self.assertIn("def on_start", app_py)


class TestAndroidPaths(unittest.TestCase):
    """Simulierter Android-Bootstrap via ANDROID_ARGUMENT + Fake-Module."""

    def _run(self, granted: bool, sdk: int):
        requested: list = []
        fakes = _fake_android_modules(granted, requested)
        with mock.patch.dict(os.environ, {"ANDROID_ARGUMENT": "1"}), \
                mock.patch.dict(sys.modules, fakes), \
                mock.patch.object(ap, "_sdk_int", return_value=sdk):
            result = ap.ensure_post_notifications()
        return result, requested

    def test_granted_needs_no_request(self) -> None:
        result, requested = self._run(granted=True, sdk=34)
        self.assertTrue(result)
        self.assertEqual(requested, [])

    def test_not_granted_triggers_request(self) -> None:
        result, requested = self._run(granted=False, sdk=34)
        self.assertFalse(result)          # Ergebnis kommt asynchron
        self.assertEqual(requested, [ap.POST_NOTIFICATIONS])

    def test_api_below_33_skips_request(self) -> None:
        result, requested = self._run(granted=False, sdk=32)
        self.assertTrue(result)
        self.assertEqual(requested, [])

    def test_missing_p4a_module_is_safe(self) -> None:
        # ANDROID_ARGUMENT gesetzt, aber kein android.permissions-Modul
        # importierbar -> True, kein Crash.
        with mock.patch.dict(os.environ, {"ANDROID_ARGUMENT": "1"}), \
                mock.patch.object(ap, "_sdk_int", return_value=34):
            sys.modules.pop("android.permissions", None)
            sys.modules.pop("android", None)
            self.assertTrue(ap.ensure_post_notifications())
            self.assertTrue(ap.has_post_notifications())

    def test_has_post_notifications_reflects_grant(self) -> None:
        for granted in (True, False):
            requested: list = []
            fakes = _fake_android_modules(granted, requested)
            with mock.patch.dict(os.environ, {"ANDROID_ARGUMENT": "1"}), \
                    mock.patch.dict(sys.modules, fakes), \
                    mock.patch.object(ap, "_sdk_int", return_value=34):
                self.assertEqual(ap.has_post_notifications(), granted)


if __name__ == "__main__":                           # pragma: no cover
    unittest.main()
