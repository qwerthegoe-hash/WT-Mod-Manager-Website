"""No-network regression coverage for file scanning and VirusTotal lookup."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
import zipfile

from src import mod_security as sec


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class ModSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def write_zip(self, entries):
        target = self.folder / "mod.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as output:
            for name, value in entries:
                output.writestr(name, value)
        return target

    def test_known_safe_structure_and_hash(self):
        target = self.write_zip([
            ("sights/scope.png", b"image payload"),
            ("readme.txt", b"local mod"),
        ])
        report = sec.inspect_mod_file(target)
        self.assertTrue(report["zip"])
        self.assertEqual(report["files"], 2)
        self.assertEqual(len(report["sha256"]), 64)
        self.assertIn("не антивирусная", report["message"].lower())

    def test_reject_path_traversal(self):
        path = self.write_zip([("../escape.png", b"bad")])
        with self.assertRaises(sec.SecurityError):
            sec.inspect_mod_file(path)

    def test_reject_script_inside_zip(self):
        path = self.write_zip([("mod.bat", b"unknown")])
        with self.assertRaises(sec.SecurityError):
            sec.inspect_mod_file(path)

    def test_reject_compression_bomb(self):
        path = self.write_zip([("large.txt", b"x" * 100000)])
        with self.assertRaises(sec.SecurityError):
            sec.inspect_mod_file(path)

    def test_reject_non_zip_script(self):
        path = self.folder / "malware.ps1"
        path.write_bytes(b"hello")
        with self.assertRaises(sec.SecurityError):
            sec.inspect_mod_file(path)

    def test_known_file_is_not_claimed_innocent(self):
        target = self.folder / "mod.png"
        target.write_bytes(b"fake png")
        report = sec.inspect_mod_file(target)
        self.assertEqual(report["files"], 1)
        self.assertIn("не антивирусная", report["message"].lower())

    def test_unknown_hash_is_not_clean(self):
        opener = unittest.mock.Mock()
        opener.open.side_effect = HTTPError(
            "https://www.virustotal.com/api/v3/files/test", 404, "not found", {}, None
        )
        with patch("src.mod_security.urllib.request.build_opener", return_value=opener):
            result = sec.lookup_vt_sha256("a" * 64, api_key="k" * 64)
        self.assertFalse(result["known"])

    def test_rate_limit_error(self):
        opener = unittest.mock.Mock()
        opener.open.side_effect = HTTPError(
            "https://www.virustotal.com/api/v3/files/test", 429, "rate limit", {}, None
        )
        with patch("src.mod_security.urllib.request.build_opener", return_value=opener):
            with self.assertRaises(sec.VirusTotalError):
                sec.lookup_vt_sha256("a" * 64, api_key="k" * 64)

    def test_hash_only_request_and_counts(self):
        content = json.dumps({
            "data": {"attributes": {"last_analysis_stats": {
                "malicious": 1, "suspicious": 2, "harmless": 10, "undetected": 55
            }}}
        }).encode("utf-8")
        opener = unittest.mock.Mock()
        opener.open.return_value = FakeResponse(content)
        with patch("src.mod_security.urllib.request.build_opener", return_value=opener):
            report = sec.lookup_vt_sha256("f" * 64, api_key="k" * 64)
        self.assertEqual(report["malicious"], 1)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.method, "GET")
        self.assertTrue(request.full_url.endswith("/" + "f" * 64))
        self.assertNotIn("file", str(request.data))

    def test_never_persist_key_without_windows_dpapi(self):
        with patch.object(sec.sys, "platform", "linux"):
            with self.assertRaises(sec.VirusTotalError):
                sec.save_vt_key("a" * 64)


if __name__ == "__main__":
    unittest.main()
