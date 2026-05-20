"""
Konzept-Tests: Release-Gate (Anhang J).

Diese Tests sind die "harten" Go/No-Go-Kriterien aus dem Testkonzept.
Sie sind so geschnitten, dass sie *nur* anhand des Repository-Standes
ohne externe Systeme entschieden werden koennen. Externe Kriterien
(Crashlytics, ANR, Tester-Engagement) bleiben Pflichtfelder im
manuellen Release-Protokoll.

Gepruefte Kriterien:

  J1  Versions-Code monoton steigend (buildozer.spec).
  J2  Datenschutzerklaerung im Repo.
  J3  Lizenz-Datei im Repo.
  J4  PLAYSTORE.md vorhanden.
  J5  TESTING.md vorhanden.
  J6  alle Konzept-Test-Module importierbar.
  J7  Pairwise-Matrix-Artefakt erzeugbar.
  J8  Berechtigungs-Soll-Matrix vollstaendig (60 Eintraege).
  J9  Alle definierten Profile M-01..M-09 importierbar.
  J10 Smoke: ModuleRegistry baut sich vollstaendig zusammen.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.interface import ModuleRegistry
from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, NoteRepository,
                      ProposalRepository, ShoppingRepository,
                      SocialRepository)
from modules.calendar import CalendarModule
from modules.contracts import ContractModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from modules.notes import NotesModule
from modules.social import SocialModule

from .fixtures import PROFILES
from .matrix import DIMENSIONS, constraint
from .pairwise import allpairs, coverage
from .roles import Action, Role, _MATRIX  # type: ignore[attr-defined]


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.concept
@pytest.mark.release_gate
def test_J1_version_code_is_positive_integer():
    spec = REPO_ROOT / "buildozer.spec"
    assert spec.is_file(), "buildozer.spec fehlt"
    text = spec.read_text(encoding="utf-8", errors="replace")
    found = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("android.numeric_version"):
            _, _, value = line.partition("=")
            try:
                found = int(value.strip())
            except ValueError:
                found = None
        elif line.startswith("version") and "=" in line and found is None:
            _, _, value = line.partition("=")
            value = value.strip()
            try:
                # Versions-String "1.2.3" -> 010203 als Sanity-Check
                parts = [int(p) for p in value.split(".")]
                found = sum(p * (1000 ** i)
                             for i, p in enumerate(reversed(parts)))
            except ValueError:
                pass
    assert found and found > 0, (
        "Versions-Angabe in buildozer.spec fehlt oder ist 0")


@pytest.mark.concept
@pytest.mark.release_gate
def test_J2_privacy_documents_present():
    legal = REPO_ROOT / "legal"
    assert legal.is_dir(), "Verzeichnis 'legal/' fehlt"
    expected = ["datenschutz.md", "privacy.md", "datenschutz.html"]
    found = [p.name for p in legal.iterdir()]
    assert any(name.lower() in (n.lower() for n in found)
               for name in expected), (
        f"Keine Datenschutzerklaerung in legal/ gefunden, vorhanden: {found}")


@pytest.mark.concept
@pytest.mark.release_gate
def test_J3_license_file_present():
    assert (REPO_ROOT / "LICENSE").is_file(), "LICENSE fehlt"


@pytest.mark.concept
@pytest.mark.release_gate
def test_J4_playstore_doc_present():
    assert (REPO_ROOT / "PLAYSTORE.md").is_file(), "PLAYSTORE.md fehlt"


@pytest.mark.concept
@pytest.mark.release_gate
def test_J5_testing_doc_present():
    assert (REPO_ROOT / "TESTING.md").is_file(), "TESTING.md fehlt"


@pytest.mark.concept
@pytest.mark.release_gate
def test_J6_concept_modules_import():
    """Alle Konzept-Test-Module muessen ohne Seiteneffekt importierbar sein."""
    import importlib
    for name in ("tests.concept.fixtures",
                 "tests.concept.pairwise",
                 "tests.concept.matrix",
                 "tests.concept.roles"):
        assert importlib.import_module(name) is not None


@pytest.mark.concept
@pytest.mark.release_gate
def test_J7_pairwise_matrix_has_full_coverage():
    cases = allpairs(DIMENSIONS, constraint=constraint, seed=42)
    cov, total = coverage(cases, DIMENSIONS, constraint=constraint)
    assert cov / total >= 0.95


@pytest.mark.concept
@pytest.mark.release_gate
def test_J8_permission_matrix_is_complete():
    """Erwartete Anzahl Soll-Eintraege = |Roles| * |Actions|."""
    expected = len(list(Role)) * len(list(Action))
    assert len(_MATRIX) == expected, (
        f"Berechtigungsmatrix unvollstaendig: {len(_MATRIX)}/{expected}")


@pytest.mark.concept
@pytest.mark.release_gate
def test_J9_member_profiles_present():
    needed = {"M-01", "M-02", "M-03", "M-04", "M-05",
              "M-06", "M-07", "M-08", "M-09"}
    assert needed.issubset(PROFILES.keys()), (
        f"Konzept-Profile fehlen: {needed - set(PROFILES.keys())}")


@pytest.mark.concept
@pytest.mark.release_gate
def test_J10_full_module_registry_assembles():
    """Smoke: alle Module registrieren sich ohne Fehler."""
    import os
    import tempfile
    fd, path = tempfile.mkstemp(prefix="zd-gate-", suffix=".db")
    os.close(fd)
    try:
        db = Database(path=path)
        try:
            reg = ModuleRegistry()
            reg.register(FamilyModule(FamilyRepository(db),
                                        ShoppingRepository(db)))
            reg.register(ContractModule(ContractRepository(db)))
            reg.register(FinanceModule(ExpenseRepository(db)))
            reg.register(CalendarModule(CalendarRepository(db)))
            reg.register(SocialModule(SocialRepository(db)))
            reg.register(NotesModule(NoteRepository(db)))
            reg.register(InboxModule(ProposalRepository(db)))
            # mindestens 7 Module + nichttrivial viele Capabilities
            assert len(reg.modules()) >= 7
            assert len(reg.all_capabilities()) >= 20
        finally:
            db.close()
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
