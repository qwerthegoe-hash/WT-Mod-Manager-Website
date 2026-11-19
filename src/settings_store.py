
"""
WT Mod Manager 1.1
Persistent Settings System

Система хранения пользовательских настроек.

Возможности:
- Сохранение и загрузка JSON
- Автоматические стандартные значения
- Проверка типов и диапазонов
- Совместимость со старыми настройками
- Пять цветовых тем
- Пять шрифтов
- Русский и английский языки
- Безопасная запись через временный файл
- Восстановление стандартных настроек

Внешние зависимости не требуются.
"""

import json
import os
import tempfile
import re

from pathlib import Path


# ==========================================
# PROJECT PATHS
# ==========================================

# Store settings per Windows user, not inside the installed application.
# Keep both package and direct-script imports supported.
try:
    from .profile_paths import DATA_DIR, SETTINGS_FILE, migrate_legacy_data
except ImportError:
    from profile_paths import DATA_DIR, SETTINGS_FILE, migrate_legacy_data

ROOT = Path(__file__).resolve().parent.parent


# ==========================================
# AVAILABLE COLOR THEMES
# ==========================================

AVAILABLE_THEMES = (
    "blue",
    "green",
    "purple",
    "red",
    "orange",
    "custom",
)


# ==========================================
# AVAILABLE FONTS
# ==========================================

AVAILABLE_FONTS = (
    "Segoe UI",
    "Arial",
    "Verdana",
    "Tahoma",
    "Georgia",
)


# ==========================================
# AVAILABLE LANGUAGES
# ==========================================

AVAILABLE_LANGUAGES = (
    "ru",
    "en",
    "uk",
    "de",
    "fr",
    "es",
    "pl",
)


# ==========================================
# DEFAULT APPLICATION SETTINGS
# ==========================================

DEFAULT_SETTINGS = {

    # --------------------------------------
    # WAR THUNDER DETECTION
    # --------------------------------------

    "show_launch_prompt": True,

    "auto_open_manager_on_detect": False,

    "enable_tray_notifications": True,

    # --------------------------------------
    # MAIN WINDOW
    # --------------------------------------

    "always_on_top": False,

    "remember_last_tab": True,

    "last_tab": 0,

    "minimize_to_tray_on_close": True,

    # --------------------------------------
    # AUDIO
    # --------------------------------------

    "preview_volume": 70,

    # --------------------------------------
    # CUSTOMIZATION
    # --------------------------------------

    "theme": "blue",
    "accent_enabled": False,  # Fully-tinted accent mode
    "appearance_enabled": True,  # Neutral system/dark/light mode

    "appearance_mode": "black",

    "font_family": "Segoe UI",

    "theme_intensity": 60,
    "custom_hex": "#4777BA",
    "animations_enabled": True,
    "animation_speed": 100,
    "appearance_presets": {},

    # --------------------------------------
    # LANGUAGE
    # --------------------------------------

    "language": "ru",
}


# ==========================================
# BOOLEAN SETTINGS
# ==========================================

_BOOLEAN_KEYS = (

    "show_launch_prompt",

    "auto_open_manager_on_detect",

    "enable_tray_notifications",

    "always_on_top",

    "remember_last_tab",

    "minimize_to_tray_on_close",
    "animations_enabled",
    "accent_enabled",
    "appearance_enabled",
)


# ==========================================
# INTEGER SETTINGS AND LIMITS
# ==========================================

_INTEGER_RANGES = {

    "last_tab": (
        0,
        4,
    ),

    "preview_volume": (
        0,
        100,
    ),
    "theme_intensity": (0, 100),
    "animation_speed": (25, 300),
}


# ==========================================
# CUSTOMIZATION VALIDATION
# ==========================================

_CHOICE_OPTIONS = {

    "theme": AVAILABLE_THEMES,

    "appearance_mode": ("black", "white", "system"),

    "font_family": AVAILABLE_FONTS,

    "language": AVAILABLE_LANGUAGES,
}


# ==========================================
# VALIDATE SETTINGS
# ==========================================

def _validated_settings(raw):
    """
    Проверяет загруженные настройки.

    Если какая-либо настройка содержит
    неправильное значение, используется
    соответствующее стандартное значение.

    Неизвестные дополнительные параметры
    сохраняются для совместимости
    с будущими модулями приложения.
    """

    # Создаём независимую копию
    result = DEFAULT_SETTINGS.copy()

    # Добавляем загруженные значения
    if isinstance(raw, dict):
        result.update(raw)

    # ======================================
    # BOOLEAN VALIDATION
    # ======================================

    for key in _BOOLEAN_KEYS:

        value = result.get(key)

        if type(value) is not bool:

            result[key] = (
                DEFAULT_SETTINGS[key]
            )

    # ======================================
    # INTEGER VALIDATION
    # ======================================

    for key, limits in _INTEGER_RANGES.items():

        minimum, maximum = limits

        value = result.get(key)

        try:

            if isinstance(value, bool):
                raise ValueError(
                    "Boolean is not an integer setting"
                )

            number = int(value)

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            number = (
                DEFAULT_SETTINGS[key]
            )

        # Ограничиваем значение
        number = max(
            minimum,
            min(
                maximum,
                number,
            ),
        )

        result[key] = number

    # ======================================
    # THEME, FONT AND LANGUAGE VALIDATION
    # ======================================

    for key, options in _CHOICE_OPTIONS.items():

        value = result.get(key)

        if (
            not isinstance(value, str)
            or value not in options
        ):

            result[key] = (
                DEFAULT_SETTINGS[key]
            )

    # Custom colors are canonical 6-digit hexadecimal RGB values.
    custom = result.get("custom_hex")
    if isinstance(custom, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", custom):
        result["custom_hex"] = custom.upper()
    else:
        result["custom_hex"] = DEFAULT_SETTINGS["custom_hex"]

    # Preset storage is kept inside settings.json, but it must never accept
    # unbounded data or arbitrary objects from malformed files.
    raw_presets = result.get("appearance_presets", {})
    validated_presets = {}
    if isinstance(raw_presets, dict):
        for name, values in raw_presets.items():
            if len(validated_presets) >= 12:
                break
            if not isinstance(name, str) or not (1 <= len(name.strip()) <= 32):
                continue
            if not isinstance(values, dict):
                continue
            preset = {}
            for key in (
                "theme", "custom_hex", "theme_intensity", "appearance_mode",
                "font_family", "animations_enabled", "animation_speed", "accent_enabled", "appearance_enabled",
            ):
                if key in values:
                    preset[key] = values[key]
            if preset:
                # Use a shallow independent validation to normalize all preset fields.
                normal = dict(DEFAULT_SETTINGS)
                normal.update(preset)
                for key in ("theme", "appearance_mode", "font_family"):
                    if normal[key] not in _CHOICE_OPTIONS[key]:
                        normal[key] = DEFAULT_SETTINGS[key]
                color = normal.get("custom_hex")
                if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                    normal["custom_hex"] = DEFAULT_SETTINGS["custom_hex"]
                normal["custom_hex"] = normal["custom_hex"].upper()
                for key, lower, upper in (("theme_intensity", 0, 100), ("animation_speed", 25, 300)):
                    try:
                        value = int(normal[key])
                    except (TypeError, ValueError, OverflowError):
                        value = DEFAULT_SETTINGS[key]
                    normal[key] = max(lower, min(upper, value))
                if type(normal["animations_enabled"]) is not bool:
                    normal["animations_enabled"] = DEFAULT_SETTINGS["animations_enabled"]
                if type(normal["accent_enabled"]) is not bool:
                    normal["accent_enabled"] = DEFAULT_SETTINGS["accent_enabled"]
                if type(normal["appearance_enabled"]) is not bool:
                    normal["appearance_enabled"] = not normal["accent_enabled"]
                validated_presets[name.strip()] = {
                    key: normal[key] for key in (
                        "theme", "custom_hex", "theme_intensity", "appearance_mode",
                        "font_family", "animations_enabled", "animation_speed", "accent_enabled", "appearance_enabled",
                    )
                }
    # Exactly one of two visual modes is active.
    if result.get("accent_enabled", False):
        result["appearance_enabled"] = False
    else:
        result["appearance_enabled"] = True
    for preset in validated_presets.values():
        preset["appearance_enabled"] = not preset.get("accent_enabled", False)

    result["appearance_presets"] = validated_presets

    return result


# ==========================================
# ATOMIC SETTINGS STORAGE AND RECOVERY
# ==========================================

# A backup contains the previous valid JSON object, not the just-written
# version. Keep it in the same per-user directory and never sync it to cloud.
SETTINGS_BACKUP_FILE = SETTINGS_FILE.with_name("settings.json.bak")


def _read_settings_json(path):
    """Read a complete JSON object; reject partial files and invalid roots."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Settings JSON root must be an object")
    return data


def _atomic_write_settings(path, data):
    """Durably prepare a sibling file before replacing its destination."""
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            prefix="settings_",
            dir=path.parent,
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(data, file, ensure_ascii=False, indent=4)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


# ==========================================
# LOAD SETTINGS
# ==========================================

def load_settings():
    """Load primary settings or recover from the last valid local backup.

    Recovery is read-only: a damaged primary file remains untouched until
    the user explicitly saves new settings. Missing or invalid copies fall
    back to defaults without aborting application startup.
    """
    migrate_legacy_data()

    try:
        stored = _read_settings_json(SETTINGS_FILE)
    except (OSError, ValueError, UnicodeError):
        try:
            stored = _read_settings_json(SETTINGS_BACKUP_FILE)
            print("[SETTINGS] Recovered settings from local backup.")
        except (OSError, ValueError, UnicodeError):
            stored = {}

    return _validated_settings(stored)


# ==========================================
# SAVE SETTINGS
# ==========================================

def save_settings(changes):
    """Validate and atomically save changes, retaining the last good JSON.

    Before replacing an existing valid settings file, commit its content to
    settings.json.bak using another atomic replacement. If the original is
    corrupt, never overwrite a potentially useful backup with its contents.
    A failed backup write aborts the primary write to avoid data loss.
    """
    if not isinstance(changes, dict):
        raise TypeError("save_settings(changes) expects a dictionary")

    settings = load_settings()
    settings.update(changes)
    settings = _validated_settings(settings)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        previous = _read_settings_json(SETTINGS_FILE)
    except (OSError, ValueError, UnicodeError):
        previous = None

    if previous is not None:
        _atomic_write_settings(SETTINGS_BACKUP_FILE, previous)

    _atomic_write_settings(SETTINGS_FILE, settings)
    return settings


# ==========================================
# RESET SETTINGS
# ==========================================

def reset_settings():
    """
    Восстанавливает стандартные значения
    всех известных параметров приложения.

    Неизвестные параметры сохраняются
    для совместимости с будущими версиями.
    """

    return save_settings(
        DEFAULT_SETTINGS.copy()
    )


# ==========================================
# APPEARANCE PRESET MANAGEMENT
# ==========================================

PRESET_FIELDS = (
    "theme", "custom_hex", "theme_intensity", "appearance_mode",
    "font_family", "animations_enabled", "animation_speed", "accent_enabled", "appearance_enabled",
)


def save_appearance_preset(name):
    """Save current theme parameters under a human-readable local name."""
    if not isinstance(name, str) or not (1 <= len(name.strip()) <= 32):
        raise ValueError("Preset name must contain 1–32 characters")
    name = name.strip()
    current = load_settings()
    presets = dict(current.get("appearance_presets", {}))
    if name not in presets and len(presets) >= 12:
        raise ValueError("Maximum 12 presets")
    presets[name] = {key: current[key] for key in PRESET_FIELDS}
    return save_settings({"appearance_presets": presets})


def apply_appearance_preset(name):
    """Apply one saved appearance without changing unrelated settings."""
    current = load_settings()
    preset = current.get("appearance_presets", {}).get(name)
    if preset is None:
        raise KeyError(name)
    return save_settings({key: preset[key] for key in PRESET_FIELDS if key in preset})


def delete_appearance_preset(name):
    current = load_settings()
    presets = dict(current.get("appearance_presets", {}))
    if name not in presets:
        return current
    del presets[name]
    return save_settings({"appearance_presets": presets})
