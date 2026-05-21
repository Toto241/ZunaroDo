# `site/` — öffentliche Statik (GitHub Pages)

Dieses Verzeichnis enthält die öffentlich hostbare Datenschutzerklärung,
die der Play Store als erreichbare URL verlangt.

- `index.html` — kleine Landing-Seite
- `privacy/index.html` — gerenderte Datenschutzerklärung
  (aus `legal/DATENSCHUTZ.md`, erzeugt mit
  `python -m tools.privacy_policy --build`)

## Neu erzeugen

```
python -m tools.privacy_policy --build
python -m tools.privacy_policy --check        # Veröffentlichungsreife
```

`--check` warnt, solange noch Vorlagen-Platzhalter (`[ANBIETER_NAME]` …)
offen sind oder `playstore.yml` eine `example.org`-URL trägt.

## Hosting per GitHub Pages

**Variante A – Branch-Deploy (ohne Workflow):**
Repo → *Settings → Pages → Build and deployment → Source: Deploy from a
branch* → Branch `main`, Ordner `/site`. Die Policy ist dann unter
`https://<user>.github.io/<repo>/privacy/` erreichbar.

**Variante B – Actions-Deploy:**
`.github/workflows/pages.yml` baut die Seite und deployed sie. Der
Workflow läuft nur manuell (*Actions → Pages → Run workflow*), damit er
auf Repos ohne aktivierte Pages nichts rot färbt. Vorher unter
*Settings → Pages → Source: GitHub Actions* einmalig aktivieren.

## Danach

Die gehostete URL in `playstore.yml → contact.privacy_policy_url` und als
GitHub-Variable `PRIVACY_POLICY_URL` eintragen — dann prüft der CI-Job
`privacy-policy-reachable` ihre Erreichbarkeit per HEAD-Request.
