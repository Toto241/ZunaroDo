"""Tests fuer services/android_permissions.py (Desktop-Fallback)."""
from __future__ import annotations

import unittest

from services.android_permissions import (has_post_notifications,
                                          request_post_notifications)


class TestAndroidPermissionsDesktop(unittest.TestCase):

    def test_request_returns_true_on_desktop(self) -> None:
        self.assertTrue(request_post_notifications("test rationale"))

    def test_has_permission_true_on_desktop(self) -> None:
        self.assertTrue(has_post_notifications())
