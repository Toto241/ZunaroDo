"""
Tests fuer core/tooltip.py - die schlanke Hover-Tooltip-Klasse.

Display-frei: ein Fake-Widget protokolliert die bind()-Aufrufe, sodass die
Binding-Logik ohne echtes Tk-Display geprueft werden kann.
"""
from __future__ import annotations

import pytest

from core.tooltip import Tooltip, attach_tooltip


pytestmark = [pytest.mark.concept, pytest.mark.release_gate]


class _FakeWidget:
    """Minimal-Stub: merkt sich (sequence, add) je bind()-Aufruf."""

    def __init__(self) -> None:
        self.binds: list[tuple[str, object]] = []

    def bind(self, sequence, _func, add=None):
        self.binds.append((sequence, add))


def test_attach_tooltip_is_noop_for_empty_text():
    assert attach_tooltip(_FakeWidget(), "") is None
    assert attach_tooltip(_FakeWidget(), None) is None  # type: ignore[arg-type]


def test_attach_tooltip_returns_instance_for_text():
    tip = attach_tooltip(_FakeWidget(), "Hilfetext")
    assert isinstance(tip, Tooltip)


def test_tooltip_registers_hover_bindings_additively():
    w = _FakeWidget()
    Tooltip(w, "Erklaerung")
    seqs = {seq for seq, _ in w.binds}
    assert "<Enter>" in seqs
    assert "<Leave>" in seqs
    # Additiv registriert (verdraengt bestehende Bindings nicht).
    assert all(add == "+" for _seq, add in w.binds)


def test_tooltip_with_empty_text_binds_nothing():
    w = _FakeWidget()
    Tooltip(w, "")
    assert w.binds == []


def test_tooltip_survives_widget_bind_errors():
    class _BrokenWidget:
        def bind(self, *_a, **_k):
            raise RuntimeError("kein Display")

    # Darf nicht hochblubbern - Tooltip ist bewusst defensiv.
    Tooltip(_BrokenWidget(), "Text")
