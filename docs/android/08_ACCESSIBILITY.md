# 08 - Accessibility & UX

## 1. Anspruch

Alltagshelfer ist eine **familienorientierte Produktivitäts-App**. Die
Zielgruppe schließt explizit ältere Nutzer und Menschen mit
eingeschränkter Sehkraft ein. Accessibility ist deshalb **funktional**,
nicht kosmetisch.

Verbindlich:

- **WCAG 2.2 Level AA** in allen App-Bereichen.
- **TalkBack-fähig** auf jedem Pflicht-Flow.
- **Touch-Targets** >= 48 dp.
- **Kontrastverhältnis** >= 4,5:1 für Text, >= 3:1 für UI-Komponenten.

## 2. Screenreader-Support (TalkBack)

### Native (Compose)

- `Modifier.semantics { contentDescription = "..." }` an Icons und
  Bildern.
- Klickbare Composables: `Modifier.clickable(role = Role.Button) { ... }`.
- Listen: `LazyColumn` propagiert Item-Reihenfolge korrekt - keine
  Custom-Reorder-Hacks.
- Live-Regions: `Modifier.liveRegion(LiveRegionMode.Polite)` für
  Statusmeldungen.
- Headings: `Modifier.heading()` an Screen-Titeln.

### KivyMD

- KivyMD-Widgets sind **nicht out-of-the-box** TalkBack-freundlich,
  weil Kivy auf Android via SDL2 läuft und keinen nativen
  AccessibilityService-Baum exposed.
- Workaround / Pflicht-Maßnahme:
  - `MDTopAppBar`/`MDLabel` Texte sind selbst lesbar (Text als
    Beschreibung).
  - Icons in Bottom-Nav: zusätzlich `text=`-Attribut setzen, damit
    Reader Text vorliest (bereits umgesetzt in
    [mobile/app.py:80-86](../../mobile/app.py#L80-L86)).
  - Custom-Widgets mit reiner Bedeutung über Icon **immer** mit
    `MDLabel`-Begleittext.
- Falls TalkBack-Kompatibilität als kritisch eingestuft wird ->
  Migration auf Compose erforderlich (Kivy-Limit).

## 3. Dynamische Schriftgrößen

### Native

- **Material 3 Type Scale** über `MaterialTheme.typography`.
- Niemals `fontSize` in Pixel; immer `sp`.
- `Text(..., maxLines = ..., overflow = TextOverflow.Ellipsis)` damit
  bei 200 % Schrift nichts brutal abschneidet.
- Tests bei `fontScale = 1.0`, `1.3`, `1.5`, `2.0`.

### KivyMD

- KivyMD-Theming: `theme_cls.font_styles` definiert Skalen. Nutzen
  statt eigener `font_size`-Werte.
- Layout-Container: `MDBoxLayout` / `MDGridLayout` mit `adaptive_height
  = True`, damit Wrapping greift.
- Manuelles Testen: `Settings -> Display -> Schriftgröße` -> XL ->
  alle Bottom-Nav-Tabs durchprüfen, kein Clipping erlaubt.

## 4. Kontrast

### Tokens

| Token | Light | Dark | Verhältnis Light |
| ----- | ----- | ---- | ---------------- |
| onPrimary on primary | `#FFFFFF` | `#0B1736` | 11.4:1 ✓ |
| onSurface on surface | `#1A1C1E` | `#E2E2E5` | 16.0:1 ✓ |
| outline on surface | `#73777F` | `#8D9199` | 4.7:1 ✓ |
| error on surface | `#BA1A1A` | `#FFB4AB` | 5.0:1 ✓ |

Pflicht-Workflow bei Theme-Änderung:

1. Tokens in `core-ui/Theme.kt` (Native) bzw. `mobile/theme.py` (Kivy)
   ändern.
2. Kontrast-Check mit `https://webaim.org/resources/contrastchecker/`
   oder `axe-android`.
3. Lint-Regel `ColorContrast` in Android Lint nicht unterdrücken.

## 5. Touch-Targets

- Mindestgröße 48 dp x 48 dp.
- Icon-Buttons: `IconButton` (Native) / `MDIconButton` (Kivy) liefert
  das von Haus aus.
- Listen-Items: mind. 56 dp Höhe (bereits in [MOBILE.md](../../MOBILE.md)
  als Konvention - beibehalten).
- Abstand zwischen Touch-Targets: >= 8 dp.

## 6. Navigations-UX

- **Konsistenz:** Bottom-Bar bleibt überall sichtbar; Modal-Dialoge
  haben eindeutigen Schließen-Button + Back-Geste.
- **Predictive Back (Android 14+):**
  - Native: `BackHandler { ... }` Composable.
  - Kivy: `on_key_down` mit Key 27 (Back); aktuell standardmäßig
    Screen-Pop. Verifizieren, dass Dialoge die Geste schlucken.
- **Empty-States:** jeder leere Bereich hat eine Erklärung +
  Call-to-Action ("Erste Ausgabe hinzufügen").
- **Loading-States:** Skeleton-Loader nach 200 ms, vorher Inhalt
  optimistisch zeigen.

## 7. Fehlermeldungen

- Nie nur "Fehler". Immer:
  1. Was ist passiert.
  2. Was kann der Nutzer tun.
- Pattern: `"Sync fehlgeschlagen. Bitte Internetverbindung prüfen und
  erneut versuchen."` + Retry-Button.
- Sprache: per Default Deutsch (App-Default), Englisch via Locale.

## 8. Internationalisierung

- Strings ausschließlich aus `locales/<lang>.json` (Kivy) bzw.
  `res/values-<lang>/strings.xml` (Native).
- Pluralregeln: `ICU MessageFormat` (Native).
- Datums-/Zahlenformat: lokale-aware (`java.time.format.DateTimeFormatter`
  Native; `babel` Python).
- Aktuelle Locales: `de`, `en`. Weitere nur, wenn übersetzt.

## 9. Automatische Accessibility-Prüfungen

| Tool | Sprache | Was es findet |
| ---- | ------- | -------------- |
| `axe-android` | Native | fehlende Content-Descriptions, kleine Targets, Kontrast |
| Android-Lint `AccessibilityFix` | Native | fehlende `contentDescription` an `ImageView`, `Button` ohne `text` |
| Compose-Test `printToLog` mit Semantics | Native | fehlende Semantics in Composables |
| Manueller TalkBack-Walkthrough | beide | Real-World-Bestätigung |
| KivyMD-Smoke | Kivy | UI-Snapshot mit großer Schrift |

Native Build-Pipeline (Gradle):

```bash
./gradlew lint                # blockt fatal accessibility issues
./gradlew connectedDebugAndroidTest   # läuft axe-android in instrumentierten Tests
```

## 10. Pre-Production-Accessibility-Smoke

5-Minuten-Smoke vor jedem Release:

- [ ] TalkBack an, App-Start, alle Bottom-Nav-Tabs antippen - Reader
  spricht jeden Tab-Namen.
- [ ] FAB-Button im Vertrags-Screen ist als "Hinzufügen" angesagt.
- [ ] Im Vertrags-Detail-Dialog sind Felder einzeln navigierbar.
- [ ] System-Schriftgröße XL: kein abgeschnittener Text in
  Dashboard-Kennzahlen.
- [ ] Dark-Mode: Kontraste wie oben.

## 11. Mensch-/Maschinen-Lesbarkeit

- Datum nie nur als Icon. Datum immer plus Text-Label
  ("Fällig am 12. Juni 2026" statt nur Icon).
- Geld-Beträge: Trennzeichen lokal-konform, Währungssymbol.
- Telefonnummern: Lesbar formatiert (z.B. via `libphonenumber`).

## 12. UX-Patterns für Familien-Use-Case

- **Mehrnutzer-Sichtbarkeit:** Wenn ein Eintrag von Familienmitglied X
  ist, dann farb- oder text-gekennzeichnet.
- **Bestätigung bei destruktiven Aktionen:** Löschen einer Ausgabe ->
  Snackbar mit Undo-Option für 6 s, danach erst Soft-Delete persistiert
  (Pattern bereits umsetzbar mit `MDSnackbar`).
- **Konflikte sichtbar machen:** Sync-Konflikte ("Anna hat denselben
  Eintrag bearbeitet") in einer dedizierten Inbox-Card.

## 13. Nicht-Ziele

- Kein Sprachsteuerung (Voice-Input) als Pflicht. Optional über
  System-Voice-Input.
- Keine eigenen Hilfetechnologien (kein eigener Screenreader-Mode).
- Kein "High-Contrast-Mode" zusätzlich zu System-Dark-Mode (System
  reicht).
