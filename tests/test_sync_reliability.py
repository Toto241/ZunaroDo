from __future__ import annotations

import unittest

from services.sync import SyncEvent, SyncedRegistry


class _Provider:
    device_id = "local"

    def __init__(self, events=None, *, fail_append: bool = False):
        self.events = list(events or [])
        self.fail_append = fail_append
        self.appended: list[SyncEvent] = []
        self.marked: list[str] = []

    def append(self, event: SyncEvent) -> None:
        if self.fail_append:
            raise OSError("disk full")
        self.appended.append(event)

    def unseen_events(self) -> list[SyncEvent]:
        return list(self.events)

    def mark_seen(self, event_id: str) -> None:
        self.marked.append(event_id)

    def compact_if_needed(self) -> int:
        return 0


class TestSyncReliability(unittest.TestCase):

    def test_local_append_failure_is_reported(self) -> None:
        provider = _Provider(fail_append=True)
        synced = SyncedRegistry(
            registry=object(), provider=provider, synced={"family.add_member"},
            inner_dispatch=lambda _cap, _args: {"status": "ok"})

        result = synced.dispatch("family.add_member", {"name": "Anna"})

        self.assertEqual(result["status"], "ok")
        self.assertIn("sync_error", result)
        self.assertEqual(provider.appended, [])

    def test_failed_remote_event_is_not_marked_seen(self) -> None:
        event = SyncEvent(
            event_id="remote-1", device_id="remote",
            timestamp="2026-01-01T00:00:00+00:00",
            capability="family.add_member", args={})
        provider = _Provider([event])
        synced = SyncedRegistry(
            registry=object(), provider=provider, synced={"family.add_member"},
            inner_dispatch=lambda _cap, _args: {"error": "missing name"})

        self.assertEqual(synced.apply_remote(), 0)
        self.assertEqual(provider.marked, [])

    def test_successful_remote_event_is_marked_seen(self) -> None:
        event = SyncEvent(
            event_id="remote-2", device_id="remote",
            timestamp="2026-01-01T00:00:00+00:00",
            capability="family.add_member", args={"name": "Anna"})
        provider = _Provider([event])
        synced = SyncedRegistry(
            registry=object(), provider=provider, synced={"family.add_member"},
            inner_dispatch=lambda _cap, _args: {"status": "ok"})

        self.assertEqual(synced.apply_remote(), 1)
        self.assertEqual(provider.marked, ["remote-2"])


if __name__ == "__main__":
    unittest.main()
