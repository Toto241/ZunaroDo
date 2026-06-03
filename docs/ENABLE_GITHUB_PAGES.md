# GitHub Pages für Datenschutz-URL (einmalig)

Die Privacy-URL in `playstore.yml` zeigt auf:

`https://toto241.github.io/ZunaroDo/privacy/`

Diese URL ist erst erreichbar, wenn GitHub Pages aktiviert ist.

## Automatisch (PowerShell, empfohlen)

Voraussetzungen: [GitHub CLI](https://cli.github.com/) (`gh auth login`), Python im Repo.

```powershell
cd D:\Tools\ZunaroDo
.\scripts\setup-github-pages.ps1
```

Das Skript:

1. Aktiviert Pages per API (`build_type: workflow`)
2. Setzt `PRIVACY_POLICY_URL`
3. Baut `site/privacy/index.html` lokal
4. Startet **Privacy-Policy Pages** und wartet auf Erfolg
5. Prüft die Privacy-URL per HTTP HEAD

**Legal-Platzhalter** werden nicht automatisch ausgefüllt — optional mit eigener JSON:

```powershell
Copy-Item config\legal-publisher.example.json config\legal-publisher.json
# legal-publisher.json ausfuellen, dann:
.\scripts\setup-github-pages.ps1 -LegalConfigJson config\legal-publisher.json
```

## Manuell (Repo Settings)

1. https://github.com/Toto241/ZunaroDo/settings/pages
2. **Build and deployment** → Source: **GitHub Actions**
3. Actions → Workflow **Privacy-Policy Pages** → **Run workflow**
4. Nach grünem Deploy: HEAD-Request auf die Privacy-URL (HTTP 200)

Die Variable `PRIVACY_POLICY_URL` kann auch per `gh variable set` gesetzt werden.

## Alternative ohne Actions

Source: **Deploy from a branch** → Branch `main`, Folder `/site`
