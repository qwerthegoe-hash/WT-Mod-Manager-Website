"""Fail-closed Windows release version, checksum and provenance verification.

Only the two intended EXEs may be published. Build provenance is recorded
for transparency and attested by GitHub Actions; it is not a substitute for
an Authenticode certificate or a malware scan.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ("WTModManager.exe", "WTModManager-Setup.exe")
VERSION = re.compile(r"^\d+\.\d+\.\d+-beta\.\d+$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = "qwerthegoe-hash/WT-Mod-Manager-Website"


def current_version(root: Path = ROOT) -> str:
    source = (root / "src/update_checker.py").read_text(encoding="utf-8")
    installer = (root / "installer/WTModManager.iss").read_text(encoding="utf-8")
    workflow = (root / ".github/workflows/build-windows-exe.yml").read_text(
        encoding="utf-8"
    )
    notes = (root / "installer/release-notes.txt").read_text(encoding="utf-8")
    found = re.search(r'^VERSION = "([^"]+)"$', source, re.MULTILINE)
    if found is None or not VERSION.fullmatch(found.group(1)):
        raise ValueError("Invalid Python release version.")
    version = found.group(1)
    expected = [
        '#define MyAppVersion "' + version + '"',
        "WTMM_VERSION: " + version,
        "WT Mod Manager " + version,
        "VersionInfoVersion=1.3.0." + version.rsplit(".", 1)[1],
    ]
    actual = [installer, workflow, notes, installer]
    for phrase, text in zip(expected, actual):
        if phrase not in text:
            raise ValueError("Release metadata is inconsistent: " + phrase)
    return version


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_manifest(
    folder: Path, version: str, repository: str, commit: str, run_url: str,
    signed: bool, signer: str = "",
) -> dict:
    if not VERSION.fullmatch(version):
        raise ValueError("Invalid release version.")
    if repository != REPOSITORY or not COMMIT.fullmatch(commit):
        raise ValueError("Invalid release origin.")
    expected_prefix = (
        "https://github.com/" + REPOSITORY + "/actions/runs/"
    )
    if not run_url.startswith(expected_prefix) or not run_url[len(expected_prefix):].isdigit():
        raise ValueError("Invalid workflow run URL.")
    if not isinstance(signed, bool):
        raise ValueError("Signing status is not boolean.")
    if signed and (not signer.strip() or len(signer) > 300):
        raise ValueError("A signed release must identify its publisher.")
    files = {}
    for name in ARTIFACTS:
        path = folder / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing regular release binary: " + name)
        size = path.stat().st_size
        if not 1024 * 1024 < size <= 350 * 1024 * 1024:
            raise ValueError("Unexpected release size: " + name)
        with path.open("rb") as stream:
            if stream.read(2) != b"MZ":
                raise ValueError("Not a Windows executable: " + name)
        files[name] = {"sha256": sha256(path), "size": size}
    return {
        "schema": 1,
        "product": "WT Mod Manager",
        "version": version,
        "tag": "v" + version,
        "repository": repository,
        "commit": commit,
        "build_url": run_url,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "authenticode": {
            "signed": signed,
            "publisher": signer.strip() if signed else None,
        },
        "files": files,
        "notes": (
            "GitHub build provenance attests the build origin, not malware "
            "safety. Unsigned releases may trigger SmartScreen."
        ),
    }


def write_manifest(folder: Path, manifest: dict) -> None:
    checksums = "".join(
        manifest["files"][name]["sha256"] + "  " + name + "\n"
        for name in ARTIFACTS
    )
    (folder / "SHA256SUMS.txt").write_text(checksums, encoding="ascii")
    (folder / "build-info.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def verify_manifest(folder: Path, version: str) -> None:
    manifest = json.loads((folder / "build-info.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise ValueError("Invalid build metadata schema.")
    if manifest.get("version") != version or manifest.get("tag") != "v" + version:
        raise ValueError("Release version mismatch.")
    if manifest.get("repository") != REPOSITORY:
        raise ValueError("Release repository mismatch.")
    if not isinstance(manifest.get("commit"), str) or not COMMIT.fullmatch(
        manifest["commit"]
    ):
        raise ValueError("Bad build commit.")
    signed = manifest.get("authenticode")
    if not isinstance(signed, dict) or type(signed.get("signed")) is not bool:
        raise ValueError("Invalid Authenticode declaration.")
    if signed["signed"] and not signed.get("publisher"):
        raise ValueError("Signed release has no publisher.")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != set(ARTIFACTS):
        raise ValueError("Release binary allowlist mismatch.")
    expected = []
    for name in ARTIFACTS:
        item = files[name]
        if not isinstance(item, dict) or not DIGEST.fullmatch(str(item.get("sha256", ""))):
            raise ValueError("Invalid SHA-256 in release manifest.")
        path = folder / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != item.get("size"):
            raise ValueError("Release file absent or wrong size: " + name)
        if sha256(path) != item["sha256"]:
            raise ValueError("Release file changed after hashing: " + name)
        expected.append(item["sha256"] + "  " + name + "\n")
    actual = (folder / "SHA256SUMS.txt").read_text(encoding="ascii")
    if actual != "".join(expected):
        raise ValueError("SHA256SUMS does not match build-info.json.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("version", "create", "verify"))
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--folder", type=Path, default=ROOT / "dist")
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--commit", default="")
    parser.add_argument("--run-url", default="")
    parser.add_argument("--signed", choices=("true", "false"), default="false")
    parser.add_argument("--publisher", default="")
    args = parser.parse_args()

    version = current_version()
    if args.expected_version != version:
        raise SystemExit("Release version mismatch: " + args.expected_version +
                         " differs from source " + version)
    if args.command == "create":
        args.folder.mkdir(parents=True, exist_ok=True)
        info = make_manifest(args.folder, version, args.repository, args.commit,
                             args.run_url, args.signed == "true", args.publisher)
        write_manifest(args.folder, info)
        verify_manifest(args.folder, version)
    elif args.command == "verify":
        verify_manifest(args.folder, version)
    print("Release integrity: " + version + " " + args.command + " OK")


if __name__ == "__main__":
    main()
