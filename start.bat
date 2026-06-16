@echo off
REM ============================================================
REM  Zunarodo - Start
REM
REM  Doppelklick oeffnet direkt das grafische Control Panel
REM  (tools/control_panel.py) im Windows-11-Look. Dort gibt es
REM  Buttons fuer:
REM    - Tests + Dashboard
REM    - Builds fuer Android / iOS / PC (Neubau je App)
REM    - Play-Store-Sync (init/validate/push/pull/diff/export)
REM    - Dokumentation oeffnen
REM
REM  Das Control Panel ist die alleinige grafische Oberflaeche;
REM  ein Konsolen-Menue gibt es bewusst nicht.
REM ============================================================

setlocal EnableExtensions
chcp 65001 >nul

pushd "%~dp0"

set "PYTHON_CMD="
set "PYTHON_VERSION="
set "PYTHONW_EXE="
set "START_LOG=logs\control-panel-startup.log"

if not exist "logs" mkdir "logs" >nul 2>nul

REM ------------------------------------------------------------
REM Python 3.10+ robust finden:
REM   1) Windows Python Launcher (py -3), falls vorhanden
REM   2) python im PATH
REM ------------------------------------------------------------
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [FEHLER] Python 3.10+ wurde nicht gefunden.
    echo.
    echo Installiere Python fuer Windows und aktiviere dabei:
    echo   [x] Add python.exe to PATH
    echo.
    echo Download: https://www.python.org/downloads/windows/
    echo.
    pause
    popd
    endlocal
    exit /b 1
)

for /f "delims=" %%V in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2^>nul') do set "PYTHON_VERSION=%%V"
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] Python 3.10+ ist erforderlich.
    echo         Gefunden: Python %PYTHON_VERSION%
    echo.
    echo Bitte aktualisieren: https://www.python.org/downloads/windows/
    echo.
    pause
    popd
    endlocal
    exit /b 1
)

echo Python: %PYTHON_VERSION%  ^(%PYTHON_CMD%^) 

REM pip pruefen
%PYTHON_CMD% -m pip --version >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] pip ist fuer diese Python-Installation nicht verfuegbar.
    echo         Reparaturversuch:
    echo           %PYTHON_CMD% -m ensurepip --upgrade
    echo           %PYTHON_CMD% -m pip install --upgrade pip
    echo.
    pause
    popd
    endlocal
    exit /b 1
)

REM Tkinter pruefen (wird von CustomTkinter benoetigt)
%PYTHON_CMD% -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] Tkinter konnte nicht importiert werden.
    echo         Installiere eine Python.org-Windows-Version mit Tcl/Tk.
    echo         Download: https://www.python.org/downloads/windows/
    echo.
    pause
    popd
    endlocal
    exit /b 1
)

REM customtkinter pruefen, ggf. installieren
%PYTHON_CMD% -c "import customtkinter" >nul 2>nul
if errorlevel 1 (
    echo customtkinter fehlt - wird installiert ...
    %PYTHON_CMD% -m pip install --upgrade customtkinter
    if errorlevel 1 (
        echo [FEHLER] customtkinter konnte nicht installiert werden.
        echo         Manuell versuchen:
        echo           %PYTHON_CMD% -m pip install --upgrade customtkinter
        pause
        popd
        endlocal
        exit /b 1
    )
)

REM Optionaler Hinweis: Release-/Play-Store-Checks brauchen Dev-Abhaengigkeiten.
%PYTHON_CMD% -c "import pytest, yaml" >nul 2>nul
if errorlevel 1 (
    echo [HINWEIS] Fuer alle Admin-Panel-Checks empfohlen:
    echo           %PYTHON_CMD% -m pip install -r requirements-dev.txt
    echo.
)

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

REM Preflight sichtbar mit Konsolen-Python ausfuehren. Wenn hier etwas
REM bricht, wuerde pythonw den Fehler sonst verstecken.
%PYTHON_CMD% -c "import tools.control_panel; print('Control Panel Import OK')" > "%START_LOG%" 2>&1
if errorlevel 1 (
    echo [FEHLER] Das Control Panel kann nicht geladen werden.
    echo         Log: %CD%\%START_LOG%
    echo.
    type "%START_LOG%"
    echo.
    pause
    popd
    endlocal
    exit /b 1
)

REM Control Panel starten - 'pythonw' versteckt das Konsolen-Fenster,
REM wenn vorhanden; Debug-Modus laesst es sichtbar in dieser Konsole laufen:
REM   set ZUNARODO_DEBUG_START=1
if "%ZUNARODO_DEBUG_START%"=="1" (
    echo Debug-Start: Control Panel laeuft sichtbar in dieser Konsole.
    %PYTHON_CMD% -m tools.control_panel
) else (
    for /f "delims=" %%P in ('%PYTHON_CMD% -c "from pathlib import Path; import sys; w=Path(sys.executable).with_name('pythonw.exe'); print(w if w.is_file() else '')" 2^>nul') do set "PYTHONW_EXE=%%P"
    if defined PYTHONW_EXE (
        start "" "%PYTHONW_EXE%" -m tools.control_panel
    ) else (
        %PYTHON_CMD% -m tools.control_panel
    )
)

popd
endlocal
exit /b 0
