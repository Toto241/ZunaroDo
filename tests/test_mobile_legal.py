"""Tests fuer Mobile-Legal-Integration."""
from __future__ import annotations

import unittest

from services.privacy_consent import consent_accepted, mark_consent_accepted

try:
    from mobile.screens.legal_doc import legal_menu_entries
    HAS_KIVY = True
except ImportError:
    HAS_KIVY = False


class _FakeSettings:
    def __init__(self):
        self._data = {}

    def get(self, key, default=""):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value


class TestPrivacyOnboarding(unittest.TestCase):

    def test_consent_not_accepted_initially(self) -> None:
        s = _FakeSettings()
        self.assertFalse(consent_accepted(s))

    def test_mark_consent(self) -> None:
        s = _FakeSettings()
        mark_consent_accepted(s)
        self.assertTrue(consent_accepted(s))


class TestLegalMenu(unittest.TestCase):

    @unittest.skipUnless(HAS_KIVY, "kivy not installed")
    def test_four_legal_docs(self) -> None:
        entries = legal_menu_entries()
        docs = [e[2] for e in entries]
        self.assertEqual(docs, ["DATENSCHUTZ", "IMPRESSUM", "AGB", "WIDERRUF"])
