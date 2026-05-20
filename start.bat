@echo off
REM ============================================================
REM  Zunarodo - QA-/Release-/Compliance-Cockpit
REM
REM  Doppelklick startet den interaktiven Modus. Optional ueber
REM  Kommandozeile:
REM
REM      start.bat                  ->  Menue
REM      start.bat open             ->  bestehende index.html oeffnen
REM      start.bat refresh          ->  Dashboard neu rendern (schnell)
REM      start.bat full             ->  gesamte Test-Suite + Dashboard
REM      start.bat playstore        ->  Play-Store-Sync-Untermenue
REM ============================================================

setlocal EnableExtensions

REM UTF-8 fuer Konsole, damit Umlaute richtig aussehen
chcp 65001 >nul

REM In den Projektordner wechseln, egal von wo aufgerufen
pushd "%~dp0"

echo.
echo ============================================================
echo  Zunarodo  -  QA / Release / Compliance  -  Cockpit
echo ============================================================
echo.

REM ---------- Python pruefen ----------
where python >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] Python ist nicht im PATH zu finden.
    echo         Installiere Python 3.10+ ^(https://www.python.org/^) und
    echo         stelle sicher, dass "python" in der Konsole funktioniert.
    echo.
    pause
    popd
    exit /b 1
)

REM ---------- Kommandozeilen-Argument auswerten ----------
set "mode=%~1"
if /I "%mode%"=="open"      goto OPEN
if /I "%mode%"=="refresh"   goto REFRESH
if /I "%mode%"=="full"      goto FULL
if /I "%mode%"=="playstore" goto PLAYSTORE_MENU
if /I "%mode%"=="build"     goto BUILD_MENU

REM Kein Argument -> interaktiver Modus (Doppelklick)
set "interactive=1"

REM ---------- Interaktives Menue ----------
echo Was moechtest du tun?
echo.
echo   [1] Schnell    -  nur Dashboard / index.html neu rendern   ^(^< 5 s^)
echo   [2] Voll       -  komplette Test-Suite + Dashboard          ^(~ 3 min^)
echo   [3] Direkt     -  bestehendes Cockpit oeffnen, nichts neu   ^(0 s^)
echo   [4] Play-Store -  YAML init/validate/push/pull/diff/export  ^(Untermenue^)
echo   [5] Build      -  App fuer Android / iOS / PC bauen         ^(Untermenue^)
echo   [Q] Beenden
echo.
set "choice="
set /p choice=Auswahl [1/2/3/4/5/Q, Enter = 1]:
if not defined choice set "choice=1"
if /I "%choice%"=="1" goto REFRESH
if /I "%choice%"=="2" goto FULL
if /I "%choice%"=="3" goto OPEN
if /I "%choice%"=="4" goto PLAYSTORE_MENU
if /I "%choice%"=="5" goto BUILD_MENU
if /I "%choice%"=="q" goto END
goto REFRESH

REM ============================================================
REM  Mode: REFRESH  -  Dashboard ohne Test-Lauf neu generieren
REM ============================================================
:REFRESH
echo.
echo --- Dashboard und Doku-HTMLs werden gerendert ---
if not exist "tests\concept\reports\protocol.json" (
    echo.
    echo [HINWEIS] Es gibt noch kein protocol.json. Ich starte
    echo           automatisch den vollen Lauf.
    echo.
    goto FULL
)
python -m tools.dashboard
if errorlevel 1 (
    echo.
    echo [FEHLER] Dashboard-Generator hat fehlgeschlagen.
    pause
    popd
    exit /b 1
)
goto OPEN

REM ============================================================
REM  Mode: FULL  -  Test-Suite + Protokoll + Dashboard
REM ============================================================
:FULL
echo.
echo --- [1/2] Test-Suite laeuft  ^(~ 2-3 min^) ---
python -m tools.test_protocol --all
set "gate_rc=%errorlevel%"

echo.
echo --- [2/2] Dashboard, Doku-HTMLs und index.html rendern ---
python -m tools.dashboard
if errorlevel 1 (
    echo.
    echo [FEHLER] Dashboard-Generator hat fehlgeschlagen.
    pause
    popd
    exit /b 1
)

if not "%gate_rc%"=="0" (
    echo.
    echo --------------------------------------------------------
    echo  HINWEIS: Test-Protokoll endete mit Status NO-GO oder
    echo  Fehler. Das Dashboard wird trotzdem geoeffnet, damit
    echo  du sehen kannst, was blockiert.
    echo --------------------------------------------------------
    echo.
)
goto OPEN

REM ============================================================
REM  Mode: PLAYSTORE_MENU  -  Untermenue fuer playstore_sync.py
REM ============================================================
:PLAYSTORE_MENU
echo.
echo --- Play-Store-Sync-Untermenue ---
echo.
echo Konfiguration: playstore.yml im Projekt-Root
echo Doku:          PLAYSTORE.md ^(Teil 1-8^)
echo.
echo   [1] init      -  Beispiel-YAML aus dem Repo erzeugen ^(--force^)
echo   [2] validate  -  YAML gegen Soll-Schema pruefen
echo   [3] push-dry  -  Aenderungen anzeigen, ohne zu schreiben
echo   [4] push      -  YAML in die Play Console schreiben
echo   [5] pull      -  Stand aus Play Console in die YAML uebernehmen
echo   [6] diff      -  Unterschiede YAML ^<^=^=^=^=^=^> Play Console
echo   [7] export    -  Markdown-Snapshot in release/ schreiben
echo   [Q] Zurueck zum Hauptmenue
echo.
set "psaction="
set /p psaction=Auswahl [1-7/Q]:
if /I "%psaction%"=="1" (
    python -m tools.playstore_sync init --force
) else if /I "%psaction%"=="2" (
    python -m tools.playstore_sync validate
) else if /I "%psaction%"=="3" (
    python -m tools.playstore_sync push --dry-run
) else if /I "%psaction%"=="4" (
    python -m tools.playstore_sync push
) else if /I "%psaction%"=="5" (
    python -m tools.playstore_sync pull --merge
) else if /I "%psaction%"=="6" (
    python -m tools.playstore_sync diff
) else if /I "%psaction%"=="7" (
    python -m tools.playstore_sync export
) else if /I "%psaction%"=="q" (
    goto END
)
echo.
echo --- Aktion abgeschlossen ---
echo.
if defined interactive (
    echo Druecke eine Taste, um das Fenster zu schliessen.
    pause >nul
)
goto END

REM ============================================================
REM  Mode: BUILD_MENU  -  Untermenue fuer Android / iOS / PC
REM ============================================================
:BUILD_MENU
echo.
echo --- Build-Untermenue ---
echo.
echo Build-Status anzeigen oder Build starten:
echo.
echo   [1] Status    -  Build-Voraussetzungen + letzte Artefakte
echo   [2] PC        -  Desktop-Build via PyInstaller starten
echo   [3] Android   -  Android-Build via Buildozer ^(braucht WSL2^)
echo   [4] iOS       -  iOS-Build-Anleitung ^(nur Lesen, braucht macOS^)
echo   [5] Dashboard -  Cockpit oeffnen, Build-Center inkl. Copy-Befehlen
echo   [Q] Zurueck
echo.
set "bchoice="
set /p bchoice=Auswahl [1-5/Q]:
if /I "%bchoice%"=="1" (
    python -m tools.build_status --no-emoji
) else if /I "%bchoice%"=="2" (
    if exist "scripts\build-desktop.bat" (
        call "scripts\build-desktop.bat"
    ) else (
        echo [FEHLER] scripts\build-desktop.bat fehlt.
    )
) else if /I "%bchoice%"=="3" (
    if exist "scripts\build-android.bat" (
        call "scripts\build-android.bat"
    ) else (
        echo [FEHLER] scripts\build-android.bat fehlt.
    )
) else if /I "%bchoice%"=="4" (
    echo.
    echo iOS-Builds erfordern macOS + Xcode. Auf Windows nicht moeglich.
    echo.
    echo Doku: scripts\build-ios.sh
    if exist "scripts\build-ios.sh" (
        echo Skript-Inhalt:
        type "scripts\build-ios.sh"
    )
) else if /I "%bchoice%"=="5" (
    goto OPEN
) else if /I "%bchoice%"=="q" (
    goto END
)
echo.
echo --- Aktion abgeschlossen ---
echo.
if defined interactive (
    echo Druecke eine Taste, um das Fenster zu schliessen.
    pause >nul
)
goto END

REM ============================================================
REM  Mode: OPEN  -  index.html im Standardbrowser oeffnen
REM ============================================================
:OPEN
if not exist "index.html" (
    echo.
    echo [FEHLER] index.html nicht gefunden.
    echo         Bitte erst Option [1] oder [2] ausfuehren.
    echo.
    pause
    popd
    exit /b 1
)
echo.
echo --- Browser wird geoeffnet ---
echo Datei: %~dp0index.html
start "Zunarodo Cockpit" "" "%~dp0index.html"

echo.
echo Fertig.

REM Bei Doppelklick ist 'interactive' gesetzt -> pause, damit das
REM Fenster nicht direkt zuklappt. Bei Aufruf mit Argument (z.B.
REM aus CI oder einer anderen Shell) wird einfach beendet.
if defined interactive (
    echo.
    echo Druecke eine Taste, um das Fenster zu schliessen.
    pause >nul
)
goto END

:END
popd
endlocal
exit /b 0
