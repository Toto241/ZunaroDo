"""
Guard-Test: alle Capabilities, die die Mobile-Screens aufrufen, muessen
in der echten Registry (main.build_registry) existieren.

Hintergrund: die Mobile-Screens referenzierten frueher Capability-Namen,
die es nie gab (z.B. 'social.list_contacts', 'search.dashboard_summary')
- der Fehler blieb unbemerkt, weil die Kivy-UI hier nicht startbar ist.
Dieser Test schliesst die Luecke ohne Kivy-Abhaengigkeit.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from database import Database
from main import build_registry
from services.output import OutputService


# Capabilities, die die Mobile-Screens via registry.dispatch(...) ansprechen.
_MOBILE_CAPABILITIES = {
    # dashboard.py
    "contracts.list", "contracts.upcoming_deadlines", "calendar.upcoming",
    "system.agenda",
    # contracts.py
    "contracts.add", "contracts.delete",
    # calendar.py
    "calendar.add_event",
    # finance.py
    "finance.list_expenses",
    # more.py
    "family.members", "notes.list", "inbox.proposals",
    "system.search", "social.contacts",
    "family.orders", "family.add_order", "family.complete_order",
}


class TestMobileScreenCapabilities(unittest.TestCase):

    def setUp(self) -> None:
        fd, self.dbpath = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db = Database(self.dbpath)
        self.out = Path(tempfile.mkdtemp(prefix="ah_out_"))
        self.registry = build_registry(self.db, OutputService(str(self.out)))

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.dbpath)

    def test_all_referenced_capabilities_exist(self) -> None:
        missing = sorted(name for name in _MOBILE_CAPABILITIES
                         if not self.registry.has_capability(name))
        self.assertEqual(missing, [],
                         f"Mobile-Screens rufen nicht existente "
                         f"Capabilities auf: {missing}")


if __name__ == "__main__":
    unittest.main()
