"""
Dimensionen und Constraints der kombinatorischen Testmatrix (Anhang C).

Die Werte sind 1:1 die im Konzept (TESTING.md, Kapitel 3) festgelegten -
mit zwei pragmatischen Anpassungen auf die reale Domaene dieses Repos:

  * Anstelle einer Cloud-Sync-Komponente steht hier die lokale Sync-Logik
    aus services/sync.py (Datei-/HTTP-Provider). Die Werte ONLINE/OFFLINE
    bleiben semantisch identisch.
  * "Recurrence" ist auf die App-Werte (1, 7, 14, 30 Tage) und ONE_OFF
    (None) abgebildet, weil HouseholdTask.interval_days int verlangt.

Constraints orientieren sich an Realitaets-Plausibilitaet:

  - Wer GUEST ist, kann nicht OWNER_CONFIRM verlangen.
  - PUSH=BLOCKED schliesst Reminder aus.
  - Eine ONE_OFF-Aufgabe hat per Definition eine Frist (nicht NONE).
"""
from __future__ import annotations


DIMENSIONS: dict[str, list] = {
    "role":       ["OWNER", "ADMIN", "MEMBER", "GUEST"],
    "members":    [1, 2, 5, 11, 12, 20],
    "task_kind":  ["STANDARD", "CHECKLIST", "APPROVAL", "EVENT"],
    "recurrence": ["ONE_OFF", "DAILY", "WEEKLY", "MONTHLY", "CUSTOM"],
    "priority":   ["LOW", "NORMAL", "HIGH", "URGENT"],
    "due":        ["NONE", "FUTURE", "TODAY", "OVERDUE"],
    "reminder":   ["OFF", "M15", "H1", "D1", "CUSTOM"],
    "confirm":    ["NONE", "SELF", "OWNER"],
    "reward":     ["NONE", "POINTS", "STARS"],
    "device":     ["phone_compact", "phone_medium", "foldable", "tablet"],
    "api":        [26, 29, 31, 34, 35],
    "network":    ["ONLINE", "OFFLINE", "SLOW", "FLAKY"],
    "push":       ["ON", "OFF", "BLOCKED"],
    "lifecycle":  ["FOREGROUND", "BACKGROUND", "DOZE", "KILLED"],
}


def constraint(case: dict) -> bool:
    """Filter fuer offensichtlich unsinnige Kombinationen."""
    if case.get("role") == "GUEST" and case.get("confirm") == "OWNER":
        return False
    if case.get("push") == "BLOCKED" and case.get("reminder") not in (
            None, "OFF"):
        return False
    if case.get("recurrence") == "ONE_OFF" and case.get("due") == "NONE":
        return False
    return True


def interval_for(recurrence: str) -> int | None:
    return {
        "ONE_OFF": None,
        "DAILY":   1,
        "WEEKLY":  7,
        "CUSTOM": 10,
        "MONTHLY": 30,
    }.get(recurrence)
