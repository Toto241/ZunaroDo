@echo off
REM ============================================================
REM  Android-Build unter Windows via WSL2 (Ubuntu)
REM
REM  Buildozer laeuft nur unter Linux/macOS. Auf Windows
REM  starten wir den Build deshalb in einer WSL2-Distribution
REM  (Default-Distribution). Voraussetzung: WSL2 + Ubuntu 22.04
REM  installiert ^(siehe MOBILE.md^).
REM ============================================================

setlocal EnableExtensions
chcp 65001 >nul

pushd "%~dp0\.."

echo.
echo === ZunaroDo  -  Android-Build via WSL2 ===
echo.

REM 1) WSL vorhanden?
where wsl >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] 'wsl' nicht gefunden.
    echo.
    echo Buildozer braucht Linux. Installiere WSL2 + Ubuntu 22.04:
    echo   1. PowerShell als Admin oeffnen
    echo   2. wsl --install -d Ubuntu-22.04
    echo   3. Distribution einmalig starten ^(User anlegen^)
    echo.
    pause
    popd
    exit /b 1
)

REM 2) Build in WSL anstossen. CWD bleibt das Repo (Windows-Pfad).
echo Starte Buildozer in WSL2 ...
echo ^(Erster Lauf laedt ca. 1 GB SDK/NDK herunter^)
echo.

wsl bash -lc "cd \"$(wslpath '%CD%')\" && (command -v buildozer >/dev/null 2>&1 || pip install --user buildozer cython==0.29.36) && buildozer android debug"

if errorlevel 1 (
    echo.
    echo [FEHLER] Buildozer hat fehlgeschlagen. Siehe Logs oben oder
    echo         .buildozer/android/platform/build-*.log
    pause
    popd
    exit /b 1
)

echo.
echo === Build fertig ===
if exist "bin" (
    dir /b "bin\*.apk" "bin\*.aab" 2>nul
)
if exist "dist" (
    dir /b "dist\*.apk" "dist\*.aab" 2>nul
)
echo.
pause
popd
endlocal
exit /b 0
