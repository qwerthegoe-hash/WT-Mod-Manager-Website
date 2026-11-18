"""Opt-in verified GitHub Releases update checking and installer download."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from src.profile_paths import DATA_DIR

VERSION = "1.2.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "update_config.json"
MAX_INSTALLER_BYTES = 350 * 1024 * 1024


def version_tuple(value):
    numbers = re.findall(r"\d+", str(value).removeprefix("v"))
    return tuple(int(v) for v in (numbers[:3] + ["0"] * 3)[:3])


def repository():
    if not CONFIG_FILE.is_file():
        return None
    conf = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    value = conf.get("github_repository", "")
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        return None
    return value


def find_update():
    repo = repository()
    if not repo:
        return None
    api = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(api, headers={"User-Agent":"WTModManager-Updater", "Accept":"application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=10) as res:
        payload = json.load(res)
    tag = payload.get("tag_name", "")
    if version_tuple(tag) <= version_tuple(VERSION):
        return None
    prefix = f"https://github.com/{repo}/releases/download/"
    for asset in payload.get("assets", []):
        url = asset.get("browser_download_url", "")
        name = asset.get("name", "")
        digest = asset.get("digest", "")
        if (isinstance(url, str) and url.startswith(prefix)
                and isinstance(name,str) and name.startswith("WTModManager-Setup-")
                and name.endswith(".exe") and isinstance(digest,str)
                and re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest)
                and isinstance(asset.get("size"),int)
                and 0 < asset["size"] <= MAX_INSTALLER_BYTES):
            return {"version":tag,"url":url,"name":name,"digest":digest.split(":",1)[1].lower(),"size":asset["size"],"release_url":payload.get("html_url", "")}
    return None


def download_verified(info):
    """Download to a per-user directory, verify size AND official asset SHA256."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target_dir = DATA_DIR / "updates"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / info["name"]
    temporary = target.with_suffix(".download")
    sha = hashlib.sha256()
    downloaded = 0
    try:
        request = urllib.request.Request(info["url"],headers={"User-Agent":"WTModManager-Updater"})
        with urllib.request.urlopen(request, timeout=30) as response, temporary.open("wb") as output:
            # urllib follows redirects. Only allow HTTPS final destinations.
            if not response.geturl().startswith("https://"):
                raise ValueError("Update redirected to a non-HTTPS URL")
            while True:
                block=response.read(1024*256)
                if not block:
                    break
                downloaded += len(block)
                if downloaded > MAX_INSTALLER_BYTES:
                    raise ValueError("Installer exceeded download limit")
                sha.update(block)
                output.write(block)
        if downloaded != info["size"] or sha.hexdigest()!=info["digest"]:
            raise ValueError("Installer size or SHA256 digest does not match release")
        temporary.replace(target)
        return target
    finally:
        temporary.unlink(missing_ok=True)
