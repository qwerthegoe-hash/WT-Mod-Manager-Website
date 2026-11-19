"""User-initiated official Windows taskbar pinning from the foreground app.

Inno Setup itself never changes the taskbar. On Windows builds where Microsoft
does not expose TaskbarManager for unpackaged desktop apps, show a trustworthy
manual fallback instead of silently using undocumented Explorer operations.
"""
from __future__ import annotations

import ctypes
import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _native():
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return None
    root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    path = root / "wtmm_taskbar.dll"
    if not path.is_file():
        return None
    helper = ctypes.WinDLL(str(path))
    callback = helper.WTMMRequestTaskbarPin
    callback.argtypes = []
    callback.restype = ctypes.c_int
    return helper, callback


def request_taskbar_pin() -> tuple[bool, str]:
    """Ask Windows to show *its own* confirmation UI after a user click."""
    try:
        native = _native()
        if native is None:
            return False, "Закрепление через API недоступно в этой сборке."
        code = native[1]()
    except (OSError, AttributeError, ValueError):
        return False, "Windows не смогла открыть запрос закрепления."
    if code == 0:
        return True, "Запрос отправлен Windows. Подтверди закрепление в системном окне."
    if code == 2:
        return False, "Windows или настройки организации запретили закрепление."
    if code == 3:
        return False, "Этой версии Windows требуется особое разрешение для закрепления."
    if code == 1:
        return False, "Эта версия Windows не поддерживает закрепление из приложения."
    return False, "Windows отклонила запрос закрепления."


def fallback_instructions() -> str:
    return (
        "Приложение останется доступно в меню «Пуск». "
        "Чтобы закрепить его вручную: открой WT Mod Manager, "
        "нажми правой кнопкой по его значку на панели задач и выбери "
        "«Закрепить на панели задач»."
    )
