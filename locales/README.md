# Locales / Übersetzungen

Jede Datei `<code>.json` ist ein flacher Key-Value-Speicher für eine
Sprache. `code` ist der ISO-639-1-Code (z. B. `fr`, `pt`). Die
Default-Sprache ist **`de`** und enthält den vollständigen Satz aller
Keys.

## Funktionsweise

Der Lookup in [services/i18n.py](../services/i18n.py) sucht in dieser
Reihenfolge:

1. gewählte Sprache (`<code>.json`)
2. Default-Sprache (`de.json`)
3. der Key selbst (damit ein vergessener Eintrag sichtbar bleibt)

Dadurch muss eine Sprache **nicht** alle Keys liefern — fehlende fallen
automatisch auf Deutsch zurück. Eine Teilübersetzung ist also gültig.

## Abdeckungsstand

Unterstützt werden die **24 EU-Amtssprachen**. Vollständig übersetzt
sind `de`, `en`, `fr`, `es`, `it`, `nl`, `pl`, `pt`. Die übrigen 16
Sprachen decken aktuell nur den `CORE_KEYS`-Satz ab (Navigation +
universelle Buttons + Settings-Einstieg) und fallen sonst auf Deutsch
zurück. Aktuelle Zahlen:

```
python -m tools.i18n_sync --coverage
```

## Sprachwahl zur Laufzeit

Der Setting-Schlüssel `i18n.language` steuert die Sprache. Neben einem
konkreten Code ist der Sonderwert `auto` erlaubt — dann wird die
Gerätesprache erkannt (`detect_device_language()`). In der Mobile-App
wählt man die Sprache im **„Mehr"-Screen**.

## Neue Übersetzung beitragen

1. Datei `locales/<code>.json` anlegen bzw. ergänzen (UTF-8).
2. Die `CORE_KEYS` sind **Pflicht** (sonst schlägt `--check` fehl).
3. **Platzhalter unverändert lassen**: `{count}`, `{amount:.2f}`,
   `{days}`, `{name}` usw. müssen exakt wie in `de.json` vorkommen.
4. Keine Keys erfinden, die `de.json` nicht kennt — das wird abgelehnt.
5. Prüfen:

```
python -m tools.i18n_sync --check
```

Die Prüfung läuft auch in der CI
([.github/workflows/android-compliance.yml](../.github/workflows/android-compliance.yml)).
