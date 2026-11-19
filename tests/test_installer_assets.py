"""Visual regression for the rounded, transparent Inno Setup mini logo."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools import build_installer_assets


class BrandedMiniLogoTests(unittest.TestCase):
    def test_mini_card_has_transparent_antialiased_rounded_corners(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            with patch.object(build_installer_assets, "OUT", destination):
                build_installer_assets.main()
            image = Image.open(destination / "wizard-small.png").convert("RGBA")
            self.assertEqual(image.size, (320, 320))
            self.assertEqual(image.getpixel((0, 0))[3], 0)
            self.assertEqual(image.getpixel((319, 0))[3], 0)
            self.assertEqual(image.getpixel((0, 319))[3], 0)
            self.assertEqual(image.getpixel((319, 319))[3], 0)
            self.assertEqual(image.getpixel((160, 160))[3], 255)
            self.assertTrue(
                any(0 < image.getpixel((x, 5))[3] < 255 for x in range(0, 50)),
                "Rounded edge is not antialiased"
            )
            self.assertTrue((destination / "WTModManager.ico").is_file())
            with Image.open(destination / "wizard.png") as large:
                self.assertEqual(large.mode, "RGB")


if __name__ == "__main__":
    unittest.main()
