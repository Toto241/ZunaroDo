# Play Console — manuelle Einreichung

Schritte, die nicht aus dem Repo automatisiert werden können. Antworten aus dem Code: `python -m tools.data_safety --markdown`.

## Reihenfolge

1. **Developer-Konto** verifizieren (Identität, Support-E-Mail erreichbar)
2. **Internal Testing**: AAB hochladen → Pre-Launch-Report prüfen
3. **Closed Testing**: ≥12 Tester, ≥14 Tage → Nachweis in `release/closed-test-*.md` + Screenshot in `release/assets/`
4. **Store-Listing**: Texte aus `playstore.yml`, Assets aus `assets/store/`
5. **Data Safety**: `release/DATA_SAFETY_CONSOLE_ANSWERS.md` / `tools.data_safety --markdown`
6. **Content Rating**: Produktivität, keine Gewalt, Zielgruppe ≥13
7. **Privacy URL**: `https://toto241.github.io/ZunaroDo/privacy/` (HTTP 200)
8. **Datenlöschung**: In-App unter Mehr → Alle Daten löschen
9. **Export Compliance** (US): in Console bestätigen
10. **Production**: Staged Rollout 10 %

## Pflichtfelder

| Feld | Quelle |
|------|--------|
| Package | `de.alltagshelfer.alltagshelfer` |
| versionCode | `playstore.yml` → `identity.version_code` |
| Support-E-Mail | `zunarodo.support@toto241.github.io` |
| Privacy URL | `playstore.yml` → `contact.privacy_policy_url` |

## Nach Rollout (48 h)

- Crash-free Users ≥ 99,5 %
- ANR < 0,47 %
- Negative Reviews prüfen
