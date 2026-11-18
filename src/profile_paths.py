"""Private per-Windows-user storage. Never write into Program Files."""
import json
import os
import re
import shutil
import sys
from pathlib import Path

APP_NAME = "WTModManager"
PROJECT_ROOT = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
                else Path(__file__).resolve().parent.parent)
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

# Synced mods are kept separate for each authenticated website account.
# Local files added from the PC remain in MODS_DIR and are never moved.
_active_online_account = None


def set_active_online_account(account_id):
    global _active_online_account
    import re
    value = str(account_id or "")
    _active_online_account = (
        value if re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            value, flags=re.IGNORECASE
        ) else None
    )


def online_mod_folder(category):
    categories = {"sights", "sounds", "camouflages"}
    if _active_online_account is None or category not in categories:
        return None
    return DATA_DIR / "accounts" / _active_online_account / "mods" / category



# Named sets group imported online assets in the Windows UI. A set changes
# visibility only; it never copies, deletes or changes original downloaded files.
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)


def _account_path(account_id):
    if not isinstance(account_id, str) or not _UUID.fullmatch(account_id):
        raise ValueError("Invalid online account")
    return DATA_DIR / "accounts" / account_id


def load_mod_profiles(account_id):
    account = _account_path(account_id)
    try:
        data = json.loads((account / "mod-profiles.json").read_text("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("profiles"), dict):
            raise ValueError("Invalid profile data")
        profiles = {}
        for name, ids in data["profiles"].items():
            if (isinstance(name, str) and 2 <= len(name) <= 40
                    and isinstance(ids, list) and len(ids) <= 300):
                valid = list(dict.fromkeys(
                    ident for ident in ids
                    if isinstance(ident, str) and _UUID.fullmatch(ident)
                ))
                profiles[name] = valid
        active = data.get("active")
        if active not in profiles:
            active = None
        return {"active": active, "profiles": profiles}
    except (OSError, ValueError, TypeError):
        return {"active": None, "profiles": {}}


def _write_mod_profiles(account_id, data):
    path = _account_path(account_id) / "mod-profiles.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def save_mod_profile(account_id, name, mod_ids):
    if (not isinstance(name, str) or not 2 <= len(name.strip()) <= 40
            or any(ord(char) < 32 for char in name)):
        raise ValueError("Profile name must contain 2–40 characters")
    name = name.strip()
    if not isinstance(mod_ids, list) or len(mod_ids) > 300:
        raise ValueError("Invalid mod selection")
    account = _account_path(account_id)
    available = {}
    try:
        available = json.loads((account / "imported-mods.json").read_text("utf-8"))
        if not isinstance(available, dict):
            available = {}
    except (OSError, ValueError):
        pass
    selected = list(dict.fromkeys(
        ident for ident in mod_ids
        if isinstance(ident, str) and _UUID.fullmatch(ident) and ident in available
    ))
    state = load_mod_profiles(account_id)
    if len(state["profiles"]) >= 20 and name not in state["profiles"]:
        raise ValueError("Maximum of 20 profiles reached")
    if any(old.casefold() == name.casefold() and old != name for old in state["profiles"]):
        raise ValueError("A profile with this name exists")
    state["profiles"][name] = selected
    _write_mod_profiles(account_id, state)
    return len(selected)


def set_active_mod_profile(account_id, name=None):
    state = load_mod_profiles(account_id)
    if name is not None and name not in state["profiles"]:
        raise ValueError("Profile not found")
    state["active"] = name
    _write_mod_profiles(account_id, state)


def delete_mod_profile(account_id, name):
    state = load_mod_profiles(account_id)
    if name not in state["profiles"]:
        return False
    del state["profiles"][name]
    if state["active"] == name:
        state["active"] = None
    _write_mod_profiles(account_id, state)
    return True


def online_visible_files(category):
    """Files allowed by the linked account's active profile, if any."""
    folder = online_mod_folder(category)
    if folder is None or not folder.is_dir():
        return []
    state = load_mod_profiles(_active_online_account)
    active = state["active"]
    if active is None:
        return [
            file for file in folder.iterdir()
            if file.is_file() and not file.is_symlink()
        ]
    allowed = set(state["profiles"].get(active, []))
    account = _account_path(_active_online_account)
    try:
        entries = json.loads((account / "imported-mods.json").read_text("utf-8"))
        if not isinstance(entries, dict):
            return []
    except (OSError, ValueError):
        return []
    mapped_category = {"camouflages": "camouflage"}.get(category, category)
    results = []
    for mod_id in allowed:
        item = entries.get(mod_id)
        if not isinstance(item, dict) or item.get("category") != mapped_category:
            continue
        for name in item.get("files", []):
            if (not isinstance(name, str) or name != Path(name).name
                    or not name.startswith(mod_id[:8] + "-")):
                continue
            file = folder / name
            if file.is_file() and not file.is_symlink():
                results.append(file)
    return list(dict.fromkeys(results))


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
