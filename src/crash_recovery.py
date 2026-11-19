"""Privacy-preserving crash reports and post-update recovery suggestions.

This module never sends telemetry, stores exception messages, traceback source
lines, arguments, user names, mod file names, credentials or absolute paths.
An unexpected exit is a hint, not proof of a failed update.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import threading
import traceback
from pathlib import Path

from src.profile_paths import DATA_DIR

RECOVERY_DIR = DATA_DIR / "recovery"
SESSION_FILE = RECOVERY_DIR / "session.json"
CRASH_DIR = RECOVERY_DIR / "crashes"
MAX_REPORTS = 8
SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z_0-9]{0,70}$")
_notice: dict | None = None
_original_sys_hook = sys.excepthook
_original_thread_hook = getattr(threading, "excepthook", None)


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_json(path: Path) -> dict:
    try:
        if path.is_symlink() or path.stat().st_size > 4096:
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def start_session(updated: bool = False) -> dict:
    """Remember prior unclean exits while leaving all user files untouched."""
    global _notice
    previous = _read_json(SESSION_FILE)
    warning = bool(previous.get("running"))
    _notice = {
        "unclean": warning,
        "after_update": bool(previous.get("updated")),
        "crashed": bool(previous.get("crashed")),
    } if warning else None
    _write_json(SESSION_FILE, {
        "running": True, "updated": bool(updated), "crashed": False,
        "started_at": _utc()
    })
    return dict(_notice or {})


def last_recovery_notice() -> dict:
    return dict(_notice or {})


def report_crash(exc_type, exc, tb) -> Path | None:
    """Only limited diagnostic codes; no exception message or traceback text."""
    frames = traceback.extract_tb(tb, limit=12) if tb else []
    safe_frames = []
    for frame in frames[-8:]:
        # Store only module/function names and line numbers, not local paths.
        function = str(frame.name)
        if not SAFE_NAME.fullmatch(function):
            function = "unknown"
        safe_frames.append({"function": function, "line": max(0, frame.lineno)})
    error_type = getattr(exc_type, "__name__", "UnknownError")
    if not SAFE_NAME.fullmatch(str(error_type)):
        error_type = "UnknownError"
    payload = {
        "schema": 1,
        "time_utc": _utc(),
        "type": str(error_type),
        "frames": safe_frames,
        "privacy": "No exception messages, absolute paths or personal data.",
    }
    try:
        CRASH_DIR.mkdir(parents=True, exist_ok=True)
        file = CRASH_DIR / ("crash-" +
                            dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S%f")
                            + ".json")
        _write_json(file, payload)
        reports = sorted(CRASH_DIR.glob("crash-*.json"))
        for older in reports[:-MAX_REPORTS]:
            if older.is_file() and not older.is_symlink():
                older.unlink(missing_ok=True)
        existing = _read_json(SESSION_FILE)
        if existing.get("running"):
            existing["crashed"] = True
            _write_json(SESSION_FILE, existing)
        return file
    except OSError:
        return None


def latest_report_summary() -> str:
    try:
        files = sorted(CRASH_DIR.glob("crash-*.json"))
        for file in reversed(files):
            report = _read_json(file)
            if report.get("schema") == 1:
                return ("Последний локальный отчёт: " +
                        str(report.get("type", "UnknownError"))[:80] +
                        ". Отправка только по твоему решению.")
    except OSError:
        pass
    return "Локальных отчётов об ошибках нет."


def latest_safe_report() -> str:
    """Return user-copyable redacted JSON; no automatic uploads."""
    try:
        for file in reversed(sorted(CRASH_DIR.glob("crash-*.json"))):
            report = _read_json(file)
            if report.get("schema") == 1 and report.get("type"):
                return json.dumps(report, ensure_ascii=False, indent=2)
    except OSError:
        pass
    return ""


def clean_exit() -> None:
    try:
        existing = _read_json(SESSION_FILE)
        if existing.get("running"):
            existing["running"] = False
            existing["ended_at"] = _utc()
            _write_json(SESSION_FILE, existing)
    except OSError:
        pass


def install_error_handlers() -> None:
    def on_exception(exc_type, exc, tb):
        report_crash(exc_type, exc, tb)
        _original_sys_hook(exc_type, exc, tb)

    sys.excepthook = on_exception
    if _original_thread_hook:
        def on_thread_exception(args):
            report_crash(args.exc_type, args.exc_value, args.exc_traceback)
            _original_thread_hook(args)
        threading.excepthook = on_thread_exception
