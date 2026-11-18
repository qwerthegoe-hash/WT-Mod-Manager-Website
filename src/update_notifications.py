"""Persistent, per-Windows-user update notifications and preferences.

No account credentials, mod contents or server secrets are stored in this file.
Messages are bounded and written atomically, so an unexpected close does not
leave the notification database half-written.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.profile_paths import DATA_DIR

NOTIFICATIONS_FILE = DATA_DIR / "update-notifications.json"
MAX_EVENTS = 60
MAX_TITLE = 110
MAX_MESSAGE = 350
VALID_KINDS = {"update_available", "update_ready", "update_installed",
               "update_failed", "notice"}


def _default():
    return {"events": [], "ignored_version": None, "auto_check": True}


def load_notifications():
    try:
        obj = json.loads(NOTIFICATIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return _default()
    if not isinstance(obj, dict):
        return _default()
    events = obj.get("events", [])
    if not isinstance(events, list):
        events = []
    cleaned = []
    for item in events[-MAX_EVENTS:]:
        if not isinstance(item, dict) or item.get("kind") not in VALID_KINDS:
            continue
        cleaned.append({
            "id": str(item.get("id", ""))[:100],
            "kind": item["kind"],
            "title": str(item.get("title", ""))[:MAX_TITLE],
            "message": str(item.get("message", ""))[:MAX_MESSAGE],
            "version": str(item.get("version", ""))[:50],
            "time": str(item.get("time", ""))[:40],
            "read": bool(item.get("read", False)),
        })
    ignore = obj.get("ignored_version")
    if not isinstance(ignore, str) or len(ignore) > 50:
        ignore = None
    return {"events": cleaned,
            "ignored_version": ignore,
            "auto_check": obj.get("auto_check") is not False}


def _save(state):
    NOTIFICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".wtmm-updates-",
                                       suffix=".tmp",
                                       dir=str(NOTIFICATIONS_FILE.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
        os.replace(name, NOTIFICATIONS_FILE)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def record_event(kind, title, message, version="", event_id=None):
    if kind not in VALID_KINDS:
        raise ValueError("Unsupported update notification")
    state = load_notifications()
    key = str(event_id or (kind + ":" + str(version)))[:100]
    # One unique event per release or terminal update state, no repeated spam.
    for event in state["events"]:
        if event["id"] == key:
            return False
    state["events"].append({
        "id": key, "kind": kind, "title": str(title)[:MAX_TITLE],
        "message": str(message)[:MAX_MESSAGE], "version": str(version)[:50],
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "read": False
    })
    state["events"] = state["events"][-MAX_EVENTS:]
    _save(state)
    return True


def mark_all_read():
    state = load_notifications()
    for item in state["events"]:
        item["read"] = True
    _save(state)


def set_auto_check(value):
    state = load_notifications()
    state["auto_check"] = bool(value)
    _save(state)


def ignore_version(version):
    state = load_notifications()
    state["ignored_version"] = str(version)[:50] if version else None
    _save(state)
