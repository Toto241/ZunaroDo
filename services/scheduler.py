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

import threading
import time
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

    def __init__(self, registry: ModuleRegistry,
                 notifier: Optional[Notifier] = None,
                 warn_within_days: int = 14,
                 interval_seconds: int = 3600,
                 extra_event_sources: Optional[Iterable[EventSource]] = None):
        self.registry = registry
        self.notifier = notifier or Notifier()
        self.warn_within_days = warn_within_days
        self.interval_seconds = interval_seconds
        self._extra_sources: list[EventSource] = list(extra_event_sources or [])
        self._seen: set[tuple[str, str]] = set()
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
            if key in self._seen:
                continue
            self._seen.add(key)
            d = ev.days_remaining
            when = (f"in {d} Tagen" if d > 0
                    else "heute faellig" if d == 0
                    else f"{-d} Tage ueberfaellig")
            self.notifier.notify(ev.title, f"{when} - {ev.module_name}")
            triggered.append(ev.title)
        return triggered

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
