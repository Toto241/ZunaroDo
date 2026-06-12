# Release Notes

Kanonische Ablage der nutzerorientierten Release-Notes pro Version und
Play-Store-Locale. Referenziert von
[docs/android/09_RELEASE_CHECKLIST.md](../../docs/android/09_RELEASE_CHECKLIST.md)
(Abschnitt D).

## Konvention

```
legal/release_notes/<versionName>/<play-locale>.txt
```

- `<versionName>` ist identisch zu `version` in `buildozer.spec` /
  `pyproject.toml` (SemVer, z. B. `1.0.0`).
- `<play-locale>` ist der Play-Console-Locale-Code (`de-DE`, `en-US`,
  `fr-FR`, `es-ES`, `it-IT`, `nl-NL`, `pl-PL`, `pt-PT`).
- Jede Datei ist reiner Text, **maximal 500 Zeichen** (Play-Store-Limit
  pro Locale), keine internen Tickets.

Abgedeckt sind die acht UI-Vollsprachen. Die Inhalte sind deckungsgleich
mit dem `production`-Track in [playstore.yml](../../playstore.yml); diese
Dateien sind die versionierte Quelle, aus der die Play-Console-Felder
befüllt werden.
