"""
Systematischer Regressionsschutz gegen ungeschuetzte Zugriffe auf
GUI-Widgets, die nur in _build_*-Methoden gesetzt werden.

Hintergrund:
  Beim Lizenz-Gate werden bestimmte Tabs durch ein Upgrade-Panel
  ersetzt, anstatt vom Builder befuellt zu werden. Die zugehoerigen
  Widgets (z.B. self.expense_list, self.chat) existieren dann nicht.
  Jede Methode, die so ein Widget nutzt, muss daher mit einem
  hasattr-Check beginnen - sonst crasht die App im Free-Tier.

Dieser Test ist statisch (AST-Analyse) und verhindert, dass eine
neue Methode hinzukommt, die nicht gegen das Fehlen ihres Widgets
abgesichert ist.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


REPO = Path(__file__).resolve().parents[2]
GUI_FILE = REPO / "gui.py"


# Whitelist:
#  - Methoden, in denen ein Widget gerechtfertigt-ohne-Wache zugegriffen
#    wird (Builder, die das Widget selbst erzeugen; oder Methoden,
#    die ausschliesslich nach einem expliziten Existenz-Check oben in
#    der Klassen-Pipeline aufgerufen werden).
#  - "_safe_*", "_build_*", "_on_*"-Handler greifen typisch nur dann zu,
#    wenn der Button existiert (also auch das Widget). Wir markieren
#    nur die Methoden, die durch _refresh_all / __init__ / mainloop
#    auch ohne Builder-Lauf erreichbar sind.
WHITELIST_METHODS: set[str] = set()


def _conditional_widget_attrs(src: str) -> set[str]:
    """Liefert alle Attribute, die *innerhalb* von _build_*-Methoden
    via 'self.X = ...' gesetzt werden. Genau diese koennen fehlen,
    wenn der Builder nicht aufgerufen wurde."""
    return set().union(*_build_groups(src).values()) if _build_groups(src) \
        else set()


def _build_groups(src: str) -> dict[str, set[str]]:
    """Mapping: Builder-Methodenname -> Menge der dort gesetzten
    self.X-Attribute. Erlaubt 'Gruppen-Schutz': wenn ein Refresh
    eine Attribut-Wache hat, sind alle Attribute desselben Builders
    implizit mitgeschuetzt (sie wurden gemeinsam erzeugt)."""
    tree = ast.parse(src)
    groups: dict[str, set[str]] = {}
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        for fn in cls.body:
            if not (isinstance(fn, ast.FunctionDef)
                     and fn.name.startswith("_build_")):
                continue
            attrs: set[str] = set()
            for node in ast.walk(fn):
                if (isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "self"
                        and isinstance(node.ctx, ast.Store)):
                    attrs.add(node.attr)
            if attrs:
                groups[fn.name] = attrs
    return groups


def _group_for_attr(attr: str, groups: dict[str, set[str]]
                     ) -> set[str]:
    for _, attrs in groups.items():
        if attr in attrs:
            return attrs
    return {attr}


def _methods_using_attr(src: str, attr: str
                         ) -> list[tuple[str, int]]:
    """Liefert (method_name, lineno) Tupel fuer jede Methode, die
    self.<attr> liest, ohne dass die Methode selbst ein _build_*-
    Initialisierer ist."""
    tree = ast.parse(src)
    out: list[tuple[str, int]] = []
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        for fn in cls.body:
            if (not isinstance(fn, ast.FunctionDef)
                    or fn.name.startswith("_build_")):
                continue
            for node in ast.walk(fn):
                if not isinstance(node, ast.Attribute):
                    continue
                if (isinstance(node.value, ast.Name)
                        and node.value.id == "self"
                        and node.attr == attr
                        and isinstance(node.ctx, ast.Load)):
                    out.append((fn.name, fn.lineno))
                    break
    return out


def _has_hasattr_guard_for(method_src: str, attr: str) -> bool:
    """Sucht im (gesamten) Methoden-Body nach einem Schutz
    'if not hasattr(self, "<attr>"): return'."""
    try:
        tree = ast.parse(method_src)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)):
            continue
        inner = test.operand
        if not (isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Name)
                and inner.func.id == "hasattr"
                and len(inner.args) >= 2):
            continue
        arg0 = inner.args[0]
        arg1 = inner.args[1]
        if not (isinstance(arg0, ast.Name) and arg0.id == "self"):
            continue
        if (isinstance(arg1, ast.Constant) and arg1.value == attr):
            # Pruefen, dass der If-Body ein Return enthaelt
            for body_node in node.body:
                if isinstance(body_node, ast.Return):
                    return True
    return False


def _method_source(src: str, method_name: str,
                     line: int) -> str:
    """Extrahiert den Source-Text einer Methode aus gui.py."""
    tree = ast.parse(src)
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        for fn in cls.body:
            if (isinstance(fn, ast.FunctionDef)
                    and fn.name == method_name
                    and fn.lineno == line):
                return ast.get_source_segment(src, fn) or ""
    return ""


def test_can_load_gui_module_source():
    """Sanity: gui.py ist parsbar."""
    src = GUI_FILE.read_text(encoding="utf-8")
    ast.parse(src)


def test_chat_methods_are_guarded():
    """Konkreter Bug-Vorfall: _append_chat ohne hasattr-Wache crasht
    im Free-Tier (kein KI-Tab => kein self.chat)."""
    src = GUI_FILE.read_text(encoding="utf-8")
    for method in ("_append_chat", "_replace_last_chat",
                    "_begin_assistant_stream", "_append_to_stream"):
        hits = _methods_using_attr(src, "chat")
        targets = [(n, ln) for (n, ln) in hits if n == method]
        assert targets, (
            f"Methode {method} existiert nicht oder nutzt self.chat "
            "nicht (Test braucht Update).")
        for (name, lineno) in targets:
            body = _method_source(src, name, lineno)
            assert _has_hasattr_guard_for(body, "chat"), (
                f"{name} (Zeile {lineno}) hat keinen hasattr-Schutz "
                "fuer self.chat. Im Free-Tier (Assistent gesperrt) "
                "crasht das.")


def _methods_called_from(src: str, root_names: set[str]
                          ) -> set[str]:
    """Rueckverfolgt, welche Klassen-Methoden direkt oder transitiv
    von einer der `root_names`-Methoden aufgerufen werden.

    Erkennt zwei Aufrufmuster:
      1. self.X(...)            - direkter Methoden-Aufruf
      2. self.after(N, self.X)  - Callback uebergeben, wird spaeter
                                    durch Tk aufgerufen
    """
    tree = ast.parse(src)
    calls_of: dict[str, set[str]] = {}
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        for fn in cls.body:
            if not isinstance(fn, ast.FunctionDef):
                continue
            calls: set[str] = set()
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                # self.X(...) direkt
                if (isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "self"):
                    calls.add(node.func.attr)
                # Callback-Argumente: self.after(t, self.X) usw.
                for arg in list(node.args) + [kw.value for kw in node.keywords]:
                    if (isinstance(arg, ast.Attribute)
                            and isinstance(arg.value, ast.Name)
                            and arg.value.id == "self"
                            and isinstance(arg.ctx, ast.Load)):
                        calls.add(arg.attr)
            calls_of[fn.name] = calls

    reachable: set[str] = set()
    frontier = set(root_names)
    while frontier:
        nxt = set()
        for name in frontier:
            if name in reachable:
                continue
            reachable.add(name)
            for callee in calls_of.get(name, ()):
                if callee not in reachable:
                    nxt.add(callee)
        frontier = nxt
    return reachable


def test_methods_in_init_path_have_widget_guards():
    """Alle Methoden, die ueber __init__ oder _refresh_all erreichbar
    sind (BEVOR der User klickt), muessen Widget-Zugriffe absichern.

    Genau dieses Risiko hat im Free-Tier zweimal zu Crash gefuehrt:
      - AttributeError: ... 'expense_list'
      - AttributeError: ... 'chat'
    """
    src = GUI_FILE.read_text(encoding="utf-8")
    conditional = _conditional_widget_attrs(src)
    # Daten-Dicts ohne Tk-Bezug ignorieren
    DATA_ONLY = {
        "horizon",
        "contract_inputs", "expense_inputs", "calendar_inputs",
        "task_inputs", "order_inputs", "shopping_inputs", "social_inputs",
        "setting_inputs", "member_inputs",
        "tab_gating",
    }
    candidates = conditional - DATA_ONLY

    # Methoden, die im Init-Pfad transitiv erreichbar sind
    init_path = _methods_called_from(
        src, {"__init__", "_refresh_all", "_maybe_run_onboarding"})

    groups = _build_groups(src)

    # Helfer-Suffixe: Karten-/Reihen-Builder werden nur aus einem schon
    # geschuetzten Refresh aufgerufen.
    HELPER_SUFFIXES = ("_row", "_card")

    offenders: list[str] = []
    for attr in sorted(candidates):
        for method_name, lineno in _methods_using_attr(src, attr):
            if method_name.startswith("_build_"):
                continue
            if method_name not in init_path:
                continue                # nur durch User-Klick erreichbar
            if method_name.endswith(HELPER_SUFFIXES):
                continue                # nur aus geschuetzten Refreshes
            body = _method_source(src, method_name, lineno)
            # Gruppen-Schutz: jede Wache fuer ein Attribut aus der
            # gleichen Builder-Gruppe schuetzt auch dieses Attribut.
            sibling_attrs = _group_for_attr(attr, groups)
            has_guard = any(
                _has_hasattr_guard_for(body, sibling)
                for sibling in sibling_attrs)
            if has_guard:
                continue
            # try/except am Anfang schuetzt auch (Tk-Errors werden
            # geschluckt).
            if "try:" in body and "except" in body:
                continue
            offenders.append(
                f"{method_name} (Zeile {lineno}) liest "
                f"self.{attr} ohne Schutz")

    assert not offenders, (
        "Im Init-Pfad ungeschuetzter Widget-Zugriff:\n  "
        + "\n  ".join(offenders))
