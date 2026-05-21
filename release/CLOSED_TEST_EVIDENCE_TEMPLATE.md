# Closed-Test-Nachweis — VORLAGE (noch kein gültiger Nachweis)

> Diese Datei ist **nur eine Vorlage**. Ihr Dateiname entspricht **bewusst
> nicht** dem Muster `closed-test-*.md`, damit das Release-Gate sie **nicht**
> als echten Nachweis zählt. Erst nach einem tatsächlich durchgeführten
> Closed Test wird eine ausgefüllte Kopie unter
> `release/closed-test-JJJJ-MM.md` abgelegt — dann erkennt
> `tools.playstore_check.evaluate_closed_test_gate` den Nachweis und das
> Release-Gate kann auf **GO** springen.

## Warum dieser Nachweis Pflicht ist

Google verlangt für **neue Personal-Developer-Accounts** vor dem
Produktionszugang einen bestandenen **Closed Test** mit
**mindestens 12 Testern** über **mindestens 14 zusammenhängende Tage**
(Soll-Werte in `playstore.yml` → `tracks.closed.min_testers`/`min_days`).

## Auszufüllen nach dem Closed Test

- **Version (versionName / versionCode):** `0.9.0 / <code>`
- **Track:** Closed Testing (`zunarodo-closed-testers@googlegroups.com`)
- **Start–Ende:** `JJJJ-MM-TT` – `JJJJ-MM-TT` (≥ 14 Tage)
- **Aktive Tester (≥ 12):** `<Anzahl>`  — Opt-in-Nachweis: `<Link/Screenshot>`
- **Pre-Launch-Report:** keine Crashes / Sicherheitsbefunde → `<Link>`
- **Crash-free users:** `<%>` (Ziel ≥ 99,5 %)
- **Wesentliches Feedback / behobene Punkte:**
  - `<Stichpunkt>`
- **Play-Console-Beleg (Screenshot/Export):** `release/assets/closed-test-<datum>.png`
- **Freigabe durch Release-Owner:** `<Name>`, `JJJJ-MM-TT`

## Schritte zum gültigen Nachweis

1. Diese Datei kopieren nach `release/closed-test-JJJJ-MM.md`.
2. Alle Felder oben wahrheitsgemäß ausfüllen (keine Platzhalter mehr).
3. `python -m tools.playstore_check` zeigt dann unter `[closed_test]`
   „Closed-Test-Nachweis vorhanden: …".
4. Das Release-Gate (`evaluate_closed_test_gate`) liefert `ready = true`,
   sobald Konfiguration **und** Nachweis stimmen.
