#!/usr/bin/env bash
# Prueft, ob die Privacy-Policy-URL erreichbar ist (HTTP 200/301/302).
# Nutzung:
#   ./scripts/verify-privacy-url.sh
#   PRIVACY_POLICY_URL=https://example.com/privacy/ ./scripts/verify-privacy-url.sh
set -euo pipefail

URL="${PRIVACY_POLICY_URL:-https://toto241.github.io/ZunaroDo/privacy/}"
echo "Pruefe Privacy-URL: $URL"

code=$(curl -sS -o /dev/null -w '%{http_code}' -L --max-time 30 "$URL" || echo "000")

if [[ "$code" =~ ^(200|301|302)$ ]]; then
  echo "OK: HTTP $code"
  exit 0
fi

echo "FEHLER: HTTP $code — GitHub Pages deployen:"
echo "  1. Repo Settings -> Pages -> Source: GitHub Actions"
echo "  2. Workflow 'Privacy-Policy Pages' ausfuehren"
echo "  3. Repo-Variable PRIVACY_POLICY_URL auf $URL setzen"
exit 1
