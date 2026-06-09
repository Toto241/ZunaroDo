"""
Kanonische Projekt-Identitaet fuer Play Store, Legal und In-App-Links.

Single source of truth: legal/provider.yml
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

_PROVIDER = Path(__file__).resolve().parent.parent / "legal" / "provider.yml"

# Fallbacks, falls provider.yml nicht geladen werden kann.
_DEFAULTS: dict[str, str] = {
    "provider_name": "ZunaroDo",
    "package_name": "de.alltagshelfer.alltagshelfer",
    "github_repo": "Toto241/ZunaroDo",
    "support_email": "zunarodo.support@toto241.github.io",
    "support_url": "https://github.com/Toto241/ZunaroDo/issues",
    "product_url": "https://github.com/Toto241/ZunaroDo",
    "privacy_url": "https://toto241.github.io/ZunaroDo/privacy/",
    "marketing_url": "https://github.com/Toto241/ZunaroDo",
}


@lru_cache(maxsize=1)
def load_provider() -> dict[str, Any]:
    """Liest legal/provider.yml; bei Fehler leere Dict."""
    if yaml is None or not _PROVIDER.is_file():
        return {}
    try:
        data = yaml.safe_load(_PROVIDER.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _get(key: str) -> str:
    env_key = f"ZUNARODO_{key.upper()}"
    if os.environ.get(env_key):
        return os.environ[env_key]
    prov = load_provider()
    val = prov.get(key) or _DEFAULTS.get(key, "")
    return str(val)


def provider_name() -> str:
    return _get("provider_name")


def package_name() -> str:
    return _get("package_name")


def github_repo() -> str:
    return _get("github_repo")


def github_url() -> str:
    return f"https://github.com/{github_repo()}"


def support_email() -> str:
    prov = load_provider()
    return str(
        os.environ.get("ZUNARODO_SUPPORT_EMAIL")
        or prov.get("support_email")
        or prov.get("email")
        or _DEFAULTS["support_email"]
    )


def support_url() -> str:
    return _get("support_url")


def product_url() -> str:
    return _get("product_url")


def privacy_url() -> str:
    return _get("privacy_url")


def marketing_url() -> str:
    return _get("marketing_url") or product_url()
