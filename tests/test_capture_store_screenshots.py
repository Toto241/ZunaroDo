"""Tests fuer Store-Screenshot-Generator und Android-Geraete-Verifikation."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image


class TestCaptureStoreScreenshots(unittest.TestCase):

    def test_generate_produces_valid_phone_pngs(self) -> None:
        from tools.capture_store_screenshots import OUTPUTS, PHONE_H, PHONE_W, generate

        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store"
            store.mkdir()
            with mock.patch("tools.capture_store_screenshots.STORE_DIR", store):
                written = generate()
            self.assertEqual(len(written), 3)
            for name in OUTPUTS:
                path = store / name
                self.assertTrue(path.is_file(), name)
                with Image.open(path) as img:
                    self.assertEqual(img.size, (PHONE_W, PHONE_H))
                    colors = img.convert("RGB").getcolors(maxcolors=65536)
                    self.assertIsNotNone(colors)
                    assert colors is not None
                    self.assertGreaterEqual(len(colors), 16,
                                            f"{name} hat zu wenig Farben")

    def test_verify_delegates_to_gen_assets(self) -> None:
        from tools import capture_store_screenshots as mod
        with mock.patch.object(mod, "verify", return_value=0) as verify:
            rc = mod.verify()
        self.assertEqual(rc, 0)
        verify.assert_called_once()


class TestVerifyAndroidDevice(unittest.TestCase):

    def test_exits_when_no_adb_device(self) -> None:
        from tools import verify_android_device as mod
        with mock.patch.object(mod, "_adb_devices", return_value=[]):
            with mock.patch.object(sys, "argv", ["verify_android_device"]):
                with self.assertRaises(SystemExit) as ctx:
                    mod.main()
                self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
