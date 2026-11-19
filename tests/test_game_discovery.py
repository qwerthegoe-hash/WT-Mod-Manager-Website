"""Offline checks for read-only War Thunder folder discovery."""
import tempfile
import unittest
from pathlib import Path

from src.game_discovery import (
    find_game_roots, find_sight_folders, find_skin_templates,
)


class GameDiscoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()

    @staticmethod
    def create_game(folder):
        folder.mkdir(parents=True)
        (folder / "config.blk").write_text("video {}\n", encoding="utf-8")

    def test_standard_steam_install_detected_without_modifying_anything(self):
        program_files = self.root / "Program Files (x86)"
        game = program_files / "Steam" / "steamapps" / "common" / "War Thunder"
        self.create_game(game)
        env = {"ProgramFiles(x86)": str(program_files)}
        self.assertEqual(find_game_roots(env, self.home), (game,))
        self.assertEqual((game / "config.blk").read_text("utf-8"), "video {}\n")
        self.assertFalse((game / "UserSkins").exists())

    def test_extra_steam_library_read_from_bounded_local_manifest(self):
        steam = self.root / "apps" / "Steam"
        steamapps = steam / "steamapps"
        steamapps.mkdir(parents=True)
        library = self.root / "SteamLibrary"
        game = library / "steamapps" / "common" / "War Thunder"
        self.create_game(game)
        (steamapps / "libraryfolders.vdf").write_text(
            '"libraryfolders"\n{\n "0" { "path" "' + str(library) + '" }\n}\n',
            encoding="utf-8",
        )
        roots = find_game_roots({"ProgramFiles": str(steam.parent)}, self.home)
        self.assertEqual(roots, (game,))

    def test_missing_config_is_not_game_installation(self):
        path = self.root / "pf" / "Steam" / "steamapps" / "common" / "War Thunder"
        path.mkdir(parents=True)
        self.assertEqual(
            find_game_roots({"ProgramFiles": str(self.root / "pf")}, self.home), ()
        )

    def test_corrupt_or_large_steam_manifest_skipped(self):
        steamapps = self.root / "pf" / "Steam" / "steamapps"
        steamapps.mkdir(parents=True)
        (steamapps / "libraryfolders.vdf").write_bytes(b"x" * (256 * 1024 + 1))
        self.assertEqual(
            find_game_roots({"ProgramFiles": str(self.root / "pf")}, self.home), ()
        )

    def test_detect_sights_in_existing_profile_or_production_only(self):
        base = self.home / "Documents" / "My Games" / "WarThunder" / "Saves"
        prod1 = base / "123456" / "production"
        prod1.mkdir(parents=True)
        result = find_sight_folders({}, self.home)
        self.assertEqual(result, (prod1,))
        self.assertFalse((prod1 / "UserSights").exists())
        sight = prod1 / "UserSights"
        sight.mkdir()
        self.assertEqual(find_sight_folders({}, self.home), (sight,))

    def test_onedrive_documents_are_supported_without_creating_folders(self):
        one_drive = self.root / "OneDrive"
        production = one_drive / "Documents" / "My Games" / "WarThunder" / "Saves" / "profile" / "production"
        production.mkdir(parents=True)
        roots = find_sight_folders({"OneDrive": str(one_drive)}, self.home)
        self.assertEqual(roots, (production,))

    def test_detect_only_existing_skin_templates(self):
        game = self.root / "WT"
        self.create_game(game)
        skins = game / "UserSkins"
        (skins / "template_test_tank").mkdir(parents=True)
        (skins / "other").mkdir()
        self.assertEqual(find_skin_templates(game), (skins / "template_test_tank",))
        self.assertEqual(find_skin_templates(self.root / "uninstalled"), ())
        self.assertFalse((game / "sound").exists())


if __name__ == "__main__":
    unittest.main()
