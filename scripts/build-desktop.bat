@echo off
REM ============================================================
REM  Desktop-Build (Windows) - PyInstaller
REM
REM  Erzeugt ein Single-Folder-Bundle unter dist/Alltagshelfer/.
REM ============================================================

setlocal EnableExtensions
chcp 65001 >nul

pushd "%~dp0\.."

echo.
echo === Alltagshelfer  -  PC-Build (PyInstaller) ===
echo.

REM 1) Python vorhanden?
where python >nul 2>nul || (
    echo [FEHLER] Python nicht im PATH gefunden.
    pause
    popd
    exit /b 1
)

REM 2) PyInstaller vorhanden? Sonst installieren.
python -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo PyInstaller fehlt - wird installiert ...
    python -m pip install --upgrade pyinstaller || (
        echo [FEHLER] PyInstaller-Installation fehlgeschlagen.
        pause
        popd
        exit /b 1
    )
)

REM 3) Build aus der Spec-Datei
echo.
echo --- Build laeuft ^(kann 1-3 min dauern^) ---
python -m PyInstaller --noconfirm alltagshelfer.spec
if errorlevel 1 (
    echo.
    echo [FEHLER] Build fehlgeschlagen. Logs siehe oben.
    pause
    popd
    exit /b 1
)

REM 4) Ergebnis anzeigen
echo.
echo === Build fertig ===
if exist "dist\Alltagshelfer\Alltagshelfer.exe" (
    echo Bundle: dist\Alltagshelfer\
    dir /b "dist\Alltagshelfer\Alltagshelfer.exe"
    echo.
    echo Im Datei-Manager oeffnen? ^(J/n^)
    set "openit="
    set /p openit=
    if /I not "%openit%"=="n" (
        explorer "dist\Alltagshelfer"
    )
) else (
    echo [WARN] Erwartete Ausgabe nicht gefunden: dist\Alltagshelfer\Alltagshelfer.exe
)

echo.
pause
popd
endlocal
exit /b 0
