"""Deterministic offline diagnostics for WT Mod Manager.

This module deliberately performs NO network requests, sends NO telemetry,
does not open or parse mod ZIP contents, never executes mod files, and never
modifies game data. Reports contain only result codes and generic messages;
never include Windows usernames, file paths, tokens or private account IDs.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from src import profile_paths


@dataclass(frozen=True)
class Diagnostic:
    code: str
    status: str  # OK / WARN / ERROR
    message: str


def _result(code, status, message):
    return Diagnostic(code, status, message[:180])


def inspect_local() -> list[Diagnostic]:
    checks = []
    data = profile_paths.DATA_DIR
    try:
        data.mkdir(parents=True, exist_ok=True)
        probe = data / ".wtmm-diagnostic-write.tmp"
        if probe.exists() or probe.is_symlink():
            raise OSError("Existing diagnostic test file.")
        with probe.open("x", encoding="utf-8") as stream:
            stream.write("test")
        probe.unlink()
        checks.append(_result("D001", "OK", "Папка пользовательских данных доступна для записи."))
    except OSError:
        checks.append(_result("D001", "ERROR",
                              "Нет доступа на запись в пользовательскую папку."))

    try:
        settings = profile_paths.SETTINGS_FILE
        if not settings.is_file():
            checks.append(_result("D002", "WARN", "Настройки ещё не сохранены."))
        elif not isinstance(json.loads(settings.read_text("utf-8")), dict):
            checks.append(_result("D002", "ERROR", "Некорректный формат настроек JSON."))
        else:
            checks.append(_result("D002", "OK", "Файл настроек корректен."))
    except (OSError, UnicodeError, ValueError):
        checks.append(_result("D002", "ERROR", "Не удалось прочитать файл настроек."))

    for category, code in (
        ("sights", "D003"), ("sounds", "D004"), ("camouflages", "D005")
    ):
        folder = profile_paths.MODS_DIR / category
        if folder.is_symlink():
            checks.append(_result(code, "ERROR", "Папка модов является ссылкой."))
        elif not folder.exists():
            checks.append(_result(code, "WARN",
                                  "Локальная папка модов пока не создана."))
        elif not folder.is_dir():
            checks.append(_result(code, "ERROR", "Вместо папки модов найден файл."))
        else:
            checks.append(_result(code, "OK", "Локальная библиотека доступна."))

    config = profile_paths.PROJECT_ROOT / "config" / "update_config.json"
    try:
        # In one-file PyInstaller mode configuration lives inside _MEIPASS.
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            config = Path(sys._MEIPASS) / "config" / "update_config.json"
        payload = json.loads(config.read_text("utf-8"))
        repo = payload.get("github_repository")
        if repo != "qwerthegoe-hash/WT-Mod-Manager-Website":
            checks.append(_result("D006", "WARN", "Источник обновлений не настроен."))
        else:
            checks.append(_result("D006", "OK", "Источник обновлений настроен."))
    except (OSError, ValueError, AttributeError, TypeError):
        checks.append(_result("D006", "WARN", "Конфигурация обновлений недоступна."))

    try:
        from src.portable_updater import previous_exe_available
        if previous_exe_available():
            checks.append(_result("D007", "OK", "Есть проверенная резервная копия EXE."))
        else:
            checks.append(_result("D007", "WARN", "Проверенной копии EXE для отката нет."))
    except (OSError, ValueError, RuntimeError):
        checks.append(_result("D007", "WARN", "Проверить резервную копию не удалось."))

    try:
        from src.desktop_sync import _load_token
        if _load_token():
            checks.append(_result("D008", "OK", "Учётное устройство подключалось."))
        else:
            checks.append(_result("D008", "WARN", "Windows-клиент не привязан к сайту."))
    except (OSError, ValueError, RuntimeError):
        checks.append(_result("D008", "WARN", "Проверить привязку аккаунта не удалось."))

    checks.append(_result(
        "D009", "OK",
        "Проверка выполнена локально: моды, токены и личные файлы не отправлялись."
    ))
    try:
        if shutil.disk_usage(data).free < 256 * 1024 * 1024:
            checks.append(_result("D010","WARN",
                "Мало свободного места для резервных копий и обновлений."))
        else:
            checks.append(_result("D010","OK",
                "Достаточно места для временных файлов."))
    except OSError:
        checks.append(_result("D010","WARN","Место на диске проверить не удалось."))
    try:
        from src.offline_mode import is_offline
        checks.append(_result("D011","WARN" if is_offline() else "OK",
            "Офлайн-режим включён, сетевые проверки отключены."
            if is_offline() else "Сетевые функции разрешены (доступность не проверялась)."))
    except (OSError, ValueError):
        checks.append(_result("D011","WARN","Настройку соединения прочитать не удалось."))
    try:
        from src.crash_recovery import latest_safe_report
        count = bool(latest_safe_report())
        checks.append(_result("D012", "WARN" if count else "OK",
            "Есть локальный отчёт о сбое, можно скопировать его в Trust Center."
            if count else "Локальных аварийных отчётов нет."))
    except (OSError, ValueError):
        checks.append(_result("D012","WARN","Историю аварийных отчётов проверить не удалось."))
    return checks


def repair_safe_folders() -> list[str]:
    """Explicit opt-in; create absent per-user library dirs only.
    Never delete, overwrite, chmod, or edit Windows/game files.
    """
    base = profile_paths.MODS_DIR
    if base.is_symlink():
        raise OSError("Папка модов является символической ссылкой.")
    created = []
    for category in ("sights", "sounds", "camouflages"):
        target = base / category
        if target.is_symlink() or (target.exists() and not target.is_dir()):
            raise OSError("Небезопасная структура библиотеки модов.")
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created.append(category)
    return created


def format_report(checks: list[Diagnostic]) -> str:
    """Safe text suitable for copying into support chat without personal data."""
    lines = ["WT Mod Manager — локальная диагностика", ""]
    for entry in checks:
        lines.append(f"{entry.code} [{entry.status}]: {entry.message}")
    problems = sum(item.status == "ERROR" for item in checks)
    warnings = sum(item.status == "WARN" for item in checks)
    lines.append("")
    lines.append(f"Итог: ошибок {problems}, предупреждений {warnings}.")
    lines.append("Этот отчёт не содержит файлов, путей, паролей или токенов.")
    return "\n".join(lines)
