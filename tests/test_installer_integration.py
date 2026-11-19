"""Installed vs portable release selection, checksum and setup manifest tests."""
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import update_checker
from src.installed_updater import launch_setup_update, setup_update_arguments


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
            "FinishTaskbarPin",
            "--offer-taskbar-pin",
            "FinishAutoStart",
            "ChannelPage",
            "WizardSmallImageBackColor=#202B3A",
        ):
            self.assertIn(requirement, script)
        self.assertIn("Type: files; Name: \"{autodesktop}\\WT Mod Manager.lnk\"", script)
        self.assertNotIn("Name: \"{localappdata}\\WTModManager", script)
        self.assertNotIn("notepad.exe", script.lower())
        self.assertNotIn("Pin-to-taskbar.txt", script)
        self.assertNotIn("forcedtaskbarpin", script.lower())

    def test_setup_selected_channel_is_per_user(self):
        prefs = self.root / "update-channel.json"
        prefs.write_text('{"channel":"stable"}', encoding="utf-8")
        self.assertEqual(update_checker.update_channel(), "stable")
        prefs.write_text('{"channel":"beta"}', encoding="utf-8")
        self.assertEqual(update_checker.update_channel(), "beta")
        prefs.write_text('{"channel":"untrusted"}', encoding="utf-8")
        self.assertEqual(update_checker.update_channel(), "beta")
        prefs.write_text("not json", encoding="utf-8")
        self.assertEqual(update_checker.update_channel(), "beta")

    def test_finish_page_replaces_text_guide_with_taskbar_request(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "installer" / "WTModManager.iss").read_text("utf-8")
        self.assertIn("FinishTaskbarPin.Checked", script)
        self.assertIn("--offer-taskbar-pin", script)
        self.assertIn("Windows", script)
        self.assertNotIn("Filename: \"{sys}\\notepad.exe\"", script)

    def test_installer_distributes_one_exe_not_exposed_runtime_tree(self):
        root = Path(__file__).resolve().parents[1]
        setup = (root / "installer" / "WTModManager.iss").read_text("utf-8")
        builder = (root / "tools" / "build_windows_exe.py").read_text("utf-8")
        self.assertIn('Source: "..\\dist\\WTModManager.exe"', setup)
        self.assertNotIn('Source: "..\\dist\\WTModManager\\*"', setup)
        self.assertIn('Name: "{app}\\_internal"; Check: HasLegacyRuntime', setup)
        self.assertIn("def build() -> None:", builder)
        self.assertIn('"--onefile"', builder)
        self.assertNotIn('"--onedir"', builder)
        self.assertNotIn('build("installed")', builder)
        self.assertIn('":assets/icons"', builder)
        self.assertIn('":config"', builder)
        self.assertNotIn('str(ROOT / "config") + ":config"', builder)
        self.assertIn('"support_config.json"', builder)
        self.assertIn('"update_config.json"', builder)

    def test_setup_launcher_rejects_nonwindows_execution(self):
        with self.assertRaises(RuntimeError):
            launch_setup_update(self.root / "WTModManager-Setup.exe", "0"*64)


class OneClickInstalledUpdateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.installed_dir = self.root / "Custom Installed Folder"
        self.installed_dir.mkdir()
        self.installed_exe = self.installed_dir / "WTModManager.exe"
        self.installed_exe.write_bytes(b"MZ" + b"A" * 16)
        (self.installed_dir / "wtmm.installed").write_bytes(b"installed")
        self.updates = self.root / "updates"
        self.updates.mkdir()
        self.setup = self.updates / "WTModManager-Setup.exe"
        self.setup.write_bytes(b"MZ" + b"B" * (1024 * 1024))
        self.digest = hashlib.sha256(self.setup.read_bytes()).hexdigest()

    def test_update_command_preserves_custom_folder_without_hiding_errors(self):
        import src.installed_updater as installed
        args = setup_update_arguments(self.installed_dir)
        self.assertIn("/SILENT", args)
        self.assertIn("/NORESTART", args)
        self.assertIn("/CLOSEAPPLICATIONS", args)
        self.assertIn("/DIR=" + str(self.installed_dir), args)
        self.assertIn("/WTMMAUTOUPDATE", args)
        self.assertNotIn("/VERYSILENT", args)
        self.assertNotIn("/SUPPRESSMSGBOXES", args)
        with (
            patch.object(installed.sys, "platform", "win32"),
            patch.object(installed.sys, "frozen", True, create=True),
            patch.object(installed.sys, "executable", str(self.installed_exe)),
            patch.object(installed, "is_installed_app", return_value=True),
            patch.object(installed, "SETUP_FILE", self.setup),
            patch.object(installed.subprocess, "Popen") as popen,
        ):
            launch_setup_update(self.setup, self.digest)
        popen.assert_called_once()
        argv = popen.call_args.args[0]
        self.assertEqual(argv[0], str(self.setup))
        self.assertEqual(argv[1:], args)
        self.assertFalse(popen.call_args.kwargs["shell"])

    def test_tampered_setup_cannot_start(self):
        import src.installed_updater as installed
        with (
            patch.object(installed.sys, "platform", "win32"),
            patch.object(installed.sys, "frozen", True, create=True),
            patch.object(installed.sys, "executable", str(self.installed_exe)),
            patch.object(installed, "is_installed_app", return_value=True),
            patch.object(installed, "SETUP_FILE", self.setup),
            patch.object(installed.subprocess, "Popen") as popen,
        ):
            with self.assertRaises(ValueError):
                launch_setup_update(self.setup, "0" * 64)
        popen.assert_not_called()

    def test_installer_auto_restart_does_not_affect_regular_silent_installs(self):
        installer = (Path(__file__).resolve().parents[1]
                     / "installer" / "WTModManager.iss").read_text("utf-8")
        self.assertIn("function IsOneClickUpdate(): Boolean;", installer)
        self.assertIn("if IsOneClickUpdate() then", installer)
        self.assertIn("Check: IsOneClickUpdate", installer)
        self.assertIn("Flags: nowait skipifnotsilent runasoriginaluser", installer)
        self.assertIn('Parameters: "--updated"', installer)
        self.assertIn("last-update-status.txt", installer)
        self.assertIn("UsePreviousAppDir=yes", installer)
        self.assertIn("RestartApplications=no", installer)
        self.assertNotIn("PrivilegesRequired=admin", installer)

    def test_download_progress_only_finishes_after_verified_binary(self):
        binary = b"MZ" + b"A" * (1024 * 1024)
        digest = hashlib.sha256(binary).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            update_dir = root / "updates"
            config = root / "config.json"
            config.write_text(json.dumps({
                "github_repository": "qwerthegoe-hash/WT-Mod-Manager-Website",
                "channel": "beta"
            }), encoding="utf-8")
            release = {
                "name": "WTModManager-Setup.exe",
                "kind": "installer",
                "version": "v1.4.0-beta.1",
                "url": ("https://github.com/qwerthegoe-hash/WT-Mod-Manager-Website/"
                        "releases/download/v1.4.0-beta.1/WTModManager-Setup.exe"),
                "size": len(binary),
                "digest": digest,
            }
            with (
                patch("src.update_checker.CONFIG_FILE", config),
                patch("src.update_checker.DATA_DIR", root),
                patch("src.update_checker.is_installed_app", return_value=True),
                patch("src.update_checker.urllib.request.urlopen",
                      side_effect=lambda request, timeout:
                          FakeResponse(binary, release["url"])),
            ):
                progress = []
                target = update_checker.download_verified(release, progress.append)
                self.assertEqual(progress[0], 0)
                self.assertEqual(progress[-1], 100)
                self.assertEqual(target, update_dir / "WTModManager-Setup.exe")
                cached = []
                update_checker.download_verified(release, cached.append)
                self.assertEqual(cached, [100])


if __name__ == "__main__":
    unittest.main()
