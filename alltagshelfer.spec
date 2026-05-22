# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller-Spec fuer ZunaroDo.

Bau:
    pyinstaller --noconfirm alltagshelfer.spec

Erzeugt ein Single-Folder-Bundle unter dist/ZunaroDo/. Single-File
(`--onefile`) ist absichtlich aus, weil das den GUI-Start spuerbar
verlangsamt (Self-Extract bei jedem Start).
"""
from __future__ import annotations

import os

block_cipher = None

project_root = os.path.abspath(os.path.dirname(SPEC))   # noqa: F821


def _exists(relpath: str) -> bool:
    return os.path.isfile(os.path.join(project_root, relpath))


# Sprach-Dateien und sonstige Ressourcen optional einbinden
datas = []
for candidate in ("locales", "assets", "resources"):
    candidate_path = os.path.join(project_root, candidate)
    if os.path.isdir(candidate_path):
        datas.append((candidate_path, candidate))


a = Analysis(                                       # noqa: F821
    ["gui.py"],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # CTk und Tk-Themes
        "customtkinter",
        "tkinter",
        # Optionale Drittpakete - wenn vorhanden, mitnehmen
        "sqlcipher3",
        "cryptography",
        "google.generativeai",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "PySide6", "PyQt5", "PyQt6",        # nicht benoetigt
        "matplotlib", "scipy", "numpy",     # nicht benoetigt
        "anthropic", "openai",              # bewusst nicht gewollt
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)   # noqa: F821


exe = EXE(                                              # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ZunaroDo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,                # GUI-App
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, "assets", "app.ico")
        if _exists(os.path.join("assets", "app.ico")) else None,
)


coll = COLLECT(                                          # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ZunaroDo",
)
