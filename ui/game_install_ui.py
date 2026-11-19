"""User-confirmed installation of compatible custom content in War Thunder."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QApplication
from src.profile_paths import DATA_DIR
from src.vehicle_camouflages import (
    list_vehicle_templates, vehicle_from_template, list_scalable_layers,
    plan_vehicle_package, plan_vehicle_image, record_preset,
    installed_presets, forget_transaction,
)
from src.mod_suite import preview_install, resolve_conflicts, append_history
from src.game_mod_installer import (
    InstallError, sight_plan, camouflage_plan, sound_plan,
    install_planned, restore_transaction,
)

LAST_INSTALL = DATA_DIR / "last-game-install.json"


def _folder(parent, caption, initial):
    return QFileDialog.getExistingDirectory(parent, caption, str(initial))


def _show_error(parent, error):
    QMessageBox.warning(parent, "Установка в War Thunder", str(error))


def install_sight_dialog(parent):
    """PNG remains a preview: only user-provided .blk can be a sight."""
    path, _ = QFileDialog.getOpenFileName(
        parent, "Выбери игровой прицел .blk",
        str(Path.home()), "War Thunder Sight (*.blk)"
    )
    if not path:
        return
    folder = _folder(
        parent,
        "Выбери production или UserSights в Documents/My Games/WarThunder/Saves",
        Path.home() / "Documents" / "My Games" / "WarThunder" / "Saves",
    )
    if not folder:
        return
    scope, ok = QInputDialog.getText(
        parent, "Техника",
        "Папка all_tanks или точный ID техники из War Thunder:",
        text="all_tanks"
    )
    if not ok:
        return
    try:
        _execute(parent, sight_plan(Path(path), Path(folder), scope.strip()), "Прицел")
    except (OSError, ValueError, InstallError) as error:
        _show_error(parent, error)


def _choose_vehicle_template(parent):
    """The actual game-created vehicle template determines compatibility."""
    items = installed_presets()
    recent = Path(items[-1]["folder"]).parent if items else Path.home()
    selected = _folder(
        parent,
        "Выбери UserSkins игры или созданную в игре папку template_...",
        recent,
    )
    if not selected:
        return None
    candidate = Path(selected)
    if candidate.name.casefold() == "userskins":
        templates = list_vehicle_templates(candidate)
        if not templates:
            raise InstallError(
                "Шаблоны техники не найдены. В War Thunder открой «Внешний вид» "
                "нужной машины и нажми «Создать шаблон камуфляжа»."
            )
        options = [
            folder.name.removeprefix("template_") + " — " + folder.name
            for folder in templates
        ]
        chosen, ok = QInputDialog.getItem(
            parent, "Выбери технику",
            "Для какого транспорта установить камуфляж?",
            options, 0, False,
        )
        if not ok:
            return None
        candidate = templates[options.index(chosen)]
    vehicle_from_template(candidate)  # Fail closed on wrong/unknown folder.
    return candidate


def install_camouflage_dialog(parent, image_file=None):
    """Install an independent, numbered per-vehicle preset; never replace template."""
    if image_file is not None:
        source = Path(image_file)
        source_kind = "image"
    else:
        label, ok = QInputDialog.getItem(
            parent, "Источник камуфляжа",
            "Что нужно установить для выбранной техники?",
            [
                "Готовый камуфляж (.blk + текстуры)",
                "Картинка (простой масштабируемый камуфляж)",
            ], 0, False
        )
        if not ok:
            return
        source_kind = "image" if label.startswith("Картинка") else "package"
        if source_kind == "image":
            selected, _ = QFileDialog.getOpenFileName(
                parent, "Выбери изображение для рисунка камуфляжа",
                str(Path.home()),
                "Изображения (*.png *.jpg *.jpeg *.bmp *.webp *.dds *.tga)",
            )
        else:
            selected = _folder(
                parent, "Выбери папку готового камуфляжа с .blk и текстурами",
                Path.home()
            )
        if not selected:
            return
        source = Path(selected)

    try:
        template = _choose_vehicle_template(parent)
        if template is None:
            return
        texture_layer = None
        pattern_mode = "fit"
        if source_kind == "image":
            layers = list_scalable_layers(template)
            if not layers:
                raise InstallError(
                    "В игровом шаблоне нет подходящего цветового слоя. "
                    "Для этой машины установи готовый комплект .blk + текстуры."
                )
            if len(layers) > 1:
                texture_layer, accepted = QInputDialog.getItem(
                    parent, "Слой камуфляжа",
                    "Куда нанести изображение? Служебные normal-карты скрыты.",
                    list(layers), 0, False,
                )
                if not accepted:
                    return
            format_label, accepted = QInputDialog.getItem(
                parent, "Вид рисунка",
                "Как подготовить изображение для выбранной техники?",
                [
                    "Целая картинка с сохранением пропорций",
                    "Повторяющийся узор с зеркальными краями",
                ], 0, False,
            )
            if not accepted:
                return
            pattern_mode = "mirror" if format_label.startswith("Повторяющийся") else "fit"
        # Temporary conversion happens exclusively inside WTMM's own
        # user-data folder; game data is not written until the preview is
        # explicitly confirmed.
        stage_root = DATA_DIR / "camo-staging"
        if stage_root.is_symlink():
            raise InstallError("Небезопасная папка временных изображений.")
        stage_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=str(stage_root), prefix="wtmm-camo-"
        ) as stage:
            if source_kind == "image":
                plan, dest, vehicle, display, number = plan_vehicle_image(
                    source, template, Path(stage),
                    texture_layer=texture_layer, pattern_mode=pattern_mode
                )
            else:
                plan, dest, vehicle, display, number = plan_vehicle_package(
                    source, template
                )
            result = _execute(
                parent, plan,
                f"{display} ({vehicle})",
                on_success=lambda transaction: record_preset(
                    dest, vehicle, display, transaction
                )
            )
        if result and result["status"] == "installed":
            parent.refresh_installed_camouflages() if hasattr(
                parent, "refresh_installed_camouflages"
            ) else None
    except (OSError, ValueError, InstallError) as error:
        _show_error(parent, error)


def install_sound_dialog(parent):
    folder = _folder(
        parent, "Выбери папку FMOD-модификации с файлами .bank", Path.home()
    )
    if not folder:
        return
    root = _folder(
        parent, "Выбери папку игры War Thunder, где находится config.blk",
        Path.home()
    )
    if not root:
        return
    try:
        plan = sound_plan(Path(folder), Path(root))
        QMessageBox.information(
            parent, "FMOD звуки",
            "В отличие от предпросмотра MP3/WAV, War Thunder использует банки FMOD (.bank).\n"
            "Будет создана резервная копия config.blk, включён параметр sound.enable_mod, "
            "и файлы будут скопированы в sound/mod. Закрой игру перед продолжением."
        )
        _execute(parent, plan, "FMOD-звук", config_root=Path(root))
    except (OSError, ValueError, InstallError) as error:
        _show_error(parent, error)


def _execute(parent, plan, category, config_root=None, on_success=None):
    # Read-only preflight; no directory or game file is changed before consent.
    rows = list(plan)
    review = preview_install(rows)
    if review.additions + review.replacements == 0 and config_root is None:
        QMessageBox.information(parent, "Установка", "Файлы уже установлены и не изменились.")
        return
    summary = (
        f"{category}: предпросмотр установки\n\n"
        f"Новые файлы: {review.additions}\n"
        f"Заменить файлы: {review.replacements}\n"
        f"Без изменений: {review.unchanged}\n"
        f"Объём записи: {review.bytes_to_copy / (1024 * 1024):.1f} МиБ\n"
        f"Оценка места с резервными копиями: "
        f"{review.required_space / (1024 * 1024):.1f} МиБ\n\n"
        "Сначала просмотри конфликтующие назначения. "
        "Изменения не начнутся до подтверждения."
    )
    box = QMessageBox(parent)
    box.setWindowTitle("WT Install Preview / Conflict Resolver")
    box.setIcon(QMessageBox.Icon.Warning if review.replacements else QMessageBox.Icon.Information)
    box.setText(summary)
    if config_root is not None:
        box.setInformativeText(
            "При согласии будет также проверен и при необходимости обновлён "
            "параметр sound.enable_mod в config.blk с резервной копией."
        )
    if review.conflicting_filenames:
        box.setDetailedText("Конфликты (только имена файлов):\n" +
                            "\n".join(review.conflicting_filenames))
    replace = box.addButton("Установить с резервной копией", QMessageBox.ButtonRole.AcceptRole)
    keep = box.addButton("Сохранить существующие" if review.replacements else "Без замен",
                         QMessageBox.ButtonRole.ActionRole)
    cancel = box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
    keep.setEnabled(review.replacements > 0)
    box.setDefaultButton(cancel)
    box.exec()
    if box.clickedButton() is cancel or box.clickedButton() is None:
        return
    decision = "keep" if box.clickedButton() is keep else "replace"
    resolved = resolve_conflicts(rows, decision)
    if not resolved or (not any(not item.identical for item in resolved) and config_root is None):
        QMessageBox.information(parent, "Установка", "Изменения не требуются.")
        return
    # Additional confirmation if game is on a separate nearly-full volume.
    estimate = preview_install(resolved)
    try:
        active_files = [item.destination for item in resolved if not item.identical]
        check_target = (active_files[0] if active_files else Path(config_root) / "config.blk")
        existing_parent = check_target.parent
        while not existing_parent.exists() and existing_parent != existing_parent.parent:
            existing_parent = existing_parent.parent
        if existing_parent.exists():
            import shutil
            free = shutil.disk_usage(existing_parent).free
            if free < estimate.required_space:
                raise InstallError("На диске игры недостаточно места для установки и резервной копии.")
    except FileNotFoundError:
        raise InstallError("Не удалось проверить целевой диск игры.")

    result = install_planned(resolved, config_root=config_root)
    if result["status"] == "unchanged":
        QMessageBox.information(parent, "Установка", "Ничего не изменилось.")
        return
    LAST_INSTALL.parent.mkdir(parents=True, exist_ok=True)
    temp = LAST_INSTALL.with_suffix(".tmp")
    temp.write_text(json.dumps({
        "transaction": result["transaction"], "category": category
    }, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, LAST_INSTALL)
    try:
        append_history("installed", result["transaction"], result["copied"])
    except OSError:
        pass  # Game changes are already committed; do not falsely claim failure.
    if on_success is not None:
        try:
            on_success(result["transaction"])
        except (OSError, ValueError) as error:
            QMessageBox.warning(
                parent, "Реестр камуфляжей",
                "Файлы установлены, но не удалось обновить локальный список: "
                + str(error),
            )
    QMessageBox.information(
        parent, "Готово",
        f"{category}: установлено/обновлено файлов: {result['copied']}.\n"
        "Резервная копия создана. Прогресс отражён в истории установок."
    )
    return result


def restore_last_game_install(parent):
    try:
        state = json.loads(LAST_INSTALL.read_text(encoding="utf-8"))
        transaction = str(state["transaction"])
        answer = QMessageBox.question(
            parent, "Восстановление файлов игры",
            "Откатить последнюю установку WT Mod Manager в игре?\n"
            "Если файлы уже менялись вручную, откат не будет выполнен.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        count = restore_transaction(transaction)
        try:
            forget_transaction(transaction)
        except OSError:
            pass  # Files are already restored; do not hide a successful rollback.
        if hasattr(parent, "refresh_installed_camouflages"):
            parent.refresh_installed_camouflages()
        try:
            append_history("restored", transaction, count)
        except OSError:
            pass
        LAST_INSTALL.unlink(missing_ok=True)
        QMessageBox.information(parent, "Восстановление", f"Откат завершён. Файлов: {count}.")
    except (OSError, ValueError, KeyError, InstallError) as error:
        _show_error(parent, error)
