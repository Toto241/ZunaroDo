"""
Pairwise-(All-Pairs-)Generator fuer die kombinatorische Testmatrix
(Anhang C des Testkonzepts).

Algorithmus (Greedy Coverage Growth):

  1. Bestimme die Menge aller zulaessigen Wertepaare ueber je zwei
     Dimensionen.
  2. Beginne mit leerer Fallliste.
  3. Solange noch ungedeckte Paare existieren und das Budget nicht
     erschoepft ist:
       a. Erzeuge eine Stichprobe von Kandidaten-Faellen, indem fuer
          jeden Kandidaten ein noch ungedecktes Pivot-Paar fixiert und
          die restlichen Dimensionen greedy mit maximaler Neudeckung
          gefuellt werden.
       b. Wenn alle Kandidaten kein neues Paar mehr decken, brich ab.
       c. Sonst nimm den Kandidaten mit der hoechsten Neudeckung.

Damit liegt die 2-fach-Coverage in der Praxis ueber 95 %, wie im
Konzept (Kapitel 3.3) gefordert. Der Algorithmus ist deterministisch
(random.Random(seed)) und liefert reproduzierbare Faelle.
"""
from __future__ import annotations

import random
from itertools import combinations
from typing import Callable, Iterable, Optional


def _all_pairs(dimensions: dict[str, list],
               constraint: Callable[[dict], bool]) -> set[tuple]:
    """Zulaessige Wertepaare ueber je zwei Dimensionen.

    Ein Wertepaar gilt als "zulaessig", wenn es einen vollstaendigen
    Testfall gibt, der dieses Paar enthaelt und das Constraint
    nicht verletzt. Wir approximieren das durch eine schnelle Pruefung
    auf das Paar selbst.
    """
    pairs: set[tuple] = set()
    keys = list(dimensions)
    for a, b in combinations(keys, 2):
        for va in dimensions[a]:
            for vb in dimensions[b]:
                mini = {a: va, b: vb}
                if constraint(mini):
                    pairs.add(((a, va), (b, vb)))
    return pairs


def _covered(case: dict, pairs: set[tuple]) -> set[tuple]:
    keys = list(case)
    cov: set[tuple] = set()
    for a, b in combinations(keys, 2):
        p = ((a, case[a]), (b, case[b]))
        if p in pairs:
            cov.add(p)
    return cov


def _build_case_around(pivot_a: tuple, pivot_b: tuple,
                        dimensions: dict[str, list],
                        constraint: Callable[[dict], bool],
                        pairs_remaining: set[tuple],
                        rng: random.Random) -> Optional[dict]:
    """Baut einen Fall, der das gegebene Pivot-Paar enthaelt und die
    restlichen Dimensionen greedy mit Werten fuellt, die die meisten
    noch ungedeckten Paare decken."""
    (k1, v1), (k2, v2) = pivot_a, pivot_b
    case: dict = {k1: v1, k2: v2}
    if not constraint(case):
        return None
    keys = [k for k in dimensions if k not in case]
    rng.shuffle(keys)
    for dim in keys:
        best_val = None
        best_gain = -1
        values = list(dimensions[dim])
        rng.shuffle(values)
        for v in values:
            cand = dict(case)
            cand[dim] = v
            if not constraint(cand):
                continue
            gain = len(_covered(cand, pairs_remaining))
            if gain > best_gain:
                best_gain = gain
                best_val = v
        if best_val is None:
            return None
        case[dim] = best_val
    return case if constraint(case) else None


def allpairs(dimensions: dict[str, list],
             constraint: Optional[Callable[[dict], bool]] = None,
             seed: int = 0,
             max_cases: int = 2000) -> list[dict]:
    """Erzeugt eine pairwise-abdeckende Liste von Testfaellen."""
    if len(dimensions) < 2:
        raise ValueError("Mindestens zwei Dimensionen noetig")
    constraint = constraint or (lambda c: True)
    rng = random.Random(seed)

    target_pairs = _all_pairs(dimensions, constraint)
    remaining = set(target_pairs)
    cases: list[dict] = []

    safety = 0
    while remaining and safety < max_cases:
        safety += 1
        # Pivot-Paare in deterministischer Reihenfolge anschauen
        pivots = sorted(remaining, key=lambda p: (p[0][0], p[1][0],
                                                    repr(p[0][1]),
                                                    repr(p[1][1])))
        # Kandidatenpool: ersten 12 ungedeckten Pivot-Paaren je einen
        # Fall bauen, dann den mit hoechster Neudeckung uebernehmen.
        best: Optional[dict] = None
        best_gain = -1
        for piv in pivots[:12]:
            cand = _build_case_around(piv[0], piv[1], dimensions, constraint,
                                       remaining, rng)
            if cand is None:
                continue
            gain = len(_covered(cand, remaining))
            if gain > best_gain:
                best_gain = gain
                best = cand
        if best is None or best_gain <= 0:
            break
        cases.append(best)
        remaining -= _covered(best, target_pairs)

    return cases


def coverage(cases: Iterable[dict], dimensions: dict[str, list],
             constraint: Optional[Callable[[dict], bool]] = None
             ) -> tuple[int, int]:
    """Anzahl gedeckter zulaessiger Wertepaare (covered, total)."""
    constraint = constraint or (lambda c: True)
    target = _all_pairs(dimensions, constraint)
    covered: set[tuple] = set()
    for c in cases:
        covered |= _covered(c, target)
    return len(covered), len(target)
