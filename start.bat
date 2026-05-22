@echo off
REM ============================================================
REM  Zunarodo - Start / Build-Menue
REM
REM  Doppelklick zeigt ein Menue mit:
REM    [1] Control Panel oeffnen (GUI - Tests, Builds, Play-Store)
REM    [2] PC / Desktop neu bauen     (PyInstaller)
REM    [3] Android neu bauen          (WSL2 + Buildozer)
REM    [4] iOS bauen                  (Info - nur macOS)
REM    [5] Build-Status anzeigen
REM    [0] Beenden
REM
REM  Die Builds rufen direkt die Skripte in scripts\ auf, sodass
REM  ein Neubau der einzelnen Apps ohne Umweg ueber die GUI moeglich
REM  ist.
REM ============================================================

setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

pushd "%~dp0"

REM --- Python pruefen -----------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] Python ist nicht im PATH gefunden.
    echo         Installiere Python 3.10+ und stelle sicher,
    echo         dass "python" in der Konsole funktioniert.
    echo.
    pause
    popd
    endlocal
    exit /b 1
)

:menu
cls
echo ============================================================
echo   Zunarodo  -  Start / Build
echo ============================================================
echo.
echo   [1]  Control Panel oeffnen   (GUI: Tests, Builds, Play-Store)
echo.
echo   --- Apps neu bauen ---
echo   [2]  PC / Desktop            (PyInstaller  -^> dist\Alltagshelfer\)
echo   [3]  Android                 (WSL2 + Buildozer  -^> bin\*.apk)
echo   [4]  iOS                      (Info  -  nur auf macOS moeglich)
echo.
echo   [5]  Build-Status anzeigen
echo   [0]  Beenden
echo.
set "choice="
set /p choice=Auswahl:

if "%choice%"=="1" goto panel
if "%choice%"=="2" goto build_pc
if "%choice%"=="3" goto build_android
if "%choice%"=="4" goto build_ios
if "%choice%"=="5" goto build_status
if "%choice%"=="0" goto end
echo.
echo Ungueltige Auswahl: "%choice%"
timeout /t 2 >nul
goto menu

REM ============================================================
:panel
REM customtkinter pruefen, ggf. installieren
python -c "import customtkinter" >nul 2>nul
if errorlevel 1 (
    echo customtkinter fehlt - wird installiert ...
    python -m pip install --upgrade customtkinter
    if errorlevel 1 (
        echo [FEHLER] customtkinter konnte nicht installiert werden.
        pause
        goto menu
    )
)
REM 'pythonw' versteckt das Konsolen-Fenster, wenn vorhanden.
where pythonw >nul 2>nul
if errorlevel 1 (
    python -m tools.control_panel
) else (
    start "" pythonw -m tools.control_panel
)
goto menu

REM ============================================================
:build_pc
echo.
echo === PC / Desktop neu bauen ===
call "%~dp0scripts\build-desktop.bat"
echo.
pause
goto menu

REM ============================================================
:build_android
echo.
echo === Android neu bauen ===
call "%~dp0scripts\build-android.bat"
echo.
pause
goto menu

REM ============================================================
:build_ios
cls
echo ============================================================
echo   iOS-Build
echo ============================================================
echo.
echo   Ein iOS-Build ist nur auf macOS moeglich (Xcode + kivy-ios).
echo   Auf diesem Windows-System kann iOS nicht lokal gebaut werden.
echo.
echo   Wege zum iOS-Build:
echo     - Auf einem Mac:  scripts\build-ios.sh
echo     - In der Cloud:   GitHub Actions / CI
echo.
echo   Details siehe:  MOBILE.md
echo.
pause
goto menu

REM ============================================================
:build_status
echo.
echo === Build-Status ===
python -m tools.build_status --no-emoji
echo.
pause
goto menu

REM ============================================================
:end
popd
endlocal
exit /b 0
