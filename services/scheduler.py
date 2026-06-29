"""
Proaktiver Scheduler.

Loest das Konzept-Leitprinzip "proaktiv statt reaktiv" ein. Im Hinter-
grund laeuft ein APScheduler, der periodisch alle Module ueber
`registry.collect_events()` abfragt und Ereignisse, die naeher rueckend
sind, ueber den Notifier meldet.

Ohne 'apscheduler' im System faellt der Dienst auf eine simple
Thread-Schleife zurueck, sodass die Demo auch ohne Extra-Paket startet.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Callable, Iterable, Optional

from core.interface import ModuleRegistry
from models import Event
from services.notifier import Notifier


# Signatur eines Extra-Event-Sources: bekommt warn_within_days,
# liefert eine Liste von Event-Objekten. Wird z.B. von
# services.license_events.license_event_source genutzt, um
# Renewal-/Karenz-Warnungen einzuspielen.
EventSource = Callable[[int], list[Event]]


class ProactiveScheduler:
    """Periodischer Check anstehender Ereignisse mit Notifikation."""

    STATE_FILE_NAME = "reminder_seen.json"

    def __init__(self, registry: ModuleRegistry,
                 notifier: Optional[Notifier] = None,
                 warn_within_days: int = 14,
                 interval_seconds: int = 3600,
                 extra_event_sources: Optional[Iterable[EventSource]] = None,
                 state_path: Optional[Path] = None):
        self.registry = registry
        self.notifier = notifier or Notifier()
        self.warn_within_days = warn_within_days
        self.interval_seconds = interval_seconds
        self._extra_sources: list[EventSource] = list(extra_event_sources or [])
        # Marker bewusst zeit-/datumsfrei (module_id, title): so loest ein
        # System-/Zeitzonen-Sprung (DST) keine erneute Meldung aus.
        self.state_path = Path(state_path) if state_path else None
        self._seen: set[tuple[str, str]] = self._load_seen()
        # check_now() laeuft sowohl aus dem APScheduler-/Fallback-Thread als
        # auch manuell aus dem UI ("jetzt pruefen"). Ohne Sperre koennten zwei
        # ueberlappende Laeufe dieselbe Erinnerung doppelt melden (beide sehen
        # key noch nicht in _seen) und _persist_seen koennte ueber _seen
        # iterieren waehrend ein anderer Thread es mutiert ("set changed size").
        self._seen_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._aps = None                              # APScheduler-Instanz

    # ---- Steuerung -----------------------------------------------------
    def start(self) -> str:
        """Startet den Scheduler. Liefert den verwendeten Modus."""
        if self._try_start_apscheduler():
            return "apscheduler"
        # Fallback: simpler Thread
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return "thread"

    def stop(self) -> None:
        if self._aps is not None:
            try:
                self._aps.shutdown(wait=False)
            except Exception:                          # pragma: no cover
                pass
            self._aps = None
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def check_now(self) -> list[str]:
        """Einmaliger Check. Liefert die ausgeloesten Notifikations-Titel."""
        triggered: list[str] = []
        events = list(self.registry.collect_events(self.warn_within_days))
        for source in self._extra_sources:
            try:
                events.extend(source(self.warn_within_days))
            except Exception:                          # pragma: no cover
                continue
        for ev in events:
            key = (ev.module_id, ev.title)
            with self._seen_lock:
                if key in self._seen:
                    continue
                self._seen.add(key)
            d = ev.days_remaining
            when = (f"in {d} Tagen" if d > 0
                    else "heute faellig" if d == 0
                    else f"{-d} Tage ueberfaellig")
            self.notifier.notify(ev.title, f"{when} - {ev.module_name}")
            triggered.append(ev.title)
        if triggered:
            self._persist_seen()
        return triggered

    # ---- Persistenz der gesehenen Marker ------------------------------
    def _load_seen(self) -> set[tuple[str, str]]:
        """Laedt die persistierten Marker. Fehlt/kaputt -> leere Menge,
        damit ein Defekt nie den Start blockiert."""
        if not self.state_path or not self.state_path.exists():
            return set()
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            return {(str(m), str(t)) for m, t in data}
        except (json.JSONDecodeError, ValueError, TypeError, OSError):
            return set()

    def _persist_seen(self) -> None:
        """Schreibt die Marker atomar (tmp + replace), damit ein Absturz
        keine halbe Datei hinterlaesst."""
        if not self.state_path:
            return
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            with self._seen_lock:
                payload = sorted([m, t] for m, t in self._seen)
            tmp = self.state_path.with_name(self.state_path.name + ".tmp")
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            tmp.replace(self.state_path)
        except OSError:                                # pragma: no cover
            pass

    # ---- intern --------------------------------------------------------
    def _try_start_apscheduler(self) -> bool:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except Exception:
            return False
        from datetime import datetime, timedelta
        sched = BackgroundScheduler(daemon=True)
        # Reglaer alle 'interval_seconds' Sekunden; der erste Lauf
        # erfolgt explizit in 2 Sekunden, damit das Verhalten ueber
        # alle APScheduler-Versionen hinweg identisch ist.
        first_run = datetime.now() + timedelta(seconds=2)
        sched.add_job(self.check_now, "interval",
                      seconds=self.interval_seconds,
                      next_run_time=first_run)
        sched.start()
        self._aps = sched
        return True

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self.check_now()
            self._stop_event.wait(self.interval_seconds)
