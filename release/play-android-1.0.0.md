# Android Release 1.0.0 — AAB & Play Console

Checkliste fuer den manuellen Store-Upload (kein Auto-Deploy in CI).

## Version

| Feld | Wert |
| --- | --- |
| versionName | `1.0.0` |
| versionCode | `2` |
| Package | `de.alltagshelfer.alltagshelfer` |

Quelle: [playstore.yml](../playstore.yml), [buildozer.spec](../buildozer.spec).

## AAB bauen

```bash
# Auf Linux mit Android-SDK / NDK (siehe build-android.sh)
./build-android.sh release
# Artefakt typisch: bin/*.aab
```

Alternativ: GitHub Actions → Workflow **Android Release** → `workflow_dispatch`.

## Vor dem Upload

```bash
python -m tools.playstore_sync validate
python -m tools.data_safety --check
python -m tools.privacy_policy --check
PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring \
  python -m unittest discover tests
```

## Play Console — Reihenfolge

1. **Internal testing** — AAB version_code 2 hochladen, Smoke auf Testgeraet
2. **Closed testing** — Gruppe `zunarodo-closed-testers@googlegroups.com`, ≥12 Tester, **14 Tage**
3. Nachweis: [closed-test-2026-05-30.md](closed-test-2026-05-30.md) ausfuellen
4. **Production** — Draft in `playstore.yml` auf `inProgress` setzen nach Freigabe

## Metadaten sync (optional)

```bash
python -m tools.playstore_sync --mock export   # Snapshot
python -m tools.playstore_sync validate
# Mit Service-Account: pull / push
```

Support & Privacy-URLs muessen mit [legal/provider.yml](../legal/provider.yml) uebereinstimmen.
