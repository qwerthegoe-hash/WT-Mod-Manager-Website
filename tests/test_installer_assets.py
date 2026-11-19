"""Visual regression for a rounded mini-logo with opaque dark-mode corners."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools import build_installer_assets


class BrandedMiniLogoTests(unittest.TestCase):
    def test_mini_card_has_opaque_antialiased_rounded_corners(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            with patch.object(build_installer_assets, "OUT", destination):
                build_installer_assets.main()
            with Image.open(destination / "wizard-small.png") as loaded:
                self.assertEqual(loaded.mode, "RGB")
                image = loaded.copy()
            self.assertEqual(image.size, (320, 320))
            panel = (32, 43, 58)
            for xy in ((0, 0), (319, 0), (0, 319), (319, 319)):
                self.assertEqual(image.getpixel(xy), panel)
            self.assertNotEqual(image.getpixel((160, 160)), panel)
            # Antialiasing produces different blended colors near the card edge
            # while keeping the outside panel fully opaque.
            self.assertGreater(
                len({image.getpixel((x, 12)) for x in range(4, 50)}), 3
            )
            self.assertTrue((destination / "WTModManager.ico").is_file())
            with Image.open(destination / "wizard.png") as large:
                self.assertEqual(large.mode, "RGB")


if __name__ == "__main__":
    unittest.main()
