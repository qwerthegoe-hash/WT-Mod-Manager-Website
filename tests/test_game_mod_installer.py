"""Safety/rollback tests for custom War Thunder content (no game installation needed)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.game_mod_installer import (
    InstallError, sight_plan, camouflage_plan, sound_plan,
    install_planned, restore_transaction, patch_sound_setting,
)


class GameModInstallTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.sights = (self.root / "WarThunder" / "Saves" / "user1" /
                       "production" / "UserSights")
        self.sights.mkdir(parents=True)
        self.source = self.root / "my-reticle.blk"
        self.source.write_text("reticle definition", encoding="utf-8")
        self.patcher = patch("src.game_mod_installer.ROOT_BACKUPS", self.root / "backups")
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.game_patch = patch("src.game_mod_installer.war_thunder_running", return_value=False)
        self.game_patch.start()
        self.addCleanup(self.game_patch.stop)

    def test_safe_sight_install_and_restore(self):
        plan = sight_plan(self.source, self.sights, "all_tanks")
        self.assertFalse(plan[0].existing)
        result = install_planned(plan)
        target = self.sights / "all_tanks" / "my-reticle.blk"
        self.assertEqual(target.read_text(), "reticle definition")
        self.assertEqual(result["copied"], 1)
        self.assertEqual(restore_transaction(result["transaction"]), 1)
        self.assertFalse(target.exists())

    def test_repeated_install_does_not_duplicate(self):
        first = install_planned(sight_plan(self.source, self.sights))
        self.assertEqual(first["copied"], 1)
        repeated = install_planned(sight_plan(self.source, self.sights))
        self.assertEqual(repeated["status"], "unchanged")

    def test_sight_overwrite_restores_previous_bytes(self):
        destination = self.sights / "all_tanks"
        destination.mkdir()
        old = destination / "my-reticle.blk"
        old.write_bytes(b"old content")
        result = install_planned(sight_plan(self.source, self.sights))
        self.assertEqual(result["conflicts"], 1)
        self.assertEqual(old.read_bytes(), b"reticle definition")
        restore_transaction(result["transaction"])
        self.assertEqual(old.read_bytes(), b"old content")

    def test_refuse_rollback_after_external_edit(self):
        result = install_planned(sight_plan(self.source, self.sights))
        target = self.sights / "all_tanks" / self.source.name
        target.write_bytes(b"manual change")
        with self.assertRaises(InstallError):
            restore_transaction(result["transaction"])
        self.assertEqual(target.read_bytes(), b"manual change")

    def test_invalid_user_sights_folder_and_scope(self):
        with self.assertRaises(InstallError):
            sight_plan(self.source, self.root / "UserSights")
        with self.assertRaises(InstallError):
            sight_plan(self.source, self.sights, "../outside")

    def test_reject_png_as_playable_sight(self):
        image = self.root / "preview.png"
        image.write_bytes(b"image")
        with self.assertRaises(InstallError):
            sight_plan(image, self.sights)

    def test_refuse_install_while_game_active(self):
        with patch("src.game_mod_installer.war_thunder_running", return_value=True):
            with self.assertRaises(InstallError):
                install_planned(sight_plan(self.source, self.sights))

    def test_skin_needs_blk_and_valid_template(self):
        game = self.root / "Game"
        template = game / "UserSkins" / "template_demo_tank"
        template.mkdir(parents=True)
        (game / "config.blk").write_bytes(b"sound{ }")
        pack = self.root / "camouflage"
        pack.mkdir()
        (pack / "paint.dds").write_bytes(b"dds")
        with self.assertRaises(InstallError):
            camouflage_plan(pack, template)
        (pack / "skin.blk").write_bytes(b"skin definition")
        plan = camouflage_plan(pack, template)
        self.assertEqual(len(plan), 2)
        res = install_planned(plan)
        self.assertTrue((template / "paint.dds").exists())
        restore_transaction(res["transaction"])
        self.assertFalse((template / "paint.dds").exists())

    def test_sound_requires_fmod_bank_and_updates_block(self):
        game = self.root / "Game"
        game.mkdir()
        (game / "config.blk").write_bytes(b"game{ x:i=1 }\nsound {\n  enable_mod:b=no\n}\n")
        mod = self.root / "sounds"
        mod.mkdir()
        (mod / "sound.mp3").write_bytes(b"mp3")
        with self.assertRaises(InstallError):
            sound_plan(mod, game)
        (mod / "sound.mp3").unlink()
        (mod / "engine.bank").write_bytes(b"FMOD-bank")
        res = install_planned(sound_plan(mod, game), config_root=game)
        self.assertIn(b"enable_mod:b=yes",(game / "config.blk").read_bytes())
        self.assertTrue((game / "sound" / "mod" / "engine.bank").is_file())
        self.assertEqual(res["copied"], 2)
        restore_transaction(res["transaction"])
        self.assertIn(b"enable_mod:b=no",(game / "config.blk").read_bytes())
        self.assertFalse((game / "sound" / "mod" / "engine.bank").exists())

    def test_patch_sound_preserves_existing_config(self):
        original = b"game{x:i=1}\nsound{other:i=0}\n"
        result = patch_sound_setting(original)
        self.assertIn(b"enable_mod:b=yes", result)
        self.assertEqual(patch_sound_setting(result), result)

    def test_no_executables_inside_skin_package(self):
        game = self.root / "Game"
        template = game / "UserSkins" / "template_demo_tank"
        template.mkdir(parents=True)
        (game / "config.blk").write_bytes(b"sound{}")
        pack = self.root / "skin"
        pack.mkdir()
        (pack / "skin.blk").write_text("x")
        (pack / "run.exe").write_text("no")
        with self.assertRaises(InstallError):
            camouflage_plan(pack,template)


if __name__ == "__main__":
    unittest.main()
