"""Automated regression tests for desktop account sync and safe file imports."""
import io
import sys
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from PySide6.QtCore import QCoreApplication
from unittest.mock import patch

from src.desktop_sync import (
    PackageError, _download_zip, _install_account_mod, _safe_entries,
    _protect, imported_library, restore_previous_mod, DesktopSync,
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

    def test_restore_previous_online_mod_version(self):
        with tempfile.TemporaryDirectory() as root:
            user = str(uuid.uuid4())
            mod = str(uuid.uuid4())
            with patch("src.desktop_sync.DATA_DIR", Path(root)):
                first = {"mod_id":mod,"title":"Original texture","category":"camouflage","version":"1.0"}
                second = {"mod_id":mod,"title":"Revised texture","category":"camouflage","version":"2.0"}
                before = archive([("texture.png", b"version-1")])
                after = archive([("texture.png", b"version-2")])
                self.assertEqual(_install_account_mod(user,first,before),1)
                self.assertEqual(_install_account_mod(user,second,after),1)
                saved = imported_library(user)[mod]
                self.assertEqual(saved["version"],"2.0")
                self.assertEqual(saved["previous"]["version"],"1.0")
                count, category = restore_previous_mod(user,mod)
                self.assertEqual((count,category),(1,"camouflage"))
                current = imported_library(user)[mod]
                self.assertEqual(current["version"],"1.0")
                self.assertNotIn("previous",current)
                asset = Path(root)/"accounts"/user/"mods"/"camouflages"/current["files"][0]
                self.assertEqual(asset.read_bytes(), b"version-1")
                with self.assertRaises(PackageError):
                    restore_previous_mod(user,mod)

    def test_old_network_result_does_not_reactivate_disconnected_account(self):
        app = QCoreApplication.instance() or QCoreApplication([])
        with patch("src.desktop_sync._load_token",return_value=None):
            sync = DesktopSync()
        sync._token = "new-device-token-" + "A"*45
        sync._on_completed(("poll","old-device-token",True,{
            "paired":True,"user_id":str(uuid.uuid4()),"changed":["sounds"]
        }))
        self.assertIsNone(sync.user_id)
        sync.stop()
        self.assertIsNotNone(app)

    def test_disconnect_queues_revocation_even_during_busy_poll(self):
        app = QCoreApplication.instance() or QCoreApplication([])
        with patch("src.desktop_sync._load_token",return_value=None):
            sync = DesktopSync()
        sync._token = "old-device-token-" + "B"*45
        sync._busy = True
        with tempfile.TemporaryDirectory() as folder:
            with patch("src.desktop_sync.SECRET_FILE",Path(folder)/"credential"):
                with patch.object(sync._pool,"submit") as submit:
                    sync.unlink_account()
                    self.assertTrue(submit.called)
                    self.assertEqual(submit.call_args.args[1],"revoke")
        self.assertIsNone(sync.user_id)
        self.assertIsNone(sync._token)
        sync.stop()
        self.assertIsNotNone(app)

    @unittest.skipUnless(sys.platform == "win32", "DPAPI only available on Windows")
    def test_device_secret_is_protected_by_windows(self):
        payload = b"hello-windows-dpapi"
        self.assertNotEqual(_protect(payload), payload)
        self.assertEqual(_protect(_protect(payload), decrypt=True), payload)


if __name__ == "__main__":
    unittest.main()
