"""Automated regression tests for desktop account sync and safe file imports."""
import io
import sys
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

from src.desktop_sync import (
    PackageError, _download_zip, _install_account_mod, _safe_entries,
    _protect, imported_library,
)


def archive(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as zipper:
        for name, data in entries:
            zipper.writestr(name, data)
    return stream.getvalue()


class DesktopSyncTests(unittest.TestCase):
    def test_reject_traversal(self):
        with self.assertRaises(PackageError):
            _safe_entries(archive([("../outside.png", b"bad")]), "sights")

    def test_reject_executable_only_archives(self):
        with self.assertRaises(PackageError):
            _safe_entries(archive([("installer.exe", b"bad")]), "camouflage")

    def test_reject_broken_zip(self):
        with self.assertRaises(PackageError):
            _safe_entries(b"not a zip", "sounds")

    def test_reject_external_url_without_network(self):
        with self.assertRaises(PackageError):
            _download_zip("https://evil.example/storage/v1/object/sign/wtmm-mod-packages/a")

    def test_import_is_per_user_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as root:
            user_one = str(uuid.uuid4())
            user_two = str(uuid.uuid4())
            mod = str(uuid.uuid4())
            meta = {"mod_id":mod,"title":"Demo texture", "category":"camouflage","version":"1.0"}
            content = archive([("assets/demo.png", b"test image bytes")])
            with patch("src.desktop_sync.DATA_DIR", Path(root)):
                first = _install_account_mod(user_one, meta, content)
                again = _install_account_mod(user_one, meta, content)
                separate = _install_account_mod(user_two, meta, content)
                self.assertEqual(first, 1)
                self.assertEqual(again, 0)
                self.assertEqual(separate, 1)
                folder1 = Path(root) / "accounts" / user_one / "mods" / "camouflages"
                folder2 = Path(root) / "accounts" / user_two / "mods" / "camouflages"
                self.assertEqual(len(list(folder1.glob("*.png"))), 1)
                self.assertEqual(len(list(folder2.glob("*.png"))), 1)
                self.assertEqual(len(imported_library(user_one)), 1)
                self.assertEqual(len(imported_library(user_two)), 1)

    @unittest.skipUnless(sys.platform == "win32", "DPAPI only available on Windows")
    def test_device_secret_is_protected_by_windows(self):
        payload = b"hello-windows-dpapi"
        self.assertNotEqual(_protect(payload), payload)
        self.assertEqual(_protect(_protect(payload), decrypt=True), payload)


if __name__ == "__main__":
    unittest.main()
