"""Explicit, checksum-verified in-place upgrade of an installed WT Mod Manager.

Only an installed Windows EXE can request this. Inno Setup handles the original
uninstall entry, shortcuts and selected directory. Its /SILENT mode still shows
installation progress and any important system prompts; it does not suppress
errors, UAC or Windows security checks. No shell interpreter is involved.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from src.profile_paths import DATA_DIR
from src.update_checker import is_installed_app, _sha256

SETUP_FILE = DATA_DIR / "updates" / "WTModManager-Setup.exe"
UPDATE_FLAG = "/WTMMAUTOUPDATE"


def setup_update_arguments(install_dir: Path) -> list[str]:
    """Use the same install folder, including for non-default user installs."""
    folder = Path(install_dir)
    if not folder.is_absolute() or folder.is_symlink():
        raise ValueError("Invalid installed application directory.")
    if folder.name in ("", ".", ".."):
        raise ValueError("Invalid installed application directory.")
    return [
        "/SILENT",             # No repeated install wizard; visible progress.
        "/NORESTART",          # Never reboot Windows automatically.
        "/CLOSEAPPLICATIONS",  # Installer safely handles a still-running app.
        "/DIR=" + str(folder),
        UPDATE_FLAG,           # Only this trusted path reopens --updated.
    ]


def launch_setup_update(file_path: Path, expected_sha256: str) -> None:
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        raise RuntimeError("Installation is supported only from a Windows EXE.")
    if not is_installed_app():
        raise RuntimeError("Portable builds use the dedicated EXE updater.")

    target = Path(file_path).absolute()
    if (target != SETUP_FILE or target.is_symlink() or not target.is_file()
            or not isinstance(expected_sha256, str)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)):
        raise ValueError("Setup path or verified release metadata is invalid.")
    if target.stat().st_size < 1024 * 1024:
        raise ValueError("The setup file is incomplete.")
    with target.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError("The setup file is not a Windows executable.")
    if _sha256(target) != expected_sha256:
        raise ValueError("Installer checksum did not match GitHub Releases.")

    installed_exe = Path(sys.executable).absolute()
    installed_dir = installed_exe.parent
    if (installed_exe.name.casefold() != "wtmodmanager.exe"
            or installed_dir.is_symlink()
            or not (installed_dir / "wtmm.installed").is_file()
            or (installed_dir / "wtmm.installed").is_symlink()):
        raise ValueError("Unable to verify the existing installed application.")

    # Popen returns only after the official installer process starts.
    # The UI closes the current WTMM process after successful handoff.
    subprocess.Popen(
        [str(target), *setup_update_arguments(installed_dir)],
        cwd=str(target.parent),
        env={**os.environ, "PYINSTALLER_RESET_ENVIRONMENT": "1"},
        close_fds=True,
        shell=False,
    )
