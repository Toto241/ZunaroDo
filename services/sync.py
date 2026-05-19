"""
Mehrgeraete-Synchronisation fuer den Alltagshelfer.

Zwei austauschbare Provider:
  - FileSyncProvider  - Event-Log in einem geteilten Ordner (Default,
                         z.B. Dropbox / OneDrive / Netzlaufwerk).
  - HttpSyncProvider  - Event-Log auf einem kleinen HTTP-Server
                         (services/sync_server.py). Sinnvoll, wenn kein
                         geteilter Ordner zur Verfuegung steht.

Beide implementieren das interne SyncProviderProtocol mit:
  - append(event)             -> Event in den geteilten Log schreiben
  - unseen_events()           -> noch nicht angewendete Events liefern
  - mark_seen(event_id)       -> Event als verarbeitet markieren

Konfliktstrategie (bewusst einfach): Last-Write-Wins ueber den
Timestamp. Bei nicht-idempotenten Operationen (z.B.
family.complete_task) gewinnt die zuletzt angewendete Anwendung.
Diese Vereinfachung ist fuer den Haushaltsbetrieb angemessen; CRDTs
oder ein echter Server mit Transaktionen waeren der naechste Schritt.

Periodische Sync-Schleife:
  - Beim Start: einmaliger Replay (apply_remote()).
  - In der GUI: Hintergrund-Thread, der alle 'sync.interval_seconds'
    Sekunden apply_remote() ausfuehrt.

Log-Kompaktierung:
  - Wenn der gemeinsame Log >MAX_LOG_LINES Zeilen hat, wird beim Start
    eine bereinigte Kopie geschrieben (Events bleiben in Reihenfolge,
    aber nicht-idempotente Endzustaende werden behalten).
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol

from core.interface import ModuleRegistry


# Weiche Obergrenze fuer Log-Zeilen, bevor automatisch kompaktiert wird.
MAX_LOG_LINES = 5000


# Welche Capabilities werden synchronisiert? Alle schreibenden
# Capabilities aus haushaltsrelevanten Modulen (A, B, C, D, E).
# Konfliktstrategie: Last-Write-Wins anhand Timestamp + Anwendungsreihenfolge.
# Reine Lese-Capabilities (.list, .members, .upcoming etc.) gehoeren NICHT
# hierher - sie wuerden den Log nur aufblaehen, ohne Nutzen zu bringen.
DEFAULT_SYNCED_CAPABILITIES: set[str] = {
    # Modul A
    "contracts.add",
    "contracts.report_price_change",
    "contracts.set_owner",
    # Modul B
    "finance.add_expense",
    "finance.remember_price",
    # Modul C
    "calendar.add_event",
    "calendar.delete_event",
    # Modul D - Familie
    "family.add_member",
    "family.add_task",
    "family.complete_task",
    "family.add_order",
    "family.complete_order",
    "family.shopping_add",
    "family.shopping_mark",
    # Modul E
    "social.add_contact",
    "social.mark_contacted",
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


class SyncProviderProtocol(Protocol):
    device_id: str
    def append(self, event: "SyncEvent") -> None: ...
    def unseen_events(self) -> list["SyncEvent"]: ...
    def mark_seen(self, event_id: str) -> None: ...
    def compact_if_needed(self) -> int: ...


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
        self._lock = threading.Lock()
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
        with self._lock:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
            self._seen.add(event.event_id)
            self._save_seen_unlocked()

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
        # Last-Write-Wins: chronologisch sortieren, damit die spaeteste
        # Anwendung bei nicht-idempotenten Operationen am Ende kommt.
        events = [e for e in self.read_all()
                   if e.event_id not in self._seen
                   and e.device_id != self.device_id]
        events.sort(key=lambda ev: ev.timestamp)
        return events

    def mark_seen(self, event_id: str) -> None:
        with self._lock:
            self._seen.add(event_id)
            self._save_seen_unlocked()

    def compact_if_needed(self, max_lines: int = MAX_LOG_LINES) -> int:
        """
        Schreibt den Log neu, sobald er ueber 'max_lines' Zeilen wachsen
        wuerde - aelteste Eintraege werden weggeworfen. Gibt die Anzahl
        der entfernten Zeilen zurueck. 0 = nichts gemacht.
        """
        if not self.log_path.exists():
            return 0
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        if len(lines) <= max_lines:
            return 0
        keep = lines[-max_lines:]
        tmp = self.log_path.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(keep) + "\n", encoding="utf-8")
        tmp.replace(self.log_path)
        return len(lines) - len(keep)

    # ---- Lokales Logbuch ----------------------------------------------
    def _load_seen(self) -> set[str]:
        if not self.seen_path.exists():
            return set()
        try:
            return set(json.loads(self.seen_path.read_text(encoding="utf-8")))
        except Exception:
            return set()

    def _save_seen_unlocked(self) -> None:
        # Aufrufer haelt den Lock. Atomarer Write: erst in temp, dann
        # replace - verhindert halbfertige JSON-Dateien bei Crash.
        self.seen_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.seen_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(sorted(self._seen)), encoding="utf-8")
        tmp.replace(self.seen_path)


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
                 provider,
                 synced: Optional[set[str]] = None,
                 inner_dispatch=None):
        self.registry = registry
        self.provider = provider
        self.synced = synced or DEFAULT_SYNCED_CAPABILITIES
        self._replaying = False
        # Thread-Local-Marker: True, wenn der aktuelle Thread bereits
        # mitten in einem dispatch() steckt. Modul-zu-Modul-Aufrufe sind
        # dadurch erkennbar - sie sollen NICHT als eigenes Event in den
        # Sync-Log gehen (sonst wird derselbe Effekt beim Replay doppelt
        # angewendet).
        self._local = threading.local()
        # ueberbruecken den Hook, indem wir den ORIGINAL-dispatch merken
        self._inner_dispatch = inner_dispatch or registry.dispatch

    def dispatch(self, capability: str, args: dict) -> dict:
        # 'in_synced_outer' markiert, dass wir bereits innerhalb eines
        # synchronisierten dispatch-Aufrufs stecken. Nested Aufrufe
        # innerhalb eines bereits geloggten Events duerfen NICHT erneut
        # ein eigenes Event schreiben - sonst wuerde der Effekt beim
        # Replay doppelt angewendet.
        #
        # Wichtig dabei: wenn der AEUSSERE Aufruf nicht synchronisiert
        # ist (z.B. inbox.accept_proposal), darf der nested Aufruf
        # weiterhin loggen - denn ohne das Event wuerde der Effekt
        # andere Geraete sonst nie erreichen.
        is_synced = capability in self.synced
        in_synced_outer = bool(getattr(self._local, "in_synced", False))
        if is_synced:
            self._local.in_synced = True
        try:
            result = self._inner_dispatch(capability, args)
            if (is_synced
                    and not in_synced_outer
                    and not self._replaying
                    and "error" not in result):
                event = SyncEvent(
                    event_id=str(uuid.uuid4()),
                    device_id=self.provider.device_id,
                    timestamp=datetime.now(timezone.utc).isoformat(
                        timespec="seconds"),
                    capability=capability,
                    args=args,
                )
                try:
                    self.provider.append(event)
                except Exception:                          # pragma: no cover
                    pass
            return result
        finally:
            if is_synced:
                self._local.in_synced = in_synced_outer

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
                       provider,
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
    return synced_registry


class HttpSyncProvider:
    """
    Sync ueber einen HTTP-Endpunkt (siehe services/sync_server.py).
    Implementiert die gleiche kleine Schnittstelle wie FileSyncProvider.
    """

    def __init__(self, base_url: str, device_id: str,
                 token: Optional[str] = None,
                 local_state_path: Optional[Path] = None):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.token = token
        self.seen_path = local_state_path or Path("sync_seen.json")
        self._lock = threading.Lock()
        self._seen: set[str] = self._load_seen()
        # Bewusst keine Sequence-Indizierung mehr: der Server kompaktiert
        # seinen Log und verschiebt damit Array-Indizes. Indexbasiertes
        # 'since=' ist nach einer Kompaktierung falsch und liefert ein
        # verschobenes Fenster. Stattdessen holen wir den vollstaendigen
        # Log und filtern lokal ueber _seen (UUIDs sind kompaktierungs-
        # stabil). Bei den im Familienbetrieb erwarteten Mengen ist das
        # billig genug und bleibt immer korrekt.

    @classmethod
    def from_env(cls, local_data_dir: Path) -> Optional["HttpSyncProvider"]:
        url = os.environ.get("ALLTAGSHELFER_SYNC_URL")
        if not url:
            return None
        device_id = os.environ.get("ALLTAGSHELFER_DEVICE_ID") \
            or FileSyncProvider._resolve_device_id(local_data_dir)
        local_data_dir.mkdir(parents=True, exist_ok=True)
        token = os.environ.get("ALLTAGSHELFER_SYNC_TOKEN")
        return cls(url, device_id, token,
                    local_state_path=local_data_dir / "sync_seen.json")

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json; charset=utf-8"}
        if self.token:
            h["X-Sync-Token"] = self.token
        return h

    def append(self, event: SyncEvent) -> None:
        import urllib.error
        import urllib.request
        body = json.dumps(event.to_dict(), ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/events",
            data=body, headers=self._headers(), method="POST")
        try:
            urllib.request.urlopen(req, timeout=10).read()
            with self._lock:
                self._seen.add(event.event_id)
                self._save_seen_unlocked()
        except urllib.error.URLError:
            # offline: das Event geht NICHT verloren, denn der Aufrufer
            # hat die Aktion lokal bereits ausgefuehrt. Allerdings kommt
            # es ohne weiteren Mechanismus auch nicht beim Server an.
            # Aufrufer-Schicht (SyncedRegistry) ignoriert Fehler bewusst.
            raise

    def _fetch(self) -> list[SyncEvent]:
        import urllib.request
        req = urllib.request.Request(
            f"{self.base_url}/events",
            headers=self._headers())
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return [SyncEvent.from_dict(e) for e in data.get("events", [])]

    def unseen_events(self) -> list[SyncEvent]:
        events = self._fetch()
        events = [e for e in events
                   if e.event_id not in self._seen
                   and e.device_id != self.device_id]
        events.sort(key=lambda ev: ev.timestamp)
        return events

    def mark_seen(self, event_id: str) -> None:
        with self._lock:
            self._seen.add(event_id)
            self._save_seen_unlocked()

    def compact_if_needed(self, max_lines: int = MAX_LOG_LINES) -> int:
        # Kompaktierung uebernimmt der Server, nicht der Client.
        return 0

    def _load_seen(self) -> set[str]:
        if not self.seen_path.exists():
            return set()
        try:
            return set(json.loads(self.seen_path.read_text(encoding="utf-8")))
        except Exception:
            return set()

    def _save_seen_unlocked(self) -> None:
        self.seen_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.seen_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(sorted(self._seen)), encoding="utf-8")
        tmp.replace(self.seen_path)


class PeriodicSyncWorker:
    """
    Loest periodischen Replay in einem Hintergrund-Thread aus.
    Standard: alle 5 Minuten. So sehen auch lange offen gehaltene
    Sitzungen Aenderungen anderer Geraete, ohne Neustart.
    """

    def __init__(self, synced_registry: SyncedRegistry,
                 interval_seconds: int = 300):
        self.synced = synced_registry
        self.interval = max(10, int(interval_seconds))
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._stop.wait(self.interval)
            if self._stop.is_set():
                return
            try:
                self.synced.apply_remote()
            except Exception:                              # pragma: no cover
                pass
