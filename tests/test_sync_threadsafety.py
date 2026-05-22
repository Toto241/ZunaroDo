"""
Regressionstest fuer den Replay-Thread-Safety-Bug in services.sync
(SyncedRegistry).

Frueher war 'replaying' ein gemeinsames bool: lief ein Replay im
Hintergrund-Worker, unterdrueckte ein GLEICHZEITIGER GUI-Dispatch eines
synced-Capabilities sein Logging -> die Nutzer-Aenderung wurde lokal
angewandt, aber nie ins Sync-Log geschrieben und somit nie an andere
Geraete propagiert. 'replaying' ist jetzt thread-lokal; dieser Test
deckt den Race deterministisch ab.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from services.sync import FileSyncProvider, SyncEvent, install_sync_hook

from tests.test_smoke import _build_system


class TestSyncReplayThreadSafety(unittest.TestCase):

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ah_sync_ts_"))
        self.shared = self.root / "shared"
        self.shared.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_concurrent_user_edit_during_replay_is_logged(self) -> None:
        # Ein entferntes Event, das beim Replay angewandt wird.
        writer = FileSyncProvider(str(self.shared), "dev-writer",
                                  local_seen_path=self.root / "w.json")
        writer.append(SyncEvent(
            event_id="e-remote", device_id="dev-writer",
            timestamp="2026-01-01T00:00:00",
            capability="finance.remember_price",
            args={"product": "Eier", "price": 2.0}, lamport=1))

        db, registry, _, dbpath = _build_system()
        try:
            reader = FileSyncProvider(str(self.shared), "dev-reader",
                                      local_seen_path=self.root / "r.json")
            synced = install_sync_hook(registry, reader)

            in_replay = threading.Event()
            gate = threading.Event()
            orig = synced._inner_dispatch

            def slow(cap, args):
                # Replay des entfernten Events mitten drin anhalten, damit
                # der Haupt-Thread waehrenddessen dispatchen kann.
                if (cap == "finance.remember_price"
                        and args.get("product") == "Eier"):
                    in_replay.set()
                    gate.wait(3)
                return orig(cap, args)

            synced._inner_dispatch = slow
            worker = threading.Thread(target=synced.apply_remote)
            worker.start()
            self.assertTrue(in_replay.wait(3), "Replay nicht gestartet")

            # Haupt-(GUI-)Thread: Nutzer bearbeitet einen ANDEREN Datensatz,
            # waehrend der Worker noch repliziert.
            synced.dispatch("finance.remember_price",
                            {"product": "Milch", "price": 1.0})

            gate.set()
            worker.join(5)

            logged = {(e.capability, e.args.get("product"))
                      for e in reader.read_all()}
            self.assertIn(
                ("finance.remember_price", "Milch"), logged,
                "Nutzer-Edit waehrend Replay wurde NICHT geloggt "
                "(Thread-Safety-Race in SyncedRegistry).")
        finally:
            db.close()
            os.unlink(dbpath)


if __name__ == "__main__":
    unittest.main()
