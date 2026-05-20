"""
Regressionstest gegen den Crash:

  AttributeError: '_tkinter.tkapp' object has no attribute 'expense_list'

Ursache: `_refresh_all` ruft alle `_refresh_*`-Methoden auf, auch fuer
Tabs, die durch das Lizenz-Gate gesperrt sind. Bei gesperrten Tabs
wird der Tab-Builder nicht ausgefuehrt, das Hauptwidget (z.B.
`self.expense_list`) existiert deshalb nicht - der Refresh crasht.

Loesung: jede `_refresh_*`-Methode beginnt mit einem `hasattr`-Check
und liefert ohne Fehler zurueck, wenn das Widget fehlt.

Dieser Test ist statisch (kein Tkinter-Display noetig) und stellt
sicher, dass die Wache dauerhaft vorhanden bleibt - auch fuer
zukuenftige Refresh-Methoden.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


REPO = Path(__file__).resolve().parents[2]
GUI_FILE = REPO / "gui.py"


def _refresh_methods() -> list[ast.FunctionDef]:
    """Liefert alle Methoden, die mit '_refresh_' beginnen, in der
    AlltagshelferGUI-Klasse."""
    src = GUI_FILE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    out: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if (isinstance(child, ast.FunctionDef)
                    and child.name.startswith("_refresh_")
                    and child.name not in (
                        # Reine Composer-Methoden ohne eigenes Widget
                        "_refresh_all",)):
                out.append(child)
    return out


def test_refresh_methods_exist():
    """Sanity: wir finden ueberhaupt Refresh-Methoden."""
    methods = _refresh_methods()
    # Mindestens die Bereiche, die im Bug-Report auftauchen
    names = {m.name for m in methods}
    needed = {"_refresh_dashboard", "_refresh_contracts",
              "_refresh_members", "_refresh_tasks", "_refresh_orders",
              "_refresh_shopping", "_refresh_finance",
              "_refresh_calendar", "_refresh_social", "_refresh_inbox",
              "_refresh_status", "_refresh_statistics",
              "_refresh_module_admin"}
    missing = needed - names
    assert not missing, f"_refresh_*-Methoden fehlen in gui.py: {missing}"


def _has_hasattr_guard(method: ast.FunctionDef) -> bool:
    """True wenn die ersten 1-2 ausfuehrbaren Statements ein
    'if not hasattr(self, "X"): return' sind."""
    for stmt in method.body[:2]:
        if not isinstance(stmt, ast.If):
            continue
        test = stmt.test
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            inner = test.operand
            if (isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id == "hasattr"
                    and len(inner.args) >= 2
                    and isinstance(inner.args[0], ast.Name)
                    and inner.args[0].id == "self"):
                # Pruefen, dass im Body return steht
                for body_stmt in stmt.body:
                    if isinstance(body_stmt, ast.Return):
                        return True
    return False


@pytest.mark.parametrize("method_name", [
    "_refresh_dashboard", "_refresh_contracts", "_refresh_members",
    "_refresh_tasks", "_refresh_orders", "_refresh_shopping",
    "_refresh_finance", "_refresh_calendar", "_refresh_social",
    "_refresh_inbox", "_refresh_status", "_refresh_statistics",
    "_refresh_module_admin", "_refresh_history",
])
def test_refresh_method_has_hasattr_guard(method_name: str):
    """Jede dieser Methoden MUSS einen Early-Return haben, wenn ihr
    Hauptwidget fehlt - sonst crasht die App bei gesperrten Tabs."""
    methods = {m.name: m for m in _refresh_methods()}
    if method_name not in methods:
        pytest.skip(f"{method_name} existiert nicht in gui.py")
    method = methods[method_name]
    assert _has_hasattr_guard(method), (
        f"{method_name} hat keinen 'if not hasattr(self, ...): return'-"
        "Schutz als erstes Statement. Das fuehrt zum bekannten Bug "
        "'AttributeError ... has no attribute' bei gesperrten Tabs.")


def test_all_refresh_methods_are_guarded():
    """Negativtest: jede neue _refresh_*-Methode bekommt den Schutz
    automatisch dazu. Schlaegt Alarm, wenn jemand eine neue Methode
    ohne Wache hinzufuegt."""
    offenders: list[str] = []
    for method in _refresh_methods():
        # _refresh_license_state liest aus einem ohnehin-immer-da-
        # Settings-Repo, kein Tab-Widget - akzeptiert ohne Wache.
        if method.name in ("_refresh_license_state",):
            continue
        if not _has_hasattr_guard(method):
            offenders.append(method.name)
    assert not offenders, (
        f"Folgende _refresh_*-Methoden in gui.py haben keinen "
        f"hasattr-Schutz fuer ihr Hauptwidget: {offenders}. "
        "Fix: 'if not hasattr(self, \"<widget>\"): return' als "
        "erste Zeile einfuegen.")
