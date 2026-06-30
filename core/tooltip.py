"""
Schlanker Hover-Tooltip fuer Tkinter / CustomTkinter-Widgets.

Zeigt nach kurzer Verzoegerung ein kleines Toplevel mit Hilfetext, sobald die
Maus ueber dem Ziel-Widget steht, und blendet es bei ``<Leave>`` (oder einem
Klick) wieder aus.

Bewusst ohne Fremd-Abhaengigkeit und durchgehend defensiv: Jede Tk-Operation
ist in ``try/except`` gekapselt, damit ein Tooltip das UI niemals zum Absturz
bringt. Die Hover-Bindings werden mit ``add="+"`` registriert, sodass sie
bestehende ``<Enter>``/``<Leave>``-Bindings nicht verdraengen.

Nutzung::

    from core.tooltip import attach_tooltip
    attach_tooltip(entry, "Erklaerung, die beim Hover erscheint")
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional


class Tooltip:
    """Haengt einen verzoegerten Hover-Tooltip an ein Widget.

    Eine Referenz auf die Instanz muss nicht gehalten werden: Tkinter haelt
    die gebundenen Methoden (und damit die Instanz) am Leben, solange das
    Ziel-Widget existiert.
    """

    def __init__(self, widget, text: str, *, delay_ms: int = 450,
                 wraplength: int = 320) -> None:
        self.widget = widget
        self.text = text or ""
        self.delay_ms = delay_ms
        self.wraplength = wraplength
        self._tip: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None
        if self.text:
            try:
                widget.bind("<Enter>", self._schedule, add="+")
                widget.bind("<Leave>", self._hide, add="+")
                widget.bind("<ButtonPress>", self._hide, add="+")
            except Exception:                              # noqa: BLE001
                pass

    # -- Zeitsteuerung ---------------------------------------------------
    def _schedule(self, _event=None) -> None:
        self._cancel()
        try:
            self._after_id = self.widget.after(self.delay_ms, self._show)
        except Exception:                                  # noqa: BLE001
            self._after_id = None

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:                              # noqa: BLE001
                pass
            self._after_id = None

    # -- Anzeige ---------------------------------------------------------
    def _show(self) -> None:
        if self._tip is not None or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = (self.widget.winfo_rooty()
                 + self.widget.winfo_height() + 6)
            tip = tk.Toplevel(self.widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{x}+{y}")
            try:
                tip.attributes("-topmost", True)
            except Exception:                              # noqa: BLE001
                pass
            tk.Label(
                tip, text=self.text, justify="left",
                background="#2D2D2D", foreground="#FFFFFF",
                relief="solid", borderwidth=1,
                wraplength=self.wraplength, padx=8, pady=5,
                font=("Segoe UI", 9),
            ).pack()
            self._tip = tip
        except Exception:                                  # noqa: BLE001
            self._tip = None

    def _hide(self, _event=None) -> None:
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:                              # noqa: BLE001
                pass
            self._tip = None


def attach_tooltip(widget, text: str, **kwargs) -> Optional[Tooltip]:
    """Bequeme Fabrik: haengt einen Tooltip an; No-op (None) bei leerem Text."""
    if not text:
        return None
    return Tooltip(widget, text, **kwargs)
