"""
Mehrgeraete-Synchronisation fuer den Alltagshelfer.

Das Konzept stammt aus dem urspruenglichen Family-Modul-Entwurf: jeder
Erwachsene im Haushalt nutzt die App auf seinem eigenen Geraet, alle
Geraete teilen sich einen Familienordner (Dropbox / OneDrive / Google
Drive / Netzlaufwerk). Eine Datei in diesem Ordner ist der gemeinsame
Event-Log.

Ablauf:
  1) Jede gewuenschte mutating capability wird beim Aufruf zusaetzlich
     in den Event-Log geschrieben (JSONL: eine Zeile pro Event).
  2) Beim Start liest jedes Geraet den Log und wendet noch nicht
     gesehene Events lokal an (idempotent via Event-UUID).
  3) Ein lokales Logbuch (sync_seen.json neben der DB) merkt sich
     bereits gesehene Event-IDs - so wird jedes Event nur einmal
     angewendet.

Konfiguration:
  - ALLTAGSHELFER_SYNC_DIR  - Pfad zum geteilten Ordner.
  - ALLTAGSHELFER_DEVICE_ID - optional, Default: ein per uuid4()
                              generierter Wert (in <data_dir>/device_id).

Bewusst klein gehalten: keine Konfliktaufloesung mit CRDTs, kein Server.
Idempotente Operationen funktionieren sauber; bei nicht-idempotenten
(z.B. Zustandsaenderungen) gewinnt die zuletzt angewendete Reihenfolge.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.interface import ModuleRegistry


# Welche Capabilities werden ueberhaupt synchronisiert? (alle "schreibend"
# wirkenden Capabilities in Familien-/Hausstand-Belangen)
DEFAULT_SYNCED_CAPABILITIES: set[str] = {
    "family.add_member",
    "family.add_task",
    "family.complete_task",
    "family.add_order",
    "family.complete_order",
    "family.shopping_add",
    "family.shopping_mark",
}


@dataclass
class SyncEvent:
    event_id: str
    device_id: str
    timestamp: str
    capability: str
    args: dict

    def to_dict(self) -> dict:
        return {"event_id": self.event_id, "device_id": self.device_id,
                "timestamp": self.timestamp, "capability": self.capability,
                "args": self.args}

    @classmethod
    def from_dict(cls, data: dict) -> "SyncEvent":
        return cls(
            event_id=data["event_id"], device_id=data["device_id"],
            timestamp=data["timestamp"], capability=data["capability"],
            args=data.get("args", {}),
        )


class FileSyncProvider:
    """JSONL-basierte Sync-Schicht ueber einen geteilten Ordner."""

    LOG_FILE_NAME = "sync_events.jsonl"
    SEEN_FILE_NAME = "sync_seen.json"

    def __init__(self, sync_dir: str, device_id: str,
                 local_seen_path: Optional[Path] = None):
        self.sync_dir = Path(sync_dir)
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        self.device_id = device_id
        self.log_path = self.sync_dir / self.LOG_FILE_NAME
        self.seen_path = local_seen_path or self.sync_dir / self.SEEN_FILE_NAME
        self._seen: set[str] = self._load_seen()

    # ---- Initial-Setup ------------------------------------------------
    @classmethod
    def from_env(cls, local_data_dir: Path) -> Optional["FileSyncProvider"]:
        sync_dir = os.environ.get("ALLTAGSHELFER_SYNC_DIR")
        if not sync_dir:
            return None
        device_id = os.environ.get("ALLTAGSHELFER_DEVICE_ID") \
            or cls._resolve_device_id(local_data_dir)
        local_data_dir.mkdir(parents=True, exist_ok=True)
        return cls(sync_dir, device_id,
                    local_seen_path=local_data_dir / cls.SEEN_FILE_NAME)

    @staticmethod
    def _resolve_device_id(local_data_dir: Path) -> str:
        marker = local_data_dir / "device_id"
        if marker.exists():
            return marker.read_text(encoding="utf-8").strip()
        local_data_dir.mkdir(parents=True, exist_ok=True)
        device_id = str(uuid.uuid4())
        marker.write_text(device_id, encoding="utf-8")
        return device_id

    # ---- Lesen / Schreiben des Event-Logs -----------------------------
    def append(self, event: SyncEvent) -> None:
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        self._seen.add(event.event_id)
        self._save_seen()

    def read_all(self) -> list[SyncEvent]:
        if not self.log_path.exists():
            return []
        events: list[SyncEvent] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(SyncEvent.from_dict(json.loads(line)))
            except Exception:
                continue
        return events

    def unseen_events(self) -> list[SyncEvent]:
        return [e for e in self.read_all()
                if e.event_id not in self._seen
                and e.device_id != self.device_id]

    def mark_seen(self, event_id: str) -> None:
        self._seen.add(event_id)
        self._save_seen()

    # ---- Lokales Logbuch ----------------------------------------------
    def _load_seen(self) -> set[str]:
        if not self.seen_path.exists():
            return set()
        try:
            return set(json.loads(self.seen_path.read_text(encoding="utf-8")))
        except Exception:
            return set()

    def _save_seen(self) -> None:
        self.seen_path.parent.mkdir(parents=True, exist_ok=True)
        self.seen_path.write_text(
            json.dumps(sorted(self._seen)), encoding="utf-8")


class SyncedRegistry:
    """
    Wrapper um ModuleRegistry mit Sync-Hook.

    - Bei Aufrufen synchronisierter Capabilities wird ein Event in den
      geteilten Log geschrieben.
    - apply_remote() spielt fremde Events nach.

    Damit ein Replay nicht wieder synchronisiert wird, gibt es ein Flag
    '_replaying'.
    """

    def __init__(self, registry: ModuleRegistry,
                 provider: FileSyncProvider,
                 synced: Optional[set[str]] = None,
                 inner_dispatch=None):
        self.registry = registry
        self.provider = provider
        self.synced = synced or DEFAULT_SYNCED_CAPABILITIES
        self._replaying = False
        # ueberbruecken den hook, indem wir den ORIGINAL-dispatch merken
        self._inner_dispatch = inner_dispatch or registry.dispatch

    def dispatch(self, capability: str, args: dict) -> dict:
        result = self._inner_dispatch(capability, args)
        if (not self._replaying
                and capability in self.synced
                and "error" not in result):
            event = SyncEvent(
                event_id=str(uuid.uuid4()),
                device_id=self.provider.device_id,
                timestamp=datetime.utcnow().isoformat(timespec="seconds"),
                capability=capability,
                args=args,
            )
            try:
                self.provider.append(event)
            except Exception:                              # pragma: no cover
                pass
        return result

    def apply_remote(self) -> int:
        """Wendet alle ungesehenen Events anderer Geraete an. Liefert Anzahl."""
        applied = 0
        self._replaying = True
        try:
            for event in self.provider.unseen_events():
                result = self._inner_dispatch(event.capability, event.args)
                if "error" not in result:
                    applied += 1
                self.provider.mark_seen(event.event_id)
        finally:
            self._replaying = False
        return applied

    # ---- Pass-through: registry-aehnliche API -------------------------
    def __getattr__(self, item):
        return getattr(self.registry, item)


def install_sync_hook(registry: ModuleRegistry,
                       provider: FileSyncProvider,
                       synced: Optional[set[str]] = None) -> SyncedRegistry:
    """
    Verdrahtet den Sync-Hook so, dass auch direkte Modul-zu-Modul-Aufrufe
    durch den Wrapper laufen.

    Wir merken uns den Original-`dispatch` und ersetzen die Methode am
    Registry-Objekt durch einen Wrapper, der ueber SyncedRegistry geht.
    SyncedRegistry verwendet dabei IMMER den Original-Dispatch, damit
    keine Endlos-Rekursion entsteht.
    """
    original_dispatch = registry.dispatch
    synced_registry = SyncedRegistry(registry, provider, synced,
                                       inner_dispatch=original_dispatch)

    def hooked(capability: str, args: Optional[dict] = None) -> dict:
        return synced_registry.dispatch(capability, dict(args or {}))

    registry.dispatch = hooked                              # type: ignore[assignment]
    registry._dispatch_unhooked = original_dispatch          # type: ignore[attr-defined]
    return synced_registry
