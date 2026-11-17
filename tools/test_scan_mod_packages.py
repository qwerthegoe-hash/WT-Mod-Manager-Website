"""Regression tests for the server-side mod archive quarantine worker."""
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from scan_mod_packages import UnsafeArchive, clamav_clean, validate_zip


def write_archive(destination, members):
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, body in members:
            archive.writestr(name, body)


class PackageScannerTests(unittest.TestCase):
    def check_archive(self, members):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "mod.zip"
            write_archive(path, members)
            return validate_zip(path)

    def test_safe_archive_with_directory(self):
        self.assertEqual(self.check_archive([
            ("textures/", b""),
            ("textures/example.png", b"example"),
            ("readme.txt", b"ok"),
        ]), 3)

    def test_reject_parent_path(self):
        with self.assertRaises(UnsafeArchive):
            self.check_archive([("../unexpected.txt", b"x")])

    def test_reject_absolute_path(self):
        with self.assertRaises(UnsafeArchive):
            self.check_archive([("/outside.txt", b"x")])

    def test_reject_duplicate_name_ignoring_case(self):
        with self.assertRaises(UnsafeArchive):
            self.check_archive([("TEXTURE.bin", b"a"), ("texture.bin", b"b")])

    def test_reject_invalid_compressed_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "broken.zip"
            path.write_bytes(b"not a ZIP file")
            with self.assertRaises(UnsafeArchive):
                validate_zip(path)

    @patch("scan_mod_packages.subprocess.run")
    def test_antivirus_clean_only_on_success(self, runner):
        runner.return_value.returncode = 0
        self.assertTrue(clamav_clean(Path("/tmp/sample.zip")))
        runner.return_value.returncode = 1
        self.assertFalse(clamav_clean(Path("/tmp/sample.zip")))
        runner.return_value.returncode = 2
        with self.assertRaises(RuntimeError):
            clamav_clean(Path("/tmp/sample.zip"))


if __name__ == "__main__":
    unittest.main()
