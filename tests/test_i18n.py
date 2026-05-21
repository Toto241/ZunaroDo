"""
Tests fuer services/i18n.py und tools/i18n_sync.py.

Kein Kivy/keine Drittabhaengigkeit noetig - laeuft unter
`python -m unittest` auf der CI.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from services import i18n
from services.i18n import (EU_LANGUAGES, I18n, detect_device_language,
                            normalize_language, resolve_language)
from tools import i18n_sync

LOCALES_DIR = Path(i18n.__file__).resolve().parent.parent / "locales"


class TestNormalizeLanguage(unittest.TestCase):

    def test_plain_code(self) -> None:
        self.assertEqual(normalize_language("de"), "de")

    def test_region_variants(self) -> None:
        for raw in ("de_DE", "de-DE", "de_DE.UTF-8", "de-de", "DE"):
            self.assertEqual(normalize_language(raw), "de", raw)

    def test_modifier_and_encoding(self) -> None:
        self.assertEqual(normalize_language("ca_ES@valencia"), "ca")

    def test_garbage_returns_none(self) -> None:
        for raw in (None, "", "C", "POSIX", "x", "123", "english"):
            self.assertIsNone(normalize_language(raw), raw)


class TestDetectDeviceLanguage(unittest.TestCase):
    """Nur der Desktop-Pfad ist hier deterministisch testbar."""

    def test_reads_language_env(self) -> None:
        with mock.patch.dict("os.environ",
                             {"LANGUAGE": "fr_FR:en", "LANG": "", "LC_ALL": "",
                              "LC_MESSAGES": ""}, clear=True):
            self.assertEqual(detect_device_language(), "fr")

    def test_lang_fallback_when_no_language(self) -> None:
        with mock.patch.dict("os.environ",
                             {"LANG": "it_IT.UTF-8"}, clear=True):
            self.assertEqual(detect_device_language(), "it")

    def test_priority_language_over_lang(self) -> None:
        with mock.patch.dict("os.environ",
                             {"LANGUAGE": "pl", "LANG": "de_DE"}, clear=True):
            self.assertEqual(detect_device_language(), "pl")


class TestResolveLanguage(unittest.TestCase):

    def test_explicit_supported(self) -> None:
        self.assertEqual(resolve_language("fr"), "fr")

    def test_region_normalized(self) -> None:
        self.assertEqual(resolve_language("es-ES"), "es")

    def test_unsupported_falls_back_to_default(self) -> None:
        # 'ja' ist keine EU-Sprache -> Default
        self.assertEqual(resolve_language("ja", default="de"), "de")

    def test_custom_supported_set(self) -> None:
        self.assertEqual(
            resolve_language("fr", supported=("de", "en"), default="de"),
            "de")

    def test_auto_uses_device(self) -> None:
        with mock.patch.object(i18n, "detect_device_language",
                               return_value="nl"):
            self.assertEqual(resolve_language("auto"), "nl")

    def test_auto_unknown_device_falls_back(self) -> None:
        with mock.patch.object(i18n, "detect_device_language",
                               return_value=None):
            self.assertEqual(resolve_language("AUTO", default="de"), "de")

    def test_none_falls_back(self) -> None:
        self.assertEqual(resolve_language(None, default="de"), "de")


class TestI18nClass(unittest.TestCase):

    def test_default_german(self) -> None:
        t = I18n("de")
        self.assertEqual(t.language, "de")
        self.assertEqual(t.t("tab.dashboard"), "Dashboard")

    def test_unknown_language_falls_back_to_default(self) -> None:
        t = I18n("xx")
        self.assertEqual(t.language, "de")

    def test_translation_lookup(self) -> None:
        t = I18n("fr")
        self.assertEqual(t.language, "fr")
        self.assertEqual(t.t("common.save"), "Enregistrer")

    def test_missing_key_falls_back_to_default_lang(self) -> None:
        # 'bg' hat nur CORE_KEYS - ein Nicht-Core-Key faellt auf de zurueck.
        t = I18n("bg")
        self.assertEqual(t.t("tab.dashboard"), "Табло")        # uebersetzt
        self.assertEqual(t.t("chat.thinking"), "denkt nach ...")  # Fallback de

    def test_unknown_key_returns_key(self) -> None:
        t = I18n("de")
        self.assertEqual(t.t("does.not.exist"), "does.not.exist")

    def test_unknown_key_returns_default_arg(self) -> None:
        t = I18n("de")
        self.assertEqual(t.t("does.not.exist", "fallback"), "fallback")

    def test_auto_resolves(self) -> None:
        with mock.patch.object(i18n, "detect_device_language",
                               return_value="it"):
            t = I18n("auto")
            self.assertEqual(t.language, "it")

    def test_available_languages_includes_default(self) -> None:
        langs = dict(I18n.available_languages())
        self.assertIn("de", langs)
        self.assertEqual(langs["de"], "Deutsch")
        # Alle vorhandenen Codes sind aus dem EU-Registry.
        for code, _name in I18n.available_languages():
            self.assertIn(code, EU_LANGUAGES)


class TestEuRegistry(unittest.TestCase):

    def test_24_official_languages(self) -> None:
        self.assertEqual(len(EU_LANGUAGES), 24)

    def test_default_is_first(self) -> None:
        self.assertEqual(next(iter(EU_LANGUAGES)), "de")

    def test_codes_are_two_letters(self) -> None:
        for code in EU_LANGUAGES:
            self.assertRegex(code, r"^[a-z]{2}$")


class TestLocaleFilesIntegrity(unittest.TestCase):
    """Diese Tests schuetzen vor Tippfehlern in den Locale-Dateien."""

    def setUp(self) -> None:
        self.default_keys = set(json.loads(
            (LOCALES_DIR / "de.json").read_text(encoding="utf-8")))

    def _load(self, code: str) -> dict:
        return json.loads(
            (LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8"))

    def test_every_file_is_valid_json(self) -> None:
        for path in LOCALES_DIR.glob("*.json"):
            with self.subTest(file=path.name):
                json.loads(path.read_text(encoding="utf-8"))

    def test_no_locale_has_extra_keys(self) -> None:
        for code in EU_LANGUAGES:
            path = LOCALES_DIR / f"{code}.json"
            if not path.exists():
                continue
            extra = set(self._load(code)) - self.default_keys
            self.assertEqual(extra, set(), f"{code}.json hat Fremd-Keys")

    def test_core_keys_present_everywhere(self) -> None:
        for code in EU_LANGUAGES:
            path = LOCALES_DIR / f"{code}.json"
            if not path.exists():
                continue
            missing = set(i18n_sync.CORE_KEYS) - set(self._load(code))
            self.assertEqual(missing, set(),
                             f"{code}.json fehlen CORE_KEYS")

    def test_full_languages_have_complete_parity(self) -> None:
        for code in ("en", "fr", "es", "it", "nl", "pl", "pt"):
            self.assertEqual(set(self._load(code)), self.default_keys,
                             f"{code}.json ist nicht deckungsgleich mit de")

    def test_placeholders_preserved_in_full_languages(self) -> None:
        import re
        default = self._load("de")
        token = re.compile(r"\{[^}]*\}")
        for code in ("fr", "es", "it", "nl", "pl", "pt"):
            data = self._load(code)
            for key, de_val in default.items():
                if key not in data:
                    continue
                self.assertEqual(
                    sorted(token.findall(de_val)),
                    sorted(token.findall(data[key])),
                    f"{code}.json[{key}] hat abweichende Platzhalter")


class TestI18nSyncTool(unittest.TestCase):

    def test_check_passes(self) -> None:
        report = i18n_sync.analyze()
        self.assertEqual(i18n_sync.check(report), [])

    def test_all_eu_languages_have_files(self) -> None:
        self.assertEqual(set(i18n_sync.existing_locales()),
                         set(EU_LANGUAGES))

    def test_coverage_numbers(self) -> None:
        report = i18n_sync.analyze()
        self.assertEqual(report["languages"]["de"]["coverage"], 100.0)
        self.assertEqual(report["languages"]["fr"]["coverage"], 100.0)
        self.assertLess(report["languages"]["bg"]["coverage"], 100.0)


if __name__ == "__main__":                           # pragma: no cover
    unittest.main()
