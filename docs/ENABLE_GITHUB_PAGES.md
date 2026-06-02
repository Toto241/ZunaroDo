# GitHub Pages für Datenschutz-URL (einmalig)

Die Privacy-URL in `playstore.yml` zeigt auf:

`https://toto241.github.io/ZunaroDo/privacy/`

Diese URL ist erst erreichbar, wenn GitHub Pages aktiviert ist.

## Einrichtung (Repo Settings)

1. https://github.com/Toto241/ZunaroDo/settings/pages
2. **Build and deployment** → Source: **GitHub Actions**
3. Actions → Workflow **Privacy-Policy Pages** → **Run workflow**
4. Nach grünem Deploy: HEAD-Request auf die Privacy-URL (HTTP 200)

Die Variable `PRIVACY_POLICY_URL` ist bereits gesetzt (Repository Actions Variables).

## Alternative ohne Actions

Source: **Deploy from a branch** → Branch `main`, Folder `/site`
