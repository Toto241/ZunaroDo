# AGENTS.md

## Cursor Cloud specific instructions

### Overview

ZunaroDo (Alltagshelfer) is a Python 3.10+ privacy-focused personal assistant with **13 registered modules** (9 domain + 4 cross-cutting) exposing **92 capabilities**, a CustomTkinter desktop GUI (14 tabs), a CLI, and an optional KivyMD mobile app. All data is stored in SQLite (no external databases required). See `README.md` for full feature list and `DEVELOPING.md` for contributor workflow.

### Running tests

```bash
# Full test suite (recommended)
PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring python3 -m pytest tests/ --tb=short

# Or with unittest
PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring python3 -m unittest discover tests
```

**Critical:** Always set `PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring` when running tests. Without this, `test_pairing.py` hangs indefinitely because `_keyring_works()` blocks trying to access D-Bus/libsecret, which is not available in headless cloud VMs.

### Static analysis

```bash
python3 -m compileall . -q
```

### Running the CLI

```bash
python3 __main__.py --diagnose   # status report
python3 main.py                  # console demo
```

### Running the GUI

The GUI requires a display. In Cloud Agent VMs, use Xvfb:

```bash
export DISPLAY=:99
Xvfb :99 -screen 0 1280x720x24 &>/dev/null &
python3 gui.py
```

Older CustomTkinter builds without a `CTkTabview` theme entry are handled in `gui.py` via a guarded theme patch.

### Known pre-existing test failures

- None on the default unittest suite (`python -m unittest discover tests`). GUI boot tests live under `tests/concept/` and need Xvfb (`DISPLAY=:99`).

### Environment notes

- `python3-tk` (system package) is required for GUI-related tests and the CustomTkinter GUI.
- No Docker, external databases, or API keys are required for core development and testing.
- Optional features (Gemini AI, SQLCipher, OCR, IMAP) require their respective env vars and packages — see `README.md`.
