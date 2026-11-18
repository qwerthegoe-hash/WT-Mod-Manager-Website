"""Start a checksum-verified Inno Setup update for an installed Windows app.

No command shell, no elevation, no unattended install. The user explicitly
confirms the update in the GUI, then the original app exits normally and the
wizard takes over. The installer owns uninstall metadata and shortcuts.
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


def launch_setup_update(file_path: Path, expected_sha256: str) -> None:
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        raise RuntimeError("Installation is supported only from a Windows EXE.")
    if not is_installed_app():
        raise RuntimeError("Portable builds use the legacy EXE updater.")
    target = Path(file_path).absolute()
    if (target != SETUP_FILE or target.is_symlink() or not target.is_file()
            or not isinstance(expected_sha256, str)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)):
        raise ValueError("Setup path or signed release metadata is invalid.")
    if target.stat().st_size < 1024 * 1024:
        raise ValueError("The setup file is incomplete.")
    with target.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError("The setup file is not a Windows executable.")
    if _sha256(target) != expected_sha256:
        raise ValueError("Installer checksum did not match GitHub Releases.")

    subprocess.Popen(
        [str(target)],
        cwd=str(target.parent),
        env={**os.environ, "PYINSTALLER_RESET_ENVIRONMENT": "1"},
        close_fds=True,
    )
