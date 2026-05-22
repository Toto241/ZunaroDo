"""
Tests für die Geräte-Profil-Verwaltung (app_core.profiles).

Vollautomatisch, mit temporärem base_dir/Pointer - keine Seiteneffekte,
kein Display.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from app_core.profiles import DEFAULT_LABEL, ProfilesManager


class TestProfilesManager(unittest.TestCase):

    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="ah_profiles_"))
        self.mgr = ProfilesManager(
            base_dir=self.base,
            pointer_path=self.base / "active.json")
        # ALLTAGSHELFER_PROFILE darf die Tests nicht beeinflussen.
        self._env = os.environ.pop("ALLTAGSHELFER_PROFILE", None)

    def tearDown(self) -> None:
        if self._env is not None:
            os.environ["ALLTAGSHELFER_PROFILE"] = self._env
        shutil.rmtree(self.base, ignore_errors=True)

    def test_default_is_active_initially(self) -> None:
        self.assertEqual(self.mgr.active(), "")
        listed = self.mgr.list()
        self.assertTrue(any(p["name"] == "" and p["active"] for p in listed))
        self.assertEqual(listed[0]["label"], DEFAULT_LABEL)

    def test_create_appears_and_becomes_active(self) -> None:
        result = self.mgr.create("Anna")
        self.assertEqual(result["active"], "Anna")
        self.assertTrue(result["restart_required"])
        self.assertEqual(self.mgr.active(), "Anna")
        names = {p["name"] for p in self.mgr.list()}
        self.assertIn("Anna", names)
        self.assertIn("", names)            # Default bleibt wählbar
        # State-Verzeichnis wurde angelegt -> list_profiles erkennt es.
        self.assertTrue((self.base / ".alltagshelfer-state-Anna").is_dir())

    def test_switch_changes_active_and_persists(self) -> None:
        self.mgr.create("Anna")
        self.mgr.create("Bob")
        self.mgr.switch("Anna")
        self.assertEqual(self.mgr.active(), "Anna")
        # Frische Instanz liest denselben Pointer -> Persistenz.
        again = ProfilesManager(base_dir=self.base,
                                pointer_path=self.base / "active.json")
        self.assertEqual(again.active(), "Anna")

    def test_switch_to_default(self) -> None:
        self.mgr.create("Anna")
        self.mgr.switch("")
        self.assertEqual(self.mgr.active(), "")

    def test_invalid_name_rejected(self) -> None:
        self.assertIn("error", self.mgr.create("   "))
        self.assertIn("error", self.mgr.create("!!!"))
        self.assertEqual(self.mgr.active(), "")     # nichts gewechselt

    def test_name_is_sanitized(self) -> None:
        self.mgr.create("Anna Meier!")              # -> AnnaMeier
        self.assertEqual(self.mgr.active(), "AnnaMeier")

    def test_env_var_overrides_pointer(self) -> None:
        self.mgr.switch("Anna")
        os.environ["ALLTAGSHELFER_PROFILE"] = "ci"
        try:
            self.assertEqual(self.mgr.active(), "ci")
        finally:
            os.environ.pop("ALLTAGSHELFER_PROFILE", None)


class TestProfilesModule(unittest.TestCase):
    """Capability-Schicht über dem Manager (system.profiles*)."""

    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="ah_profmod_"))
        self._env = os.environ.pop("ALLTAGSHELFER_PROFILE", None)
        from modules.profiles import ProfilesModule
        self.mod = ProfilesModule(base_dir=str(self.base))
        # Pointer in das Temp-Verzeichnis umlenken (keine cwd-Seiteneffekte).
        self.mod._mgr.pointer_path = self.base / "active.json"

    def tearDown(self) -> None:
        if self._env is not None:
            os.environ["ALLTAGSHELFER_PROFILE"] = self._env
        shutil.rmtree(self.base, ignore_errors=True)

    def test_capabilities_use_system_prefix(self) -> None:
        names = {c.name for c in self.mod.get_capabilities()}
        self.assertEqual(names, {"system.profiles", "system.profile_create",
                                 "system.profile_switch"})
        self.assertTrue(all(n.startswith("system.") for n in names))

    def test_list_create_switch_flow(self) -> None:
        self.assertEqual(self.mod._cap_list()["active"], "")
        created = self.mod._cap_create("Anna")
        self.assertEqual(created["active"], "Anna")
        listing = self.mod._cap_list()
        self.assertEqual(listing["active"], "Anna")
        self.assertIn("Anna", {p["name"] for p in listing["profiles"]})
        self.mod._cap_switch("")
        self.assertEqual(self.mod._cap_list()["active"], "")

    def test_create_invalid_returns_error(self) -> None:
        self.assertIn("error", self.mod._cap_create("###"))


if __name__ == "__main__":
    unittest.main()
