"""Offline regression tests for privacy-safe diagnostics, rollback and shared notifications."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import diagnostics
from src import portable_updater


class DiagnosticsTests(unittest.TestCase):
    def test_check_codes_and_reports_never_include_private_directories(self):
        with tempfile.TemporaryDirectory() as home:
            root = Path(home)
            data = root / "User Secret Path"
            mods = root / "Local Mods"
            mods.mkdir()
            config = root / "config"
            config.mkdir()
            (config / "update_config.json").write_text(json.dumps({
                "github_repository": "qwerthegoe-hash/WT-Mod-Manager-Website"
            }), encoding="utf-8")
            (data / "settings.json").parent.mkdir(parents=True)
            (data / "settings.json").write_text('{"theme":"blue"}', encoding="utf-8")
            with patch("src.diagnostics.profile_paths.DATA_DIR", data), \
                 patch("src.diagnostics.profile_paths.SETTINGS_FILE", data / "settings.json"), \
                 patch("src.diagnostics.profile_paths.MODS_DIR", mods), \
                 patch("src.diagnostics.profile_paths.PROJECT_ROOT", root), \
                 patch("src.portable_updater.previous_exe_available", return_value=False), \
                 patch("src.desktop_sync._load_token", return_value=None):
                checks = diagnostics.inspect_local()
            codes = {check.code for check in checks}
            self.assertEqual(codes, {f"D{i:03}" for i in range(1, 10)})
            report = diagnostics.format_report(checks)
            self.assertNotIn("User Secret Path", report)
            self.assertNotIn("Local Mods", report)
            self.assertIn("D001 [OK]", report)
            self.assertIn("D008 [WARN]", report)
            self.assertIn("D009 [OK]", report)
            self.assertFalse((data / ".wtmm-diagnostic-write.tmp").exists())

    def test_bad_settings_are_reported_not_executed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / "settings.json"
            file.write_text("{ this is not JSON }", encoding="utf-8")
            with patch("src.diagnostics.profile_paths.DATA_DIR", root), \
                 patch("src.diagnostics.profile_paths.SETTINGS_FILE", file), \
                 patch("src.diagnostics.profile_paths.MODS_DIR", root), \
                 patch("src.diagnostics.profile_paths.PROJECT_ROOT", root), \
                 patch("src.portable_updater.previous_exe_available", return_value=False), \
                 patch("src.desktop_sync._load_token", return_value=None):
                entries = diagnostics.inspect_local()
            self.assertEqual(next(x.status for x in entries if x.code == "D002"), "ERROR")


class PortableRollbackTests(unittest.TestCase):
    def test_sha_verified_backups_are_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            binary = directory / "WTModManager.previous.exe"
            content = b"MZ" + b"A" * (1024 * 1024)
            binary.write_bytes(content)
            (directory / "WTModManager.previous.sha256").write_text(
                hashlib.sha256(content).hexdigest(),encoding="ascii")
            with patch("src.portable_updater.UPDATES", directory):
                self.assertTrue(portable_updater.previous_exe_available())
                binary.write_bytes(content + b"TAMPERED")
                self.assertFalse(portable_updater.previous_exe_available())
                self.assertFalse((directory / "WTModManager.rollback-helper.exe").exists())

    def test_malicious_backup_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / "WTModManager.previous.exe").write_bytes(
                b"MZ" + b"A" * (1024 * 1024))
            (directory / "WTModManager.previous.sha256").write_text(
                "no-valid-digest",encoding="ascii")
            with patch("src.portable_updater.UPDATES", directory):
                self.assertFalse(portable_updater.previous_exe_available())


if __name__ == "__main__":
    unittest.main()
