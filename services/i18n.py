from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# EU-wide i18n support with English as fallback language.
_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


class I18n:
    """Minimal translation lookup with EU language support."""

    DEFAULT_LANGUAGE = "en"

    SUPPORTED_LANGUAGES = (
        "bg", "hr", "cs", "da", "nl", "en", "et", "fi",
        "fr", "de", "el", "hu", "ga", "it", "lv", "lt",
        "mt", "pl", "pt", "ro", "sk", "sl", "es", "sv",
    )

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        self.language = (
            language if language in self.SUPPORTED_LANGUAGES
            else self.DEFAULT_LANGUAGE
        )
        self._strings = self._load(self.language)
        self._fallback = (
            self._load(self.DEFAULT_LANGUAGE)
            if self.language != self.DEFAULT_LANGUAGE
            else {}
        )

    def t(self, key: str, default: Optional[str] = None) -> str:
        if key in self._strings and self._strings[key]:
            return self._strings[key]
        if key in self._fallback and self._fallback[key]:
            return self._fallback[key]
        return default if default is not None else key

    @staticmethod
    def _load(language: str) -> dict[str, str]:
        path = _LOCALES_DIR / f"{language}.json"
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {k: str(v) for k, v in data.items() if isinstance(k, str)}
