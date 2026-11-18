"""Offline tests for verified portable Windows update discovery and downloads."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import update_checker


class DownloadResponse(io.BytesIO):
    def __init__(self, content, url):
        super().__init__(content)
        self._url = url
        self.headers = {}

    def geturl(self):
        return self._url


class PortableUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        conf = self.root / "config.json"
        conf.write_text(json.dumps({
            "github_repository":"qwerthegoe-hash/WT-Mod-Manager-Website",
            "channel":"beta"
        }), encoding="utf-8")
        patches = [
            patch("src.update_checker.CONFIG_FILE",conf),
            patch("src.update_checker.DATA_DIR",self.root)
        ]
        for patched in patches:
            patched.start()
            self.addCleanup(patched.stop)

    @staticmethod
    def fixture(tag="v1.3.0-beta.2", digest="a"*64, size=2000000, prerelease=True):
        url = ("https://github.com/qwerthegoe-hash/WT-Mod-Manager-Website/"
               "releases/download/" + tag + "/WTModManager.exe")
        return {
            "tag_name":tag,"draft":False,"prerelease":prerelease,
            "assets":[{"name":"WTModManager.exe","size":size,
                       "digest":"sha256:"+digest,"browser_download_url":url}]
        }

    def test_versions_and_pre_release_order(self):
        compare = update_checker.version_tuple
        self.assertLess(compare("v1.3.0-beta.1"), compare("1.3.0-beta.2"))
        self.assertLess(compare("1.3.0-rc.1"), compare("1.3.0"))
        self.assertLess(compare("1.3.0-beta.100"), compare("1.3.0"))
        self.assertIsNone(compare("latest"))

    def test_discover_best_approved_release(self):
        beta = self.fixture("v1.3.0-beta.2")
        new = self.fixture("v1.4.0-beta.1", digest="b"*64)
        wrong = self.fixture("v1.6.0-beta.1")
        wrong["assets"][0]["browser_download_url"] = "https://evil.example/WTModManager.exe"
        with patch("src.update_checker._api_json", return_value=[wrong,beta,new]):
            found = update_checker.find_update()
        self.assertEqual(found["version"],"v1.4.0-beta.1")
        self.assertEqual(found["digest"],"b"*64)
        self.assertNotIn("_sort_key",found)

    def test_stable_channel_filters_prereleases(self):
        with patch("src.update_checker.update_channel",return_value="stable"):
            self.assertIsNone(update_checker._release_candidate(
                self.fixture("v1.4.0-beta.1"),update_checker.repository()))
            stable = self.fixture("v1.4.0",prerelease=False)
            self.assertIsNotNone(update_checker._release_candidate(
                stable,update_checker.repository()))

    def test_strict_digest_required(self):
        entry = self.fixture(digest="bad")
        self.assertIsNone(update_checker._release_candidate(
            entry,update_checker.repository()))

    def test_download_sha_verified_before_replacement(self):
        content = b"MZ" + b"A" * (1024*1024)
        digest = hashlib.sha256(content).hexdigest()
        release = self.fixture(tag="v1.3.0-beta.3",size=len(content),digest=digest)
        data = update_checker._release_candidate(release,update_checker.repository())
        self.assertIsNotNone(data)
        with patch("src.update_checker.urllib.request.urlopen",
                   side_effect=lambda request,timeout:DownloadResponse(content,data["url"])):
            path = update_checker.download_verified(data)
        self.assertEqual(path.read_bytes(),content)
        self.assertEqual(path.name,"WTModManager.exe")
        self.assertFalse((path.parent/"WTModManager.download").exists())

    def test_corrupted_binary_never_replaces_previous_copy(self):
        existing = self.root/"updates"/"WTModManager.exe"
        existing.parent.mkdir()
        existing.write_bytes(b"previous verified content")
        content = b"MZ" + b"B"*(1024*1024)
        release = self.fixture(tag="v1.3.0-beta.3",size=len(content),digest="0"*64)
        data = update_checker._release_candidate(release,update_checker.repository())
        self.assertIsNotNone(data, "The tamper test must exercise a real upgrade candidate.")
        with patch("src.update_checker.urllib.request.urlopen",
                   side_effect=lambda request,timeout:DownloadResponse(content,data["url"])):
            with self.assertRaises(ValueError):
                update_checker.download_verified(data)
        self.assertEqual(existing.read_bytes(),b"previous verified content")
        self.assertFalse((existing.parent/"WTModManager.download").exists())

    def test_update_target_restricts_other_executables(self):
        from src.portable_updater import _validate_target
        another = self.root/"something.exe"
        another.write_bytes(b"EXE")
        with self.assertRaises(ValueError):
            _validate_target(another)


if __name__ == "__main__":
    unittest.main()
