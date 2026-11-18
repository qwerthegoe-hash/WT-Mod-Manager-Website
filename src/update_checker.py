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
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from src.profile_paths import DATA_DIR

VERSION = "1.3.0-beta.1"
PROJECT_ROOT = (Path(sys._MEIPASS) if getattr(sys, "frozen", False)
                and hasattr(sys, "_MEIPASS") else Path(__file__).resolve().parent.parent)
CONFIG_FILE = PROJECT_ROOT / "config" / "update_config.json"
MAX_EXE_BYTES = 350 * 1024 * 1024
_VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)[.-]?(\d+))?$", re.I)
_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA_PATTERN = re.compile(r"^sha256:([a-f0-9]{64})$", re.I)


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
    value = _configuration().get("channel", "stable")
    return value if value in ("stable", "beta") else "stable"


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
    for item in payload.get("assets", []):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        url = item.get("browser_download_url")
        digest = item.get("digest")
        size = item.get("size")
        if (name == "WTModManager.exe" and url == prefix + "WTModManager.exe"
                and isinstance(digest, str) and _SHA_PATTERN.fullmatch(digest)
                and isinstance(size, int) and 1024 * 1024 <= size <= MAX_EXE_BYTES):
            return {
                "version": tag, "url": url, "name": name,
                "digest": digest.split(":", 1)[1].lower(), "size": size,
                "release_url": prefix.rsplit("/releases/download/", 1)[0] +
                               "/releases/tag/" + str(tag),
                "_sort_key": key,
            }
    return None


def find_update():
    repo = repository()
    if not repo:
        return None
    payload = _api_json(f"https://api.github.com/repos/{repo}/releases?per_page=30")
    if not isinstance(payload, list):
        raise ValueError("Unexpected release metadata.")
    found = [_release_candidate(item, repo) for item in payload]
    valid = [item for item in found if item is not None]
    if not valid:
        return None
    newest = max(valid, key=lambda item: item["_sort_key"])
    return {key: value for key, value in newest.items() if key != "_sort_key"}


def download_verified(info):
    """Bounded stream from the official release, verified before staging."""
    repo = repository()
    if not repo or not isinstance(info, dict):
        raise ValueError("Updater is not configured.")
    tag = str(info.get("version", ""))
    url = f"https://github.com/{repo}/releases/download/{tag}/WTModManager.exe"
    if (info.get("url") != url or version_tuple(tag) is None
            or not isinstance(info.get("digest"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", info["digest"])
            or not isinstance(info.get("size"), int)
            or not 1024 * 1024 <= info["size"] <= MAX_EXE_BYTES):
        raise ValueError("Update manifest failed validation.")
    target_dir = DATA_DIR / "updates"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "WTModManager.exe"
    temp = target_dir / "WTModManager.download"
    if target.exists() and target.is_file() and target.stat().st_size == info["size"]:
        if _sha256(target) == info["digest"]:
            return target
    downloaded = 0
    sha = hashlib.sha256()
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
        if downloaded != info["size"] or sha.hexdigest() != info["digest"]:
            raise ValueError("Update SHA-256 or file size mismatch.")
        if temp.read_bytes()[:2] != b"MZ":
            raise ValueError("Download is not a Windows executable.")
        temp.replace(target)
        return target
    finally:
        temp.unlink(missing_ok=True)


def _sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(256 * 1024), b""):
            h.update(block)
    return h.hexdigest()
