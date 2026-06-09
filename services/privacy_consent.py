"""
Persistierte Datenschutz-Zustimmung (Play Store / DSGVO).
"""
from __future__ import annotations

_CONSENT_KEY = "privacy.consent_accepted"


def consent_accepted(settings_repo) -> bool:
    if settings_repo is None:
        return True
    return str(settings_repo.get(_CONSENT_KEY, "0")) == "1"


def mark_consent_accepted(settings_repo) -> None:
    if settings_repo is not None:
        settings_repo.set(_CONSENT_KEY, "1")
