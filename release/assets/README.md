# Release-Belege (Screenshots, Exporte)

Dieser Ordner ist **absichtlich nicht versioniert** mit Binärdateien
(`.gitignore`). Vor einem Production-Upload legt der Release-Owner hier
lokal (oder als CI-Artefakt) die Play-Console-Belege ab.

## Closed Test (Pflicht vor Production)

| Datei | Inhalt |
| ----- | ------ |
| `closed-test-YYYY-MM-DD.png` | Screenshot aus der Play Console: Closed-Testing-Track, Tester-Anzahl, Zeitraum |

In der Nachweis-Datei `release/closed-test-YYYY-MM-DD.md` muss derselbe
Dateiname unter **Play-Console-Beleg** stehen, z. B.:

```text
release/assets/closed-test-2026-05-30.png
```

Prüfung im Repo (ohne Bilddatei):

```bash
PYTHONPATH=. python3 -m tools.playstore_check --strict
```

Der Check `[closed_test]` verlangt eine Markdown-Nachweisdatei
(`release/closed-test-*.md`), nicht das PNG — das PNG ist für Audits
und das Release-Team.

## Weitere Belege (optional)

- Pre-Launch-Report (PDF/PNG)
- Data-Safety-Bestätigung
- Staged-Rollout-Vitals nach Tag 1
