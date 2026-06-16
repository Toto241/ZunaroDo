# Closed Testing — Runbook

Stand: 2026-06-16. Anleitung fuer den **Pflicht-Closed-Test** vor dem
Produktionszugang (neue Personal-Developer-Accounts: ≥12 Tester, ≥14 Tage).

Repo-Vorbereitung ist abgeschlossen:
- `playstore.yml` → `tracks.closed` (min_testers/min_days)
- Nachweis-Vorlage: [`CLOSED_TEST_EVIDENCE_TEMPLATE.md`](CLOSED_TEST_EVIDENCE_TEMPLATE.md)
- Vorbereiteter Nachweis: [`closed-test-2026-05-30.md`](closed-test-2026-05-30.md)
- Beleg-Ablage: [`assets/README.md`](assets/README.md)

---

## Phase 1 — Voraussetzungen

1. Signed AAB aus CI (Workflow **Android Release (AAB)**) oder lokalem Build.
2. Keystore-Secrets gesetzt (siehe [`PLAY_CONSOLE_SETUP.md`](PLAY_CONSOLE_SETUP.md)).
3. Pre-Submit gruen:

   ```bash
   python -m tools.playstore_check --strict
   python -m tools.gen_assets --check
   ```

---

## Phase 2 — Internal Testing

1. Play Console → **Testing → Internal testing** → AAB hochladen.
2. **Pre-launch report** pruefen (Crashes, Sicherheit, Policy).
3. Optional: Robo-Test in Console starten (ergaenzt CI-Monkey-Lauf).

---

## Phase 3 — Closed Testing (Pflicht)

1. **Testing → Closed testing** → Track `zunarodo-closed-testers@googlegroups.com`
   (siehe `playstore.yml`).
2. AAB vom Internal- oder frischen Build promoten/hochladen.
3. **≥12 Tester** einladen:
   - Google Group `zunarodo-closed-testers@googlegroups.com` pflegen, oder
   - E-Mail-Einladungen an Einzeltester.
4. **≥14 aufeinanderfolgende Tage** Test laeuft (Google zaehlt Opt-in-Tage).
5. Crash-/ANR-Rate beobachten (Ziel ≥99,5 % crash-free, siehe `playstore.yml` → `monitoring`).

---

## Phase 4 — Nachweis dokumentieren

1. Vorlage kopieren oder [`closed-test-2026-05-30.md`](closed-test-2026-05-30.md) mit **echten** Console-Daten aktualisieren:
   - Start-/Enddatum
   - Tester-Anzahl (≥12)
   - Crash-free-Rate
   - Pre-Launch-Report-Link
2. Screenshot aus Play Console (Tester-/Zeitraum-Ansicht) ablegen als
   `release/assets/closed-test-YYYY-MM-DD.png`.
3. Gate pruefen:

   ```bash
   python -m tools.playstore_check
   # [closed_test] muss "Nachweis vorhanden" zeigen
   ```

   Programmatisch:

   ```python
   from pathlib import Path
   from tools.playstore_check import evaluate_closed_test_gate, _load_playstore_yml
   gate = evaluate_closed_test_gate(_load_playstore_yml(), Path("release"))
   assert gate["ready"]  # config_ok + evidence_present
   ```

---

## Phase 5 — Produktionszugang

1. Console: **Release → Production** → **Apply for production access** (falls noetig).
2. Closed-Test-Nachweis anhaengen.
3. Gestaffelten Rollout planen (`playstore.yml` → `monitoring.staged_rollout`).
4. Finaler Check aus [`GO_LIVE_TODO.md`](GO_LIVE_TODO.md) §3.

---

## Troubleshooting

| Problem | Massnahme |
|---------|-----------|
| `playstore_check` FAIL closed-Track | `playstore.yml` → `tracks.closed.min_testers` / `min_days` pruefen |
| Kein Nachweis erkannt | Datei muss `release/closed-test-*.md` heissen (nicht `CLOSED_TEST_EVIDENCE_TEMPLATE.md`) |
| Zu wenige Tester-Tage | Test verlaengern; Google zaehlt nur aktive Opt-in-Tester |
| Crash-Rate zu hoch | CI Robo-Workflow + Logcat; Fixes vor Production |

---

## Referenzen

- [`GO_LIVE_TODO.md`](GO_LIVE_TODO.md) §1.6
- [`PLAY_CONSOLE_SETUP.md`](PLAY_CONSOLE_SETUP.md)
- [Google: Test tracks](https://support.google.com/googleplay/android-developer/answer/9845334)
