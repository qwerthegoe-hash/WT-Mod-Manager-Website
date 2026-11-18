"""User-confirmed installation of compatible custom content in War Thunder."""
from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from src.profile_paths import DATA_DIR
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


def install_camouflage_dialog(parent):
    folder = _folder(
        parent, "Выбери папку скачанного камуфляжа с .blk и текстурами",
        Path.home()
    )
    if not folder:
        return
    template = _folder(
        parent,
        "Выбери шаблон техники в War Thunder/UserSkins/template_...",
        Path.home()
    )
    if not template:
        return
    try:
        _execute(parent, camouflage_plan(Path(folder), Path(template)), "Камуфляж")
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


def _execute(parent, plan, category, config_root=None):
    changes = [item for item in plan if not item.identical]
    conflicts = sum(item.existing and not item.identical for item in plan)
    if not changes and config_root is None:
        QMessageBox.information(parent, "Установка", "Файлы уже установлены и не изменились.")
        return
    answer = QMessageBox.question(
        parent, "Подтвердить установку",
        f"{category}: файлов к копированию — {len(changes)}; существующих файлов, "
        f"которые будут заменены, — {conflicts}.\n"
        "Перед изменениями программа создаст резервную копию. Продолжить?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    if answer != QMessageBox.StandardButton.Yes:
        return
    result = install_planned(plan, config_root=config_root)
    if result["status"] == "unchanged":
        QMessageBox.information(parent, "Установка", "Ничего не изменилось.")
        return
    LAST_INSTALL.parent.mkdir(parents=True, exist_ok=True)
    temp = LAST_INSTALL.with_suffix(".tmp")
    temp.write_text(json.dumps({
        "transaction": result["transaction"], "category": category
    }, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, LAST_INSTALL)
    QMessageBox.information(
        parent, "Готово",
        f"{category}: установлено/обновлено файлов: {result['copied']}.\n"
        "Перезапусти War Thunder или обнови список игровых модификаций в настройках игры."
    )


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
        LAST_INSTALL.unlink(missing_ok=True)
        QMessageBox.information(parent, "Восстановление", f"Откат завершён. Файлов: {count}.")
    except (OSError, ValueError, KeyError, InstallError) as error:
        _show_error(parent, error)
