# Android-Port des Alltagshelfers

Diese Datei beschreibt, wie die Mobile-Version gebaut und entwickelt wird.

## Warum ein zweites Frontend?

Die Desktop-GUI basiert auf **Tkinter / CustomTkinter** - das laeuft nicht
auf Android. Statt das Frontend mit Hacks portabel zu machen, gibt es
eine **zweite UI-Schicht** in `mobile/`. Das ist sauber moeglich, weil:

- Alle Geschaeftslogik in `modules/`, `services/`, `core/`, `database.py`
  liegt - **GUI-frei**.
- Die Registry (`build_registry`) ist der einzige Einstiegspunkt fuer
  jede UI - Desktop wie Mobile.

Beide Frontends teilen also 100 % der Datenschicht und der Capabilities.

## Stack

- **KivyMD 1.2** auf **Kivy 2.3** - Material-Design-Widgets in Python.
- **Buildozer + python-for-android** fuer den APK-Build.
- Pakete: `kivy`, `kivymd`, `certifi`, `requests` (siehe
  [buildozer.spec](buildozer.spec)).

## UI-Adaption fuer Phones

Die Desktop-App hat 14 Tabs. Auf einem 6"-Display ist das nicht
benutzbar. Die Mobile-App reduziert auf eine **Bottom-Navigation mit 5
Bereichen**:

| Bottom-Tab     | Screen                                                       |
| -------------- | ------------------------------------------------------------ |
| Start          | Kennzahlen + naechste Fristen/Termine                        |
| Vertraege      | Vertragsliste, Detail-Dialog, Schnell-Anlegen via FAB        |
| Finanzen       | Ausgaben letzte 30 Tage, gruppiert nach Tag, FAB             |
| Termine        | Kommende Termine, Urgency-Farbcode                           |
| Mehr           | Familie, Kontakte, Notizen, Inbox, Suche                     |

Konkrete Phone-Patterns:

- **Floating-Action-Button** unten rechts auf jedem Listen-Screen.
- **MDDialog** mit `type="custom"` als Modal-Eingabe (touch-freundlich).
- **MDCard** fuer Listeneintraege - mindestens 56dp hoch (Tap-Target).
- **MDTopAppBar** mit Refresh-Aktion (manueller Pull-to-Refresh).
- Vertikale Listen statt mehrspaltiger Tabellen (kein horizontales
  Scrollen).
- Material-3-Theme (`material_style = "M3"`), Primaerfarbe Blau.

## Datenort auf Android

- DB landet im **App-Sandbox-Verzeichnis** (`MDApp.user_data_dir`).
  Standard ist `/data/data/de.alltagshelfer.alltagshelfer/files/`.
- Backups, Logs und `ausgaben/` ebenfalls im Sandbox-Pfad.
- Auf Android koennen **keine Foreign-File-Manager** in das Verzeichnis
  schauen - das ist Absicht (Datenschutz-Leitprinzip).

## Build (Schritt fuer Schritt)

Buildozer braucht Linux/macOS. Unter Windows: **WSL2 mit Ubuntu 22.04**.

```bash
# Einmalig:
sudo apt update
sudo apt install -y python3-pip openjdk-17-jdk \
    autoconf libtool pkg-config zlib1g-dev libncurses-dev \
    libtinfo5 cmake unzip libffi-dev libssl-dev

pip install --user buildozer cython==0.29.36

# Im Projektordner:
buildozer android debug

# Erzeugt: dist/alltagshelfer-0.9.0-arm64-v8a-debug.apk
```

Der erste Build laedt SDK/NDK (~1 GB). Folge-Builds dauern Minuten.

### Installieren auf dem Geraet

```bash
adb install dist/alltagshelfer-0.9.0-arm64-v8a-debug.apk
adb logcat | grep python   # Live-Log
```

## Entwicklung auf dem Desktop

Die Mobile-App laeuft als Desktop-Fenster - perfekt fuers Iterieren:

```pwsh
pip install kivy kivymd
python -m mobile.app
```

Das oeffnet ein **smartphonegrosses Fenster** mit derselben UI, die auf
Android landet.

## Tests

- **mobile/helpers.py** ist pure Logik (Formatierung, Aggregation) und
  hat **28 unittest-Tests** in `tests/test_mobile_helpers.py`.
- Die Screens selbst nutzen Kivy-Widgets und werden nicht headless
  getestet - sie sind aber so duenn, dass Logik nur in `helpers.py`
  landet.

## Was *nicht* in der Mobile-Version enthalten ist

- **CLI/IMAP/SMTP-Tabs**: zu nischig fuer den Phone-Alltag.
- **Drucken**: gibt es auf Android nicht im selben Sinne (PDF wird
  einfach geoeffnet, der Nutzer waehlt selbst die App).
- **Sync-Server hosten**: der Server laeuft auf einem Heimrechner /
  Container; das Phone ist nur Client.

## Weiterentwicklung

Ein neuer Screen ist immer ein File unter `mobile/screens/`:

1. Klasse `Foo(MDScreen)` mit Methoden `_build()` und `_refresh()`.
2. Auf gemeinsame Logik aus `mobile/helpers.py` setzen.
3. In `mobile/app.py::_RootShell` als Bottom-Nav-Eintrag registrieren
   (oder als Sub-Screen in `MoreScreen`).
4. Tests fuer neue Helper-Funktionen ergaenzen.

Kein Direktzugriff auf Repositories - alles geht durch
`registry.dispatch(...)`. So bleibt das Mobile-Frontend mit dem Desktop
synchron, sobald eine neue Capability dazukommt.

## Presenter-/Headless-Schicht (vollautomatisch testbar)

Das **Verhalten** der Screens (welche Capability mit welchen Args, wie das
Ergebnis zu Anzeige-Daten inkl. Leer-/Fehlerzuständen wird) liegt in
`mobile/presenters.py`. Die Kivy-Screens sind nur noch dünne Adapter, die
einen Presenter aufrufen und dessen Modell rendern - es gibt also **keine**
doppelte Logik.

`mobile/headless_app.py` (`HeadlessApp`) ist eine UI-freie Variante der App
über dieselbe Registry. Damit lässt sich das komplette UI-Verhalten **ohne
Display, Kivy oder Emulator** testen (`tests/test_presenters.py`,
`tests/test_headless_app.py`). Neue Screen-Logik gehört in einen Presenter
(+ Test); der Screen bleibt reines Rendering.
