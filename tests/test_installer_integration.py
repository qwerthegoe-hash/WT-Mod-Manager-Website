"""Installed vs portable release selection, checksum and setup manifest tests."""
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import update_checker
from src.installed_updater import launch_setup_update


class FakeResponse(io.BytesIO):
    def __init__(self, data, url):
        super().__init__(data)
        self.url = url
        self.headers = {}

    def geturl(self):
        return self.url


class BrandedInstallerTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.cfg = self.root / "release.json"
        self.cfg.write_text(json.dumps({
            "github_repository": "qwerthegoe-hash/WT-Mod-Manager-Website",
            "channel": "beta"
        }), encoding="utf-8")
        for target, value in (
            ("src.update_checker.CONFIG_FILE", self.cfg),
            ("src.update_checker.DATA_DIR", self.root),
        ):
            p = patch(target, value)
            p.start()
            self.addCleanup(p.stop)

    @staticmethod
    def release(filename):
        tag = "v1.4.0-beta.1"
        return {
            "tag_name": tag, "draft": False, "prerelease": True,
            "assets": [{
                "name": filename,
                "size": 2_000_000,
                "digest": "sha256:" + "1" * 64,
                "browser_download_url": (
                    "https://github.com/qwerthegoe-hash/WT-Mod-Manager-Website/"
                    "releases/download/" + tag + "/" + filename
                )
            }]
        }

    def test_setup_is_selected_for_installed_application(self):
        with patch("src.update_checker.is_installed_app", return_value=True):
            candidate = update_checker._release_candidate(
                self.release("WTModManager-Setup.exe"),
                update_checker.repository()
            )
            self.assertEqual(candidate["name"], "WTModManager-Setup.exe")
            self.assertEqual(candidate["kind"], "installer")
            self.assertIsNone(update_checker._release_candidate(
                self.release("WTModManager.exe"),
                update_checker.repository()
            ))

    def test_portable_release_remains_supported_for_old_clients(self):
        with patch("src.update_checker.is_installed_app", return_value=False):
            candidate = update_checker._release_candidate(
                self.release("WTModManager.exe"),
                update_checker.repository()
            )
            self.assertEqual(candidate["kind"], "portable")
            self.assertIsNone(update_checker._release_candidate(
                self.release("WTModManager-Setup.exe"),
                update_checker.repository()
            ))

    def test_verified_installer_download_retains_name(self):
        binary = b"MZ" + b"A" * (1024 * 1024)
        digest = hashlib.sha256(binary).hexdigest()
        release = self.release("WTModManager-Setup.exe")
        release["assets"][0]["digest"] = "sha256:" + digest
        release["assets"][0]["size"] = len(binary)
        with patch("src.update_checker.is_installed_app", return_value=True):
            info = update_checker._release_candidate(release, update_checker.repository())
            with patch("src.update_checker.urllib.request.urlopen",
                       side_effect=lambda req, timeout: FakeResponse(binary, info["url"])):
                path = update_checker.download_verified(info)
        self.assertEqual(path.name, "WTModManager-Setup.exe")
        self.assertEqual(path.read_bytes(), binary)
        self.assertFalse((path.parent / "WTModManager-Setup.download").exists())

    def test_setup_download_rejects_tampered_sha(self):
        binary = b"MZ" + b"B" * (1024 * 1024)
        release = self.release("WTModManager-Setup.exe")
        release["assets"][0]["size"] = len(binary)
        with patch("src.update_checker.is_installed_app", return_value=True):
            info = update_checker._release_candidate(release, update_checker.repository())
            with patch("src.update_checker.urllib.request.urlopen",
                       side_effect=lambda req, timeout: FakeResponse(binary, info["url"])):
                with self.assertRaises(ValueError):
                    update_checker.download_verified(info)
        self.assertFalse((self.root / "updates" / "WTModManager-Setup.exe").exists())

    def test_installer_script_preserves_uninstall_and_user_data(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "installer" / "WTModManager.iss").read_text("utf-8")
        for requirement in (
            "WizardStyle=modern dark",
            "SetupIconFile=",
            "WizardImageFile=",
            "DefaultDirName={localappdata}",
            "PrivilegesRequired=lowest",
            "DisableDirPage=no",
            "FinishDesktopShortcut",
            "CreateShellLink(",
            "Name: \"{group}\\WT Mod Manager\"",
            "Filename: \"{uninstallexe}\"",
            "Filename: \"{sys}\\notepad.exe\"",
        ):
            self.assertIn(requirement, script)
        self.assertIn("Type: files; Name: \"{autodesktop}\\WT Mod Manager.lnk\"", script)
        self.assertNotIn("Name: \"{localappdata}\\WTModManager", script)
        self.assertNotIn("forcedtaskbarpin", script.lower())

    def test_setup_launcher_rejects_nonwindows_execution(self):
        with self.assertRaises(RuntimeError):
            launch_setup_update(self.root / "WTModManager-Setup.exe", "0"*64)


if __name__ == "__main__":
    unittest.main()
