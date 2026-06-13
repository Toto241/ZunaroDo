"""
Sichert die generierten AI-Studio-Contracts gegen Code-Drift ab.

Die Artefakte unter docs/ai-studio/contracts/ werden aus der echten Registry
und dem echten DB-Schema erzeugt. Dieser Test stellt sicher, dass sie aktuell
sind (sonst: `python -m tools.gen_ai_studio_contracts` ausfuehren) und dass der
Contract strukturell zur Capability-Registry passt.
"""
from __future__ import annotations

import json
import os
import unittest

from tools import gen_ai_studio_contracts as gen

_OUT = gen.OUT_DIR


def _read(name: str) -> str:
    with open(os.path.join(_OUT, name), encoding="utf-8") as fh:
        return fh.read()


class TestAiStudioContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = gen.generate()

    def test_committed_contracts_are_current(self) -> None:
        """Committete Dateien == frisch generierte (kein Drift)."""
        for name, content in self.artifacts.items():
            with self.subTest(artifact=name):
                self.assertEqual(
                    _read(name), content,
                    f"{name} veraltet - "
                    "`python -m tools.gen_ai_studio_contracts` ausfuehren.")

    def test_capabilities_and_openapi_consistent(self) -> None:
        caps = json.loads(self.artifacts["capabilities.json"])
        openapi = json.loads(self.artifacts["openapi.json"])
        self.assertGreater(caps["count"], 0)
        self.assertEqual(caps["count"], len(caps["capabilities"]))
        # Jede Capability hat genau einen POST-Endpunkt.
        self.assertEqual(len(openapi["paths"]), caps["count"])
        for cap in caps["capabilities"]:
            path = f"/api/{cap['name']}"
            self.assertIn(path, openapi["paths"])
            self.assertIn("post", openapi["paths"][path])

    def test_destructive_and_internal_flags_present(self) -> None:
        caps = json.loads(self.artifacts["capabilities.json"])
        self.assertTrue(caps["destructive"], "destruktive Liste leer?")
        self.assertTrue(caps["internal"], "interne Liste leer?")
        # Flags spiegeln sich in OpenAPI als x-destructive/x-internal.
        openapi = json.loads(self.artifacts["openapi.json"])
        for name in caps["destructive"]:
            op = openapi["paths"][f"/api/{name}"]["post"]
            self.assertTrue(op["x-destructive"])

    def test_sql_and_prisma_cover_core_tables(self) -> None:
        sql = self.artifacts["schema.sql"]
        prisma = self.artifacts["schema.prisma"]
        for table in ("contracts", "expenses", "calendar_events",
                      "family_members", "app_settings"):
            with self.subTest(table=table):
                self.assertIn(table, sql)
                self.assertIn(f'@@map("{table}")', prisma)


if __name__ == "__main__":
    unittest.main()
