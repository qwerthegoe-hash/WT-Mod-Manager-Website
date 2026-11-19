"""Offline checks for privacy-safe build SBOM inventory."""
import unittest
from types import SimpleNamespace
from tools import build_sbom

class FakeDistribution:
    def __init__(self, name, version):
        self.metadata = {"Name": name}
        self.version = version

class SBOMTests(unittest.TestCase):
    def test_component_names_are_sanitized(self):
        data = build_sbom.inventory([
            FakeDistribution("PySide6", "6.12.0"),
            FakeDistribution("Pillow", "13.0.0"),
            FakeDistribution("psutil", "7.2.2"),
            FakeDistribution("pyinstaller", "6.22.3"),
            FakeDistribution("Injected/Value", "1.0"),
        ])
        self.assertEqual(len(data["components"]), 4)
        self.assertEqual(build_sbom.validate_sbom(data), 4)
        self.assertTrue(all("path" not in component for component in data["components"]))

    def test_missing_required_dependencies_fail(self):
        with self.assertRaises(ValueError):
            build_sbom.validate_sbom(build_sbom.inventory([
                FakeDistribution("Pillow", "13.0.0"),
                FakeDistribution("psutil", "7.2.2"),
                FakeDistribution("pyinstaller", "6.22.3"),
            ]))

if __name__ == "__main__":
    unittest.main()
