"""
Konzept-Test: Pairwise-Matrix (Anhang C).

Erzeugt die kombinatorische Testfall-Liste aus den Dimensionen in
concept/matrix.py mit dem All-Pairs-Generator aus concept/pairwise.py.

Pruefungen:

  1. Der Generator liefert deterministisch dieselbe Anzahl Faelle
     fuer denselben Seed.
  2. Jeder erzeugte Fall verletzt KEIN Constraint.
  3. Die 2-fach-Abdeckung ueber alle zulaessigen Wertepaare betraegt
     mindestens 95 % (Konzept-Anforderung Kapitel 3.3).
  4. Jeder erzeugte Fall ist gegen die App-Domaene ausfuehrbar:
     wird eine HouseholdTask konstruiert und gegen die FamilyRepository
     gespeichert/gelesen.
  5. Die Matrix wird zusaetzlich als Artefakt nach
     `tests/concept/pairwise-matrix.tsv` geschrieben (Anhang C-Ausgabe).
"""
from __future__ import annotations

import csv
import os
from datetime import date, timedelta
from pathlib import Path

import pytest

from models import FamilyMember, HouseholdTask

from .fixtures import fresh_repos
from .matrix import DIMENSIONS, constraint, interval_for
from .pairwise import allpairs, coverage


ARTIFACT_DIR = Path("tests/concept/reports")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_TSV = ARTIFACT_DIR / "pairwise-matrix.tsv"


@pytest.fixture(scope="module")
def pairwise_cases() -> list[dict]:
    cases = allpairs(DIMENSIONS, constraint=constraint, seed=42)
    # Auch als Artefakt schreiben (siehe Anhang C des Konzepts)
    with open(ARTIFACT_TSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["#", *DIMENSIONS.keys()])
        for i, c in enumerate(cases, start=1):
            writer.writerow([i, *(c[k] for k in DIMENSIONS)])
    return cases


@pytest.mark.concept
@pytest.mark.combinatorics
def test_matrix_is_deterministic():
    """Zwei Aufrufe mit gleichem Seed liefern identische Faelle."""
    a = allpairs(DIMENSIONS, constraint=constraint, seed=42)
    b = allpairs(DIMENSIONS, constraint=constraint, seed=42)
    assert a == b


@pytest.mark.concept
@pytest.mark.combinatorics
def test_matrix_respects_constraints(pairwise_cases):
    for case in pairwise_cases:
        assert constraint(case), f"Constraint verletzt: {case}"


@pytest.mark.concept
@pytest.mark.combinatorics
def test_matrix_has_acceptable_size(pairwise_cases):
    """Die Matrix darf zwischen 50 und 2000 Faellen liegen.

    Volle Kombination waeren ~9.4 Mrd. Faelle; pairwise schrumpft das
    Universum drastisch. Wir setzen eine grosszuegige Bandbreite, damit
    Aenderungen an den Constraints offensichtlich werden.
    """
    assert 50 <= len(pairwise_cases) <= 2000, len(pairwise_cases)


@pytest.mark.concept
@pytest.mark.combinatorics
def test_matrix_covers_at_least_95_percent_of_pairs(pairwise_cases):
    covered, total = coverage(pairwise_cases, DIMENSIONS)
    ratio = covered / total
    assert ratio >= 0.95, (
        f"2-fach-Coverage zu niedrig: {ratio:.1%} ({covered}/{total})")


@pytest.mark.concept
@pytest.mark.combinatorics
@pytest.mark.parametrize("idx", list(range(0, 196, 25)))
def test_sampled_cases_persist_in_real_repo(pairwise_cases, idx):
    """Stichproben aus der Matrix laufen gegen die echte Datenschicht.

    Wir simulieren pro Stichprobe eine kleine Familie und legen genau
    eine Aufgabe an, die den case beschreibt. Damit ist nachgewiesen,
    dass die Pairwise-Faelle nicht nur theoretisch existieren, sondern
    auch in der echten App-Datenbank funktionieren.
    """
    if idx >= len(pairwise_cases):
        pytest.skip("Index liegt jenseits der erzeugten Matrix")
    case = pairwise_cases[idx]
    repos = fresh_repos()
    try:
        # 1) Mitglieder gemaess case["members"]
        size = case["members"]
        members: list[FamilyMember] = []
        for i in range(size):
            members.append(repos.family.add_member(
                FamilyMember(name=f"P-{i + 1}", role="erwachsen")))

        # 2) Eine HouseholdTask, die so viele Aspekte wie moeglich abbildet
        interval = interval_for(case["recurrence"]) or 9999
        today = date(2026, 5, 20)
        due_offset = {
            "NONE": 30,
            "FUTURE": 7,
            "TODAY": 0,
            "OVERDUE": -3,
        }[case["due"]]
        next_due = today + timedelta(days=due_offset)
        rotation = [m.id for m in members if m.id is not None]
        task = repos.family.add_task(HouseholdTask(
            title=f"case-{idx:04d}",
            interval_days=interval,
            next_due=next_due,
            rotation=rotation,
            current_index=0,
        ))
        assert task.id is not None
        # Re-Read laeuft fehlerfrei
        again = repos.family.get_task(task.id)
        assert again is not None
        assert again.title == task.title
        assert len(again.rotation) == size
    finally:
        repos.close()


@pytest.mark.concept
@pytest.mark.combinatorics
def test_artifact_tsv_written(pairwise_cases):
    assert ARTIFACT_TSV.is_file()
    head = ARTIFACT_TSV.read_text(encoding="utf-8").splitlines()[0]
    expected = ["#", *DIMENSIONS.keys()]
    assert head.split("\t") == expected
