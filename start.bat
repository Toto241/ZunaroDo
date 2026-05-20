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
if /I "%mode%"=="open"    goto OPEN
if /I "%mode%"=="refresh" goto REFRESH
if /I "%mode%"=="full"    goto FULL

REM Kein Argument -> interaktiver Modus (Doppelklick)
set "interactive=1"

REM ---------- Interaktives Menue ----------
echo Was moechtest du tun?
echo.
echo   [1] Schnell  -  nur Dashboard / index.html neu rendern  ^(^< 5 s^)
echo   [2] Voll     -  komplette Test-Suite + Dashboard         ^(~ 3 min^)
echo   [3] Direkt   -  bestehendes Cockpit oeffnen, nichts neu  ^(0 s^)
echo   [Q] Beenden
echo.
set "choice="
set /p choice=Auswahl [1/2/3/Q, Enter = 1]:
if not defined choice set "choice=1"
if /I "%choice%"=="1" goto REFRESH
if /I "%choice%"=="2" goto FULL
if /I "%choice%"=="3" goto OPEN
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
