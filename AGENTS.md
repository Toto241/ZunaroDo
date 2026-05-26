# AGENTS.md

## Cursor Cloud specific instructions

### Overview

ZunaroDo (Alltagshelfer) is a Python 3.10+ privacy-focused personal assistant with 8 domain modules, a CustomTkinter desktop GUI, a CLI, and an optional KivyMD mobile app. All data is stored in SQLite (no external databases required). See `README.md` for full feature list and `DEVELOPING.md` for contributor workflow.

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
python3 main.py                  # console demo (has a pre-existing crash in the mail-analysis section)
```

### Running the GUI

The GUI requires a display. In Cloud Agent VMs, use Xvfb:

```bash
export DISPLAY=:99
Xvfb :99 -screen 0 1280x720x24 &>/dev/null &
python3 gui.py
```

Note: The GUI may crash on startup with a `KeyError: 'CTkTabview'` due to a theme compatibility issue with the installed customtkinter version. This is a pre-existing issue.

### Known pre-existing test failures

- `test_smoke.TestLicensing.test_scheduler_picks_up_extra_event_sources` — consistently fails (assertion on "Abo" string in notifier calls).
- `test_gui_free_tier_boot` — requires a working X display connection on `:1`; use `DISPLAY=:99` with Xvfb on `:99` if needed.

### Environment notes

- `python3-tk` (system package) is required for GUI-related tests and the CustomTkinter GUI.
- No Docker, external databases, or API keys are required for core development and testing.
- Optional features (Gemini AI, SQLCipher, OCR, IMAP) require their respective env vars and packages — see `README.md`.
