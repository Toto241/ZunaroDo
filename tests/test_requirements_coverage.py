"""
Meta-Test: jede Anforderung ist automatisiert getestet.

Erzwingt die Traceability aus ``tools.test_protocol``:
  - Jede in REQUIREMENTS definierte Anforderung (R1-R10) ist mindestens
    einer Testdatei zugeordnet.
  - Das Mapping referenziert keine unbekannte Anforderungs-ID.
  - Jede gemappte Testdatei existiert wirklich und enthaelt mindestens
    einen ``test_*``-Fall (kein totes Mapping).

So schlaegt die CI automatisch fehl, sobald eine Anforderung ohne Test
bleibt oder ein Mapping ins Leere zeigt - ganz ohne manuelle Pflege.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from tools.test_protocol import FILE_REQUIREMENTS, REQUIREMENTS

_REPO = Path(__file__).resolve().parents[1]
_ROOTS = (_REPO / "tests", _REPO / "tests" / "concept")


def _locate(stem: str) -> Path | None:
    for root in _ROOTS:
        candidate = root / f"{stem}.py"
        if candidate.exists():
            return candidate
    return None


def _has_test_function(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    return any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and node.name.startswith("test_")
               for node in ast.walk(tree))


class TestRequirementsCoverage(unittest.TestCase):

    def test_every_requirement_has_at_least_one_test(self) -> None:
        covered = {req for reqs in FILE_REQUIREMENTS.values() for req in reqs}
        missing = sorted(set(REQUIREMENTS) - covered)
        self.assertEqual(missing, [],
                         f"Anforderungen ohne zugeordneten Test: {missing}")

    def test_mapping_uses_only_known_requirements(self) -> None:
        known = set(REQUIREMENTS)
        unknown = sorted({req for reqs in FILE_REQUIREMENTS.values()
                          for req in reqs if req not in known})
        self.assertEqual(unknown, [],
                         f"Mapping referenziert unbekannte Anforderungen: "
                         f"{unknown}")

    def test_mapped_files_exist_and_contain_tests(self) -> None:
        problems: list[str] = []
        for stem in sorted(FILE_REQUIREMENTS):
            path = _locate(stem)
            if path is None:
                problems.append(f"{stem}: Datei fehlt in tests/ bzw. "
                                f"tests/concept/")
            elif not _has_test_function(path):
                problems.append(f"{stem}: enthaelt keinen test_*-Fall")
        self.assertEqual(problems, [], "Defekte Test-Zuordnungen:\n  "
                         + "\n  ".join(problems))

    def test_requirement_catalog_is_complete(self) -> None:
        # R1..R10 muessen lueckenlos definiert sein.
        expected = {f"R{i}" for i in range(1, 11)}
        self.assertEqual(set(REQUIREMENTS), expected,
                         "REQUIREMENTS-Katalog ist nicht R1..R10")

    def test_every_test_file_is_mapped(self) -> None:
        # Rueckrichtung: jede vorhandene Testdatei steht im Mapping -
        # sonst fehlt sie stillschweigend in der Dashboard-Matrix
        # (requirements=[]). Genau so blieben 2026-06 vierzehn Dateien
        # (87 Tests) unbemerkt unzugeordnet.
        stems = {p.stem for root in _ROOTS
                 for p in root.glob("test_*.py")}
        unmapped = sorted(stems - set(FILE_REQUIREMENTS))
        self.assertEqual(unmapped, [],
                         "Testdateien ohne Anforderungs-Zuordnung in "
                         "tools/test_protocol.py FILE_REQUIREMENTS: "
                         f"{unmapped}")


if __name__ == "__main__":
    unittest.main()
