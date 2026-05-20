@echo off
REM ============================================================
REM  Zunarodo - Control Panel
REM
REM  Doppelklick oeffnet das grafische Steuerwerk
REM  (tools/control_panel.py). Dort gibt es Buttons fuer:
REM    - Tests + Dashboard
REM    - Builds fuer Android / iOS / PC
REM    - Play-Store-Sync (init/validate/push/pull/diff/export)
REM    - Dokumentation oeffnen
REM ============================================================

setlocal EnableExtensions
chcp 65001 >nul

pushd "%~dp0"

REM Python pruefen
where python >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] Python ist nicht im PATH gefunden.
    echo         Installiere Python 3.10+ und stelle sicher,
    echo         dass "python" in der Konsole funktioniert.
    echo.
    pause
    popd
    exit /b 1
)

REM customtkinter pruefen, ggf. installieren
python -c "import customtkinter" >nul 2>nul
if errorlevel 1 (
    echo customtkinter fehlt - wird installiert ...
    python -m pip install --upgrade customtkinter
    if errorlevel 1 (
        echo [FEHLER] customtkinter konnte nicht installiert werden.
        pause
        popd
        exit /b 1
    )
)

REM Control Panel starten - 'pythonw' versteckt das Konsolen-Fenster,
REM wenn vorhanden; ansonsten ueber normales 'python'.
where pythonw >nul 2>nul
if errorlevel 1 (
    python -m tools.control_panel
) else (
    start "" pythonw -m tools.control_panel
)

popd
endlocal
exit /b 0
