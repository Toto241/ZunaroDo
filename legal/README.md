# Legal-Templates

**Hinweis:** Diese Vorlagen sind **kein Ersatz fuer Rechtsberatung.**
Sie sind generische Geruestdokumente mit eckigen Platzhaltern
`[ANBIETER]`, `[ADRESSE]` usw., die vor der ersten Veroeffentlichung
zwingend von einer Anwaltskanzlei mit Schwerpunkt IT-/E-Commerce-Recht
geprueft und an den konkreten Vertrieb (Direkt, Stripe/Paddle, App-Store)
angepasst werden muessen.

## Welches Dokument wofuer

| Datei | Pflicht? | Wofuer |
| --- | --- | --- |
| `IMPRESSUM.md` | ja (DE: DDG §5) | Wer betreibt die App |
| `DATENSCHUTZ.md` | ja (DSGVO Art. 13) | Was wird mit Nutzerdaten gemacht |
| `AGB.md` | empfohlen | Vertragsbedingungen, Haftung, Kuendigung |
| `WIDERRUF.md` | ja bei Verkauf an Verbraucher | 14-tägiges Widerrufsrecht (BGB §312g) |

## Workflow

1. Platzhalter durch konkrete Daten ersetzen (Firmenname, Adresse, USt.-IdNr.)
2. Rechtskanzlei zur Pruefung geben (~ 200 - 600 EUR fuer alle 4 Doks)
3. Im Repo finalisieren, im Settings-Tab der App verlinken
4. Vor erster Pro-Aktivierung: Widerrufsverzicht abfragen (siehe
   [services/license_gate.py](../services/license_gate.py) und
   `gui.py:_show_pro_activation_dialog`)

## Mehrsprachige Rechtstexte

Rechtstexte sind **rechtsverbindlich** und werden bewusst **nicht**
maschinell uebersetzt - jede Sprachfassung muss von einer Anwaltskanzlei
des jeweiligen Rechtsraums geprueft werden. Die App liefert technisch
aber bereits eine lokalisierte Aufloesung mit Deutsch-Fallback:

- Verbindliche deutsche Fassung: `legal/<DOK>.md` (z.B. `DATENSCHUTZ.md`)
- Gepruefte Uebersetzung: `legal/<lang>/<DOK>.md` (z.B. `legal/fr/DATENSCHUTZ.md`)

Der Loader [services/legal.py](../services/legal.py) waehlt automatisch
die beste verfuegbare Fassung und faellt sonst auf Deutsch zurueck:

```python
from services.legal import resolve_legal
text, effektive_sprache = resolve_legal("DATENSCHUTZ", "fr")
```

Den aktuellen Uebersetzungsstand zeigt:

```text
python -m tools.legal_status
```

Solange keine geprueften Uebersetzungen vorliegen, sieht der Nutzer die
deutsche Fassung - das ist juristisch sauberer als eine ungepruefte
Maschinenuebersetzung.

## Verkauf ueber Drittanbieter (empfohlen)

Wenn du **Paddle** oder **Lemon Squeezy** als Merchant of Record nutzt,
uebernimmt der Drittanbieter:

- EU-Umsatzsteuer (OSS-Verfahren)
- Rechnungen
- Refund-Abwicklung
- 14-Tage-Widerrufsfrist

Dein Impressum bleibt erforderlich, AGB werden teilweise durch
Paddle's eigene Endkunden-AGB ergaenzt. Datenschutz bleibt komplett
deine Verantwortung, weil die App die Daten verarbeitet.
