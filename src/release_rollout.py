"""Consent-based staged Beta releases. A public manifest can only *restrict*
ordinary GitHub Releases, never authorize unsigned or arbitrary download URLs.
No hardware fingerprint, IP logging, or remote telemetry.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen, Request

from src.profile_paths import DATA_DIR

SETTING = DATA_DIR / "early-beta.json"
SOURCE = ("https://raw.githubusercontent.com/qwerthegoe-hash/"
          "WT-Mod-Manager-Website/main/docs/json/release-rollout.json")
TAG = re.compile(r"^v\d+\.\d+\.\d+(?:-beta\.\d+)?$")
LIMIT = 16 * 1024


def _load() -> dict:
    try:
        if SETTING.is_symlink() or SETTING.stat().st_size > 2048:
            return {}
        data = json.loads(SETTING.read_text("utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def early_access() -> bool:
    return _load().get("opt_in") is True


def set_early_access(value: bool) -> bool:
    if type(value) is not bool:
        raise ValueError("Invalid early access state.")
    old = _load()
    # Random per-install seed never leaves the PC; not based on hardware.
    seed = str(old.get("seed", ""))
    if not re.fullmatch(r"[a-f0-9]{32}", seed):
        seed = secrets.token_hex(16)
    SETTING.parent.mkdir(parents=True, exist_ok=True)
    if SETTING.is_symlink():
        raise OSError("Unexpected early access preference link.")
    tmp = SETTING.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps({"schema": 1, "opt_in": value, "seed": seed}),
                       encoding="utf-8")
        os.replace(tmp, SETTING)
    finally:
        tmp.unlink(missing_ok=True)
    return value


def fetch_policy() -> dict | None:
    """A temporary network failure must not silently enable early Beta rollout."""
    try:
        req = Request(SOURCE, headers={
            "User-Agent": "WTModManager-Rollout/1.0",
            "Accept": "application/json"
        })
        with urlopen(req, timeout=6) as response:
            if urlsplit(response.geturl()).hostname != "raw.githubusercontent.com":
                return None
            raw = response.read(LIMIT + 1)
        if len(raw) > LIMIT:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) and data.get("schema") == 1 else None
    except (OSError, ValueError, TypeError):
        return None


def eligible(tag: str, policy: dict | None, preference: dict | None = None) -> bool:
    if not isinstance(tag, str) or not TAG.fullmatch(tag):
        return False
    # Release lists are still filtered by GitHub official digest and HTTPS.
    if policy is None:
        return "-beta." not in tag  # fail closed for Beta on policy outage
    blocked = policy.get("blocked_tags", [])
    if not isinstance(blocked, list) or len(blocked) > 100:
        return False
    if tag in blocked:
        return False
    staged = policy.get("staged", {})
    if not isinstance(staged, dict) or len(staged) > 100:
        return False
    percent = staged.get(tag, 100)
    if type(percent) is not int or not 0 <= percent <= 100:
        return False
    if percent == 100:
        return True
    if percent == 0:
        return False
    state = preference if preference is not None else _load()
    if state.get("opt_in") is not True:
        return False
    seed = str(state.get("seed", ""))
    if not re.fullmatch(r"[a-f0-9]{32}", seed):
        return False
    bucket = int(hashlib.sha256((tag + ":" + seed).encode()).hexdigest()[:8], 16)
    return (bucket % 100) < percent
