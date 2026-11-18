
import re

from PySide6.QtCore import (
    QObject,
    Qt,
    QTimer,
    QRectF,
    Property,
    QPropertyAnimation,
    QEasingCurve,
)

from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QCheckBox,
    QGraphicsOpacityEffect,
)


# ==========================================
# FIVE COLOR THEMES
# ==========================================

THEMES = {
    "blue": (
        "Синяя / Blue",
        "#4777BA",
        "#365F9C",
        "#4675B5",
    ),
    "green": (
        "Изумрудная / Emerald",
        "#34B887",
        "#197D60",
        "#289F79",
    ),
    "purple": (
        "Фиолетовая / Purple",
        "#9868D9",
        "#6842A8",
        "#8155BD",
    ),
    "red": (
        "Рубиновая / Ruby",
        "#DB6677",
        "#9B3346",
        "#B8465A",
    ),
    "orange": (
        "Янтарная / Amber",
        "#DB9C43",
        "#996422",
        "#B77D2C",
    ),
}

# ==========================================
# FIVE FONT OPTIONS
# ==========================================

FONTS = (
    "Segoe UI",
    "Arial",
    "Verdana",
    "Tahoma",
    "Georgia",
)


# ==========================================
# TRANSLATION DICTIONARY
# ==========================================

RU_EN = {
    # Navigation
    "Прицелы": "Sights",
    "Камуфляжи": "Camouflages",
    "Звуки": "Sounds",
    "Конфигурации": "Configurations",
    "Настройки": "Settings",

    # Pages
    "Пользовательские прицелы": "Custom sights",
    "Пользовательские камуфляжи": "Custom camouflages",
    "Звуковые модификации": "Sound modifications",
    "Профили и конфигурации": "Profiles and configurations",
    "Настройки приложения": "Application settings",

    # General actions
    "Добавить": "Add",
    "Обновить": "Refresh",
    "Удалить": "Delete",
    "Предпросмотр": "Preview",
    "Файл не выбран": "No file selected",
    "Нет выбранного файла": "No file selected",
    "Выберите файл": "Select a file",
    "Выберите файл для предпросмотра": "Select a file to preview",

    # Sights
    "Список прицелов": "Sight library",
    "Нет доступных прицелов": "No sights available",
    "Здесь будет предпросмотр прицела": "Sight preview appears here",
    "Папка mods/sights пуста": "The mods/sights folder is empty",
    "Текущий выбранный прицел: нет": "Selected sight: none",
    "Не удалось загрузить изображение": "Could not load image",
    "Не удалось открыть изображение": "Could not open image",
    "Неподдерживаемый или повреждённый файл":
        "Unsupported or damaged file",
    "Загружай изображения прицелов, выбирай их и смотри предпросмотр.":
        "Import and preview custom sight images.",

    # Camouflages
    "Здесь будет изображение камуфляжа":
        "Camouflage preview appears here",
    "Список: камуфляжи": "Camouflage library",
    "Добавляйте камуфляжи и текстуры, просматривайте изображения и управляйте своей библиотекой.":
        "Import and preview camouflage textures.",

    # Sounds
    "Библиотека звуков": "Sound library",
    "Предпросмотр аудио": "Audio preview",
    "Громкость": "Volume",
    "Выберите файл для прослушивания": "Select an audio file",
    "Аудио не выбрано": "No audio selected",
    "Аудиофайл не найден": "Audio file not found",
    "Готово к воспроизведению": "Ready to play",
    "Воспроизводится": "Playing",
    "Воспроизведение остановлено": "Playback stopped",
    "Ошибка воспроизведения": "Playback error",
    "Пауза": "Paused",
    "Ⅱ Пауза": "Ⅱ Pause",
    "■ Стоп": "■ Stop",
    "▶ Играть": "▶ Play",
    "▶ Продолжить": "▶ Resume",
    "Поддерживаемые форматы: WAV, MP3, OGG, FLAC":
        "Supported formats: WAV, MP3, OGG, FLAC",
    "Добавляйте звуковые файлы, прослушивайте их и управляйте своей библиотекой.":
        "Import, preview and manage your sounds.",

    # Settings
    "Обнаружение War Thunder": "War Thunder detection",
    "Показывать предложение запуска": "Show launch prompt",
    "Автоматически открывать менеджер": "Automatically open manager",
    "Показывать уведомления в трее": "Show tray notifications",
    "Интерфейс": "Interface",
    "Поверх остальных окон": "Always on top",
    "Запоминать последнюю вкладку": "Remember last tab",
    "Сворачивать в трей при закрытии": "Minimize to tray on close",
    "Сервис": "Maintenance",
    "Персонализация WT Mod Manager": "Personalize WT Mod Manager",
    "Восстановить стандартные настройки": "Restore default settings",
    "Здесь сохраняются все основные настройки WT Mod Manager.":
        "WT Mod Manager preferences are saved here.",
    "При обнаружении игры предлагать открыть менеджер модов.":
        "Offer to open the manager when the game is detected.",
    "Если включено, менеджер откроется сам после обнаружения игры.":
        "Open the manager automatically when the game is detected.",
    "Показывать всплывающие уведомления о запуске игры и менеджера.":
        "Show notifications about the game and manager.",
    "Держать главное окно менеджера поверх других окон.":
        "Keep the manager above other windows.",
    "После перезапуска открывать последний выбранный раздел.":
        "Restore the last selected section after restart.",
    "Кнопка закрытия не завершает приложение, а скрывает его в системный трей.":
        "Hide the application in the system tray when closing.",

    # Launch prompt
    "WAR THUNDER ОБНАРУЖЕН": "WAR THUNDER DETECTED",
    "Да, открыть": "Yes, open",
    "Нет, пропустить": "No, skip",
    "Запустить менеджер модификаций?\nСохранённые настройки останутся без изменений.":
        "Open the mod manager?\nSaved settings remain unchanged.",

    # Configurations
    "Здесь можно будет создавать, сохранять, загружать и удалять пользовательские конфигурации.":
        "Create, save, load and delete custom configurations here.",

    # Dialogs
    "Ошибка": "Error",
    "Ошибка импорта": "Import error",
    "Ошибка удаления": "Deletion error",
    "Ошибка аудио": "Audio error",
    "Удаление": "Delete",
    "Подтверждение": "Confirmation",
    "Подтверждение удаления": "Confirm deletion",
    "Замена файла": "Replace file",
    "Сброс настроек": "Reset settings",
    "Восстановить стандартные настройки?":
        "Restore default settings?",
    "Сначала выберите файл.": "Select a file first.",
    "Сначала выберите звук.": "Select a sound first.",
    "Сначала выберите звуковой файл.":
        "Select an audio file first.",
    "Сначала выбери прицел из списка.":
        "Select a sight first.",
    "Файл не найден": "File not found",
    "Выбранный файл больше не существует.":
        "The selected file no longer exists.",
    "Исходный файл не найден.": "Source file not found.",
    "Неподдерживаемый формат аудио.":
        "Unsupported audio format.",
    "Не удалось воспроизвести файл.":
        "Could not play the audio file.",
    "Файл не является поддерживаемым изображением.":
        "The selected file is not a supported image.",
}


# ==========================================
# DYNAMIC TEXT PREFIXES
# ==========================================

PREFIXES = {
    "Текущий выбранный прицел: ": "Selected sight: ",
    "Текущий выбранный камуфляж: ": "Selected camouflage: ",
    "Найдено звуков: ": "Sounds found: ",
    "Разрешение: ": "Resolution: ",
    "Размер: ": "Size: ",
    "Формат: ": "Format: ",
    "Список: ": "Library: ",
}


def translate(value, language):
    """Translate registered UI text without changing file names."""

    if language != "en" or not value:
        return value

    if value in RU_EN:
        return RU_EN[value]

    for source, target in PREFIXES.items():
        if value.startswith(source):
            return target + value[len(source):]

    return value


# ==========================================
# ANIMATED CHECKBOX
# ==========================================

class AnimatedCheckBox(QCheckBox):
    """
    Procedurally rendered checkmark and cross.

    On state change, smoothly interpolates
    between inactive and active appearance.
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self._progress = (
            1.0 if self.isChecked() else 0.0
        )

        self.setMinimumHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.animation = QPropertyAnimation(
            self, b"progress", self
        )
        self.animation.setDuration(180)
        self.animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.toggled.connect(self.animate_toggle)

    def get_progress(self):
        return self._progress

    def set_progress(self, value):
        self._progress = float(value)
        self.update()

    progress = Property(
        float, get_progress, set_progress
    )

    def animate_toggle(self, checked):
        self.animation.stop()
        self.animation.setStartValue(self._progress)
        self.animation.setEndValue(
            1.0 if checked else 0.0
        )
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        y = (self.height() - 20) / 2
        progress = self._progress

        inactive = QColor("#242933")
        accent = QColor(
            self.property("accent") or "#4777BA"
        )

        blended = QColor.fromRgbF(
            inactive.redF() * (1-progress)
            + accent.redF() * progress,
            inactive.greenF() * (1-progress)
            + accent.greenF() * progress,
            inactive.blueF() * (1-progress)
            + accent.blueF() * progress,
        )

        painter.setPen(QPen(QColor("#5C6675"), 1.3))
        painter.setBrush(blended)

        painter.drawRoundedRect(
            QRectF(1, y, 20, 20), 5, 5
        )

        # Animated checkmark
        painter.setPen(
            QPen(
                QColor("#FFFFFF"),
                2.3,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.setOpacity(progress)
        painter.drawLine(6, int(y) + 10, 10, int(y) + 14)
        painter.drawLine(10, int(y) + 14, 17, int(y) + 6)

        # Animated cross
        painter.setOpacity(1.0-progress)
        painter.setPen(QPen(QColor("#B5C1D0"), 1.7))
        painter.drawLine(7, int(y) + 7, 15, int(y) + 15)
        painter.drawLine(15, int(y) + 7, 7, int(y) + 15)

        painter.setOpacity(1.0)
        painter.setPen(QColor("#E7EBF2"))

        painter.drawText(
            32, 0,
            max(0, self.width()-32),
            self.height(),
            Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignLeft,
            self.text()
        )
        painter.end()


# ==========================================
# APPEARANCE CONTROLLER
# ==========================================

class AppearanceController(QObject):
    """
    Coordinates:
    - Theme application
    - Font updates
    - English/Russian text
    - Page fade-in animations
    """

    def __init__(self, window, base_style):
        super().__init__(window)

        self.window = window
        self.base_style = base_style
        self.language = "ru"
        self._animation = None

        # Refresh dynamically generated labels,
        # such as selected audio file information.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_text)
        self.timer.start(350)

    def apply(self, settings):
        theme_key = settings.get("theme", "blue")

        if theme_key not in THEMES:
            theme_key = "blue"

        _, accent, deep, hover = THEMES[theme_key]

        replacements = {
            "#4777BA": accent,
            "#365F9C": deep,
            "#4675B5": hover,
            "#284E82": deep,
            "#313B4B": deep,
            "#39475C": hover,
            "#6C9AE0": accent,
            "#91A9CC": accent,
        }

        font_name = settings.get(
            "font_family", "Segoe UI"
        )

        if font_name not in FONTS:
            font_name = "Segoe UI"

        # Global window stylesheet
        self.window.setStyleSheet(
            self._color_style(
                self.base_style,
                replacements,
                font_name,
            )
        )

        app = QApplication.instance()

        if app is not None:
            app.setFont(QFont(font_name, 10))

        # Preserve original local styles to avoid
        # accumulating replacements on theme changes.
        widgets = (
            [self.window]
            + self.window.findChildren(QWidget)
        )

        for widget in widgets:
            if widget is self.window:
                continue

            original = widget.property("_base_qss")

            if original is None:
                original = widget.styleSheet()
                widget.setProperty(
                    "_base_qss", original
                )

            if original:
                widget.setStyleSheet(
                    self._color_style(
                        original,
                        replacements,
                        font_name,
                    )
                )

            if isinstance(widget, AnimatedCheckBox):
                widget.setProperty("accent", accent)
                widget.update()

            # Also update the custom RoundedSlider
            # used in sounds_page.py.
            if hasattr(widget, "progress_color"):
                widget.progress_color = QColor(accent)
                widget.update()

        self.language = settings.get("language", "ru")
        self.refresh_text()

    @staticmethod
    def _color_style(style, colors, font):
        for original, replacement in colors.items():
            style = re.sub(
                re.escape(original),
                replacement,
                style,
                flags=re.IGNORECASE,
            )

        return style.replace(
            '"Segoe UI"', f'"{font}"'
        )

    def refresh_text(self):
        widgets = (
            [self.window]
            + self.window.findChildren(QWidget)
        )

        for widget in widgets:
            if not isinstance(
                widget,
                (QLabel, QPushButton, QCheckBox),
            ):
                continue

            current = widget.text()
            last = widget.property("_last_translation")

            # Detect dynamically changed labels.
            if current != last:
                widget.setProperty(
                    "_source_ru", current
                )

            original = widget.property("_source_ru")

            if original is None:
                original = current

            translated = translate(
                original, self.language
            )

            if current != translated:
                widget.setText(translated)

            widget.setProperty(
                "_last_translation", translated
            )

    def animate_page(self, index):
        if index < 0:
            return

        page = self.window.pages.widget(index)

        if page is None:
            return

        if self._animation is not None:
            self._animation.stop()

        effect = page.graphicsEffect()

        if not isinstance(
            effect, QGraphicsOpacityEffect
        ):
            effect = QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(effect)

        effect.setOpacity(0.25)

        self._animation = QPropertyAnimation(
            effect, b"opacity", self
        )
        self._animation.setDuration(220)
        self._animation.setStartValue(0.25)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )
        self._animation.start()
