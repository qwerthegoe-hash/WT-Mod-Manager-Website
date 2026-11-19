"""Synthetic War Thunder directory tests; NEVER write to a live game installation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src import vehicle_camouflages as camo
from src.game_mod_installer import InstallError, install_planned, restore_transaction


VEHICLE = "ussr_kv_1_l_11"
CONFIG = (
    'name:t="user"\n'
    'replace_tex {\n'
    '  from:t="ussr_camo_green*"\n'
    '  to:t="default_green.tga"\n'
    '}\n'
)


class VehicleCamouflageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.game = self.root / "Fake WarThunder"
        self.game.mkdir()
        (self.game / "config.blk").write_text("game { sound {} }", encoding="utf-8")
        self.skins = self.game / "UserSkins"
        self.template = self.skins / ("template_" + VEHICLE)
        self.template.mkdir(parents=True)
        self.original_blk = self.template / (VEHICLE + ".blk")
        self.original_blk.write_text(CONFIG, encoding="utf-8")
        self.original_skin = self.template / "default_green.tga"
        self.original_skin.write_bytes(b"template-tga-unmodified")
        self.camo_file = self.root / "rainbow.png"
        picture = Image.new("RGB", (256, 128), (240, 10, 250))
        for x in range(0, 256, 2):
            for y in range(0, 128, 2):
                picture.putpixel((x, y), ((x * 5) % 256, (y * 3) % 256, (x + y) % 256))
        picture.save(self.camo_file, "PNG")
        self.registry_patch = patch.object(
            camo, "PRESETS", self.root / "user-data" / "camouflages.json"
        )
        self.registry_patch.start()
        self.addCleanup(self.registry_patch.stop)
        self.backup_patch = patch("src.game_mod_installer.ROOT_BACKUPS",
                                  self.root / "user-data" / "backups")
        self.backup_patch.start()
        self.addCleanup(self.backup_patch.stop)
        self.running_patch = patch(
            "src.game_mod_installer.war_thunder_running", return_value=False
        )
        self.running_patch.start()
        self.addCleanup(self.running_patch.stop)

    def test_vehicle_picker_discovers_only_valid_game_templates(self):
        self.assertEqual(camo.list_vehicle_templates(self.skins), (self.template,))
        (self.skins / "template_missing_blk").mkdir()
        self.assertEqual(camo.list_vehicle_templates(self.skins), (self.template,))
        self.assertEqual(camo.vehicle_from_template(self.template), VEHICLE)

    def test_image_creates_independent_numbered_skin_and_safe_rollback(self):
        with tempfile.TemporaryDirectory() as stage:
            plan, destination, vehicle, label, serial = camo.plan_vehicle_image(
                self.camo_file, self.template, Path(stage)
            )
            self.assertEqual((vehicle, label, serial),
                             (VEHICLE, "WT Mod камуфляж №001", 1))
            self.assertEqual(destination.parent, self.skins)
            self.assertEqual(len(plan), 3)  # old texture, patched .blk, new texture
            self.assertFalse(destination.exists())
            self.assertEqual(self.original_blk.read_text("utf-8"), CONFIG)
            result = install_planned(plan)
        self.assertTrue((destination / f"{VEHICLE}.blk").is_file())
        self.assertIn("wtmm_pattern_001.tga",
                      (destination / f"{VEHICLE}.blk").read_text("utf-8"))
        self.assertEqual(self.original_blk.read_text("utf-8"), CONFIG)
        self.assertEqual(self.original_skin.read_bytes(), b"template-tga-unmodified")
        with Image.open(destination / "wtmm_pattern_001.tga") as picture:
            self.assertEqual((picture.width, picture.height), (1024, 1024))
        camo.record_preset(destination, vehicle, label, result["transaction"])
        self.assertEqual(len(camo.installed_presets()), 1)
        self.assertEqual(camo.next_preset_destination(self.template)[2], 2)
        restored = restore_transaction(result["transaction"])
        self.assertEqual(restored, 3)
        self.assertFalse((destination / f"{VEHICLE}.blk").exists())
        camo.forget_transaction(result["transaction"])
        self.assertEqual(camo.installed_presets(), [])

    def test_package_only_targets_user_selected_vehicle(self):
        package = self.root / "downloaded_skin"
        package.mkdir()
        (package / f"{VEHICLE}.blk").write_text(CONFIG, encoding="utf-8")
        (package / "rainbow.dds").write_bytes(b"DDS ")
        plan, destination, vehicle, label, num = camo.plan_vehicle_package(
            package, self.template
        )
        self.assertEqual((vehicle, num), (VEHICLE, 1))
        self.assertEqual(len(plan), 2)
        install_planned(plan)
        self.assertTrue((destination / "rainbow.dds").exists())
        self.assertTrue(self.original_blk.is_file())

    def test_reject_wrong_vehicle_instead_of_installing_incompatible_skin(self):
        package = self.root / "wrong_skin"
        package.mkdir()
        (package / "ussr_other_vehicle.blk").write_text(CONFIG, "utf-8")
        (package / "rainbow.dds").write_bytes(b"DDS ")
        with self.assertRaises(InstallError):
            camo.plan_vehicle_package(package, self.template)
        self.assertEqual(list(self.skins.iterdir()), [self.template])

    def test_reject_non_scalable_template_without_touching_game_files(self):
        initial = self.original_blk.read_bytes()
        self.original_blk.write_text('name:t="user"\nset_tex { to:t="body.tga" }')
        with tempfile.TemporaryDirectory() as stage:
            with self.assertRaises(InstallError):
                camo.plan_vehicle_image(self.camo_file, self.template, Path(stage))
        self.assertEqual(list(self.skins.iterdir()), [self.template])
        self.assertNotEqual(initial, self.original_blk.read_bytes())

    def test_reject_multiple_scalable_layers_in_ambiguous_template(self):
        self.original_blk.write_text(CONFIG + CONFIG, encoding="utf-8")
        with tempfile.TemporaryDirectory() as stage:
            with self.assertRaises(InstallError):
                camo.plan_vehicle_image(self.camo_file, self.template, Path(stage))
        self.assertEqual(list(self.skins.iterdir()), [self.template])

    def test_multilayer_template_supports_explicit_color_selection_and_mirror(self):
        extra = (
            'replace_tex {\n'
            '  from:t="camo_desert*"\n'
            '  to:t="second_color.dds"\n'
            '}\n'
            'replace_tex {\n'
            '  from:t="camo_normal_n*"\n'
            '  to:t="normal_n.tga"\n'
            '}\n'
        )
        self.original_blk.write_text(CONFIG + extra, encoding="utf-8")
        (self.template / "second_color.dds").write_bytes(b"DDS ")
        (self.template / "normal_n.tga").write_bytes(b"normal-map")
        layers = camo.list_scalable_layers(self.template)
        self.assertEqual(len(layers), 2)
        self.assertIn("second_color.dds", layers[1])
        self.assertFalse(any("normal_n.tga" in label for label in layers))
        with tempfile.TemporaryDirectory() as stage:
            with self.assertRaisesRegex(InstallError, "Выбери один слой"):
                camo.plan_vehicle_image(
                    self.camo_file, self.template, Path(stage)
                )
            plan, destination, _, _, _ = camo.plan_vehicle_image(
                self.camo_file, self.template, Path(stage),
                texture_layer=layers[1], pattern_mode="mirror"
            )
            # Do not modify either mapping until the install is confirmed.
            self.assertIn('to:t="second_color.dds"', self.original_blk.read_text("utf-8"))
            self.assertFalse(destination.exists())
            result = install_planned(plan)
        cfg = (destination / f"{VEHICLE}.blk").read_text("utf-8")
        self.assertIn('to:t="default_green.tga"', cfg)
        self.assertIn('to:t="wtmm_pattern_001.tga"', cfg)
        self.assertIn('to:t="normal_n.tga"', cfg)
        self.assertEqual(
            (destination / "normal_n.tga").read_bytes(), b"normal-map"
        )
        with Image.open(destination / "wtmm_pattern_001.tga") as image:
            self.assertEqual(image.size, (1024, 1024))
            for y in (0, 100, 511, 1023):
                self.assertEqual(image.getpixel((0, y)), image.getpixel((1023, y)))
            for x in (0, 100, 511, 1023):
                self.assertEqual(image.getpixel((x, 0)), image.getpixel((x, 1023)))
        self.assertEqual(restore_transaction(result["transaction"]), len(plan))
        self.assertEqual(self.original_blk.read_text("utf-8"), CONFIG + extra)

    def test_one_color_dds_template_accepts_regular_image(self):
        self.original_blk.write_text(
            CONFIG.replace("default_green.tga", "base_color.dds"),
            encoding="utf-8"
        )
        self.original_skin.unlink()
        (self.template / "base_color.dds").write_bytes(b"DDS ")
        layers = camo.list_scalable_layers(self.template)
        self.assertEqual(len(layers), 1)
        with tempfile.TemporaryDirectory() as stage:
            plan, destination, _, _, _ = camo.plan_vehicle_image(
                self.camo_file, self.template, Path(stage)
            )
            install_planned(plan)
        rewritten = (destination / f"{VEHICLE}.blk").read_text("utf-8")
        self.assertIn("wtmm_pattern_001.tga", rewritten)
        self.assertTrue((destination / "base_color.dds").exists())

    def test_reject_unknown_color_layer_or_invalid_pattern_mode(self):
        with tempfile.TemporaryDirectory() as stage:
            with self.assertRaises(InstallError):
                camo.plan_vehicle_image(
                    self.camo_file, self.template, Path(stage),
                    texture_layer="fake layer"
                )
            with self.assertRaises(InstallError):
                camo.plan_vehicle_image(
                    self.camo_file, self.template, Path(stage),
                    pattern_mode="invalid"
                )
        self.assertEqual(list(self.skins.iterdir()), [self.template])

    def test_reject_symlink_inside_package(self):
        package = self.root / "linked_pack"
        package.mkdir()
        (package / f"{VEHICLE}.blk").write_text(CONFIG)
        try:
            (package / "external.tga").symlink_to(self.original_skin)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are not available on this Windows runner.")
        with self.assertRaises(InstallError):
            camo.plan_vehicle_package(package, self.template)


if __name__ == "__main__":
    unittest.main()
