#!/usr/bin/env bash
# Einmalige GitHub-Pages-Einrichtung fuer die Privacy-Policy-URL.
# Voraussetzung: gh CLI authentifiziert (gh auth login).
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-Toto241/ZunaroDo}"
PRIVACY_URL="https://toto241.github.io/ZunaroDo/privacy/"

echo "==> Privacy-Policy lokal bauen"
python3 -m tools.privacy_policy --build --out site/privacy/index.html
python3 -m tools.privacy_policy --check

if command -v gh >/dev/null 2>&1; then
  echo "==> Repo-Variable PRIVACY_POLICY_URL setzen"
  gh variable set PRIVACY_POLICY_URL --body "$PRIVACY_URL" -R "$REPO" || true

  echo "==> Pages-Workflow ausloesen"
  gh workflow run "Privacy-Policy Pages" -R "$REPO" || true

  echo "Hinweis: In Repo Settings -> Pages -> Source auf 'GitHub Actions' stellen."
else
  echo "gh CLI nicht verfuegbar — manuell:"
  echo "  1. Settings -> Pages -> GitHub Actions"
  echo "  2. Workflow 'Privacy-Policy Pages' starten"
  echo "  3. Variable PRIVACY_POLICY_URL=$PRIVACY_URL setzen"
fi

echo "==> URL pruefen (nach Deploy ggf. 1-2 Min. warten)"
PRIVACY_POLICY_URL="$PRIVACY_URL" ./scripts/verify-privacy-url.sh || true
