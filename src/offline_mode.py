"""Explicit per-user offline switch: local assets/settings always remain usable."""
from __future__ import annotations
import json
import os
from pathlib import Path
from src.profile_paths import DATA_DIR

PATH = DATA_DIR / "connectivity.json"


def is_offline() -> bool:
    try:
        if PATH.is_symlink() or PATH.stat().st_size > 2048:
            return False
        record = json.loads(PATH.read_text("utf-8"))
        return isinstance(record, dict) and record.get("offline") is True
    except (OSError, ValueError, TypeError, UnicodeError):
        return False


def set_offline(enabled: bool) -> bool:
    if type(enabled) is not bool:
        raise ValueError("Invalid offline state.")
    PATH.parent.mkdir(parents=True, exist_ok=True)
    if PATH.is_symlink():
        raise OSError("Unsafe connectivity preference path.")
    tmp = PATH.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as out:
            json.dump({"schema": 1, "offline": enabled}, out)
        os.replace(tmp, PATH)
    finally:
        tmp.unlink(missing_ok=True)
    return enabled


def require_network() -> None:
    if is_offline():
        raise RuntimeError(
            "Включён WT Offline Mode. Отключи его в разделе «Загрузки», "
            "чтобы использовать сайт, синхронизацию и VirusTotal."
        )
