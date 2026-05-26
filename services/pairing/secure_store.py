"""
Abstraktion fuer plattformeigene Schluessel-Ablage.

Geraete-Langzeit-Schluessel (`IK_priv`), per-Peer-PSKs (`sync_psk`)
und das Bootstrap-Geheimnis fuer den Pairing-Cache gehoeren *nicht*
in die App-DB - das ist die zentrale Aussage von PAIRING.md Kapitel 7.
Stattdessen nutzt jedes OS seinen eigenen Secure-Store:

    Windows   Credential Manager / DPAPI
    macOS     Keychain Services
    Linux     SecretService (gnome-keyring, kwallet, ...) via D-Bus
    Android   Keystore (folgt in eigenem PR, Native-Bridge)
    iOS       Keychain Services (folgt in eigenem PR, Native-Bridge)

Auf Windows / macOS / Linux uebernimmt die Bibliothek `keyring` die
Vermittlung an das jeweilige OS-Backend. Wir kapseln sie hinter einem
schlanken `SecureStore`-Protokoll, damit:

  * Tests deterministisch laufen koennen (InMemorySecureStore).
  * Die Mobile-Bridges spaeter eigene Backends einklinken koennen,
    ohne den Aufruf-Code zu aendern.

Aufruf-Konvention: Schluessel sind Strings mit Punkt-Namespace
(`alltagshelfer.identity`, `alltagshelfer.peer.<device_id>`).
Werte sind Bytes - die Krypto-Module entscheiden ueber die Serialisierung
(Raw-Key-Bytes, JSON-encoded-Bundle, ...).
"""
from __future__ import annotations

import base64
import os
import sys
from typing import Optional, Protocol, runtime_checkable


class SecureStoreError(RuntimeError):
    """Backend nicht verfuegbar oder schreib-/lesefehler."""


@runtime_checkable
class SecureStore(Protocol):
    """Minimaler Vertrag fuer alle Backend-Implementierungen."""

    def set(self, key: str, value: bytes) -> None:
        ...

    def get(self, key: str) -> Optional[bytes]:
        ...

    def delete(self, key: str) -> None:
        ...

    def list_keys(self, prefix: str = "") -> list[str]:
        ...


class InMemorySecureStore:
    """RAM-Backend - ausschliesslich fuer Tests und CI gedacht.

    Beim Prozessende geht alles verloren. Nicht in Produktion verwenden.
    """

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def set(self, key: str, value: bytes) -> None:
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("SecureStore-Werte muessen bytes sein")
        self._data[key] = bytes(value)

    def get(self, key: str) -> Optional[bytes]:
        return self._data.get(key)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def list_keys(self, prefix: str = "") -> list[str]:
        return sorted(k for k in self._data if k.startswith(prefix))


# `keyring` speichert Strings, nicht Bytes. Wir kodieren die Werte
# transparent als Base64, damit Aufrufer mit Raw-Key-Bytes arbeiten
# koennen. Der Service-Name `_KEYRING_SERVICE` ist die Namespacing-
# Wurzel auf der OS-Seite - alle Schluessel landen unter diesem
# Service, einzeln benannt nach `key`.
_KEYRING_SERVICE = "alltagshelfer.pairing"

# Eine "Manifest"-Datei je Backend listet, welche Keys das Backend
# kennt. Das brauchen wir nur, weil das `keyring`-Protokoll kein
# `list_keys()` definiert - die meisten OS-Stores koennen das
# durchaus, aber die Bibliothek macht es nicht zugaenglich. Das
# Manifest wird im Secure-Store selbst gespeichert (unter
# `_MANIFEST_KEY`), damit es exakt mit den realen Eintraegen
# wandert (Backup, Sync-zwischen-Profilen).
_MANIFEST_KEY = "__manifest__"


def _has_linux_secret_service_session() -> bool:
    """True, wenn keyring auf Linux sinnvoll ein SecretService erreichen kann."""
    if not sys.platform.startswith("linux"):
        return True
    if os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        return True
    # Explizit gesetzte Backends duerfen weiterhin selbst entscheiden.
    return bool(os.environ.get("PYTHON_KEYRING_BACKEND"))


class KeyringSecureStore:
    """Default-Backend fuer Desktop (Windows, macOS, Linux).

    Setzt das PyPI-Paket `keyring` voraus. Auf Linux wird ein laufender
    SecretService-Daemon (z.B. gnome-keyring) erwartet; ist keiner da,
    wirft das erste `set()` eine `SecureStoreError`.
    """

    def __init__(self, service: str = _KEYRING_SERVICE) -> None:
        try:
            import keyring  # noqa: F401  (Import-Probe)
        except ImportError as exc:
            raise SecureStoreError(
                "Bibliothek 'keyring' nicht installiert - "
                "siehe requirements.txt"
            ) from exc
        self._service = service

    def _kr(self):  # Lazy-Import, weil Tests evtl. keyring nicht haben
        import keyring
        return keyring

    def set(self, key: str, value: bytes) -> None:
        if not isinstance(value, (bytes, bytearray)):
            raise TypeError("SecureStore-Werte muessen bytes sein")
        if key == _MANIFEST_KEY:
            raise ValueError(f"'{_MANIFEST_KEY}' ist reserviert")
        try:
            encoded = base64.b64encode(bytes(value)).decode("ascii")
            self._kr().set_password(self._service, key, encoded)
            self._add_to_manifest(key)
        except Exception as exc:  # keyring.errors.KeyringError u.a.
            raise SecureStoreError(f"set({key!r}) fehlgeschlagen: {exc}") from exc

    def get(self, key: str) -> Optional[bytes]:
        try:
            raw = self._kr().get_password(self._service, key)
        except Exception as exc:
            raise SecureStoreError(f"get({key!r}) fehlgeschlagen: {exc}") from exc
        if raw is None:
            return None
        try:
            return base64.b64decode(raw.encode("ascii"))
        except Exception as exc:
            raise SecureStoreError(
                f"Wert unter {key!r} ist kein Base64 - Store ist korrupt"
            ) from exc

    def delete(self, key: str) -> None:
        try:
            self._kr().delete_password(self._service, key)
        except Exception:
            # delete_password wirft, wenn nichts da war - das ist fuer
            # uns kein Fehler. Andere Fehler ignorieren wir bewusst,
            # damit `delete()` idempotent ist.
            pass
        self._remove_from_manifest(key)

    def list_keys(self, prefix: str = "") -> list[str]:
        return sorted(k for k in self._read_manifest() if k.startswith(prefix))

    # ---- Manifest-Verwaltung ----

    def _read_manifest(self) -> list[str]:
        raw = self._kr().get_password(self._service, _MANIFEST_KEY)
        if not raw:
            return []
        # newline-separierte Liste; einfach genug und atomar genug.
        return [line for line in raw.splitlines() if line]

    def _write_manifest(self, keys: list[str]) -> None:
        self._kr().set_password(
            self._service, _MANIFEST_KEY, "\n".join(sorted(set(keys)))
        )

    def _add_to_manifest(self, key: str) -> None:
        keys = self._read_manifest()
        if key not in keys:
            keys.append(key)
            self._write_manifest(keys)

    def _remove_from_manifest(self, key: str) -> None:
        keys = self._read_manifest()
        if key in keys:
            keys.remove(key)
            self._write_manifest(keys)


def default_secure_store() -> SecureStore:
    """Liefert das passendste verfuegbare Backend fuer diese Plattform.

    Reihenfolge:
      1. Env-Override `ALLTAGSHELFER_PAIRING_BACKEND=memory|keyring`
         (memory ausschliesslich fuer Tests/CI gedacht).
      2. KeyringSecureStore, wenn `keyring` importierbar ist.
      3. Fallback: InMemorySecureStore mit *Warnung* via Logger.

    Der Fallback ist absichtlich nicht persistent: lieber Daten beim
    naechsten Start neu pairen muessen, als sie unverschluesselt auf
    Platte legen. Aufrufer sollten den Fallback-Fall in der UI sichtbar
    machen.
    """
    override = os.environ.get("ALLTAGSHELFER_PAIRING_BACKEND", "").strip().lower()
    if override == "memory":
        return InMemorySecureStore()
    if override == "keyring":
        return KeyringSecureStore()

    if not _has_linux_secret_service_session():
        return InMemorySecureStore()

    try:
        return KeyringSecureStore()
    except SecureStoreError:
        # Falls keine Bibliothek installiert ist, faellt der naechste
        # Startup auf den fluechtigen Store zurueck. Wir loggen das
        # nicht direkt hier (Modul soll log-frei bleiben), sondern
        # ueberlassen das dem Aufrufer, der den Typ pruefen kann.
        return InMemorySecureStore()


def is_persistent(store: SecureStore) -> bool:
    """Hilfsfunktion fuer die UI: 'koennen wir ueberhaupt persistieren?'"""
    return not isinstance(store, InMemorySecureStore)


# Plattform-Hinweis fuer das spaetere Mobile-Bridge-PR:
#
#   Android   :  androidx.security.crypto + Tink (StrongBox falls
#                vorhanden), aufrufbar via PyJNIus oder einer
#                eigenen JNI-Bridge in mobile/.
#   iOS       :  CryptoKit/Keychain via PyObjC-Brücke. Attribute:
#                kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
#                kSecAttrSynchronizable = false.
#
# Diese Backends implementieren dasselbe `SecureStore`-Protocol; sie
# werden in default_secure_store() vor dem Keyring-Fallback eingehaengt,
# sobald sie existieren.
