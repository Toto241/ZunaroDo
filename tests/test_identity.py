"""Tests fuer services/identity.py."""
from __future__ import annotations

import unittest

from services import identity as ident


class TestIdentity(unittest.TestCase):

    def test_defaults_when_provider_missing_keys(self) -> None:
        ident.load_provider.cache_clear()
        self.assertEqual(ident.package_name(), "de.alltagshelfer.alltagshelfer")
        self.assertIn("Toto241", ident.github_repo())
        self.assertIn("@", ident.support_email())
        self.assertTrue(ident.privacy_url().startswith("https://"))

    def test_github_url(self) -> None:
        self.assertIn("github.com", ident.github_url())
