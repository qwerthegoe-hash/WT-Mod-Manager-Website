"""Safe, explicit War Thunder custom-content installer.

Only writes supported custom content, never game binaries. User must pick the
destination, and the game must be closed. Every replacement has a local backup.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.profile_paths import DATA_DIR

MAX_FILES = 128
MAX_TOTAL_BYTES = 350 * 1024 * 1024
MAX_FILE_BYTES = 90 * 1024 * 1024
ROOT_BACKUPS = DATA_DIR / "game-installs"
CUSTOM_SIGHT_EXT = {".blk"}
CAMO_EXT = {".blk", ".dds", ".tga", ".png", ".jpg", ".jpeg"}
SOUND_EXT = {".bank", ".strings.bank"}
SCOPE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$", re.I)
TRANSACTION_RE = re.compile(r"^[0-9a-f]{32}$")
_GAME_NAMES = {"aces.exe", "aces64.exe", "warthunder.exe", "warthunder64.exe"}


class InstallError(ValueError):
    pass


@dataclass(frozen=True)
class CopyPlan:
    source: Path
    destination: Path
    existing: bool
    identical: bool


def war_thunder_running() -> bool:
    """Conservative check: refuse game file changes while the game is active."""
    try:
        import psutil
    except ImportError:
        return False
    for process in psutil.process_iter(["name"]):
        try:
            if str(process.info.get("name") or "").lower() in _GAME_NAMES:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def _assert_closed():
    if war_thunder_running():
        raise InstallError("Закрой War Thunder перед установкой или восстановлением модификаций.")


def _no_links(path: Path, root: Path) -> None:
    """Reject symlinks along the portion we're about to write to."""
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise InstallError("Недопустимая папка назначения.") from error
    current = root
    if current.is_symlink():
        raise InstallError("Установка через символические ссылки не разрешена.")
    for segment in relative.parts:
        current = current / segment
        if current.is_symlink():
            raise InstallError("Установка через символические ссылки не разрешена.")


def validate_sights_folder(folder: Path) -> Path:
    """Allow production/UserSights for current War Thunder profile only."""
    folder = Path(folder).expanduser()
    if folder.name.lower() == "production":
        folder = folder / "UserSights"
    if folder.name.lower() != "usersights" or folder.parent.name.lower() != "production":
        raise InstallError("Выбери папку production или production/UserSights из сохранений War Thunder.")
    ancestors = [part.lower() for part in folder.parts]
    if "warthunder" not in ancestors or "saves" not in ancestors:
        raise InstallError("Прицелы устанавливаются в WarThunder/Saves/.../production/UserSights.")
    index = max(i for i, value in enumerate(ancestors) if value == "warthunder")
    if "saves" not in ancestors[index + 1:-2]:
        raise InstallError("Путь должен находиться внутри сохранений WarThunder/Saves.")
    _no_links(folder, folder.anchor and Path(folder.anchor) or folder)
    return folder


def validate_skin_template(folder: Path) -> Path:
    folder = Path(folder).expanduser()
    if folder.parent.name.lower() != "userskins" or not folder.name.lower().startswith("template_"):
        raise InstallError("Выбери шаблон техники в War Thunder/UserSkins/template_... .")
    if not folder.is_dir() or folder.is_symlink() or folder.parent.is_symlink():
        raise InstallError("Сначала создай шаблон камуфляжа в игре и выбери его папку.")
    if not (folder.parent.parent / "config.blk").is_file():
        raise InstallError("В выбранной папке War Thunder не найден config.blk.")
    _no_links(folder, folder.parent.parent)
    return folder


def validate_game_root(folder: Path) -> Path:
    folder = Path(folder).expanduser()
    if not folder.is_dir() or not (folder / "config.blk").is_file():
        raise InstallError("Выбери папку установленной War Thunder, содержащую config.blk.")
    _no_links(folder / "sound" / "mod", folder)
    _no_links(folder / "config.blk", folder)
    return folder


def _iter_source_files(source: Path, extensions: set[str]) -> list[Path]:
    source = Path(source)
    if not source.is_dir() or source.is_symlink():
        raise InstallError("Выбери обычную папку с файлами модификации.")
    all_files = list(source.rglob("*"))
    if len(all_files) > MAX_FILES * 2:
        raise InstallError("В архиве слишком много объектов.")
    picked = []
    total = 0
    for file in all_files:
        if file.is_symlink():
            raise InstallError("Ссылки внутри модификации запрещены.")
        if not file.is_file():
            continue
        if file.suffix.lower() not in extensions:
            raise InstallError("Неподдерживаемый файл в наборе: " + file.name)
        size = file.stat().st_size
        if size > MAX_FILE_BYTES:
            raise InstallError("Файл слишком большой: " + file.name)
        total += size
        picked.append(file)
    if not picked or len(picked) > MAX_FILES or total > MAX_TOTAL_BYTES:
        raise InstallError("Набор пустой или превышает ограничения безопасности.")
    return picked


def sight_plan(sight: Path, user_sights: Path, scope: str = "all_tanks") -> list[CopyPlan]:
    sight = Path(sight)
    target_root = validate_sights_folder(user_sights)
    if not SCOPE_RE.fullmatch(scope) or scope in {".", ".."}:
        raise InstallError("Неверный ID техники или имя all_tanks.")
    if sight.suffix.lower() not in CUSTOM_SIGHT_EXT or not sight.is_file() or sight.is_symlink():
        raise InstallError("Для игрового прицела выбери файл .blk, а не PNG.")
    if sight.stat().st_size > 2 * 1024 * 1024:
        raise InstallError("Прицел .blk слишком большой.")
    dest = target_root / scope / sight.name
    _no_links(dest, target_root)
    return [_entry(sight, dest)]


def camouflage_plan(package_folder: Path, template_folder: Path) -> list[CopyPlan]:
    template = validate_skin_template(template_folder)
    source = Path(package_folder)
    files = _iter_source_files(source, CAMO_EXT)
    if not any(x.suffix.lower() == ".blk" for x in files):
        raise InstallError("Камуфляж должен включать игровой .blk и текстуры.")
    result = []
    for file in files:
        destination = template / file.relative_to(source)
        _no_links(destination, template)
        result.append(_entry(file, destination))
    return result


def sound_plan(package_folder: Path, game_root: Path) -> list[CopyPlan]:
    root = validate_game_root(game_root)
    source = Path(package_folder)
    files = _iter_source_files(source, SOUND_EXT)
    if not any(file.suffix.lower() == ".bank" for file in files):
        raise InstallError("Звуковой мод War Thunder использует FMOD .bank, не MP3/WAV.")
    dest_root = root / "sound" / "mod"
    return [_entry(file, dest_root / file.relative_to(source)) for file in files]


def _entry(source: Path, dest: Path) -> CopyPlan:
    if dest.is_symlink():
        raise InstallError("Отказ: файл назначения является ссылкой.")
    existing = dest.is_file()
    if dest.exists() and not existing:
        raise InstallError("Вместо файла назначения находится папка.")
    identical = existing and _sha256(source) == _sha256(dest)
    return CopyPlan(source, dest, existing, identical)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(256 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def patch_sound_setting(original: bytes) -> bytes:
    """Switch enable_mod in the existing sound block while preserving all other bytes."""
    match = re.search(rb"(?m)\bsound\s*\{", original)
    if not match:
        raise InstallError("В config.blk нет блока sound {}; менять конфигурацию автоматически небезопасно.")
    depth = 1
    end = match.end()
    while end < len(original) and depth:
        if original[end] == 123:
            depth += 1
        elif original[end] == 125:
            depth -= 1
        end += 1
    if depth:
        raise InstallError("Блок sound {} повреждён.")
    inside = original[match.end():end - 1]
    present = re.search(rb"\benable_mod:b=(?:yes|no)\b", inside)
    if present:
        new_inside = inside[:present.start()] + b"enable_mod:b=yes" + inside[present.end():]
    else:
        new_inside = b"\r\n  enable_mod:b=yes\r\n" + inside
    return original[:match.end()] + new_inside + original[end - 1:]


def sound_plan_with_config(package_folder: Path, game_root: Path) -> tuple[list[CopyPlan], bytes]:
    root = validate_game_root(game_root)
    return sound_plan(package_folder, root), patch_sound_setting((root / "config.blk").read_bytes())


def install_planned(plan: Iterable[CopyPlan], config_root: Path | None = None) -> dict:
    """Atomic copies with backup + rollback of any partly completed transaction."""
    _assert_closed()
    entries = list(plan)
    if not entries or len(entries) > MAX_FILES:
        raise InstallError("Нечего устанавливать.")
    paths = [e.destination for e in entries]
    if len(paths) != len(set(paths)):
        raise InstallError("В наборе повторяются пути назначения.")
    change = [e for e in entries if not e.identical]
    config_data = None
    if config_root is not None:
        root = validate_game_root(config_root)
        config = root / "config.blk"
        config_data = patch_sound_setting(config.read_bytes())
        if config_data != config.read_bytes():
            change.append(_entry(config, config))
    if not change:
        return {"status": "unchanged", "copied": 0, "conflicts": 0}
    tid = uuid.uuid4().hex
    transaction = ROOT_BACKUPS / tid
    backup = transaction / "files"
    backup.mkdir(parents=True, exist_ok=False)
    manifest = []
    committed = []
    try:
        for idx, entry in enumerate(change):
            dest = entry.destination
            if dest.is_symlink():
                raise InstallError("Путь назначения изменился на символическую ссылку.")
            dest.parent.mkdir(parents=True, exist_ok=True)
            if entry.existing:
                shutil.copy2(dest, backup / str(idx))
            content = config_data if config_data is not None and dest.name == "config.blk" else None
            with tempfile.NamedTemporaryFile(dir=dest.parent, prefix=".wtmm-", delete=False) as tmp:
                temp_name = Path(tmp.name)
                if content is not None:
                    tmp.write(content)
                else:
                    with entry.source.open("rb") as src:
                        shutil.copyfileobj(src, tmp)
            try:
                os.replace(temp_name, dest)
            finally:
                temp_name.unlink(missing_ok=True)
            committed.append((dest, backup / str(idx) if entry.existing else None))
            manifest.append({
                "target": str(dest),
                "backup": str(idx) if entry.existing else None,
                "installed_digest": _sha256(dest),
            })
        (transaction / "manifest.json").write_text(
            json.dumps({"files": manifest, "created_at": int(time.time())}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return {
            "status": "installed", "transaction": tid, "copied": len(change),
            "conflicts": sum(e.existing for e in change)
        }
    except Exception:
        for dest, old_backup in reversed(committed):
            try:
                if old_backup is not None and old_backup.is_file():
                    os.replace(old_backup, dest)
                elif dest.is_file():
                    dest.unlink()
            except OSError:
                pass
        shutil.rmtree(transaction, ignore_errors=True)
        raise


def restore_transaction(transaction_id: str) -> int:
    _assert_closed()
    if not TRANSACTION_RE.fullmatch(transaction_id):
        raise InstallError("Неверный идентификатор резервной копии.")
    folder = ROOT_BACKUPS / transaction_id
    manifest_file = folder / "manifest.json"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    changes = data.get("files", [])
    if not isinstance(changes, list) or len(changes) > MAX_FILES:
        raise InstallError("Некорректная история установки.")
    # Never overwrite changes made after WTMM installed the files.
    for row in changes:
        if not isinstance(row, dict):
            raise InstallError("Некорректная запись истории.")
        target = Path(row["target"])
        if target.is_symlink() or not target.is_file() or _sha256(target) != row["installed_digest"]:
            raise InstallError("Файл был изменён после установки. Откат отменён: " + target.name)
        old = row.get("backup")
        if old is not None and (not isinstance(old, str) or not old.isdigit()
                                 or not (folder / "files" / old).is_file()):
            raise InstallError("Резервная копия отсутствует.")
    for row in reversed(changes):
        target = Path(row["target"])
        old = row.get("backup")
        if old is None:
            target.unlink()
        else:
            shutil.copy2(folder / "files" / old, target)
    shutil.rmtree(folder)
    return len(changes)
