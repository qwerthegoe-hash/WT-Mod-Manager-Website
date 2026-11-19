"""Offline regression coverage for per-user settings backup and safe legacy migration."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import profile_paths, settings_store


class SettingsRecoveryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.data = self.root / "private"
        self.settings = self.data / "settings.json"
        self.backup = self.data / "settings.json.bak"
        self.data.mkdir()
        self.patchers = [
            patch.object(settings_store, "DATA_DIR", self.data),
            patch.object(settings_store, "SETTINGS_FILE", self.settings),
            patch.object(settings_store, "SETTINGS_BACKUP_FILE", self.backup),
            patch.object(settings_store, "migrate_legacy_data", return_value=None),
        ]
        for item in self.patchers:
            item.start()
            self.addCleanup(item.stop)

    def test_corrupt_primary_uses_previous_backup_without_rewriting(self):
        settings_store.save_settings({"language": "uk"})
        self.assertFalse(self.backup.exists())
        settings_store.save_settings({"theme": "purple"})
        old = json.loads(self.backup.read_text("utf-8"))
        self.assertEqual(old["language"], "uk")
        self.assertEqual(old["theme"], "blue")

        self.settings.write_text('{"language":', encoding="utf-8")
        recovered = settings_store.load_settings()
        self.assertEqual(recovered["language"], "uk")
        self.assertEqual(recovered["theme"], "blue")
        self.assertEqual(self.settings.read_text("utf-8"), '{"language":')

        settings_store.save_settings({"preview_volume": 42})
        self.assertEqual(json.loads(self.settings.read_text("utf-8"))["preview_volume"], 42)
        self.assertEqual(json.loads(self.backup.read_text("utf-8")), old)

    def test_missing_primary_can_use_existing_backup(self):
        self.backup.write_text('{"theme":"green","language":"pl"}', encoding="utf-8")
        self.assertEqual(settings_store.load_settings()["theme"], "green")
        self.assertFalse(self.settings.exists())

    def test_corrupt_primary_and_backup_use_defaults(self):
        self.settings.write_text("{invalid", encoding="utf-8")
        self.backup.write_text("[]", encoding="utf-8")
        result = settings_store.load_settings()
        self.assertEqual(result["language"], settings_store.DEFAULT_SETTINGS["language"])
        self.assertEqual(self.settings.read_text("utf-8"), "{invalid")

    def test_backup_failure_does_not_replace_primary_or_leave_temps(self):
        settings_store.save_settings({"language": "uk"})
        old = self.settings.read_bytes()
        with patch.object(settings_store.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                settings_store.save_settings({"language": "fr"})
        self.assertEqual(self.settings.read_bytes(), old)
        self.assertFalse(self.backup.exists())
        self.assertEqual(list(self.data.glob("settings_*.tmp")), [])

    def test_failed_primary_replace_leaves_previous_primary_and_backup(self):
        settings_store.save_settings({"language": "uk"})
        old = self.settings.read_bytes()
        actual_replace = settings_store.os.replace

        def reject_primary(source, target):
            if Path(target) == self.settings:
                raise OSError("interrupted before commit")
            return actual_replace(source, target)

        with patch.object(settings_store.os, "replace", side_effect=reject_primary):
            with self.assertRaises(OSError):
                settings_store.save_settings({"theme": "red"})
        self.assertEqual(self.settings.read_bytes(), old)
        self.assertEqual(json.loads(self.backup.read_text("utf-8"))["language"], "uk")
        self.assertEqual(list(self.data.glob("settings_*.tmp")), [])


class LegacyMigrationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.legacy_data = self.root / "legacy-data"
        self.legacy_mods = self.root / "legacy-mods"
        self.data = self.root / "private"
        self.settings = self.data / "settings.json"
        self.mods = self.data / "mods"
        self.marker = self.data / ".migration-v1-complete"
        for item in [
            patch.object(profile_paths, "DATA_DIR", self.data),
            patch.object(profile_paths, "SETTINGS_FILE", self.settings),
            patch.object(profile_paths, "MODS_DIR", self.mods),
            patch.object(profile_paths, "LEGACY_DATA", self.legacy_data),
            patch.object(profile_paths, "LEGACY_MODS", self.legacy_mods),
        ]:
            item.start()
            self.addCleanup(item.stop)

    def test_interrupted_legacy_settings_copy_retries_without_partial_file(self):
        self.legacy_data.mkdir()
        (self.legacy_data / "settings.json").write_text(
            '{"language":"uk"}', encoding="utf-8")
        with patch.object(profile_paths.shutil, "copyfileobj", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                profile_paths.migrate_legacy_data()
        self.assertFalse(self.settings.exists())
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.data.glob(".wtmm-migrate-*.tmp")), [])

        profile_paths.migrate_legacy_data()
        self.assertEqual(json.loads(self.settings.read_text("utf-8"))["language"], "uk")
        self.assertTrue(self.marker.exists())
        self.assertTrue((self.legacy_data / "settings.json").exists())

    def test_interrupted_mod_copy_retries_without_overwriting_user_files(self):
        source = self.legacy_mods / "sounds"
        source.mkdir(parents=True)
        (source / "one.wav").write_bytes(b"original")
        with patch.object(profile_paths.shutil, "copyfileobj", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                profile_paths.migrate_legacy_data()
        self.assertFalse((self.mods / "sounds" / "one.wav").exists())
        self.assertFalse(self.marker.exists())
        profile_paths.migrate_legacy_data()
        copied = self.mods / "sounds" / "one.wav"
        self.assertEqual(copied.read_bytes(), b"original")
        copied.write_bytes(b"user-edited")
        self.marker.unlink()
        profile_paths.migrate_legacy_data()
        self.assertEqual(copied.read_bytes(), b"user-edited")

    def test_existing_user_settings_win_over_legacy(self):
        self.data.mkdir()
        self.legacy_data.mkdir()
        self.settings.write_text('{"language":"de"}', encoding="utf-8")
        (self.legacy_data / "settings.json").write_text(
            '{"language":"en"}', encoding="utf-8")
        profile_paths.migrate_legacy_data()
        self.assertEqual(json.loads(self.settings.read_text("utf-8"))["language"], "de")
        self.assertTrue(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
