# Legal-Dokumente (ZunaroDo)

Die verbindlichen deutschen Texte liegen in diesem Ordner. Stammdaten
(Anbieter, E-Mail, URLs) werden zentral in [provider.yml](provider.yml)
gepflegt und in Impressum/AGB/Widerruf eingearbeitet.

## Dateien

| Datei | Zweck |
| --- | --- |
| `IMPRESSUM.md` / `IMPRESSUM_en.md` | TMG / Anbieterkennzeichnung |
| `DATENSCHUTZ.md` | DSGVO Art. 13 |
| `AGB.md` / `AGB_en.md` | Nutzungsbedingungen |
| `WIDERRUF.md` | Widerrufsbelehrung (BGB §312g) |
| `provider.yml` | Zentrale Kontakt- und URL-Daten |

## Veroeffentlichungs-Check

```bash
python -m tools.privacy_policy --check
python -m tools.privacy_policy --build --out site/privacy/index.html
```

Die öffentliche Privacy-URL muss mit `provider.yml` → `privacy_url` und
[playstore.yml](../playstore.yml) übereinstimmen.

## Hinweis

Die Texte sind fuer ein Open-Source-Projekt ohne eingetragenen Kaufmann
formuliert. **Vor kommerziellem Vertrieb** (bezahltes Pro-Abo, Play Store)
empfehlen wir eine anwaltliche Pruefung — insbesondere bei Aenderungen an
Preisen, MoR-Vertraegen (Paddle/Lemon) oder internationalen Stores.
