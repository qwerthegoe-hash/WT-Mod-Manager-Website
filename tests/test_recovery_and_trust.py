"""Offline regression tests for crash reports, trust and safe updates."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src import crash_recovery, trust_center, update_checker


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        p1 = patch.object(crash_recovery, "SESSION_FILE", self.folder / "session.json")
        p2 = patch.object(crash_recovery, "CRASH_DIR", self.folder / "crashes")
        p3 = patch.object(crash_recovery, "_notice", None)
        for p in (p1, p2, p3):
            p.start()
            self.addCleanup(p.stop)

    def test_normal_shutdown_does_not_trigger_recovery(self):
        self.assertFalse(crash_recovery.start_session(updated=True))
        crash_recovery.clean_exit()
        self.assertFalse(crash_recovery.start_session(updated=False))

    def test_interrupted_update_is_suggested_not_auto_restored(self):
        self.assertFalse(crash_recovery.start_session(updated=True))
        result = crash_recovery.start_session()
        self.assertTrue(result["unclean"])
        self.assertTrue(result["after_update"])
        self.assertFalse(result["crashed"])

    def test_crash_record_has_no_exception_message_or_paths(self):
        crash_recovery.start_session()
        try:
            raise ValueError("PRIVATE_TOKEN=SECRET123")
        except ValueError as error:
            saved = crash_recovery.report_crash(type(error), error, error.__traceback__)
        self.assertIsNotNone(saved)
        report = json.loads(saved.read_text("utf-8"))
        self.assertEqual(report["type"], "ValueError")
        self.assertNotIn("PRIVATE_TOKEN", saved.read_text("utf-8"))
        self.assertNotIn(str(self.folder), saved.read_text("utf-8"))
        self.assertTrue(crash_recovery.start_session()["crashed"])


class TrustTests(unittest.TestCase):
    def test_hash_and_unsigned_signature_are_not_confused(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "WTModManager.exe"
            file.write_bytes(b"MZ" + b"X" * 200)
            with patch.object(trust_center.sys, "platform", "linux"):
                report = trust_center.local_executable_trust(file)
            self.assertEqual(len(report["sha256"]), 64)
            self.assertNotEqual(report["authenticode"], "Valid")
            self.assertIn("SHA-256", trust_center.format_local_trust(report))


class SmartUpdateTests(unittest.TestCase):
    def test_insufficient_disk_space_stops_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(update_checker, "DATA_DIR", Path(tmp)):
                with patch.object(update_checker, "repository", return_value=
                                  "qwerthegoe-hash/WT-Mod-Manager-Website"):
                    with patch.object(update_checker, "is_installed_app", return_value=False):
                        with patch.object(update_checker.shutil, "disk_usage",
                                          return_value=SimpleNamespace(free=1024)):
                            with self.assertRaisesRegex(OSError, "Недостаточно"):
                                update_checker.download_verified({
                                    "version": "v9.9.9-beta.2",
                                    "name": "WTModManager.exe",
                                    "kind": "portable",
                                    "url": "https://github.com/qwerthegoe-hash/"
                                           "WT-Mod-Manager-Website/releases/download/"
                                           "v9.9.9-beta.2/WTModManager.exe",
                                    "digest": "a" * 64,
                                    "size": 2 * 1024 * 1024,
                                })


if __name__ == "__main__":
    unittest.main()
