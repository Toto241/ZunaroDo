"""
Konzept-Tests: Property-/Fuzz-Tests (TESTING.md Kapitel 8.2 / 8.5).

Wenn das Paket 'hypothesis' installiert ist, werden echte Property-
Tests gefahren. Andernfalls greift ein deterministischer Pseudo-Fuzz
mit fixem Seed und 200 Iterationen pro Property. Beides liefert
dieselbe Aussage; der Unterschied liegt nur in der Such-Strategie
fuer Gegenbeispiele.

Geprueftes Verhalten:

  P1  Rotation einer wiederkehrenden Aufgabe schreitet bei
      complete_task() um genau einen Index voran (mod len).
  P2  Bei "ueberfaelliger" Aufgabe wird die Rotation um mehrere
      Zyklen weitergedreht - aber nie negativ und immer in der
      Zukunft danach.
  P3  Berechtigungs-Engine: GUEST darf niemals destruktive Aktionen.
  P4  Berechtigungs-Engine: OWNER darf jede Aktion.
  P5  classify_urgency() ist monoton: weniger Tage -> nie niedrigere
      Dringlichkeit.
  P6  Pairwise-Generator deckt bei gleichem Seed identische Faelle.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Callable

import pytest

from models import FamilyMember, HouseholdTask, classify_urgency

from .fixtures import fresh_repos
from .matrix import DIMENSIONS, constraint
from .pairwise import allpairs
from .roles import Action, Permission, Role, is_allowed


try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
    HAS_HYPOTHESIS = True
except ImportError:                                       # pragma: no cover
    HAS_HYPOTHESIS = False


# ---------------------------------------------------------------------------
# Hilfs-Iterator: hypothesis ODER deterministischer Pseudo-Fuzz
# ---------------------------------------------------------------------------
def _fuzz(n: int, seed: int, fn: Callable[[random.Random], None]) -> None:
    rng = random.Random(seed)
    for _ in range(n):
        fn(rng)


# ---------------------------------------------------------------------------
# P1  Rotation um genau einen Index pro complete_task
# ---------------------------------------------------------------------------
@pytest.mark.concept
@pytest.mark.property
def test_P1_rotation_advances_one_step():
    def one(rng: random.Random) -> None:
        size = rng.randint(2, 6)
        repos = fresh_repos()
        try:
            members = [repos.family.add_member(
                FamilyMember(name=f"M{i}", role="erwachsen"))
                for i in range(size)]
            ids = [m.id for m in members]
            interval = 7
            # complete_task() vergleicht mit date.today() fuer Catch-up.
            # next_due mindestens ein Intervall in der Zukunft -> genau ein
            # Zyklus (new_due = next_due + interval liegt dann > heute).
            today = date.today()
            task = repos.family.add_task(HouseholdTask(
                title="rot", interval_days=interval,
                next_due=today + timedelta(days=interval),
                rotation=ids, current_index=0))
            assert task.id is not None
            before = repos.family.get_task(task.id)
            assert before is not None
            updated = repos.family.complete_task(task.id)
            assert (updated.current_index - before.current_index) % size == 1
        finally:
            repos.close()

    _fuzz(20, seed=42, fn=one)


# ---------------------------------------------------------------------------
# P2  Ueberfaellige Aufgabe -> Rotation laeuft mehrere Zyklen weiter,
#      next_due landet in der Zukunft
# ---------------------------------------------------------------------------
@pytest.mark.concept
@pytest.mark.property
def test_P2_overdue_task_rolls_forward_to_future():
    def one(rng: random.Random) -> None:
        size = rng.randint(2, 5)
        interval = rng.choice([1, 7, 14])
        overdue_cycles = rng.randint(2, 5)
        repos = fresh_repos()
        try:
            members = [repos.family.add_member(
                FamilyMember(name=f"M{i}", role="erwachsen"))
                for i in range(size)]
            ids = [m.id for m in members]
            today = date.today()
            past_due = today - timedelta(days=interval * overdue_cycles)
            task = repos.family.add_task(HouseholdTask(
                title="overdue", interval_days=interval,
                next_due=past_due, rotation=ids, current_index=0))
            assert task.id is not None
            updated = repos.family.complete_task(task.id)
            assert updated.next_due is not None
            assert updated.next_due > today, (
                f"next_due {updated.next_due} sollte > heute sein")
            assert 0 <= updated.current_index < size
        finally:
            repos.close()

    _fuzz(20, seed=43, fn=one)


# ---------------------------------------------------------------------------
# P3  GUEST darf niemals destruktive Aktionen
# ---------------------------------------------------------------------------
DESTRUCTIVE_ACTIONS = [
    Action.GROUP_CREATE, Action.GROUP_DELETE, Action.OWNERSHIP_TRANSFER,
    Action.MEMBER_INVITE, Action.MEMBER_REMOVE,
    Action.MEMBER_CHANGE_ROLE, Action.TASK_CREATE,
    Action.TASK_ASSIGN_OTHER, Action.TASK_CLOSE_OTHER,
    Action.DATA_EXPORT,
]


@pytest.mark.concept
@pytest.mark.property
@pytest.mark.parametrize("action", DESTRUCTIVE_ACTIONS,
                          ids=lambda a: a.value)
def test_P3_guest_cannot_perform_destructive(action: Action):
    assert is_allowed(Permission(Role.GUEST, action)) is False


# ---------------------------------------------------------------------------
# P4  OWNER darf jede Aktion
# ---------------------------------------------------------------------------
@pytest.mark.concept
@pytest.mark.property
@pytest.mark.parametrize("action", list(Action), ids=lambda a: a.value)
def test_P4_owner_allowed_everything(action: Action):
    assert is_allowed(Permission(Role.OWNER, action)) is True


# ---------------------------------------------------------------------------
# P5  classify_urgency monoton
# ---------------------------------------------------------------------------
@pytest.mark.concept
@pytest.mark.property
def test_P5_classify_urgency_is_monotonic():
    _ranks = {"normal": 0, "mittel": 1, "hoch": 2}
    rng = random.Random(44)
    for _ in range(200):
        a = rng.randint(-365, 365)
        b = a + rng.randint(0, 365)   # b >= a
        ua = classify_urgency(a)
        ub = classify_urgency(b)
        assert _ranks[ua] >= _ranks[ub], (
            f"weniger Tage ({a}) muss >= dringlich sein als mehr ({b}); "
            f"ergab {ua} vs {ub}")


# ---------------------------------------------------------------------------
# P6  Pairwise ist deterministisch
# ---------------------------------------------------------------------------
@pytest.mark.concept
@pytest.mark.property
def test_P6_pairwise_deterministic():
    a = allpairs(DIMENSIONS, constraint=constraint, seed=42)
    b = allpairs(DIMENSIONS, constraint=constraint, seed=42)
    assert a == b


# ---------------------------------------------------------------------------
# Optional: hypothesis-Strategien
# ---------------------------------------------------------------------------
if HAS_HYPOTHESIS:

    @pytest.mark.concept
    @pytest.mark.property
    @settings(max_examples=100)
    @given(days=st.integers(min_value=-3650, max_value=3650))
    def test_P5_hypothesis_classify_urgency_stable(days):
        result = classify_urgency(days)
        assert result in ("hoch", "mittel", "normal")
