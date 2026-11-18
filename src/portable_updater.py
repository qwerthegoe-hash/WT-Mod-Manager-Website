"""Windows-only self-update helper for a single PyInstaller one-file EXE.

The current EXE downloads and verifies a new release, then launches the
*new* verified EXE in helper mode. After the old process closes, the new EXE
atomically replaces the previous file and starts the updated application.
Never requires administrator elevation or executes a remote script.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from src.profile_paths import DATA_DIR

UPDATES = DATA_DIR / "updates"
TARGET_NAME = "WTModManager.exe"


def _validate_target(path: Path):
    path = Path(path).absolute()
    if (path.name.lower() != TARGET_NAME.lower()
            or not path.is_file() or path.is_symlink()):
        raise ValueError("The update target must be the existing WTModManager.exe.")
    if not path.resolve().is_file():
        raise ValueError("The current executable is missing.")
    return path


def _reset_env():
    return {**os.environ, "PYINSTALLER_RESET_ENVIRONMENT": "1"}


def launch_verified_update(new_exe: Path, expected_digest: str) -> None:
    """Called only after SHA-256 verification and explicit user confirmation."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        raise RuntimeError("Automatic replacement requires the packaged Windows EXE.")
    old = _validate_target(Path(sys.executable))
    new = Path(new_exe).absolute()
    if new != UPDATES / TARGET_NAME or new == old or new.is_symlink() or not new.is_file():
        raise ValueError("Staged update must be the verified user-local EXE.")
    if new.stat().st_size < 1024 * 1024:
        raise ValueError("Update executable is incomplete.")
    if not isinstance(expected_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_digest):
        raise ValueError("Invalid update checksum.")
    if _file_sha256(new) != expected_digest:
        raise ValueError("Staged update checksum changed before installation.")
    # Fail before closing the app if its directory is not writable.
    try:
        with tempfile.NamedTemporaryFile(dir=old.parent, prefix=".wtmm-permission-", delete=True):
            pass
    except OSError as error:
        raise PermissionError(
            "Cannot replace the program in this protected folder. "
            "Move WTModManager.exe to a writable folder and try again."
        ) from error
    subprocess.Popen(
        [str(new), "--apply-update", str(old), str(os.getpid()),
         expected_digest],
        cwd=str(new.parent),
        env=_reset_env(),
        close_fds=True,
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
    )


def _save_status(message: str) -> None:
    UPDATES.mkdir(parents=True, exist_ok=True)
    (UPDATES / "last-update-status.txt").write_text(
        message[:350] + "\n", encoding="utf-8"
    )


def _wait_for_old_process(pid: int, seconds: int = 90) -> None:
    if pid <= 0:
        raise ValueError("Missing parent process.")
    import psutil
    try:
        original = psutil.Process(pid)
        original_created = original.create_time()
    except psutil.NoSuchProcess:
        return
    start = time.monotonic()
    while time.monotonic() - start < seconds:
        try:
            if (not original.is_running()
                    or original.create_time() != original_created
                    or original.status() == psutil.STATUS_ZOMBIE):
                return
        except psutil.NoSuchProcess:
            return
        time.sleep(0.3)
    raise TimeoutError("Old WT Mod Manager did not close within the update window.")


def _file_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(256 * 1024), b""):
            sha.update(data)
    return sha.hexdigest()


def apply_verified_update(args: list[str]) -> int:
    """Entry point activated only via --apply-update from the signed-off UI."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return 2
    if len(args) != 3:
        return 2
    try:
        helper = Path(sys.executable).absolute()
        if helper != UPDATES / TARGET_NAME or helper.is_symlink():
            raise ValueError("Update helper must run from the user's updates directory.")
        digest = args[2]
        if not re.fullmatch(r"[a-f0-9]{64}", digest) or _file_sha256(helper) != digest:
            raise ValueError("Update helper checksum failed verification.")
        target = _validate_target(Path(args[0]))
        pid = int(args[1])
        _wait_for_old_process(pid)
        target = _validate_target(target)
        UPDATES.mkdir(parents=True, exist_ok=True)
        backup = UPDATES / "WTModManager.previous.exe"
        pending = target.parent / ".wtmm-update-pending.exe"
        if pending.exists() or pending.is_symlink():
            raise ValueError("An existing update operation must be cleared.")
        shutil.copy2(target, backup)
        try:
            shutil.copy2(helper, pending)
            if pending.stat().st_size < 1024 * 1024:
                raise ValueError("The staged executable is incomplete.")
            os.replace(pending, target)
        finally:
            pending.unlink(missing_ok=True)
        _save_status("Обновление установлено. Предыдущая версия сохранена в updates.")
        try:
            subprocess.Popen(
                [str(target), "--updated"],
                cwd=str(target.parent),
                env=_reset_env(),
                close_fds=True,
                creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
            )
        except OSError:
            # If the new EXE cannot start, restore the previous version.
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".wtmm-rollback-",
                                             suffix=".exe", delete=False) as temporary:
                rollback = Path(temporary.name)
            try:
                shutil.copy2(backup, rollback)
                os.replace(rollback, target)
            finally:
                rollback.unlink(missing_ok=True)
            _save_status("Не удалось запустить обновление. Восстановлена прежняя версия.")
            raise
        return 0
    except Exception as error:
        try:
            _save_status("Не удалось обновить приложение: " + str(error))
        except OSError:
            pass
        return 1
