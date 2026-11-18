
"""
WT MOD MANAGER 1.2
SETTINGS PAGE

Полностью встроенная система настроек.

Возможности:
    - Анимированные переключатели
    - Процедурный ползунок громкости
    - Настройки обнаружения игры
    - Настройки интерфейса
    - Кастомизация без отдельных окон
    - Выбор языка без отдельных окон
    - Пять акцентных тем
    - Три режима оформления
    - Пять шрифтов
    - Семь языков
    - Автоматическое сохранение
    - Сброс настроек
    - Синхронизация с ManagerWindow

Зависимости:
    src.settings_store
    ui.i18n
    ui.theme_engine
"""

from PySide6.QtCore import (
    Qt,
    Signal,
    Property,
    QRectF,
    QPointF,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
    QSignalBlocker,
    QTimer,
)

from pathlib import Path

from PySide6.QtGui import (
    QIcon,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QPainterPath,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QFrame,
    QPushButton,
    QScrollArea,
    QMessageBox,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QSizePolicy,
    QStackedWidget,
    QGraphicsOpacityEffect,
    QDialog,
)

from src.settings_store import (
    load_settings,
    save_settings,
    DEFAULT_SETTINGS,
    save_appearance_preset,
    apply_appearance_preset,
    delete_appearance_preset,
)

from ui.i18n import (
    tr,
    LANGUAGES,
)

from ui.theme_engine import (
    transform_stylesheet,
    effective_mode,
    theme_palette,
    accent_color,
)


# ==========================================
# PNG ICONS FROM ASSETS (OPTIONAL)
# ==========================================

def load_back_icon(settings):
    """Load themed left arrow icon from White/Black assets folders."""
    variant = "Black" if effective_mode(settings) == "white" else "White"
    path = (
        Path(__file__).resolve().parent.parent
        / "assets" / "icons" / variant / "arrow.png"
    )
    return QIcon(str(path)) if path.is_file() else QIcon()


def load_reset_icon(settings):
    """Use white icons for dark UI, black icons for light UI.

    Missing PNGs leave the procedural reset arrow available.
    The application root is one directory above ui/.
    """
    variant = (
        "Black" if effective_mode(settings) == "white" else "White"
    )
    path = (
        Path(__file__).resolve().parent.parent
        / "assets" / "icons" / variant / "reset.png"
    )
    return QIcon(str(path)) if path.is_file() else QIcon()


# ==========================================
# AVAILABLE COLOR THEMES
# ==========================================

COLOR_THEMES = {
    "blue": {
        "accent": "#4777BA",
        "hover": "#5B8BD2",
        "deep": "#365F9C",
    },
    "green": {
        "accent": "#34B887",
        "hover": "#45D5A0",
        "deep": "#197D60",
    },
    "purple": {
        "accent": "#9868D9",
        "hover": "#B184EC",
        "deep": "#6842A8",
    },
    "red": {
        "accent": "#DB6677",
        "hover": "#EB8090",
        "deep": "#9B3346",
    },
    "orange": {
        "accent": "#DB9C43",
        "hover": "#ECB45F",
        "deep": "#996422",
    },
}


# ==========================================
# AVAILABLE FONT OPTIONS
# ==========================================

FONT_OPTIONS = (
    "Segoe UI",
    "Arial",
    "Verdana",
    "Tahoma",
    "Georgia",
)


# ==========================================
# APPEARANCE MODES
# ==========================================

APPEARANCE_MODES = (
    "black",
    "white",
    "system",
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_theme(theme_key):
    return COLOR_THEMES.get(
        theme_key,
        COLOR_THEMES["blue"],
    )


def get_accent(settings):
    theme_key = settings.get(
        "theme",
        "blue",
    )

    return get_theme(theme_key)["accent"]


def blend_colors(start, end, progress):
    progress = max(
        0.0,
        min(1.0, float(progress)),
    )

    start = QColor(start)
    end = QColor(end)

    return QColor.fromRgbF(
        start.redF() * (1 - progress)
        + end.redF() * progress,

        start.greenF() * (1 - progress)
        + end.greenF() * progress,

        start.blueF() * (1 - progress)
        + end.blueF() * progress,
    )


# ==========================================
# ANIMATED PROCEDURAL CHECKBOX
# ==========================================

class PaintedCheckBox(QCheckBox):
    """
    Переключатель с собственным рисунком.

    Включено:
        Плавно появляется галочка.

    Выключено:
        Плавно появляется крестик.

    Анимация выполняется внутри виджета.
    Она не изменяет стиль главного окна.
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self._progress = 0.0
        self._accent = QColor("#4777BA")
        self._light_mode = False
        self._inactive_color = QColor("#171B22")
        self._border_color = QColor("#647084")
        self._text_color = QColor("#E5EAF2")
        self._cross_color = QColor("#A3ADBC")

        self.setMinimumHeight(34)

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        # ==================================
        # CHECKBOX ANIMATION
        # ==================================

        self.animation = QPropertyAnimation(
            self,
            b"progress",
            self,
        )

        self.animation.setDuration(190)
        # Анимация не изменяет stylesheet и не перестраивает окно.
        # Перерисовывается только небольшой прямоугольник переключателя.

        self.animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.toggled.connect(
            self.animate_toggle
        )

    # ======================================
    # ANIMATION PROPERTY
    # ======================================

    def get_progress(self):
        return self._progress

    def set_progress(self, value):
        self._progress = max(
            0.0,
            min(1.0, float(value)),
        )

        self.update()

    progress = Property(
        float,
        get_progress,
        set_progress,
    )

    # ======================================
    # ACCENT COLOR
    # ======================================

    def set_accent(self, color):
        new_color = QColor(color)

        if self._accent != new_color:
            self._accent = new_color
            self.update()

    # ======================================
    # APPLY FULL THEME PALETTE
    # ======================================

    def set_theme_palette(self, palette):
        """Update QPainter colors without rebuilding QWidget styles."""
        new_light = palette.get("mode") == "white"
        new_accent = QColor(palette["accent"])
        new_inactive = QColor(palette["surface"])
        new_border = QColor(palette["border"])
        new_text = QColor(palette["text"])
        new_cross = QColor(palette["text_muted"])
        changed = (
            self._light_mode != new_light
            or self._accent != new_accent
            or self._inactive_color != new_inactive
            or self._border_color != new_border
            or self._text_color != new_text
            or self._cross_color != new_cross
        )
        self._light_mode = new_light
        self._accent = new_accent
        self._inactive_color = new_inactive
        self._border_color = new_border
        self._text_color = new_text
        self._cross_color = new_cross
        if changed:
            self.update()

    # ======================================
    # ANIMATE CHECKMARK
    # ======================================

    def animate_toggle(self, checked):
        self.animation.stop()

        self.animation.setStartValue(
            self._progress
        )

        self.animation.setEndValue(
            1.0 if checked else 0.0
        )

        self.animation.start()

    # ======================================
    # IMMEDIATE STATE UPDATE
    # ======================================

    def set_checked_immediately(self, checked):
        checked = bool(checked)

        self.animation.stop()

        with QSignalBlocker(self):
            self.setChecked(checked)

        self.set_progress(
            1.0 if checked else 0.0
        )

    # ======================================
    # SIZE
    # ======================================

    def sizeHint(self):
        metrics = self.fontMetrics()

        width = (
            42
            + metrics.horizontalAdvance(
                self.text()
            )
        )

        height = max(
            36,
            metrics.height() + 12,
        )

        return QSize(width, height)

    # ======================================
    # PROCEDURAL PAINT
    # ======================================

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        progress = self._progress

        box_size = 20

        box_y = (
            self.height() - box_size
        ) / 2

        box = QRectF(
            1,
            box_y,
            box_size,
            box_size,
        )

        # ==================================
        # COLORS
        # ==================================

        # All switch colors now follow the selected application palette.
        # Keep temporary QColor copies since disabled text changes alpha.
        inactive = QColor(self._inactive_color)
        border = QColor(self._border_color)
        text_color = QColor(self._text_color)
        cross_color = QColor(self._cross_color)

        background = blend_colors(
            inactive,
            self._accent,
            progress,
        )

        border_color = blend_colors(
            border,
            self._accent,
            progress,
        )

        # ==================================
        # DRAW CHECKBOX BACKGROUND
        # ==================================

        painter.setPen(
            QPen(
                border_color,
                1.3,
            )
        )

        painter.setBrush(
            QBrush(background)
        )

        painter.drawRoundedRect(
            box,
            5,
            5,
        )

        # ==================================
        # DRAW CHECKMARK
        # ==================================

        painter.setOpacity(progress)

        check_pen = QPen(
            QColor("#FFFFFF"),
            2.2,
        )

        check_pen.setCapStyle(
            Qt.PenCapStyle.RoundCap
        )

        check_pen.setJoinStyle(
            Qt.PenJoinStyle.RoundJoin
        )

        painter.setPen(check_pen)

        painter.drawLine(
            QPointF(box.center().x() - 6, box.center().y()),
            QPointF(box.center().x() - 2, box.center().y() + 4),
        )

        painter.drawLine(
            QPointF(box.center().x() - 2, box.center().y() + 4),
            QPointF(box.center().x() + 6, box.center().y() - 4),
        )

        # ==================================
        # DRAW CROSS
        # ==================================

        painter.setOpacity(
            1.0 - progress
        )

        cross_pen = QPen(
            cross_color,
            1.8,
        )

        cross_pen.setCapStyle(
            Qt.PenCapStyle.RoundCap
        )

        painter.setPen(cross_pen)

        # Geometric center of the 20x20 indicator: (11, box_y + 10).
        cx, cy = box.center().x(), box.center().y()
        offset = 3.8
        painter.drawLine(
            QPointF(cx - offset, cy - offset),
            QPointF(cx + offset, cy + offset),
        )
        painter.drawLine(
            QPointF(cx + offset, cy - offset),
            QPointF(cx - offset, cy + offset),
        )

        # ==================================
        # DRAW TEXT
        # ==================================

        painter.setOpacity(1.0)

        if not self.isEnabled():
            text_color.setAlpha(110)

        painter.setPen(text_color)

        text_rect = QRectF(
            34,
            0,
            max(0, self.width() - 34),
            self.height(),
        )

        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
            self.text(),
        )

        painter.end()


# ==========================================
# ROUNDED PROCEDURAL SLIDER
# ==========================================

class SettingsSlider(QSlider):
    """
    Ползунок громкости с круглыми краями.

    Поддерживает:
        - Изменение мышью
        - Перетаскивание
        - Клавиатуру
        - Выбранный акцентный цвет
        - Светлую и тёмную темы
    """

    def __init__(self, parent=None):
        super().__init__(
            Qt.Orientation.Horizontal,
            parent,
        )

        self._accent = QColor("#4777BA")
        self._light_mode = False
        self._dragging = False
        self._track_color = QColor("#303742")
        self._handle_color = QColor("#E5EDF8")
        self._handle_border_color = QColor("#15191F")

        self.handle_radius = 9
        self.track_height = 7

        self.setMinimumHeight(32)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

    # ======================================
    # THEME COLOR
    # ======================================

    def set_accent(self, color):
        new_color = QColor(color)

        if self._accent != new_color:
            self._accent = new_color
            self.update()

    # ======================================
    # FULL THEME COLORS
    # ======================================

    def set_theme_palette(self, palette):
        """Repaint the slider only if a visual color actually changed."""
        next_accent = QColor(palette["accent"])
        next_track = QColor(palette["surface"])
        next_handle = QColor(palette["card"] if palette["mode"] == "white" else palette["text"])
        next_border = QColor(palette["border"])
        next_light = palette["mode"] == "white"
        changed = (
            self._accent != next_accent
            or self._track_color != next_track
            or self._handle_color != next_handle
            or self._handle_border_color != next_border
            or self._light_mode != next_light
        )
        self._accent = next_accent
        self._track_color = next_track
        self._handle_color = next_handle
        self._handle_border_color = next_border
        self._light_mode = next_light
        if changed:
            self.update()

    # ======================================
    # SIZE
    # ======================================

    def sizeHint(self):
        return QSize(180, 32)

    # ======================================
    # SLIDER GEOMETRY
    # ======================================

    def slider_geometry(self):
        left = self.handle_radius + 2

        right = max(
            left,
            self.width()
            - self.handle_radius
            - 2,
        )

        center_y = self.height() / 2

        return left, right, center_y

    # ======================================
    # HANDLE POSITION
    # ======================================

    def handle_position(self):
        left, right, center_y = (
            self.slider_geometry()
        )

        minimum = self.minimum()
        maximum = self.maximum()

        if maximum <= minimum:
            ratio = 0.0
        else:
            ratio = (
                self.value() - minimum
            ) / (
                maximum - minimum
            )

        x = left + (
            right - left
        ) * ratio

        return x, center_y

    # ======================================
    # PAINT
    # ======================================

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        left, right, middle = (
            self.slider_geometry()
        )

        half_height = self.track_height / 2

        track_color = self._track_color
        handle_color = self._handle_color
        border_color = self._handle_border_color

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            track_color
        )

        track = QRectF(
            left,
            middle - half_height,
            max(0, right - left),
            self.track_height,
        )

        painter.drawRoundedRect(
            track,
            half_height,
            half_height,
        )

        position, _ = self.handle_position()

        # ==================================
        # FILLED TRACK
        # ==================================

        if position > left:
            progress = QRectF(
                left,
                middle - half_height,
                position - left,
                self.track_height,
            )

            painter.setBrush(
                self._accent
            )

            painter.drawRoundedRect(
                progress,
                half_height,
                half_height,
            )

        # ==================================
        # HANDLE
        # ==================================

        painter.setBrush(
            handle_color
        )

        painter.setPen(
            QPen(
                border_color,
                1.5,
            )
        )

        painter.drawEllipse(
            QPointF(position, middle),
            self.handle_radius,
            self.handle_radius,
        )

        painter.end()

    # ======================================
    # POSITION TO VALUE
    # ======================================

    def set_value_from_position(self, x):
        left, right, _ = (
            self.slider_geometry()
        )

        if right <= left:
            return

        ratio = (
            x - left
        ) / (
            right - left
        )

        ratio = max(
            0.0,
            min(1.0, ratio),
        )

        value = self.minimum() + ratio * (
            self.maximum() - self.minimum()
        )

        self.setValue(
            round(value)
        )

    # ======================================
    # MOUSE EVENTS
    # ======================================

    def mousePressEvent(self, event):
        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):
            self._dragging = True
            self.setSliderDown(True)

            self.set_value_from_position(
                event.position().x()
            )

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.set_value_from_position(
                event.position().x()
            )

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            self._dragging
            and event.button()
            == Qt.MouseButton.LeftButton
        ):
            self.set_value_from_position(
                event.position().x()
            )

            self._dragging = False
            self.setSliderDown(False)

            event.accept()
            return

        super().mouseReleaseEvent(event)


# ==========================================
# COMPACT COMBOBOX WITH CONSISTENT ARROW
# ==========================================

class SettingsComboBox(QComboBox):
    """Native popup, but a custom painted arrow; no detached native square."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setMinimumWidth(190)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._arrow_color = QColor("#E9EDF3")

    def set_arrow_color(self, color):
        color = QColor(color)
        if color != self._arrow_color:
            self._arrow_color = color
            self.update()

    def paintEvent(self, event):
        # Qt draws the native combo text/focus. The QSS explicitly hides
        # its default arrow, then this draws our consistent chevron.
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._arrow_color, 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        x = self.width() - 19
        y = self.height() / 2
        p.drawLine(QPointF(x - 5, y - 2), QPointF(x, y + 3))
        p.drawLine(QPointF(x, y + 3), QPointF(x + 5, y - 2))
        p.end()


# ==========================================
# PROCEDURAL RESET BUTTON WITH CURVED ARROW
# ==========================================

class ResetSliderButton(QPushButton):
    """Draw a curved reset arrow using QPainter, with no icon assets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResetSliderButton")
        self.setMinimumHeight(40)
        self.setMinimumWidth(138)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._icon_color = QColor("#E9EDF3")

    def set_icon_color(self, color):
        updated = QColor(color)
        if updated != self._icon_color:
            self._icon_color = updated
            self.update()

    def paintEvent(self, event):
        # Let Qt draw the themed button, text, hover and focus state.
        super().paintEvent(event)
        # Qt already drew our PNG icon. Do not overlay the procedural arrow.
        # When assets/icons is missing, retain the original fallback.
        if not self.icon().isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        color = QColor(self._icon_color)
        if not self.isEnabled():
            color.setAlpha(105)
        pen = QPen(color, 1.9)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # Locate the icon just before the centered translated button text.
        text_width = self.fontMetrics().horizontalAdvance(self.text())
        center_x = max(14.0, (self.width() - text_width) / 2.0 - 15.0)
        center_y = self.height() / 2.0
        rect = QRectF(center_x - 6.5, center_y - 6.5, 13.0, 13.0)
        path = QPainterPath()
        path.arcMoveTo(rect, 45.0)
        path.arcTo(rect, 45.0, 285.0)
        painter.drawPath(path)

        # Arrowhead at the end of the curved arc, pointing clockwise.
        # These segments are painted, not loaded from SVG/PNG/font icons.
        tip = path.currentPosition()
        painter.drawLine(tip, QPointF(tip.x() - 4.6, tip.y() - 1.1))
        painter.drawLine(tip, QPointF(tip.x() - 0.4, tip.y() - 4.8))
        painter.end()


# ==========================================
# MAIN SETTINGS PAGE
# ==========================================

class SettingsPage(QWidget):
    """
    Главная страница настроек.

    Все дополнительные панели встроены
    в один QStackedWidget.

    Никаких QDialog для кастомизации
    или смены языка не создаётся.

    Сигнал:
        settings_changed(dict)
    """

    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()

        self.settings = load_settings()
        self.setObjectName("SettingsPageRoot")

        self.checkboxes = {}

        self._updating_controls = False
        self._last_visual_signature = None
        self._panel_title_animation = None
        self._slider_save_timer = QTimer(self)
        self._slider_save_timer.setSingleShot(True)
        self._slider_save_timer.setInterval(240)
        self._slider_save_timer.timeout.connect(self._save_slider_changes)
        # Coalesce expensive QSS updates to ~20 FPS while the mouse moves.
        # Saving to disk remains a separate, slower operation.
        self._intensity_preview_timer = QTimer(self)
        self._intensity_preview_timer.setSingleShot(True)
        self._intensity_preview_timer.setInterval(45)
        self._intensity_preview_timer.timeout.connect(self._apply_live_intensity_preview)

        self.build_ui()
        # При первом открытии показываем сохранённые значения,
        # даже если пользователь ещё не заходил в подстраницы.
        # Сигналы блокируются внутри метода: никакой лишней записи
        # в settings.json и никаких лишних анимаций.
        self.sync_controls()
        self.apply_appearance()
        self.update_language()

    # ======================================
    # CARD FACTORY
    # ======================================

    def make_card(self):
        card = QFrame()

        card.setObjectName(
            "SettingCard"
        )

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        layout.setSpacing(13)

        return card, layout

    # ======================================
    # CREATE SWITCH
    # ======================================

    def add_switch(
        self,
        layout,
        setting_key,
        title_key,
        description_key,
    ):
        checkbox = PaintedCheckBox()

        checkbox.set_checked_immediately(
            self.settings.get(
                setting_key,
                False,
            )
        )

        description = QLabel()

        description.setObjectName(
            "SettingDescription"
        )

        description.setWordWrap(True)
        # Пользователь просил сделать меньше поясняющего текста.
        # Смысл подсказки сохраняется через tooltip и accessibleDescription.
        description.setVisible(False)
        checkbox.setToolTip(description_key)

        layout.addWidget(
            checkbox
        )

        layout.addWidget(
            description
        )

        self.checkboxes[setting_key] = {
            "checkbox": checkbox,
            "description": description,
            "title_key": title_key,
            "description_key": description_key,
        }

        checkbox.toggled.connect(
            lambda checked, key=setting_key:
                self.change_setting(
                    key,
                    checked,
                )
        )

        return checkbox

    # ======================================
    # BUILD COMPLETE INTERFACE
    # ======================================

    def build_ui(self):
        outer = QVBoxLayout(self)

        outer.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        outer.setSpacing(0)

        # ==================================
        # INNER PAGE STACK
        # ==================================

        self.panel_stack = QStackedWidget()

        self.panel_stack.setObjectName(
            "SettingsPanelStack"
        )
        # Do not let QStackedWidget's changing sizeHint resize the window.
        # Each child owns a scroll area, so its content may grow independently.
        self.panel_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.panel_stack.setMinimumHeight(0)

        outer.addWidget(
            self.panel_stack
        )

        # 0 - Main settings
        # 1 - Customization
        # 2 - Language
        # 3 - Appearance presets (embedded; no modal dialog)

        self.main_page = QWidget()
        self.custom_page = QWidget()
        self.language_page = QWidget()
        self.presets_page = QWidget()
        self.main_page.setObjectName("SettingsMainPage")
        self.custom_page.setObjectName("SettingsCustomPage")
        self.language_page.setObjectName("SettingsLanguagePage")
        self.presets_page.setObjectName("SettingsPresetsPage")
        for panel in (self.main_page, self.custom_page, self.language_page, self.presets_page):
            panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

        self.panel_stack.addWidget(
            self.main_page
        )

        self.panel_stack.addWidget(
            self.custom_page
        )

        self.panel_stack.addWidget(
            self.language_page
        )

        self.panel_stack.addWidget(self.presets_page)
        self.build_main_page()
        self.build_custom_page()
        self.build_language_page()

        self.panel_stack.setCurrentIndex(0)

    # ======================================
    # MAIN SETTINGS PAGE
    # ======================================

    def build_main_page(self):
        root = QVBoxLayout(
            self.main_page
        )

        root.setContentsMargins(
            0, 0, 0, 0
        )

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)
        # Stable scrolling geometry: hiding/showing a scrollbar no longer
        # changes the available content width during navigation.
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        root.addWidget(
            self.scroll
        )

        container = QWidget()

        layout = QVBoxLayout(container)

        layout.setContentsMargins(
            12, 12, 12, 20
        )

        layout.setSpacing(18)

        # ==================================
        # HEADER
        # ==================================

        self.page_title = QLabel()
        self.page_title.setObjectName("Title")

        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("Subtitle")
        self.page_subtitle.setWordWrap(True)

        layout.addWidget(self.page_title)
        layout.addWidget(self.page_subtitle)

        # ==================================
        # GAME DETECTION
        # ==================================

        detection_card, detection_layout = (
            self.make_card()
        )

        self.detection_title = QLabel()

        self.detection_title.setObjectName(
            "SettingSectionTitle"
        )

        detection_layout.addWidget(
            self.detection_title
        )

        self.popup_checkbox = self.add_switch(
            detection_layout,
            "show_launch_prompt",
            "popup",
            "popup_desc",
        )

        self.auto_open_checkbox = self.add_switch(
            detection_layout,
            "auto_open_manager_on_detect",
            "auto_open",
            "auto_open_desc",
        )

        self.notifications_checkbox = self.add_switch(
            detection_layout,
            "enable_tray_notifications",
            "notifications",
            "notifications_desc",
        )

        layout.addWidget(
            detection_card
        )

        # ==================================
        # INTERFACE SETTINGS
        # ==================================

        interface_card, interface_layout = (
            self.make_card()
        )

        self.interface_title = QLabel()

        self.interface_title.setObjectName(
            "SettingSectionTitle"
        )

        interface_layout.addWidget(
            self.interface_title
        )

        self.top_checkbox = self.add_switch(
            interface_layout,
            "always_on_top",
            "always_on_top",
            "always_on_top_desc",
        )

        self.tab_checkbox = self.add_switch(
            interface_layout,
            "remember_last_tab",
            "remember_tab",
            "remember_tab_desc",
        )

        self.minimize_checkbox = self.add_switch(
            interface_layout,
            "minimize_to_tray_on_close",
            "minimize_tray",
            "minimize_tray_desc",
        )

        layout.addWidget(
            interface_card
        )

        # ==================================
        # PERSONALIZATION
        # ==================================

        personal_card, personal_layout = (
            self.make_card()
        )

        self.personal_title = QLabel()

        self.personal_title.setObjectName(
            "SettingSectionTitle"
        )

        personal_layout.addWidget(
            self.personal_title
        )

        # Buttons have the same neutral style.
        # Only hovered button receives accent.

        self.customization_button = QPushButton()

        self.customization_button.setObjectName(
            "PersonalLink"
        )

        self.customization_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.customization_button.clicked.connect(
            self.open_customization
        )

        personal_layout.addWidget(
            self.customization_button
        )

        self.language_button = QPushButton()

        self.language_button.setObjectName(
            "PersonalLink"
        )

        self.language_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.language_button.clicked.connect(
            self.open_language_panel
        )

        personal_layout.addWidget(
            self.language_button
        )

        layout.addWidget(
            personal_card
        )

        # ==================================
        # AUDIO
        # ==================================

        sound_card, sound_layout = (
            self.make_card()
        )

        self.sound_title = QLabel()

        self.sound_title.setObjectName(
            "SettingSectionTitle"
        )

        sound_layout.addWidget(
            self.sound_title
        )

        volume_row = QHBoxLayout()

        self.volume_label = QLabel()

        self.volume_text = QLabel()

        self.volume_text.setMinimumWidth(45)

        self.volume_text.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        volume_row.addWidget(
            self.volume_label
        )

        volume_row.addStretch()

        volume_row.addWidget(
            self.volume_text
        )

        self.volume_slider = SettingsSlider()

        self.volume_slider.setRange(
            0,
            100,
        )

        self.volume_slider.setValue(
            self.settings.get(
                "preview_volume",
                70,
            )
        )

        self.volume_slider.valueChanged.connect(
            self.change_volume
        )

        sound_layout.addLayout(
            volume_row
        )

        sound_layout.addWidget(
            self.volume_slider
        )

        layout.addWidget(
            sound_card
        )

        # ==================================
        # SERVICE
        # ==================================

        service_card, service_layout = (
            self.make_card()
        )

        self.service_title = QLabel()

        self.service_title.setObjectName(
            "SettingSectionTitle"
        )

        service_layout.addWidget(
            self.service_title
        )

        self.reset_button = QPushButton()

        self.reset_button.clicked.connect(
            self.reset_settings
        )

        service_layout.addWidget(
            self.reset_button
        )

        layout.addWidget(
            service_card
        )

        layout.addStretch()

        self.scroll.setWidget(
            container
        )

    # ======================================
    # SUBPAGE FACTORY
    # ======================================

    def make_subpage(self, page):
        outer = QVBoxLayout(page)

        outer.setContentsMargins(
            0, 0, 0, 0
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        outer.addWidget(scroll)

        content = QWidget()

        layout = QVBoxLayout(content)

        layout.setContentsMargins(
            16, 16, 16, 20
        )

        layout.setSpacing(16)

        back_button = QPushButton()

        back_button.setObjectName(
            "BackButton"
        )

        back_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        # Theme-aware high-resolution navigation arrow.
        back_button.setIcon(load_back_icon(self.settings))
        back_button.setIconSize(QSize(23, 23))
        back_button.setMinimumHeight(40)
        back_button.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        back_button.clicked.connect(
            self.go_back
        )

        layout.addWidget(
            back_button,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )

        title = QLabel()
        title.setObjectName("Title")

        layout.addWidget(title)

        scroll.setWidget(content)

        return layout, back_button, title

    # ======================================
    # CUSTOMIZATION PAGE
    # ======================================

    def build_custom_page(self):
        (
            layout,
            self.custom_back,
            self.custom_title,
        ) = self.make_subpage(
            self.custom_page
        )

        # ==================================
        # APPEARANCE MODE
        # ==================================

        mode_card, mode_layout = self.make_card()

        self.mode_label = QLabel()

        self.mode_label.setObjectName(
            "SettingSectionTitle"
        )

        mode_layout.addWidget(
            self.mode_label
        )

        self.mode_combo = SettingsComboBox()

        for mode in APPEARANCE_MODES:
            self.mode_combo.addItem(
                mode,
                mode,
            )

        mode_layout.addWidget(
            self.mode_combo
        )

        self.appearance_toggle = PaintedCheckBox()
        self.appearance_toggle.set_checked_immediately(
            not self.settings.get("accent_enabled", False)
        )
        self.appearance_toggle.toggled.connect(self.change_appearance_enabled)
        mode_layout.addWidget(self.appearance_toggle)

        layout.addWidget(
            mode_card
        )

        # ==================================
        # COLOR THEME
        # ==================================

        theme_card, theme_layout = self.make_card()

        self.accent_label = QLabel()

        self.accent_label.setObjectName(
            "SettingSectionTitle"
        )

        theme_layout.addWidget(
            self.accent_label
        )

        self.theme_combo = SettingsComboBox()

        for theme_id in COLOR_THEMES:
            self.theme_combo.addItem(
                theme_id,
                theme_id,
            )

        self.theme_combo.addItem("Свой цвет", "custom")
        theme_layout.addWidget(
            self.theme_combo
        )

        # Opt-in accent control. Light/dark backgrounds remain neutral.
        self.accent_toggle = PaintedCheckBox()
        self.accent_toggle.set_checked_immediately(
            self.settings.get("accent_enabled", False)
        )
        self.accent_toggle.toggled.connect(self.change_accent_enabled)
        theme_layout.addWidget(self.accent_toggle)

        layout.addWidget(
            theme_card
        )

        # ==================================
        # THEME INTENSITY (0–100%)
        # ==================================

        intensity_card, intensity_layout = self.make_card()
        self.intensity_label = QLabel()
        self.intensity_label.setObjectName("SettingSectionTitle")
        intensity_layout.addWidget(self.intensity_label)
        self.intensity_slider = SettingsSlider()
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(self.settings.get("theme_intensity", 60))
        self.intensity_value = QLabel("60%")
        intensity_layout.addWidget(self.intensity_slider)
        intensity_layout.addWidget(self.intensity_value)
        self.intensity_reset_button = ResetSliderButton()
        self.intensity_reset_button.setObjectName("ResetSliderButton")
        self.intensity_reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.intensity_reset_button.clicked.connect(self.reset_intensity)
        self.intensity_reset_button.setVisible(
            self.intensity_slider.value() != DEFAULT_SETTINGS["theme_intensity"]
        )
        intensity_layout.addWidget(self.intensity_reset_button)
        layout.addWidget(intensity_card)

        # ==================================
        # USER-DEFINED HEX COLOR
        # ==================================

        hex_card, hex_layout = self.make_card()
        self.hex_label = QLabel()
        self.hex_label.setObjectName("SettingSectionTitle")
        hex_layout.addWidget(self.hex_label)
        hex_row = QHBoxLayout()
        self.hex_edit = QLineEdit()
        self.hex_edit.setMaxLength(7)
        self.hex_edit.setPlaceholderText("#4777BA")
        self.hex_edit.setText(self.settings.get("custom_hex", "#4777BA"))
        self.hex_apply = QPushButton()
        self.hex_apply.setObjectName("Primary")
        self.hex_apply.clicked.connect(self.apply_hex_color)
        self.hex_edit.returnPressed.connect(self.apply_hex_color)
        hex_row.addWidget(self.hex_edit, 1)
        hex_row.addWidget(self.hex_apply)
        hex_layout.addLayout(hex_row)
        layout.addWidget(hex_card)

        # ==================================
        # ANIMATION CONTROLS
        # ==================================

        animation_card, animation_layout = self.make_card()
        self.animation_title = QLabel()
        self.animation_title.setObjectName("SettingSectionTitle")
        animation_layout.addWidget(self.animation_title)
        self.animation_toggle = PaintedCheckBox()
        self.animation_toggle.set_checked_immediately(
            self.settings.get("animations_enabled", True)
        )
        self.animation_toggle.toggled.connect(self.change_animation_enabled)
        animation_layout.addWidget(self.animation_toggle)
        self.animation_speed_label = QLabel()
        self.animation_speed_label.setObjectName("SettingSectionTitle")
        animation_layout.addWidget(self.animation_speed_label)
        self.animation_slider = SettingsSlider()
        self.animation_slider.setRange(25, 300)
        self.animation_slider.setValue(self.settings.get("animation_speed", 100))
        self.animation_value = QLabel("100%")
        animation_layout.addWidget(self.animation_slider)
        animation_layout.addWidget(self.animation_value)
        self.animation_reset_button = ResetSliderButton()
        self.animation_reset_button.setObjectName("ResetSliderButton")
        self.animation_reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.animation_reset_button.clicked.connect(self.reset_animation_speed)
        self.animation_reset_button.setVisible(
            self.animation_slider.value() != DEFAULT_SETTINGS["animation_speed"]
        )
        animation_layout.addWidget(self.animation_reset_button)
        layout.addWidget(animation_card)

        # Avoid repainting the window for each step of slider dragging.
        self.intensity_slider.setTracking(True)
        self.animation_slider.setTracking(True)
        self.intensity_slider.valueChanged.connect(self._intensity_changed)
        self.animation_slider.valueChanged.connect(self._animation_speed_changed)
        self.intensity_slider.sliderReleased.connect(self._save_slider_changes)
        self.animation_slider.sliderReleased.connect(self._save_slider_changes)

        # ==================================
        # APPEARANCE PRESETS
        # ==================================

        self.presets_open_button = QPushButton()
        self.presets_open_button.setObjectName("PersonalLink")
        self.presets_open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.presets_open_button.clicked.connect(self.open_presets_dialog)
        layout.addWidget(self.presets_open_button)

        # Presets share the application's internal page stack, like Language.
        (preset_page_layout, self.presets_back, self.presets_page_title) = (
            self.make_subpage(self.presets_page)
        )
        self.presets_back.clicked.connect(lambda: self._switch_internal_panel(1))
        preset_card, preset_layout = self.make_card()
        self.presets_title = QLabel()
        self.presets_title.setObjectName("SettingSectionTitle")
        preset_layout.addWidget(self.presets_title)
        self.preset_name = QLineEdit()
        self.preset_name.setMaxLength(32)
        preset_layout.addWidget(self.preset_name)
        self.preset_save = QPushButton()
        self.preset_save.clicked.connect(self.save_current_preset)
        preset_layout.addWidget(self.preset_save)
        self.preset_combo = SettingsComboBox()
        preset_layout.addWidget(self.preset_combo)
        preset_buttons = QHBoxLayout()
        self.preset_apply = QPushButton()
        self.preset_delete = QPushButton()
        self.preset_apply.clicked.connect(self.apply_selected_preset)
        self.preset_delete.clicked.connect(self.delete_selected_preset)
        preset_buttons.addWidget(self.preset_apply)
        preset_buttons.addWidget(self.preset_delete)
        preset_layout.addLayout(preset_buttons)
        preset_page_layout.addWidget(preset_card)
        preset_page_layout.addStretch()
        self.refresh_preset_choices()

        # ==================================
        # FONT
        # ==================================

        font_card, font_layout = self.make_card()

        self.font_label = QLabel()

        self.font_label.setObjectName(
            "SettingSectionTitle"
        )

        font_layout.addWidget(
            self.font_label
        )

        self.font_combo = SettingsComboBox()

        for font_name in FONT_OPTIONS:
            self.font_combo.addItem(
                font_name,
                font_name,
            )

        font_layout.addWidget(
            self.font_combo
        )

        layout.addWidget(
            font_card
        )

        # ==================================
        # PREVIEW
        # ==================================

        preview_card, preview_layout = (
            self.make_card()
        )

        self.preview_label = QLabel()

        self.preview_label.setObjectName(
            "SettingSectionTitle"
        )

        self.preview_text = QLabel()

        self.preview_text.setWordWrap(True)

        self.preview_swatch = QFrame()

        self.preview_swatch.setObjectName(
            "AccentPreview"
        )

        self.preview_swatch.setFixedHeight(20)

        preview_layout.addWidget(
            self.preview_label
        )

        preview_layout.addWidget(
            self.preview_text
        )

        preview_layout.addWidget(
            self.preview_swatch
        )

        layout.addWidget(
            preview_card
        )

        layout.addStretch()

        # ==================================
        # CONNECT CHANGES
        # ==================================

        self.mode_combo.currentIndexChanged.connect(
            lambda _:
                self.change_visual_setting(
                    "appearance_mode",
                    self.mode_combo.currentData(),
                )
        )

        self.theme_combo.currentIndexChanged.connect(
            lambda _:
                self.change_visual_setting(
                    "theme",
                    self.theme_combo.currentData(),
                )
        )

        self.font_combo.currentIndexChanged.connect(
            lambda _:
                self.change_visual_setting(
                    "font_family",
                    self.font_combo.currentData(),
                )
        )

    # ======================================
    # LANGUAGE PAGE
    # ======================================

    def build_language_page(self):
        (
            layout,
            self.lang_back,
            self.lang_title,
        ) = self.make_subpage(
            self.language_page
        )

        language_card, language_layout = (
            self.make_card()
        )

        self.language_choice_label = QLabel()

        self.language_choice_label.setObjectName(
            "SettingSectionTitle"
        )

        language_layout.addWidget(
            self.language_choice_label
        )

        self.language_combo = SettingsComboBox()

        for language_code, native_name in (
            LANGUAGES.items()
        ):
            self.language_combo.addItem(
                native_name,
                language_code,
            )

        language_layout.addWidget(
            self.language_combo
        )

        layout.addWidget(
            language_card
        )

        layout.addStretch()

        self.language_combo.currentIndexChanged.connect(
            lambda _:
                self.change_visual_setting(
                    "language",
                    self.language_combo.currentData(),
                )
        )

    # ======================================
    # NAVIGATE TO CUSTOMIZATION
    # ======================================

    def open_customization(self):
        self.sync_embedded_controls()
        # Страница открывается внутри приложения, без QDialog.
        # Возврат всегда ведёт к основным настройкам.
        self._switch_internal_panel(1)

    # ======================================
    # NAVIGATE TO LANGUAGE
    # ======================================

    def open_language_panel(self):
        self.sync_embedded_controls()
        self._switch_internal_panel(2)

    # ======================================
    # RETURN TO MAIN SETTINGS
    # ======================================

    def go_back(self):
        self._switch_internal_panel(0)

    # ======================================
    # NO-JITTER INTERNAL PAGE TRANSITIONS
    # ======================================

    def _switch_internal_panel(self, index):
        """Stable page switch with optional fade of ONLY the title label.

        Animating a whole QScrollArea can force Qt to repaint a giant cached
        surface and cause jumps. This never animates the page geometry.
        """
        if index == self.panel_stack.currentIndex():
            return
        if not (0 <= index < self.panel_stack.count()):
            return
        if self._panel_title_animation is not None:
            previous_effect = self._panel_title_animation.targetObject()
            self._panel_title_animation.stop()
            if isinstance(previous_effect, QGraphicsOpacityEffect):
                previous_effect.setOpacity(1.0)
            self._panel_title_animation = None
        self.panel_stack.setUpdatesEnabled(False)
        try:
            self.panel_stack.setCurrentIndex(index)
        finally:
            self.panel_stack.setUpdatesEnabled(True)
        self.panel_stack.update()
        if not self.settings.get("animations_enabled", True):
            return
        titles = (self.page_title, self.custom_title, self.lang_title, self.presets_page_title)
        title = titles[index]
        effect = title.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(title)
            title.setGraphicsEffect(effect)
        effect.setOpacity(0.55)
        try:
            speed = max(25, min(300, int(self.settings.get("animation_speed", 100))))
        except (TypeError, ValueError, OverflowError):
            speed = 100
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(max(65, round(19000 / speed)))
        animation.setStartValue(0.55)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: effect.setOpacity(1.0))
        self._panel_title_animation = animation
        animation.start()

    # ======================================
    # UPDATE ALL TEXT
    # ======================================

    def update_language(self):
        language = self.settings.get(
            "language",
            "ru",
        )

        # ==================================
        # MAIN PAGE
        # ==================================

        self.page_title.setText(
            tr("title", language)
        )

        self.page_subtitle.setText(
            tr("subtitle", language)
        )

        self.detection_title.setText(
            tr("detection", language)
        )

        self.interface_title.setText(
            tr("interface", language)
        )

        self.personal_title.setText(
            tr("personalization", language)
        )

        self.customization_button.setText(
            tr("customize", language)
        )

        self.language_button.setText(
            tr("language", language)
        )

        self.sound_title.setText(
            tr("audio", language)
        )

        self.volume_label.setText(
            tr("volume", language)
        )

        self.service_title.setText(
            tr("service", language)
        )

        self.reset_button.setText(
            tr("reset", language)
        )

        # ==================================
        # SWITCH LABELS
        # ==================================

        for data in self.checkboxes.values():
            data["checkbox"].setText(
                tr(
                    data["title_key"],
                    language,
                )
            )

            explanation = tr(
                data["description_key"],
                language,
            )
            data["description"].setText(explanation)
            data["checkbox"].setToolTip(explanation)
            data["checkbox"].setAccessibleDescription(explanation)

        # ==================================
        # CUSTOMIZATION
        # ==================================

        self.custom_back.setText(
            tr("back", language).lstrip("← ")
        )

        self.custom_title.setText(
            tr("customize", language)
        )

        self.mode_label.setText(
            tr("appearance_mode", language)
        )

        self.accent_label.setText(
            tr("theme", language)
        )

        self.font_label.setText(
            tr("font", language)
        )

        self.preview_label.setText(
            tr("preview_title", language)
        )

        self.preview_text.setText(
            tr("preview_text", language)
        )
        self.intensity_label.setText(tr("intensity", language))
        self.hex_label.setText(tr("custom_hex", language))
        self.hex_apply.setText(tr("apply_hex", language))
        self.animation_title.setText(tr("animation_section", language))
        self.animation_toggle.setText(tr("animations_enabled", language))
        self.animation_speed_label.setText(tr("animation_speed", language))
        self.intensity_reset_button.setText(tr("reset_value", language))
        self.animation_reset_button.setText(tr("reset_value", language))
        self.presets_title.setText(tr("presets", language))
        self.presets_open_button.setText(tr("presets", language) + "  ›")
        self.presets_page_title.setText(tr("presets", language))
        self.presets_back.setText(tr("back", language).lstrip("← "))
        self.appearance_toggle.setText({
            "ru": "Использовать режим оформления",
            "uk": "Використовувати режим оформлення",
            "en": "Use appearance mode",
            "de": "Darstellungsmodus verwenden",
            "fr": "Utiliser le mode d’apparence",
            "es": "Utilizar modo de apariencia",
            "pl": "Użyj trybu wyglądu",
        }.get(language, "Use appearance mode"))
        self.accent_toggle.setText({
            "ru": "Включить цвет акцента",
            "uk": "Увімкнути акцентний колір",
            "en": "Enable accent color",
            "de": "Akzentfarbe aktivieren",
            "fr": "Activer la couleur d’accent",
            "es": "Activar color de acento",
            "pl": "Włącz kolor akcentu",
        }.get(language, "Enable accent color"))
        self.preset_name.setPlaceholderText(tr("preset_placeholder", language))
        self.preset_save.setText(tr("save_preset", language))
        self.preset_apply.setText(tr("apply_preset", language))
        self.preset_delete.setText(tr("delete_preset", language))

        # ==================================
        # LANGUAGE PANEL
        # ==================================

        self.lang_back.setText(
            tr("back", language).lstrip("← ")
        )

        self.lang_title.setText(
            tr("language", language)
        )

        self.language_choice_label.setText(
            tr("language_option", language)
        )

        # ==================================
        # COMBOBOX LABELS
        # ==================================

        with QSignalBlocker(self.mode_combo):
            for index, mode in enumerate(APPEARANCE_MODES):
                self.mode_combo.setItemText(index, tr(mode, language))

        with QSignalBlocker(self.theme_combo):
            for index, theme_key in enumerate(COLOR_THEMES):
                self.theme_combo.setItemText(
                    index, tr("color_" + theme_key, language)
                )
            self.theme_combo.setItemText(
                self.theme_combo.findData("custom"), tr("color_custom", language)
            )

    # ======================================
    # APPLY APPEARANCE
    # ======================================

    def apply_appearance(self):
        """
        Обновляет оформление страницы
        только при смене визуальных
        параметров.

        Обычные переключатели не вызывают
        этот метод.
        """

        # The resolved system mode belongs in this signature, otherwise
        # Windows dark/light changes can be skipped as "unchanged settings".
        signature = (
            effective_mode(self.settings),
            self.settings.get("theme", "blue"),
            self.settings.get("appearance_mode", "black"),
            self.settings.get("font_family", "Segoe UI"),
            self.settings.get("custom_hex", "#4777BA"),
            self.settings.get("theme_intensity", 60),
            self.settings.get("accent_enabled", False),
            self.settings.get("appearance_enabled", True),
        )

        if signature == self._last_visual_signature:
            return

        theme = get_theme(
            self.settings.get(
                "theme",
                "blue",
            )
        )

        palette = theme_palette(self.settings)
        accent = palette["accent"]
        hover = palette["accent_hover"]

        font_name = self.settings.get(
            "font_family",
            "Segoe UI",
        )

        if font_name not in FONT_OPTIONS:
            font_name = "Segoe UI"

        self.setFont(
            QFont(font_name, 10)
        )

        light_mode = (
            effective_mode(self.settings) == "white"
        )

        # ==================================
        # PAINTED CONTROLS
        # ==================================

        for data in self.checkboxes.values():
            checkbox = data["checkbox"]
            checkbox.set_theme_palette(palette)

        # Custom arrow is painted in a matching foreground color.
        arrow_color = "#202A38" if light_mode else "#E9EDF3"
        for combo in (
            self.mode_combo,
            self.theme_combo,
            self.font_combo,
            self.language_combo,
            self.preset_combo,
        ):
            combo.set_arrow_color(arrow_color)

        # Update icons on every appearance change (including OS system mode).
        back_icon = load_back_icon(self.settings)
        for back_button in (
            self.custom_back,
            self.presets_back,
            self.lang_back,
        ):
            back_button.setIcon(back_icon)
            back_button.setIconSize(QSize(23, 23))

        reset_icon = load_reset_icon(self.settings)
        for reset_button in (
            self.intensity_reset_button,
            self.animation_reset_button,
        ):
            reset_button.set_icon_color(palette["text"])
            reset_button.setIcon(reset_icon)
            reset_button.setIconSize(QSize(18, 18))

        # The settings reset action uses the same image as slider resets.
        self.reset_button.setIcon(reset_icon)
        self.reset_button.setIconSize(QSize(18, 18))

        self.volume_slider.set_theme_palette(palette)
        self.intensity_slider.set_theme_palette(palette)
        self.animation_slider.set_theme_palette(palette)
        self.animation_toggle.set_theme_palette(palette)
        self.accent_toggle.set_theme_palette(palette)
        self.appearance_toggle.set_theme_palette(palette)
        self.intensity_value.setText(f"{self.settings.get('theme_intensity', 60)}%")
        self.animation_value.setText(f"{self.settings.get('animation_speed', 100)}%")

        # ==================================
        # PROCEDURAL PREVIEW
        # ==================================

        self.preview_swatch.setStyleSheet(
            f"""
            QFrame#AccentPreview {{
                background-color: {accent};
                border: 1px solid {hover};
                border-radius: 8px;
            }}
            """
        )

        # ==================================
        # BASE STYLESHEET
        # ==================================

        source_style = f"""
        /* Root surfaces should never remain in the previous gray scheme. */
        QWidget#SettingsPageRoot,
        QWidget#SettingsMainPage,
        QWidget#SettingsCustomPage,
        QWidget#SettingsLanguagePage {{
            background-color: #15171B;
        }}

        QScrollArea,
        QScrollArea > QWidget > QWidget {{
            background-color: #15171B;
        }}

        QStackedWidget#SettingsPanelStack {{
            background-color: #15171B;
        }}

        QWidget {{
            color: #E9EDF3;
            font-family: "{font_name}";
        }}

        QLabel {{
            background: transparent;
            border: none;
        }}

        QLabel#Title {{
            color: #FFFFFF;
            font-size: 23px;
            font-weight: 700;
        }}

        QLabel#Subtitle {{
            color: #949EAD;
            font-size: 12px;
        }}

        QLabel#SettingSectionTitle {{
            color: #F0F2F6;
            font-size: 16px;
            font-weight: 600;
        }}

        QLabel#SettingDescription {{
            color: #939EAF;
            font-size: 12px;
        }}

        QFrame#SettingCard {{
            background-color: #1D2026;
            border: 1px solid #353A43;
            border-radius: 14px;
        }}

        QFrame#SettingCard QLabel {{
            background: transparent;
            border: none;
        }}

        QPushButton {{
            background-color: #282C33;
            color: #E9EDF3;
            border: 1px solid #414956;
            border-radius: 9px;
            padding: 11px 14px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background-color: #343A44;
            border-color: {accent};
        }}

        QPushButton:pressed {{
            background-color: #22262D;
        }}

        QPushButton#PersonalLink {{
            background-color: #292E36;
            color: #E9EDF3;
            border: 1px solid #414956;
            text-align: left;
        }}

        QPushButton#PersonalLink:hover {{
            background-color: {accent};
            color: #FFFFFF;
            border-color: {accent};
        }}

        QPushButton#BackButton {{
            background-color: #292E36;
            text-align: left;
        }}

        QPushButton#ResetSliderButton {{
            background-color: #292E36;
            border: 1px solid #414956;
            text-align: center;
        }}

        QPushButton#ResetSliderButton:hover {{
            border-color: {accent};
        }}

        QPushButton#BackButton:hover {{
            background-color: {accent};
            color: #FFFFFF;
            border-color: {accent};
        }}

        /* One unified field; the native drop-down button is invisible. */
        QComboBox {{
            background-color: #282C33;
            color: #E9EDF3;
            border: 1px solid #414956;
            border-radius: 9px;
            padding: 9px 43px 9px 12px;
            min-height: 26px;
        }}
        QComboBox:hover {{
            border: 1px solid {accent};
        }}
        QComboBox:focus {{
            border: 1px solid {accent};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 36px;
            border: 0px;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            image: none;
            width: 0px;
            height: 0px;
        }}
        QComboBox QAbstractItemView {{
            background-color: #23272F;
            color: #E9EDF3;
            border: 1px solid #414956;
            selection-background-color: {accent};
            selection-color: #FFFFFF;
            outline: none;
            padding: 5px;
        }}

        QLineEdit {{
            background-color: #282C33;
            color: #E9EDF3;
            border: 1px solid #414956;
            border-radius: 9px;
            padding: 9px 12px;
            min-height: 26px;
        }}
        QLineEdit:focus {{
            border: 1px solid {accent};
        }}

        QScrollArea {{
            background: transparent;
            border: none;
        }}

        QStackedWidget#SettingsPanelStack {{
            background: transparent;
            border: none;
        }}
        """

        result_style = transform_stylesheet(
            source_style,
            self.settings,
            apply_accent=False,
        )

        # The full-color engine transforms the neutral surfaces as well.
        # Use an explicit contrast override AFTER transformation, because
        # its light-mode lookup intentionally converts plain white text.
        # Selected and hovered accent buttons must still use white glyphs.
        result_style += f"""
        QPushButton#PersonalLink:hover,
        QPushButton#BackButton:hover,
        QComboBox QAbstractItemView::item:selected {{
            color: #FFFFFF;
        }}
        QComboBox QAbstractItemView {{
            selection-background-color: {accent};
            selection-color: #FFFFFF;
        }}
        """

        if self.styleSheet() != result_style:
            self.setStyleSheet(result_style)

        # Запоминаем состояние только после успешного обновления.
        self._last_visual_signature = signature

        # Theme applies to the entire application
        # through ManagerWindow.apply_settings().
        # This class only styles its own controls.

    # ======================================
    # NEW CUSTOMIZATION CONTROLS
    # ======================================

    def _update_slider_reset_buttons(self):
        """Show reset controls only when values differ from their defaults."""
        self.intensity_reset_button.setVisible(
            self.intensity_slider.value() != DEFAULT_SETTINGS["theme_intensity"]
        )
        self.animation_reset_button.setVisible(
            self.animation_slider.value() != DEFAULT_SETTINGS["animation_speed"]
        )

    def _intensity_changed(self, *_args):
        """Update numeric label and schedule a LIVE, unsaved theme preview."""
        self.intensity_value.setText(f"{self.intensity_slider.value()}%")
        self._update_slider_reset_buttons()
        if self._updating_controls:
            return
        # A running timer is not restarted: continuous dragging keeps producing
        # previews instead of waiting for the mouse to stop moving.
        if not self._intensity_preview_timer.isActive():
            self._intensity_preview_timer.start()
        self._slider_save_timer.start()

    def _animation_speed_changed(self, *_args):
        self.animation_value.setText(f"{self.animation_slider.value()}%")
        self._update_slider_reset_buttons()
        if not self._updating_controls:
            self._slider_save_timer.start()

    def _apply_live_intensity_preview(self):
        """Preview the whole application WITHOUT writing settings.json."""
        if self._updating_controls:
            return
        value = self.intensity_slider.value()
        self.settings["theme_intensity"] = value
        manager = self.window()
        if manager is not self and hasattr(manager, "preview_theme_intensity"):
            manager.preview_theme_intensity(value)
        else:
            self.apply_appearance()

    def _save_slider_changes(self):
        self._slider_save_timer.stop()
        self._intensity_preview_timer.stop()
        if self._updating_controls:
            return
        # Never save or synchronize widgets in the middle of a drag.
        # The sliderReleased signal commits the final selection.
        if self.intensity_slider.isSliderDown() or self.animation_slider.isSliderDown():
            return
        changes = {
            "theme_intensity": self.intensity_slider.value(),
            "animation_speed": self.animation_slider.value(),
        }
        # Live previews change in-memory values. Compare against persisted
        # values, not self.settings, to ensure the final value gets saved.
        latest = load_settings()
        actual_changes = {
            key: value for key, value in changes.items()
            if latest.get(key) != value
        }
        if actual_changes:
            self._commit_customization(actual_changes)
        self._update_slider_reset_buttons()

    def reset_intensity(self):
        """Restore the standard theme intensity and apply it immediately."""
        self._slider_save_timer.stop()
        self._intensity_preview_timer.stop()
        target = DEFAULT_SETTINGS["theme_intensity"]
        with QSignalBlocker(self.intensity_slider):
            self.intensity_slider.setValue(target)
        self.intensity_value.setText(f"{target}%")
        self._update_slider_reset_buttons()
        self.settings["theme_intensity"] = target
        manager = self.window()
        if manager is not self and hasattr(manager, "preview_theme_intensity"):
            manager.preview_theme_intensity(target)
        else:
            self.apply_appearance()
        self._save_slider_changes()

    def reset_animation_speed(self):
        """Restore the standard animation speed without changing other options."""
        self._slider_save_timer.stop()
        target = DEFAULT_SETTINGS["animation_speed"]
        with QSignalBlocker(self.animation_slider):
            self.animation_slider.setValue(target)
        self.animation_value.setText(f"{target}%")
        self._update_slider_reset_buttons()
        self._save_slider_changes()

    def _commit_customization(self, changes):
        try:
            updated = save_settings(changes)
        except (ValueError, TypeError, OSError) as error:
            QMessageBox.warning(self, tr("error_title", self.settings.get("language", "ru")), str(error))
            self.sync_controls()
            return
        self.on_personalization_change(updated)

    def apply_hex_color(self):
        import re
        value = self.hex_edit.text().strip().upper()
        if not re.fullmatch(r"#[0-9A-F]{6}", value):
            QMessageBox.warning(
                self, tr("error_title", self.settings.get("language", "ru")),
                tr("invalid_hex", self.settings.get("language", "ru"))
            )
            return
        self._commit_customization({
            "custom_hex": value, "theme": "custom",
            "accent_enabled": True, "appearance_enabled": False,
        })

    def change_animation_enabled(self, checked):
        if self._updating_controls:
            return
        self._commit_customization({"animations_enabled": bool(checked)})

    def change_accent_enabled(self, checked):
        if self._updating_controls:
            return
        self._commit_customization({
            "accent_enabled": bool(checked),
            "appearance_enabled": not bool(checked),
        })

    def change_appearance_enabled(self, checked):
        if self._updating_controls:
            return
        self._commit_customization({
            "appearance_enabled": bool(checked),
            "accent_enabled": not bool(checked),
        })

    def open_presets_dialog(self):
        """Retained public method name, now opens an embedded settings page."""
        self.refresh_preset_choices()
        self._switch_internal_panel(3)

    @staticmethod
    def _presets_base_qss():
        return """
        QDialog { background-color: #15171B; color: #E9EDF3; }
        QLabel { color: #E9EDF3; background: transparent; }
        QFrame#SettingCard {
            background-color: #1D2026;
            border: 1px solid #353A43;
            border-radius: 14px;
        }
        QLineEdit, QComboBox {
            background-color: #282C33;
            color: #E9EDF3;
            border: 1px solid #414956;
            border-radius: 8px;
            padding: 9px;
        }
        QPushButton {
            color: #E9EDF3;
            background-color: #282C33;
            border: 1px solid #414956;
            border-radius: 8px;
            padding: 10px;
        }
        QPushButton:hover { background-color: #343A44; }
        """

    def refresh_preset_choices(self):
        if not hasattr(self, "preset_combo"):
            return
        current = self.preset_combo.currentData()
        entries = self.settings.get("appearance_presets", {})
        with QSignalBlocker(self.preset_combo):
            self.preset_combo.clear()
            for name in sorted(entries):
                self.preset_combo.addItem(name, name)
            if current is not None:
                idx = self.preset_combo.findData(current)
                if idx >= 0:
                    self.preset_combo.setCurrentIndex(idx)
        available = bool(entries)
        self.preset_apply.setEnabled(available)
        self.preset_delete.setEnabled(available)

    def save_current_preset(self):
        name = self.preset_name.text().strip()
        try:
            latest = save_appearance_preset(name)
        except (OSError, ValueError, TypeError) as error:
            QMessageBox.warning(self, tr("preset_error", self.settings.get("language", "ru")), str(error))
            return
        self.settings = latest
        self.refresh_preset_choices()
        idx = self.preset_combo.findData(name)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
        self.settings_changed.emit(latest.copy())

    def apply_selected_preset(self):
        name = self.preset_combo.currentData()
        if not name:
            return
        try:
            latest = apply_appearance_preset(name)
        except (KeyError, ValueError, TypeError, OSError) as error:
            QMessageBox.warning(self, tr("preset_error", self.settings.get("language", "ru")), str(error))
            return
        self.on_personalization_change(latest)
        self.sync_controls()

    def delete_selected_preset(self):
        name = self.preset_combo.currentData()
        if not name:
            return
        try:
            latest = delete_appearance_preset(name)
        except (OSError, ValueError, TypeError) as error:
            QMessageBox.warning(self, tr("preset_error", self.settings.get("language", "ru")), str(error))
            return
        self.settings = latest
        self.refresh_preset_choices()
        self.settings_changed.emit(latest.copy())

    # ======================================
    # SAVE BOOLEAN SETTING
    # ======================================

    def change_setting(self, key, value):
        if self._updating_controls:
            return

        if self.settings.get(key) == bool(value):
            return

        try:
            updated = save_settings({
                key: bool(value)
            })

        except (
            OSError,
            ValueError,
            TypeError,
        ) as error:
            QMessageBox.warning(
                self,
                tr(
                    "error_title",
                    self.settings.get(
                        "language",
                        "ru",
                    ),
                ),
                str(error),
            )

            self.sync_controls()
            return

        self.settings = updated

        # Important:
        # Do not call apply_appearance() here.
        # This prevents whole-window flickering.

        self.settings_changed.emit(
            updated.copy()
        )

    # ======================================
    # SAVE VOLUME
    # ======================================

    def change_volume(self, value):
        if self._updating_controls:
            return

        self.volume_text.setText(
            f"{value}%"
        )

        if (
            self.settings.get("preview_volume")
            == value
        ):
            return

        try:
            updated = save_settings({
                "preview_volume": value
            })

        except (
            OSError,
            ValueError,
            TypeError,
        ) as error:
            QMessageBox.warning(
                self,
                tr(
                    "error_title",
                    self.settings.get(
                        "language",
                        "ru",
                    ),
                ),
                str(error),
            )

            self.sync_controls()
            return

        self.settings = updated

        self.settings_changed.emit(
            updated.copy()
        )

    # ======================================
    # CHANGE THEME / FONT / LANGUAGE
    # ======================================

    def change_visual_setting(self, key, value):
        if self._updating_controls:
            return

        if value is None:
            return

        # Не сохраняем произвольные значения, попавшие в обработчик
        # из внешнего кода или некорректного сигнала QComboBox.
        supported = {
            "theme": tuple(COLOR_THEMES) + ("custom",),
            "appearance_mode": APPEARANCE_MODES,
            "font_family": FONT_OPTIONS,
            "language": tuple(LANGUAGES),
        }
        if key not in supported or value not in supported[key]:
            return

        if self.settings.get(key) == value:
            return

        changes = {key: value}
        if key == "appearance_mode":
            changes.update(appearance_enabled=True, accent_enabled=False)
        elif key == "theme":
            changes.update(appearance_enabled=False, accent_enabled=True)
        try:
            updated = save_settings(changes)

        except (
            OSError,
            ValueError,
            TypeError,
        ) as error:
            QMessageBox.warning(
                self,
                tr(
                    "error_title",
                    self.settings.get(
                        "language",
                        "ru",
                    ),
                ),
                str(error),
            )

            self.sync_controls()
            return

        self.on_personalization_change(
            updated
        )

    # ======================================
    # VISUAL SETTINGS CALLBACK
    # ======================================

    def on_personalization_change(self, settings):
        previous = self.settings.copy()

        self.settings = settings.copy()
        # Подстраницы могут быть открыты во время обновления.
        # Меняем выделение в списках, не отправляя повторные сигналы.
        self.sync_embedded_controls()
        self.refresh_preset_choices()
        # Keep the two mutually-exclusive checkmarks in sync immediately.
        with QSignalBlocker(self.accent_toggle):
            self.accent_toggle.set_checked_immediately(
                self.settings.get("accent_enabled", False)
            )
        with QSignalBlocker(self.appearance_toggle):
            self.appearance_toggle.set_checked_immediately(
                not self.settings.get("accent_enabled", False)
            )

        visuals_changed = any(
            previous.get(key)
            != self.settings.get(key)
            for key in (
                "theme",
                "appearance_mode",
                "font_family",
                "custom_hex",
                "theme_intensity",
                "accent_enabled",
                "appearance_enabled",
            )
        )

        if visuals_changed:
            self.apply_appearance()

        self.update_language()

        self.settings_changed.emit(
            self.settings.copy()
        )

    # ======================================
    # UPDATE COMBOBOXES
    # ======================================

    def sync_embedded_controls(self):
        selections = (
            (
                self.mode_combo,
                "appearance_mode",
                "black",
            ),
            (
                self.theme_combo,
                "theme",
                "blue",
            ),
            (
                self.font_combo,
                "font_family",
                "Segoe UI",
            ),
            (
                self.language_combo,
                "language",
                "ru",
            ),
        )

        for combo, key, fallback in selections:
            desired = self.settings.get(
                key,
                fallback,
            )

            with QSignalBlocker(combo):
                index = combo.findData(
                    desired
                )

                combo.setCurrentIndex(
                    max(0, index)
                )

    # ======================================
    # SYNCHRONIZE CONTROLS
    # ======================================

    def sync_controls(self):
        self._updating_controls = True

        try:
            for key, data in self.checkboxes.items():
                checkbox = data["checkbox"]

                desired = self.settings.get(
                    key,
                    False,
                )

                # Avoid needless animations.
                if checkbox.isChecked() != desired:
                    checkbox.set_checked_immediately(
                        desired
                    )

            with QSignalBlocker(
                self.volume_slider
            ):
                self.volume_slider.setValue(
                    self.settings.get(
                        "preview_volume",
                        70,
                    )
                )

            self.volume_text.setText(
                f"{self.settings.get('preview_volume', 70)}%"
            )

            with QSignalBlocker(self.intensity_slider):
                self.intensity_slider.setValue(self.settings.get("theme_intensity", 60))
            with QSignalBlocker(self.animation_slider):
                self.animation_slider.setValue(self.settings.get("animation_speed", 100))
            self.intensity_value.setText(f"{self.settings.get('theme_intensity', 60)}%")
            self.animation_value.setText(f"{self.settings.get('animation_speed', 100)}%")
            self._update_slider_reset_buttons()
            self.animation_toggle.set_checked_immediately(
                self.settings.get("animations_enabled", True)
            )
            self.accent_toggle.set_checked_immediately(
                self.settings.get("accent_enabled", False)
            )
            self.appearance_toggle.set_checked_immediately(
                not self.settings.get("accent_enabled", False)
            )
            self.hex_edit.setText(self.settings.get("custom_hex", "#4777BA"))
            self.refresh_preset_choices()
            self.sync_embedded_controls()

        finally:
            self._updating_controls = False

    # ======================================
    # RESET SETTINGS
    # ======================================

    def reset_settings(self):
        language = self.settings.get(
            "language",
            "ru",
        )

        answer = QMessageBox.question(
            self,
            tr("reset_title", language),
            tr("reset_question", language),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            updated = save_settings(
                DEFAULT_SETTINGS.copy()
            )

        except OSError as error:
            QMessageBox.critical(
                self,
                tr("error_title", language),
                str(error),
            )

            return

        self.on_personalization_change(
            updated
        )

        self.sync_controls()

        self.go_back()

    # ======================================
    # REFRESH FROM DISK
    # ======================================

    def refresh_settings(self):
        latest = load_settings()

        if latest == self.settings:
            return

        previous = self.settings.copy()

        self.settings = latest

        self.sync_controls()

        visuals_changed = any(
            previous.get(key) != latest.get(key)
            for key in (
                "theme",
                "appearance_mode",
                "font_family",
                "custom_hex",
                "theme_intensity",
                "accent_enabled",
                "appearance_enabled",
            )
        )

        if visuals_changed:
            self.apply_appearance()

        if (
            previous.get("language")
            != latest.get("language")
        ):
            self.update_language()

        # Отдельные служебные изменения не запускают полную
        # перерисовку — лишь синхронизируют содержимое контролов.

    # ======================================
    # EXTERNAL SETTINGS UPDATE
    # ======================================

    def apply_external_settings(self, settings):
        """
        Called by ManagerWindow.

        Does not repeatedly repaint the page
        when all values are unchanged.
        """

        if not isinstance(settings, dict):
            return

        if settings == self.settings:
            # System color scheme can change without any settings change.
            if self.settings.get("appearance_mode") == "system":
                self.apply_appearance()
            return

        previous = self.settings.copy()

        self.settings = settings.copy()

        self.sync_controls()

        visuals_changed = any(
            previous.get(key)
            != settings.get(key)
            for key in (
                "theme",
                "appearance_mode",
                "font_family",
                "custom_hex",
                "theme_intensity",
                "accent_enabled",
                "appearance_enabled",
            )
        )

        if visuals_changed:
            self.apply_appearance()

        if (
            previous.get("language")
            != settings.get("language")
        ):
            self.update_language()

    # ======================================
    # SHOW EVENT
    # ======================================

    def showEvent(self, event):
        super().showEvent(event)

        self.refresh_settings()
        # Системная тема может измениться пока вкладка скрыта.
        # Проверка сигнатуры гарантирует отсутствие лишних обновлений.
        if self.settings.get("appearance_mode") == "system":
            self.apply_appearance()
