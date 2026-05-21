"""
Determinismus der Sync-Konfliktaufloesung (R5).

Wenn zwei Geraete denselben Datensatz mit demselben Lamport-Wert
bearbeiten, muss das Ergebnis reproduzierbar sein: der Tie-Break laeuft
ueber die device_id (alphabetisch), unabhaengig von der Reihenfolge, in
der die Events im geteilten Log landen. Last-Write-Wins liefert damit auf
allen Geraeten denselben Endzustand.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from services.sync import FileSyncProvider, SyncEvent, install_sync_hook

from tests.test_smoke import _build_system

_TS = "2026-05-21T10:00:00"
_PRICES = {"dev-a": 1.0, "dev-b": 2.0}


def _price_event(dev: str, lamport: int = 5, ts: str = _TS) -> SyncEvent:
    """Beide Events treffen denselben Datensatz (Produkt 'Milch')."""
    return SyncEvent(event_id=f"e-{dev}", device_id=dev, timestamp=ts,
                     capability="finance.remember_price",
                     args={"product": "Milch", "price": _PRICES[dev]},
                     lamport=lamport)


class TestSyncConflictDeterminism(unittest.TestCase):

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ah_conflict_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _seed(self, shared: Path, order: list[str]) -> None:
        """Schreibt die zwei konkurrierenden Events in der gegebenen
        Reihenfolge ins geteilte Log (jeder Writer mit eigenem seen-File)."""
        for dev in order:
            writer = FileSyncProvider(
                str(shared), dev,
                local_seen_path=self.root / f"seen-{dev}.json")
            writer.append(_price_event(dev))

    def test_unseen_events_tiebreak_is_order_independent(self) -> None:
        # Gleicher Lamport + Timestamp -> device_id entscheidet; 'dev-b' kommt
        # zuletzt (LWW-Gewinner), egal in welcher Reihenfolge geloggt wurde.
        for i, order in enumerate((["dev-a", "dev-b"], ["dev-b", "dev-a"])):
            shared = self.root / f"shared-{i}"
            shared.mkdir()
            self._seed(shared, order)
            reader = FileSyncProvider(
                str(shared), "dev-reader",
                local_seen_path=self.root / f"reader-{i}.json")
            seq = [e.device_id for e in reader.unseen_events()]
            self.assertEqual(seq, ["dev-a", "dev-b"], f"Reihenfolge {order}")

    def test_concurrent_edit_same_record_resolves_deterministically(self) -> None:
        # End-to-End: egal in welcher Reihenfolge die Events ankommen, der
        # Endzustand ist der Wert des alphabetisch letzten Geraets (dev-b).
        for i, order in enumerate((["dev-a", "dev-b"], ["dev-b", "dev-a"])):
            shared = self.root / f"e2e-{i}"
            shared.mkdir()
            self._seed(shared, order)
            db, registry, _, dbpath = _build_system()
            try:
                reader = FileSyncProvider(
                    str(shared), "dev-reader",
                    local_seen_path=self.root / f"e2e-reader-{i}.json")
                synced = install_sync_hook(registry, reader)
                synced.apply_remote()
                pm = registry.dispatch("finance.price_memory", {})
                milch = next(p for p in pm["products"]
                             if p["product"] == "Milch")
                self.assertEqual(milch["last_price"], 2.0,
                                 f"Reihenfolge {order}")
            finally:
                db.close()
                os.unlink(dbpath)


if __name__ == "__main__":
    unittest.main()
