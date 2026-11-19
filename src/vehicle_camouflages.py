"""Vehicle-bound local camouflage presets, never shared with other War Thunder clients.

Make a separate UserSkins folder per skin; never overwrite the game's
template_... directory. Game writes still go through the existing preview,
consent, backup and rollback installer. All discovery is local and bounded.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path

from src.profile_paths import DATA_DIR
from src.game_mod_installer import (
    CAMO_EXT, InstallError, _entry, _iter_source_files, _no_links,
    validate_skin_template,
)

PRESETS = DATA_DIR / "vehicle-camouflages.json"
VEHICLE_ID = re.compile(r"^[a-z0-9][a-z0-9_]{0,75}$", re.I)
CAMO_FOLDER = re.compile(r"^WT_Mod_Camouflage_([0-9]{3})__([a-z0-9_]+)$", re.I)
TEXTURE_TO = re.compile(rb'\bto\s*:\s*t\s*=\s*"([^"\r\n]+)"', re.I)
REPLACE_BLOCK = re.compile(rb'\breplace_tex\s*\{([^{}]*)\}', re.I | re.S)
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga", ".dds"}


def vehicle_from_template(template_folder: Path) -> str:
    template = validate_skin_template(template_folder)
    vehicle_id = template.name[len("template_"):]
    if not VEHICLE_ID.fullmatch(vehicle_id):
        raise InstallError("Шаблон содержит недопустимый ID техники.")
    blk = template / (vehicle_id + ".blk")
    if not blk.is_file() or blk.is_symlink():
        raise InstallError(
            "В шаблоне отсутствует игровой .blk для выбранной техники. "
            "Сначала создай новый шаблон через меню «Внешний вид» War Thunder."
        )
    return vehicle_id


def list_vehicle_templates(userskins: Path) -> tuple[Path, ...]:
    root = Path(userskins)
    if root.name.casefold() != "userskins" or not root.is_dir() or root.is_symlink():
        raise InstallError("Выбери папку War Thunder/UserSkins.")
    if not (root.parent / "config.blk").is_file():
        raise InstallError("Это не папка UserSkins установленной War Thunder.")
    result = []
    try:
        entries = sorted(root.iterdir(), key=lambda entry: entry.name.casefold())
    except OSError as error:
        raise InstallError("Не получилось открыть папку с шаблонами техники.") from error
    if len(entries) > 2048:
        raise InstallError("В UserSkins слишком много объектов для безопасного поиска.")
    for folder in entries:
        if folder.is_symlink() or not folder.name.casefold().startswith("template_"):
            continue
        if folder.is_dir():
            try:
                vehicle_from_template(folder)
                result.append(folder)
            except InstallError:
                continue
    return tuple(result[:100])


def next_preset_destination(template_folder: Path) -> tuple[Path, str, int]:
    template = validate_skin_template(template_folder)
    vehicle_id = vehicle_from_template(template)
    skins = template.parent
    try:
        existing = list(skins.iterdir())
    except OSError as error:
        raise InstallError("Не удалось проверить существующие камуфляжи.") from error
    if len(existing) > 2048:
        raise InstallError("Слишком много пользовательских папок.")
    occupied = {item.name.casefold() for item in existing}
    for serial in range(1, 1000):
        name = f"WT_Mod_Camouflage_{serial:03d}__{vehicle_id}"
        if name.casefold() not in occupied:
            target = skins / name
            _no_links(target, skins.parent)
            return target, f"WT Mod камуфляж №{serial:03d}", serial
    raise InstallError("Достигнут предел нумерации камуфляжей для этой техники.")


def plan_vehicle_package(package_folder: Path, template_folder: Path):
    """Require the exact vehicle BLK; do not silently install another vehicle's skin."""
    vehicle_id = vehicle_from_template(template_folder)
    source = Path(package_folder)
    files = _iter_source_files(source, CAMO_EXT)
    blks = [file for file in files if file.suffix.casefold() == ".blk"]
    if len(blks) != 1 or blks[0].name.casefold() != f"{vehicle_id}.blk".casefold():
        raise InstallError(
            "Файл .blk не совпадает с выбранной техникой. "
            f"Для этого шаблона требуется {vehicle_id}.blk. "
            "Выбери подходящий пакет, а не переименовывай чужой .blk."
        )
    if not any(file.suffix.casefold() != ".blk" for file in files):
        raise InstallError("Готовый камуфляж должен содержать текстуры.")
    destination, display, serial = next_preset_destination(template_folder)
    plan = []
    for file in files:
        target = destination / file.relative_to(source)
        _no_links(target, template_folder.parent.parent)
        plan.append(_entry(file, target))
    return plan, destination, vehicle_id, display, serial


def plan_vehicle_image(image_file: Path, template_folder: Path, staging: Path):
    """Turn one image into a simple scalable texture using a real game template.

    Refuse templates with zero/multiple replace_tex rules. Fixed/UV-mapped
    skins require a matching ready-made .blk package instead.
    """
    from PIL import Image, ImageOps, UnidentifiedImageError

    source = Path(image_file)
    if (not source.is_file() or source.is_symlink()
            or source.suffix.casefold() not in IMAGE_EXT
            or source.stat().st_size > 32 * 1024 * 1024):
        raise InstallError("Выбери обычную картинку PNG/JPG/TGA/DDS до 32 МиБ.")

    template = validate_skin_template(template_folder)
    vehicle_id = vehicle_from_template(template)
    src_files = _iter_source_files(template, CAMO_EXT)
    config_path = template / f"{vehicle_id}.blk"
    config = config_path.read_bytes()
    if len(config) > 2 * 1024 * 1024:
        raise InstallError("Конфигурация шаблона слишком большая.")

    replace_blocks = [match for match in REPLACE_BLOCK.finditer(config)
                      if TEXTURE_TO.search(match.group(1))]
    if len(replace_blocks) != 1:
        raise InstallError(
            "У машины нет одного однозначного масштабируемого слоя. "
            "Для сложного камуфляжа загрузи готовый комплект .blk + текстуры."
        )
    entry = replace_blocks[0]
    target_match = TEXTURE_TO.search(entry.group(1))
    referenced = target_match.group(1).decode("utf-8", errors="replace")
    if (Path(referenced).name != referenced
            or not referenced.casefold().endswith(".tga")
            or not any(p.name.casefold() == referenced.casefold() for p in src_files)):
        raise InstallError(
            "Не найден оригинальный масштабируемый TGA-слой шаблона."
        )

    destination, display, serial = next_preset_destination(template)
    staged = Path(staging)
    if staged.is_symlink():
        raise InstallError("Нельзя создавать текстуры в символической ссылке.")
    staged.mkdir(parents=True, exist_ok=True)
    converted = staged / f"wtmm_pattern_{serial:03d}.tga"
    # Keep the whole pattern without random clipping: use square fit with
    # padding so portrait/landscape images still produce a valid texture.
    try:
        with Image.open(source) as original:
            if (original.width > 8192 or original.height > 8192
                    or original.width * original.height > 32_000_000):
                raise InstallError("Слишком большое разрешение изображения.")
            image = ImageOps.exif_transpose(original)
            image = image.convert("RGB")
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (1024, 1024), image.getpixel((0, 0)))
            canvas.paste(image, ((1024 - image.width) // 2, (1024 - image.height) // 2))
            canvas.save(converted, format="TGA")
    except (OSError, ValueError, UnidentifiedImageError) as error:
        raise InstallError("Не удалось подготовить картинку в формат TGA.") from error

    # Replace ONLY the unique destination within the unique scalable rule.
    block = entry.group(0)
    new_block, count = TEXTURE_TO.subn(
        lambda match: match.group(0).replace(
            match.group(1), converted.name.encode("ascii")), block, count=1
    )
    if count != 1:
        raise InstallError("Не удалось подготовить безопасный .blk.")
    rewritten = config[:entry.start()] + new_block + config[entry.end():]
    generated_blk = staged / config_path.name
    generated_blk.write_bytes(rewritten)

    plan = []
    for source_file in src_files:
        if source_file == config_path:
            continue
        destination_file = destination / source_file.relative_to(template)
        _no_links(destination_file, template.parent.parent)
        plan.append(_entry(source_file, destination_file))
    plan.extend([
        _entry(generated_blk, destination / generated_blk.name),
        _entry(converted, destination / converted.name),
    ])
    return plan, destination, vehicle_id, display, serial


def installed_presets() -> list[dict]:
    try:
        if PRESETS.is_symlink() or PRESETS.stat().st_size > 256 * 1024:
            return []
        data = json.loads(PRESETS.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data[-100:] if isinstance(item, dict)
            and isinstance(item.get("label"), str)
            and isinstance(item.get("vehicle"), str)
            and isinstance(item.get("folder"), str)
            and isinstance(item.get("transaction"), str)]


def _save_presets(items: list[dict]) -> None:
    PRESETS.parent.mkdir(parents=True, exist_ok=True)
    if PRESETS.is_symlink():
        raise OSError("Локальный реестр камуфляжей не должен быть ссылкой.")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=PRESETS.parent,
        prefix=".wtmm-camos-", suffix=".tmp", delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(items[-100:], handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, PRESETS)
    finally:
        temporary.unlink(missing_ok=True)


def record_preset(destination: Path, vehicle: str, label: str, transaction: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{32}", transaction):
        raise ValueError("Некорректная транзакция установки.")
    name = Path(destination).name
    if not CAMO_FOLDER.fullmatch(name) or not VEHICLE_ID.fullmatch(vehicle):
        raise ValueError("Некорректные данные камуфляжа.")
    entries = installed_presets()
    entries.append({
        "label": label[:100], "vehicle": vehicle, "folder": str(destination),
        "transaction": transaction, "created": int(time.time())
    })
    _save_presets(entries)


def forget_transaction(transaction: str) -> None:
    entries = installed_presets()
    if any(item.get("transaction") == transaction for item in entries):
        _save_presets([item for item in entries if item.get("transaction") != transaction])
