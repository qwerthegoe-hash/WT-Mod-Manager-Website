"""Secure opt-in updates for a single portable Windows EXE.

Fetch a trusted GitHub Release, verify its server-published SHA-256 digest,
then stage the new EXE in the user's %LOCALAPPDATA% directory. A separate
verified copy will replace the old EXE only after the user approves and closes
the running app. Website/catalog data never need an EXE update.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from src.profile_paths import DATA_DIR
from src.offline_mode import is_offline
from src.release_rollout import eligible, fetch_policy

VERSION = "1.3.0-beta.14"
PROJECT_ROOT = (Path(sys._MEIPASS) if getattr(sys, "frozen", False)
                and hasattr(sys, "_MEIPASS") else Path(__file__).resolve().parent.parent)
CONFIG_FILE = PROJECT_ROOT / "config" / "update_config.json"
MAX_EXE_BYTES = 350 * 1024 * 1024
_VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)[.-]?(\d+))?$", re.I)
_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA_PATTERN = re.compile(r"^sha256:([a-f0-9]{64})$", re.I)


def is_installed_app():
    """Inno Setup installs the app payload plus a harmless local marker.

    PyInstaller onefile portable builds do not have this marker. The marker
    is outside _internal so both layouts resolve it at the same location.
    """
    return (sys.platform == "win32"
            and bool(getattr(sys, "frozen", False))
            and (Path(sys.executable).parent / "wtmm.installed").is_file())


def version_tuple(value):
    """Comparable numeric version; final is newer than beta of the same version."""
    found = _VERSION_PATTERN.fullmatch(str(value or "").strip())
    if not found:
        return None
    stage = {"alpha": 0, "beta": 1, "rc": 2}.get((found.group(4) or "").lower(), 3)
    return (int(found.group(1)), int(found.group(2)), int(found.group(3)),
            stage, int(found.group(5) or 0))


def _configuration():
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data
    except (OSError, ValueError):
        return {}


def repository():
    value = _configuration().get("github_repository", "")
    return value if isinstance(value, str) and _REPO_PATTERN.fullmatch(value) else None


def update_channel():
    """Per-user channel preference selected during setup, never a repo secret."""
    preference = DATA_DIR / "update-channel.json"
    try:
        state = json.loads(preference.read_text(encoding="utf-8"))
        if isinstance(state, dict) and state.get("channel") in ("stable", "beta"):
            return state["channel"]
    except (OSError, ValueError, TypeError):
        pass
    value = _configuration().get("channel", "stable")
    return value if value in ("stable", "beta") else "stable"


def set_update_channel(channel: str) -> str:
    """Save the selected update channel for this Windows user atomically."""
    if channel not in ("stable", "beta"):
        raise ValueError("Unknown update channel.")
    preference = DATA_DIR / "update-channel.json"
    preference.parent.mkdir(parents=True, exist_ok=True)
    if preference.is_symlink():
        raise ValueError("Update channel settings cannot be a symlink.")
    temporary = preference.with_suffix(".tmp")
    try:
        temporary.write_text(json.dumps({"channel": channel}), encoding="utf-8")
        temporary.replace(preference)
    finally:
        temporary.unlink(missing_ok=True)
    return channel


def _api_json(url):
    request = urllib.request.Request(url, headers={
        "User-Agent": "WTModManager/1.3 Portable Updater",
        "Accept": "application/vnd.github+json"
    })
    with urllib.request.urlopen(request, timeout=15) as stream:
        if int(stream.headers.get("Content-Length", "0")) > 2 * 1024 * 1024:
            raise ValueError("Release metadata too large.")
        raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Release metadata too large.")
    return json.loads(raw)


def _release_candidate(payload, repo):
    if not isinstance(payload, dict) or payload.get("draft"):
        return None
    tag = payload.get("tag_name")
    key = version_tuple(tag)
    if key is None or key <= version_tuple(VERSION):
        return None
    if update_channel() == "stable" and payload.get("prerelease"):
        return None
    if not re.fullmatch(r"v?[0-9A-Za-z.-]{5,40}", str(tag)):
        return None
    prefix = f"https://github.com/{repo}/releases/download/{tag}/"
    name_required = "WTModManager-Setup.exe" if is_installed_app() else "WTModManager.exe"
    for item in payload.get("assets", []):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        url = item.get("browser_download_url")
        digest = item.get("digest")
        size = item.get("size")
        if (name == name_required and url == prefix + name_required
                and isinstance(digest, str) and _SHA_PATTERN.fullmatch(digest)
                and isinstance(size, int) and 1024 * 1024 <= size <= MAX_EXE_BYTES):
            return {
                "version": tag, "url": url, "name": name,
                "kind": "installer" if name == "WTModManager-Setup.exe" else "portable",
                "digest": digest.split(":", 1)[1].lower(), "size": size,
                "release_url": prefix.rsplit("/releases/download/", 1)[0] +
                               "/releases/tag/" + str(tag),
                "_sort_key": key,
            }
    return None


def find_update():
    if is_offline():
        return None  # No GitHub calls in explicit offline mode.
    repo = repository()
    if not repo:
        return None
    payload = _api_json(f"https://api.github.com/repos/{repo}/releases?per_page=30")
    if not isinstance(payload, list):
        raise ValueError("Unexpected release metadata.")
    policy = fetch_policy()
    found = [_release_candidate(item, repo) for item in payload]
    valid = [item for item in found if item is not None and
             eligible(str(item["version"]), policy)]
    if not valid:
        return None
    newest = max(valid, key=lambda item: item["_sort_key"])
    return {key: value for key, value in newest.items() if key != "_sort_key"}


def download_verified(info, progress_callback=None):
    """Download into user-local staging with hash verification and optional progress.

    A callback reports integer percentages (0..100). Existing callers can
    omit it; progress is only reported for the verified release asset.
    """
    if is_offline():
        raise OSError("WT Offline Mode включён: скачивание обновлений остановлено.")
    repo = repository()
    if not repo or not isinstance(info, dict):
        raise ValueError("Updater is not configured.")
    tag = str(info.get("version", ""))
    filename = "WTModManager-Setup.exe" if is_installed_app() else "WTModManager.exe"
    kind = "installer" if filename == "WTModManager-Setup.exe" else "portable"
    url = f"https://github.com/{repo}/releases/download/{tag}/{filename}"
    if (info.get("name") != filename or info.get("kind") != kind
            or info.get("url") != url or version_tuple(tag) is None
            or not isinstance(info.get("digest"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", info["digest"])
            or not isinstance(info.get("size"), int)
            or not 1024 * 1024 <= info["size"] <= MAX_EXE_BYTES):
        raise ValueError("Update manifest failed validation.")
    target_dir = DATA_DIR / "updates"
    target_dir.mkdir(parents=True, exist_ok=True)
    if target_dir.is_symlink():
        raise ValueError("Update cache folder must not be a symbolic link.")
    target = target_dir / filename
    temp = target_dir / filename.replace(".exe", ".download")
    if target.exists() and target.is_file() and not target.is_symlink() and target.stat().st_size == info["size"]:
        if _sha256(target) == info["digest"]:
            if progress_callback is not None:
                progress_callback(100)
            return target
    # Reserve space for both the partial download and verified staged copy.
    # Installed/portable updates never delete personal mods to free space.
    remaining = shutil.disk_usage(target_dir).free
    required = info["size"] * 2 + 64 * 1024 * 1024
    if remaining < required:
        raise OSError(
            "Недостаточно места для безопасного обновления. "
            "Освободи место на диске и повтори загрузку."
        )
    downloaded = 0
    last_percent = -1
    sha = hashlib.sha256()
    if progress_callback is not None:
        progress_callback(0)
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": "WTModManager-Updater/1.3"
        })
        with urllib.request.urlopen(request, timeout=45) as response, temp.open("wb") as file:
            if urlsplit(response.geturl()).scheme != "https":
                raise ValueError("Update redirected to insecure HTTP.")
            while True:
                block = response.read(256 * 1024)
                if not block:
                    break
                downloaded += len(block)
                if downloaded > info["size"] or downloaded > MAX_EXE_BYTES:
                    raise ValueError("Downloaded update is larger than expected.")
                sha.update(block)
                file.write(block)
                percent = min(99, downloaded * 100 // info["size"])
                if progress_callback is not None and percent > last_percent:
                    last_percent = percent
                    progress_callback(percent)
        if downloaded != info["size"] or sha.hexdigest() != info["digest"]:
            raise ValueError("Update SHA-256 or file size mismatch.")
        with temp.open("rb") as downloaded_file:
            signature = downloaded_file.read(2)
        if signature != b"MZ":
            raise ValueError("Download is not a Windows executable.")
        temp.replace(target)
        if progress_callback is not None:
            progress_callback(100)
        return target
    finally:
        temp.unlink(missing_ok=True)


def _sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(256 * 1024), b""):
            h.update(block)
    return h.hexdigest()
