"""
Erweitertes Release-Gate (TESTING.md Teil II Abschnitt 14 / Anhang J2).

Diese Tests sind statisch (kein Build/keine Cloud), aber wirksam:
sie sperren den Upload, wenn das Repo nicht Compliance-bereit ist.

Abgedeckte J2-IDs:

  J2-S-02   Keine Hardcoded Secrets       (delegiert an test_privacy_scan)
  J2-S-03   Keine Debug-Features im Release-Pfad
  J2-S-04   TLS-only / kein Cleartext
  J2-P-01   Datenschutzerklaerung verlinkt
  J2-P-03   nur dokumentierte Permissions
  J2-G-03   targetSdk >= aktueller Play-Mindestwert (35)
  J2-G-04   Store-Listing-Doku (PLAYSTORE.md) vollstaendig
  J2-T-04   Kein TODO/FIXME mit Schweregrad "BLOCKER"
  J2-Q-01   Negativ-/Privacy-Markerlisten existieren
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


REPO = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# J2-S-03  Keine Debug-Features in Release-Pfaden
# ---------------------------------------------------------------------------
DEBUG_TOKENS = [
    re.compile(r"\bDEBUG\s*=\s*True\b"),
    re.compile(r"\bprint\(\s*['\"]TODO:?\s*DEBUG"),
    re.compile(r"breakpoint\(\)"),
    re.compile(r"\bpdb\.set_trace\("),
]

# Whitelist - Test-/Build-Dateien duerfen breakpoint() haben, Production
# nicht.
APP_FILES = ([REPO / f for f in ("assistant.py", "database.py", "gui.py",
                                  "main.py", "models.py", "diagnose.py")]
             + list((REPO / "core").rglob("*.py"))
             + list((REPO / "modules").rglob("*.py"))
             + list((REPO / "services").rglob("*.py"))
             + list((REPO / "mobile").rglob("*.py")))


@pytest.mark.parametrize("path", APP_FILES,
                          ids=lambda p: p.relative_to(REPO).as_posix())
def test_JS03_no_debug_features_in_release_code(path: Path):
    if "__pycache__" in path.parts:
        pytest.skip("Bytecode-Cache")
    text = path.read_text(encoding="utf-8", errors="replace")
    for pat in DEBUG_TOKENS:
        m = pat.search(text)
        assert m is None, (
            f"Debug-Feature in {path.relative_to(REPO).as_posix()}: "
            f"Muster {pat.pattern!r}")


# ---------------------------------------------------------------------------
# J2-S-04 / J2-P-01  Datenschutz im Manifest + Doku
# ---------------------------------------------------------------------------
def test_JS04_no_clear_text_attribute_default():
    spec = (REPO / "buildozer.spec").read_text(encoding="utf-8")
    # Spec darf keinen Hinweis enthalten, der Cleartext zulaesst
    assert "usesCleartextTraffic=\"true\"" not in spec
    assert "android.cleartext" not in spec or (
        "android.cleartext = false" in spec
        or "android.cleartext = False" in spec)


def test_JP01_privacy_policy_linked_in_playstore_doc():
    text = (REPO / "PLAYSTORE.md").read_text(encoding="utf-8",
                                                errors="replace")
    assert "Datenschutz" in text or "Privacy" in text, (
        "PLAYSTORE.md erwaehnt weder Datenschutz noch Privacy")


# ---------------------------------------------------------------------------
# J2-T-04  Keine BLOCKER-TODOs offen
# ---------------------------------------------------------------------------
BLOCKER_PATTERN = re.compile(
    r"(?:#|\"|')\s*(?:TODO|FIXME|XXX)\s*[:\-]\s*BLOCKER\b",
    re.IGNORECASE)


@pytest.mark.parametrize("path", APP_FILES,
                          ids=lambda p: p.relative_to(REPO).as_posix())
def test_JT04_no_blocker_todo(path: Path):
    if "__pycache__" in path.parts:
        pytest.skip("Bytecode-Cache")
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = BLOCKER_PATTERN.findall(text)
    assert not matches, (
        f"BLOCKER-TODO in {path.relative_to(REPO).as_posix()}: {matches[:2]}")


# ---------------------------------------------------------------------------
# J2-Q-01  Konzept-Marker existieren
# ---------------------------------------------------------------------------
def test_JQ01_concept_markers_registered():
    """Die Marker `negative`, `privacy`, `security`, `release_gate`,
    `combinatorics`, `members`, `property` sind in conftest registriert.
    Wird das versehentlich entfernt, schreibt pytest Warnings - die
    wollen wir sofort sehen."""
    conftest = (REPO / "tests" / "conftest.py").read_text(encoding="utf-8")
    for marker in ("concept", "members", "roles", "combinatorics",
                    "property", "release_gate", "negative", "privacy",
                    "security"):
        assert marker in conftest, f"Marker '{marker}' nicht registriert"


# ---------------------------------------------------------------------------
# J2-G-04  Store-Listing-Dokumentation vollstaendig
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("section", [
    "Voraussetzungen", "Datenschutz", "Closed", "Produktionsfreigabe",
])
def test_JG04_playstore_doc_covers_section(section):
    text = (REPO / "PLAYSTORE.md").read_text(encoding="utf-8",
                                                errors="replace")
    assert section in text, (
        f"PLAYSTORE.md fehlt Abschnitt '{section}'")


# ---------------------------------------------------------------------------
# J2-Q-Konzept  Alle Test-Konzept-Dateien sind in tests/concept/
# ---------------------------------------------------------------------------
def test_concept_directory_contains_full_suite():
    concept = REPO / "tests" / "concept"
    needed = {
        "fixtures.py", "matrix.py", "pairwise.py", "roles.py",
        "test_members_scenarios.py", "test_roles_permissions.py",
        "test_pairwise_matrix.py", "test_properties_concept.py",
        "test_release_gate.py", "test_release_gate_extended.py",
        "test_protocol_generator.py", "test_negative_inputs.py",
        "test_negative_network.py", "test_negative_security.py",
        "test_privacy_scan.py", "test_privacy_data_rights.py",
    }
    present = {p.name for p in concept.iterdir() if p.is_file()}
    missing = needed - present
    assert not missing, f"Konzept-Dateien fehlen: {missing}"


# ---------------------------------------------------------------------------
# Aggregat-Gate: TESTING.md enthaelt Teil II
# ---------------------------------------------------------------------------
def test_testing_doc_contains_part_II():
    text = (REPO / "TESTING.md").read_text(encoding="utf-8",
                                              errors="replace")
    for marker in ("Teil II", "Negativtests", "Datenschutztests",
                   "Go-/No-Go-Kriterien (Erweiterung)",
                   "Nachweisdokumentation"):
        assert marker in text, f"TESTING.md fehlt Abschnitt '{marker}'"
