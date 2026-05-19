"""
Mobile-Frontend (Android-Port) des Alltagshelfers.

Diese Schicht setzt auf KivyMD (Material Design auf Kivy) und ist
bewusst von der Desktop-GUI (gui.py, CustomTkinter) entkoppelt:

- Backend (database.py, modules/*, services/*, core/*) wird 1:1 wiederverwendet.
- Eingang ist `build_registry(db, output)` aus main.py - identische
  Capabilities wie auf dem Desktop.
- UI-Patterns sind phone-spezifisch:
    * Bottom-Navigation mit 5 Hauptbereichen statt 14 Desktop-Tabs
    * Vertikale Listen statt mehrspaltiger Tabellen
    * Floating-Action-Button fuer Schnellaktionen
    * Grosse Tap-Ziele (>=48dp), keine Multi-Klick-Menues

Build auf Android: siehe MOBILE.md.
"""
from __future__ import annotations

__all__ = ["helpers"]
