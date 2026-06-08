"""
Ableitung des SQLCipher-Datenbankschluessels (ALLTAGSHELFER_DB_KEY).

database.py verschluesselt die SQLite-Datei mit SQLCipher, sobald ein
Schluessel vorliegt UND 'sqlcipher3' installiert ist. Dieses Modul
liefert diesen Schluessel plattformabhaengig:

  - Desktop / CI: aus der Umgebungsvariable ALLTAGSHELFER_DB_KEY
    (oder dem OS-Keyring via services/config.py-Mechanik, falls gesetzt).
  - Android: aus dem Hardware-gestuetzten Keystore ueber die
    Java-Bruecke de.alltagshelfer.dbkey.DbKeyProvider (pyjnius). Diese
    legt beim ersten Start einen zufaelligen Schluessel in
    EncryptedSharedPreferences ab (MasterKey im Android Keystore) und
    gibt ihn danach zurueck.

WICHTIGE FAIL-SAFE-REGEL:
  Es wird NUR dann ein Schluessel zurueckgegeben, wenn 'sqlcipher3'
  importierbar ist. So bricht ein Build OHNE die SQLCipher-Recipe nicht
  beim Start ab (database.py wuerde sonst hart abbrechen, weil Key
  gesetzt aber Engine fehlt). Sobald die Recipe im Buildozer-Build
  eingebunden ist, aktiviert sich die Verschluesselung automatisch.
"""
from __future__ import annotations

import os
from typing import Optional


def _sqlcipher_available() -> bool:
    try:
        import sqlcipher3  # noqa: F401  (nur Verfuegbarkeitstest)
        return True
    except Exception:
        return False


def _on_android() -> bool:
    try:
        from kivy.utils import platform as kivy_platform
        return kivy_platform == "android"
    except Exception:
        return False


def _android_keystore_key() -> Optional[str]:
    """Holt/erzeugt den DB-Schluessel ueber die Android-Keystore-Bruecke."""
    try:
        from jnius import autoclass  # type: ignore[import-untyped]

        provider = autoclass("de.alltagshelfer.dbkey.DbKeyProvider")
        key = provider.getOrCreateKey()
        return str(key) if key else None
    except Exception:
        return None


def resolve_db_key() -> Optional[str]:
    """
    Liefert den DB-Schluessel oder None (= unverschluesselt).

    Gibt bewusst None zurueck, wenn 'sqlcipher3' fehlt - siehe Fail-Safe
    im Modul-Docstring.
    """
    # Manuell/Override per Env hat Vorrang (Desktop, Tests, CI).
    env_key = os.environ.get("ALLTAGSHELFER_DB_KEY")
    if env_key:
        return env_key

    if not _sqlcipher_available():
        # Ohne Engine niemals einen Key liefern - sonst Startabbruch.
        return None

    if _on_android():
        return _android_keystore_key()

    return None
