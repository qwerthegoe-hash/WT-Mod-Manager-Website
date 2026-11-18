"""Private per-Windows-user storage. Never write into Program Files."""
import os
import shutil
import sys
from pathlib import Path

APP_NAME = "WTModManager"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEGACY_DATA = PROJECT_ROOT / "data"
LEGACY_MODS = PROJECT_ROOT / "mods"


def user_data_dir():
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_NAME
    # Non-Windows testing/development fallback, never the installation folder.
    return Path.home() / ".local" / "share" / APP_NAME


DATA_DIR = user_data_dir()
SETTINGS_FILE = DATA_DIR / "settings.json"
MODS_DIR = DATA_DIR / "mods"


def migrate_legacy_data():
    """Copy old data once; keep originals and never overwrite user files.

    Migration can be retried if interrupted. The marker is written only after
    every copy succeeds. On failure, raise an error rather than silently
    replacing an existing profile with defaults.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    marker = DATA_DIR / ".migration-v1-complete"
    if marker.exists():
        return

    legacy_settings = LEGACY_DATA / "settings.json"
    if legacy_settings.is_file() and not SETTINGS_FILE.exists():
        shutil.copy2(legacy_settings, SETTINGS_FILE)

    if LEGACY_MODS.is_dir():
        for category in ("sights", "camouflages", "sounds", "configurations"):
            old = LEGACY_MODS / category
            if not old.is_dir():
                continue
            destination = MODS_DIR / category
            destination.mkdir(parents=True, exist_ok=True)
            for item in old.iterdir():
                # Only copy regular files, never overwrite existing files.
                if item.is_file() and not item.is_symlink():
                    target = destination / item.name
                    if not target.exists():
                        shutil.copy2(item, target)
    marker.write_text("Migration completed; legacy files retained.\n", encoding="utf-8")
