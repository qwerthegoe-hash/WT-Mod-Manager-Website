"""Release checks run without GitHub secrets or a Windows certificate."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import release_integrity as rel


class ReleaseIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        for name in rel.ARTIFACTS:
            (self.folder / name).write_bytes(b"MZ" + b"x" * (1024 * 1024 + 4))
        self.kwargs = {
            "folder": self.folder,
            "version": "1.3.0-beta.12",
            "repository": rel.REPOSITORY,
            "commit": "a" * 40,
            "run_url": (
                "https://github.com/" + rel.REPOSITORY +
                "/actions/runs/12345678"
            ),
            "signed": False,
        }

    def test_version_matches_app_installer_and_notes(self):
        self.assertEqual(rel.current_version(), "1.3.0-beta.12")

    def test_unsigned_release_is_explicit(self):
        obj = rel.make_manifest(**self.kwargs)
        self.assertEqual(obj["authenticode"], {
            "signed": False, "publisher": None
        })
        rel.write_manifest(self.folder, obj)
        rel.verify_manifest(self.folder, obj["version"])
        self.assertEqual(set(obj["files"]), set(rel.ARTIFACTS))

    def test_signed_release_requires_publisher(self):
        self.kwargs["signed"] = True
        with self.assertRaises(ValueError):
            rel.make_manifest(**self.kwargs)
        self.kwargs["signer"] = "CN=Official Publisher"
        self.assertEqual(rel.make_manifest(**self.kwargs)
                         ["authenticode"]["publisher"], "CN=Official Publisher")

    def test_reject_modified_binary_even_if_size_same(self):
        obj = rel.make_manifest(**self.kwargs)
        rel.write_manifest(self.folder, obj)
        with (self.folder / rel.ARTIFACTS[0]).open("r+b") as file:
            file.seek(100)
            file.write(b"z")
        with self.assertRaisesRegex(ValueError, "changed"):
            rel.verify_manifest(self.folder, obj["version"])

    def test_reject_modified_checksum_manifest(self):
        obj = rel.make_manifest(**self.kwargs)
        rel.write_manifest(self.folder, obj)
        (self.folder / "SHA256SUMS.txt").write_text("0" * 64 + "\n", "ascii")
        with self.assertRaisesRegex(ValueError, "SHA256SUMS"):
            rel.verify_manifest(self.folder, obj["version"])

    def test_reject_manifest_with_bad_source(self):
        obj = rel.make_manifest(**self.kwargs)
        obj["repository"] = "another/example"
        rel.write_manifest(self.folder, obj)
        with self.assertRaisesRegex(ValueError, "repository"):
            rel.verify_manifest(self.folder, obj["version"])

    def test_reject_version_mismatch(self):
        obj = rel.make_manifest(**self.kwargs)
        rel.write_manifest(self.folder, obj)
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            rel.verify_manifest(self.folder, "1.3.0-beta.13")

    def test_reject_unexpected_binary_type(self):
        (self.folder / rel.ARTIFACTS[1]).write_bytes(
            b"ZZ" + b"x" * (1024 * 1024 + 4)
        )
        with self.assertRaisesRegex(ValueError, "Not a Windows executable"):
            rel.make_manifest(**self.kwargs)


if __name__ == "__main__":
    unittest.main()
