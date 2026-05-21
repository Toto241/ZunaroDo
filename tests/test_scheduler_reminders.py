"""
Erinnerungs- und Benachrichtigungstests (Anforderung R2).

Deckt das proaktive Ausloesen von Erinnerungen ueber den
``ProactiveScheduler`` ab: korrekte Faelligkeits-Formulierung relativ
zur Systemzeit (zukuenftig / heute / ueberfaellig), das Ausloesen
mehrerer faelliger Ereignisse sowie die Deduplizierung, damit eine
einmal gemeldete Erinnerung nicht bei jedem Folge-Check (z. B. nach
einem Neustart-bedingten erneuten Lauf) erneut feuert.

Diese Tests schliessen eine Luecke im bisherigen Bestand: das
Scheduler-Verhalten wurde nur fuer Lizenz-Events geprueft, nicht fuer
die eigentliche Erinnerungs-Mechanik der Module.
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from core.interface import ModuleRegistry
from models import Event
from services.notifier import Notifier
from services.scheduler import ProactiveScheduler


class _RecordingNotifier(Notifier):
    """Notifier-Doppel, das alle Meldungen sammelt statt sie anzuzeigen."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, str]] = []

    def notify(self, title: str, message: str = "") -> None:  # noqa: A003
        self.calls.append((title, message))


def _event_source(events: list[Event]):
    """Baut eine EventSource-Callable, die feste Events zurueckgibt."""
    def _source(_warn_within_days: int) -> list[Event]:
        return list(events)
    return _source


def _make_event(title: str, days_remaining: int) -> Event:
    return Event(
        title=title,
        due_date=date.today() + timedelta(days=days_remaining),
        module_id="calendar",
        module_name="Termine & Kalender",
        category="erinnerung",
        days_remaining=days_remaining,
    )


class TestReminderTriggering(unittest.TestCase):

    def _scheduler(self, events: list[Event]) -> tuple[
            ProactiveScheduler, _RecordingNotifier]:
        notifier = _RecordingNotifier()
        sched = ProactiveScheduler(
            ModuleRegistry(),                      # keine Modul-Events
            notifier=notifier, warn_within_days=14,
            extra_event_sources=[_event_source(events)])
        return sched, notifier

    def test_future_event_phrasing(self) -> None:
        sched, notifier = self._scheduler([_make_event("TUEV faellig", 5)])
        triggered = sched.check_now()
        self.assertEqual(triggered, ["TUEV faellig"])
        self.assertIn("in 5 Tagen", notifier.calls[0][1])

    def test_today_event_phrasing(self) -> None:
        sched, notifier = self._scheduler([_make_event("Geburtstag", 0)])
        sched.check_now()
        self.assertIn("heute faellig", notifier.calls[0][1])

    def test_overdue_event_phrasing(self) -> None:
        sched, notifier = self._scheduler([_make_event("Steuer", -3)])
        sched.check_now()
        self.assertIn("ueberfaellig", notifier.calls[0][1])

    def test_multiple_due_events_all_trigger(self) -> None:
        sched, notifier = self._scheduler([
            _make_event("Termin A", 1),
            _make_event("Termin B", 2),
            _make_event("Termin C", 7),
        ])
        triggered = sched.check_now()
        self.assertEqual(set(triggered), {"Termin A", "Termin B", "Termin C"})
        self.assertEqual(len(notifier.calls), 3)

    def test_reminder_not_repeated_on_recheck(self) -> None:
        # Eine einmal gemeldete Erinnerung darf bei einem erneuten Check
        # (z. B. naechster Scheduler-Tick) nicht erneut feuern.
        sched, notifier = self._scheduler([_make_event("Garantie", 4)])
        sched.check_now()
        notifier.calls.clear()
        sched.check_now()
        self.assertEqual(notifier.calls, [])

    def test_new_event_after_first_check_still_fires(self) -> None:
        # Dedup darf nur fuer bereits gesehene Erinnerungen greifen -
        # ein neu hinzugekommenes Ereignis muss weiterhin melden.
        events = [_make_event("Erste", 3)]
        notifier = _RecordingNotifier()
        sched = ProactiveScheduler(
            ModuleRegistry(), notifier=notifier, warn_within_days=14,
            extra_event_sources=[_event_source(events)])
        sched.check_now()
        notifier.calls.clear()
        events.append(_make_event("Zweite", 6))
        triggered = sched.check_now()
        self.assertEqual(triggered, ["Zweite"])


class TestReminderPersistence(unittest.TestCase):
    """Gesehene Marker ueberleben einen Neustart und sind robust gegen
    System-/Zeitzonen-Spruenge (R2)."""

    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="ah_sched_"))
        self.state_path = self.dir / ProactiveScheduler.STATE_FILE_NAME

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def _scheduler(self, events: list[Event]) -> tuple[
            ProactiveScheduler, _RecordingNotifier]:
        notifier = _RecordingNotifier()
        sched = ProactiveScheduler(
            ModuleRegistry(), notifier=notifier, warn_within_days=14,
            extra_event_sources=[_event_source(events)],
            state_path=self.state_path)
        return sched, notifier

    def test_seen_markers_survive_restart(self) -> None:
        events = [_make_event("TUEV faellig", 5)]
        sched1, notifier1 = self._scheduler(events)
        self.assertEqual(sched1.check_now(), ["TUEV faellig"])
        self.assertTrue(self.state_path.exists())
        # "Neustart": frische Instanz mit demselben State-Pfad.
        sched2, notifier2 = self._scheduler(events)
        self.assertEqual(sched2.check_now(), [])
        self.assertEqual(notifier2.calls, [])

    def test_clock_change_does_not_resend(self) -> None:
        # Erst melden, dann simulieren wir einen Zeitsprung, indem sich
        # die verbleibenden Tage aendern (z. B. DST/Datumswechsel). Da der
        # Marker datumsfrei ist, darf dieselbe Erinnerung nicht erneut
        # feuern - auch nicht nach einem Neustart.
        sched1, _ = self._scheduler([_make_event("Garantie", 4)])
        sched1.check_now()
        sched2, notifier2 = self._scheduler([_make_event("Garantie", 3)])
        self.assertEqual(sched2.check_now(), [])
        self.assertEqual(notifier2.calls, [])

    def test_new_event_after_restart_still_fires(self) -> None:
        sched1, _ = self._scheduler([_make_event("Alt", 2)])
        sched1.check_now()
        sched2, notifier2 = self._scheduler([
            _make_event("Alt", 2), _make_event("Neu", 6)])
        self.assertEqual(sched2.check_now(), ["Neu"])

    def test_corrupt_state_file_is_ignored(self) -> None:
        self.state_path.write_text("nicht-json{", encoding="utf-8")
        sched, notifier = self._scheduler([_make_event("Steuer", 1)])
        # Defekte Datei -> leere Menge -> Meldung feuert dennoch.
        self.assertEqual(sched.check_now(), ["Steuer"])

    def test_without_state_path_refires_after_restart(self) -> None:
        # Ohne Persistenzpfad bleibt das alte In-Memory-Verhalten: ein
        # "Neustart" verliert die Marker und meldet erneut.
        events = [_make_event("Fluechtig", 3)]
        n1 = _RecordingNotifier()
        ProactiveScheduler(ModuleRegistry(), notifier=n1, warn_within_days=14,
                           extra_event_sources=[_event_source(events)]
                           ).check_now()
        n2 = _RecordingNotifier()
        triggered = ProactiveScheduler(
            ModuleRegistry(), notifier=n2, warn_within_days=14,
            extra_event_sources=[_event_source(events)]).check_now()
        self.assertEqual(triggered, ["Fluechtig"])


if __name__ == "__main__":
    unittest.main()
