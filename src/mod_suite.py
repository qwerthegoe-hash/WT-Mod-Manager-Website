"""WT Mod Suite: dry-run, conflicts, integrity, modpack interchange, timeline.

All writes here affect WTMM's per-user metadata only. Actual game file
changes remain exclusively in game_mod_installer.install_planned and require
explicit user confirmation. Exported modpacks list identifiers, not ZIP bytes.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from src.profile_paths import DATA_DIR
from src.game_mod_installer import CopyPlan, InstallError, MAX_FILES

REGISTRY_DIR = DATA_DIR / "game-installs"
TIMELINE_PATH = REGISTRY_DIR / "timeline.json"
UUID = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", re.I)
TRANSACTION = re.compile(r"^[a-f0-9]{32}$")
HASH = re.compile(r"^[a-f0-9]{64}$")
SAFE_NAME = re.compile(r"^[\w .()\-]{1,72}$", re.UNICODE)
MAX_LOG = 100


@dataclass(frozen=True)
class Preview:
    files: int
    additions: int
    replacements: int
    unchanged: int
    bytes_to_copy: int
    required_space: int
    conflicting_filenames: tuple[str, ...]


def preview_install(plan: Iterable[CopyPlan], available_bytes: int | None = None) -> Preview:
    """Read-only inspection. Overwriting an identical file is not a conflict."""
    entries = list(plan)
    if not entries or len(entries) > MAX_FILES:
        raise InstallError("Некорректный список файлов установки.")
    seen: set[Path] = set()
    additions = replacements = unchanged = copy_size = backup_size = 0
    names: list[str] = []
    for item in entries:
        src, dst = Path(item.source), Path(item.destination)
        if dst in seen:
            raise InstallError("Дублирующиеся назначения модификации.")
        seen.add(dst)
        if not src.is_file() or src.is_symlink() or dst.is_symlink():
            raise InstallError("Источник или назначение недоступно/является ссылкой.")
        if dst.exists() and not dst.is_file():
            raise InstallError("Вместо назначения обнаружена папка.")
        if item.identical:
            unchanged += 1
            continue
        size = src.stat().st_size
        if size > 250 * 1024 * 1024:
            raise InstallError("Файл мода превышает лимит 250 МиБ.")
        copy_size += size
        if dst.exists():
            replacements += 1
            backup_size += dst.stat().st_size
            names.append(dst.name[:80])
        else:
            additions += 1
    required = copy_size * 2 + backup_size + 16 * 1024 * 1024
    if available_bytes is not None and available_bytes < required:
        raise InstallError("Недостаточно места для установки и резервных копий.")
    return Preview(len(entries), additions, replacements, unchanged,
                   copy_size, required, tuple(names[:20]))


def resolve_conflicts(plan: Iterable[CopyPlan], decision: str) -> list[CopyPlan]:
    if decision not in {"replace", "keep", "cancel"}:
        raise ValueError("Неизвестное решение конфликта.")
    if decision == "cancel":
        return []
    entries = list(plan)
    if decision == "replace":
        return entries
    return [item for item in entries if not (item.existing and not item.identical)]


def _atomic_json(target: Path, data: dict | list) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise OSError("Ссылка вместо локального журнала.")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=target.parent,
        prefix=".wtmm-history-", suffix=".tmp", delete=False
    ) as handle:
        tmp = Path(handle.name)
        json.dump(data, handle, ensure_ascii=False, indent=2)
    try:
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)


def _read_json(path: Path, limit: int = 256 * 1024):
    try:
        if path.is_symlink() or path.stat().st_size > limit:
            return None
        return json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None


def history() -> list[dict]:
    raw = _read_json(TIMELINE_PATH)
    if not isinstance(raw, list):
        return []
    result = []
    for item in raw[-MAX_LOG:]:
        if not isinstance(item, dict) or not TRANSACTION.fullmatch(str(item.get("transaction", ""))):
            continue
        if item.get("event") not in {"installed", "restored"}:
            continue
        count = item.get("files", 0)
        if type(count) is not int:
            continue
        result.append({
            "transaction": item["transaction"],
            "event": item["event"],
            "time_utc": str(item.get("time_utc", ""))[:32],
            "files": min(1000, max(0, count)),
        })
    return result


def append_history(event: str, transaction: str, files: int) -> None:
    if event not in {"installed", "restored"} or not TRANSACTION.fullmatch(transaction):
        raise ValueError("Некорректное событие установки.")
    events = history()
    events.append({
        "event": event, "transaction": transaction,
        "files": int(files), "time_utc": datetime.now(timezone.utc).isoformat(),
    })
    _atomic_json(TIMELINE_PATH, events[-MAX_LOG:])


def installed_integrity() -> list[dict]:
    """Read-only audit. Only file names and status codes leave this function."""
    results = []
    if not REGISTRY_DIR.is_dir() or REGISTRY_DIR.is_symlink():
        return results
    snapshots = []
    for folder in REGISTRY_DIR.iterdir():
        if not folder.is_dir() or folder.is_symlink() or not TRANSACTION.fullmatch(folder.name):
            continue
        data = _read_json(folder / "manifest.json")
        if isinstance(data, dict) and isinstance(data.get("files"), list) and \
                len(data["files"]) <= MAX_FILES:
            timestamp = data.get("created_at", 0)
            snapshots.append((timestamp if type(timestamp) is int else 0,
                              folder, data["files"]))
    snapshots.sort(key=lambda row: row[0], reverse=True)
    latest_targets = set()
    for _, folder, rows in snapshots[:MAX_LOG]:
        for item in rows:
            if not isinstance(item, dict) or not HASH.fullmatch(str(item.get("installed_digest", ""))):
                continue
            dest = Path(str(item.get("target", "")))
            if dest in latest_targets:
                continue  # Previous versions replaced by a new install aren't broken.
            latest_targets.add(dest)
            status = "unknown"
            try:
                if dest.is_symlink():
                    status = "link"
                elif not dest.is_file():
                    status = "missing"
                elif dest.stat().st_size > 250 * 1024 * 1024:
                    status = "oversized"
                else:
                    with dest.open("rb") as stream:
                        dig = hashlib.file_digest(stream, "sha256").hexdigest()
                    status = "ok" if dig == item["installed_digest"] else "changed"
            except OSError:
                status = "unavailable"
            results.append({"file": dest.name[:80], "status": status,
                            "transaction": folder.name})
            if len(results) >= 200:
                return results
    return results


def compatibility(metadata: dict, game_version: str | None = None) -> dict:
    """No invented automatic game version or claims of tested compatibility."""
    if not isinstance(metadata, dict):
        return {"status": "unknown", "reason": "Нет метаданных."}
    declared = metadata.get("game_version")
    if not isinstance(declared, str) or not re.fullmatch(r"\d+(?:\.\d+){1,3}", declared):
        return {"status": "unknown", "reason": "Автор не указал версию игры."}
    if not game_version or not re.fullmatch(r"\d+(?:\.\d+){1,3}", game_version):
        return {"status": "unknown", "reason": "Текущая версия War Thunder не указана."}
    return {"status": "match" if game_version == declared else "review",
            "reason": "Версия заявлена автором; реальную работу мода нужно проверить.",
            "declared": declared, "actual": game_version}


def modpack_manifest(account_dir: Path, selected: list[str], name: str) -> dict:
    if not SAFE_NAME.fullmatch(name) or len(selected) > 300:
        raise ValueError("Неверное название или размер модпака.")
    if account_dir.is_symlink():
        raise ValueError("Недопустимая папка аккаунта.")
    installed = _read_json(account_dir / "imported-mods.json")
    if not isinstance(installed, dict):
        installed = {}
    mods = []
    for key in dict.fromkeys(selected):
        if not isinstance(key, str) or not UUID.fullmatch(key) or key not in installed:
            continue
        entry = installed[key]
        if not isinstance(entry, dict):
            continue
        mods.append({"id": key, "version": str(entry.get("version", ""))[:32]})
    return {"schema": 1, "type": "wtmm-modpack", "name": name,
            "mods": mods, "notice": "Manifest only; no files or automatic installation."}


def read_modpack(data: dict, available_ids: set[str]) -> list[str]:
    if not isinstance(data, dict) or data.get("schema") != 1 or data.get("type") != "wtmm-modpack":
        raise ValueError("Неподдерживаемый модпак.")
    mods = data.get("mods")
    if not isinstance(mods, list) or len(mods) > 300:
        raise ValueError("Недопустимый список модов.")
    if any(not isinstance(row, dict) or not UUID.fullmatch(str(row.get("id", ""))) for row in mods):
        raise ValueError("Повреждённый идентификатор мода.")
    return list(dict.fromkeys(row["id"] for row in mods if row["id"] in available_ids))
