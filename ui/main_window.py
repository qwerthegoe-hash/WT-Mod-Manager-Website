
"""
WT Mod Manager 1.3
Main Window

Главное окно менеджера модификаций.

Функции:
- Прицелы
- Камуфляжи
- Звуки
- Конфигурации
- Настройки
- Плавные переходы между разделами
- Цветовые темы
- Светлый / тёмный / системный режим
- Настройка шрифта
- Переключение языков
- Сохранение выбранной вкладки
- Режим поверх окон
- Сворачивание в системный трей
- Управление громкостью аудиоплеера
"""

import sys
import ctypes

from PySide6.QtCore import (
    Qt,
    QTimer,
    Signal,
    QPropertyAnimation,
    QEasingCurve,
)

from PySide6.QtGui import (
    QFont,
    QColor,
    QPalette,
    QPixmap,
    QPainter,
    QPainterPath,
)

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QMainWindow,
    QSystemTrayIcon,
    QSizePolicy,
    QGraphicsOpacityEffect,
    QListWidget,
)

from ui.sights_page import SightsPage
from ui.camouflages_page import CamouflagesPage
from ui.sounds_page import SoundsPage
from ui.settings_page import SettingsPage
from ui.online_page import OnlinePage
from src.update_checker import VERSION as APP_VERSION
from src.game_discovery import find_game_roots, find_sight_folders

from src.settings_store import (
    load_settings,
    save_settings,
)

from ui.i18n import translate_ui as translate_text

from ui.icon_assets import apply_icon
from pathlib import Path
from PySide6.QtGui import QIcon

from ui.theme_engine import (
    transform_stylesheet,
    effective_mode,
    theme_palette,
)


# ==========================================
# APPLICATION LOGO
# ==========================================

LOGO_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets" / "icons" / "Logotip" / "LogotipProject.png"
)


def application_logo_icon():
    """Load the project logo, falling back to the global application icon."""
    if LOGO_PATH.is_file():
        icon = QIcon(str(LOGO_PATH))
        if not icon.isNull():
            return icon
    app = QApplication.instance()
    return app.windowIcon() if app is not None else QIcon()


# ==========================================
# PERSONALIZATION
# ==========================================

THEME_COLORS = {
    "blue": (
        "#4777BA",
        "#365F9C",
        "#4675B5",
    ),
    "green": (
        "#34B887",
        "#197D60",
        "#289F79",
    ),
    "purple": (
        "#9868D9",
        "#6842A8",
        "#8155BD",
    ),
    "red": (
        "#DB6677",
        "#9B3346",
        "#B8465A",
    ),
    "orange": (
        "#DB9C43",
        "#996422",
        "#B77D2C",
    ),
}

SUPPORTED_FONTS = {
    "Segoe UI",
    "Arial",
    "Verdana",
    "Tahoma",
    "Georgia",
}


def translate_ui(text, language):
    """
    Переводит текст интерфейса.
    """
    return translate_text(text, language)


def theme_stylesheet(source, settings):
    """
    Применяет цветовую тему, фон и шрифт
    к исходному стилю.
    """
    return transform_stylesheet(
        source,
        settings,
    )


# ==========================================
# MAIN APPLICATION STYLE
# ==========================================

STYLE = """
QWidget {
    background-color: #15171B;
    color: #E9EDF3;
    font-family: "Segoe UI";
    font-size: 13px;
}

QLabel {
    background-color: transparent;
    border: none;
}

QLabel#Title {
    background-color: transparent;
    border: none;
    font-size: 23px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel#Subtitle {
    background-color: transparent;
    border: none;
    font-size: 12px;
    color: #949EAD;
}

QPushButton {
    background-color: #282C33;
    border: 1px solid #383E47;
    border-radius: 9px;
    padding: 11px 14px;
    color: #E9EDF3;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #343A44;
}

QPushButton:pressed {
    background-color: #22262D;
}

QPushButton:disabled {
    background-color: #24272D;
    color: #697382;
}

QPushButton#Primary {
    background-color: #365F9C;
    border: 1px solid #4777BA;
    color: #FFFFFF;
}

QPushButton#Primary:hover {
    background-color: #4675B5;
}

QPushButton#Primary:pressed {
    background-color: #284E82;
}

QPushButton#Nav {
    text-align: left;
    background-color: transparent;
    border: none;
    border-radius: 9px;
    padding: 13px;
    font-size: 13px;
}

QPushButton#Nav:hover {
    background-color: #30353F;
}

QPushButton#Nav:checked {
    background-color: #313B4B;
    color: #FFFFFF;
}

QPushButton#Nav:checked:hover {
    background-color: #39475C;
}

QFrame#Sidebar {
    background-color: #1D2026;
    border: none;
    border-right: 1px solid #353A43;
}

QFrame#Sidebar QLabel {
    background-color: transparent;
    border: none;
}

QStackedWidget {
    background-color: #15171B;
    border: none;
}

QFrame#ContentCard {
    background-color: #1D2026;
    border: 1px solid #353A43;
    border-radius: 14px;
}

QFrame#ContentCard QLabel {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    background-color: #191C22;
    width: 8px;
    margin: 2px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #444D5A;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #627084;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
    border: none;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #191C22;
    height: 8px;
    margin: 2px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #444D5A;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #627084;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
    border: none;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

QToolTip {
    background-color: #282C33;
    color: #FFFFFF;
    border: 1px solid #454C57;
    border-radius: 6px;
    padding: 6px;
}

/* ======================================
   UNIFIED LISTS / TREE / TABLE
   ====================================== */

QListWidget, QTreeWidget, QTableWidget {
    background-color: #14171C;
    color: #E9EDF3;
    border: 1px solid #353A43;
    border-radius: 9px;
    outline: none;
    alternate-background-color: #1D2026;
    selection-background-color: #365F9C;
    selection-color: #FFFFFF;
}

QListWidget::item, QTreeWidget::item, QTableWidget::item {
    color: #E9EDF3;
    padding: 5px;
    border-radius: 5px;
}

QListWidget::item:hover:!selected,
QTreeWidget::item:hover:!selected,
QTableWidget::item:hover:!selected {
    background-color: #30353F;
}

QListWidget::item:selected,
QTreeWidget::item:selected,
QTableWidget::item:selected {
    background-color: #365F9C;
    color: #FFFFFF;
}

/* ======================================
   DEFAULT INPUT WIDGETS
   ====================================== */

QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
    color: #E9EDF3;
    background-color: #282C33;
    border: 1px solid #414956;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 22px;
}

QComboBox:hover, QLineEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #4777BA;
}

QComboBox:focus, QLineEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #4675B5;
}

QComboBox::drop-down {
    background: transparent;
    border: none;
    width: 26px;
}

QComboBox QAbstractItemView {
    color: #E9EDF3;
    background-color: #23272F;
    border: 1px solid #414956;
    selection-background-color: #365F9C;
    selection-color: #FFFFFF;
    outline: none;
}

/* ======================================
   SCROLLABLE PANELS AND POPUP MENUS
   ====================================== */

QScrollArea {
    border: none;
    background-color: #15171B;
}

QScrollArea > QWidget > QWidget {
    background-color: #15171B;
}

QMenu {
    background-color: #1D2026;
    color: #E9EDF3;
    border: 1px solid #353A43;
    padding: 5px;
}

QMenu::item {
    background: transparent;
    color: #E9EDF3;
    border-radius: 5px;
    padding: 7px 24px;
}

QMenu::item:selected {
    background-color: #365F9C;
    color: #FFFFFF;
}

QMenu::separator {
    background-color: #353A43;
    height: 1px;
    margin: 4px;
}

QDialog, QMessageBox {
    color: #E9EDF3;
    background-color: #15171B;
}

QTextEdit, QPlainTextEdit {
    color: #E9EDF3;
    background-color: #14171C;
    border: 1px solid #353A43;
    border-radius: 9px;
    selection-background-color: #365F9C;
}

/* ======================================
   MISCELLANEOUS NATIVE-STYLE CONTROLS
   ====================================== */

QProgressBar {
    color: #E9EDF3;
    background-color: #282C33;
    border: 1px solid #353A43;
    border-radius: 6px;
    text-align: center;
    min-height: 12px;
}

QProgressBar::chunk {
    background-color: #4777BA;
    border-radius: 5px;
}

QTabWidget::pane {
    background-color: #15171B;
    border: 1px solid #353A43;
}

QTabBar::tab {
    background-color: #1D2026;
    color: #E9EDF3;
    padding: 8px 14px;
}

QTabBar::tab:selected {
    background-color: #365F9C;
    color: #FFFFFF;
}
"""


# ==========================================
# WAR THUNDER LAUNCH PROMPT
# ==========================================

class LaunchPrompt(QDialog):
    """
    Окно предложения запуска менеджера
    после обнаружения War Thunder.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "WT Mod Manager"
        )

        self.setWindowIcon(application_logo_icon())

        self.setMinimumSize(
            340,
            220,
        )

        self.resize(
            440,
            265,
        )

        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setStyleSheet(
            STYLE
        )

        # ==================================
        # SCREEN SIZE
        # ==================================

        screen = QApplication.primaryScreen()

        if screen is not None:
            geometry = screen.availableGeometry()

            width = min(
                440,
                max(
                    300,
                    int(geometry.width() * 0.90),
                ),
            )

            height = min(
                265,
                max(
                    200,
                    int(geometry.height() * 0.90),
                ),
            )

            self.resize(
                width,
                height,
            )

            center_x = (
                geometry.x()
                + (geometry.width() - width) // 2
            )

            center_y = (
                geometry.y()
                + (geometry.height() - height) // 2
            )

            self.move(
                center_x,
                center_y,
            )

        # ==================================
        # LAYOUT
        # ==================================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(14)

        # ==================================
        # TITLE
        # ==================================

        title = QLabel(
            "WAR THUNDER ОБНАРУЖЕН"
        )

        title.setObjectName(
            "Title"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setWordWrap(True)

        # ==================================
        # SUBTITLE
        # ==================================

        subtitle = QLabel(
            "Запустить менеджер модификаций?\n"
            "Сохранённые настройки останутся "
            "без изменений."
        )

        subtitle.setObjectName(
            "Subtitle"
        )

        subtitle.setWordWrap(True)

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # ==================================
        # BUTTONS
        # ==================================

        buttons = QHBoxLayout()

        buttons.setSpacing(12)

        yes_button = QPushButton(
            "Да, открыть"
        )

        yes_button.setObjectName(
            "Primary"
        )

        yes_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        yes_button.clicked.connect(
            self.accept
        )

        no_button = QPushButton(
            "Нет, пропустить"
        )

        no_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        no_button.clicked.connect(
            self.reject
        )

        buttons.addWidget(
            yes_button
        )

        buttons.addWidget(
            no_button
        )

        # ==================================
        # ASSEMBLE DIALOG
        # ==================================

        layout.addStretch()

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(12)

        layout.addLayout(
            buttons
        )

        layout.addStretch()

        # ==================================
        # PERSONALIZATION
        # ==================================

        prompt_settings = load_settings()

        self.setStyleSheet(
            theme_stylesheet(
                STYLE,
                prompt_settings,
            )
        )

        font_name = prompt_settings.get(
            "font_family",
            "Segoe UI",
        )

        if font_name in SUPPORTED_FONTS:
            self.setFont(
                QFont(font_name, 10)
            )

        language = prompt_settings.get(
            "language",
            "ru",
        )

        for widget in (
            title,
            subtitle,
            yes_button,
            no_button,
        ):
            widget.setText(
                translate_ui(
                    widget.text(),
                    language,
                )
            )


# ==========================================
# MAIN MANAGER WINDOW
# ==========================================

class ManagerWindow(QMainWindow):
    check_update_requested = Signal()
    rollback_update_requested = Signal()
    """
    Главное окно WT Mod Manager.

    Разделы:
        0. Прицелы
        1. Камуфляжи
        2. Звуки
        3. Конфигурации
        4. Настройки

    Возможности:
        - Адаптивный интерфейс
        - Переключение языков
        - Смена цветовых тем
        - Смена шрифтов
        - Светлый, тёмный и системный фон
        - Анимации вкладок
        - Сохранение последней вкладки
        - Режим поверх остальных окон
        - Системный трей
        - Синхронизация громкости
    """

    def __init__(self):
        super().__init__()

        # ==================================
        # SETTINGS
        # ==================================

        self.settings = load_settings()

        self._force_close = False
        self._layout_ready = False

        self._page_animation = None
        self._title_animation = None

        self._theme_source_styles = {}

        self._current_language = "ru"
        self._last_theme_signature = None
        self._last_local_qss_count = 0

        # ==================================
        # WINDOW CONFIGURATION
        # ==================================

        self.setWindowTitle(
            "WT Mod Manager " + APP_VERSION
        )

        self.setWindowIcon(application_logo_icon())

        self.setMinimumSize(
            650,
            420,
        )

        screen = QApplication.primaryScreen()

        if screen is not None:
            geometry = screen.availableGeometry()

            window_width = min(
                1150,
                int(geometry.width() * 0.90),
            )

            window_height = min(
                720,
                int(geometry.height() * 0.90),
            )

            window_width = max(
                650,
                window_width,
            )

            window_height = max(
                420,
                window_height,
            )

            self.resize(
                window_width,
                window_height,
            )

        else:
            self.resize(
                1000,
                650,
            )

        # ==================================
        # INITIAL STYLESHEET
        # ==================================

        self.setStyleSheet(
            STYLE
        )

        # ==================================
        # ALWAYS ON TOP
        # ==================================

        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            self.settings.get(
                "always_on_top",
                False,
            ),
        )

        # ==================================
        # ROOT WIDGET
        # ==================================

        root = QWidget()

        root.setObjectName(
            "MainRoot"
        )

        self.setCentralWidget(
            root
        )

        layout = QHBoxLayout(root)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(0)

        # ==================================
        # SIDEBAR
        # ==================================

        self.sidebar = QFrame()

        self.sidebar.setObjectName(
            "Sidebar"
        )

        self.sidebar.setMinimumWidth(
            155
        )

        self.sidebar.setMaximumWidth(
            235
        )

        side_layout = QVBoxLayout(
            self.sidebar
        )

        side_layout.setContentsMargins(
            15,
            25,
            15,
            20,
        )

        side_layout.setSpacing(8)

        # ==================================
        # LOGO
        # ==================================

        self.logo = QLabel(
            "WT MOD MANAGER"
        )

        self.logo.setObjectName(
            "Title"
        )

        self.logo.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                font-size: 17px;
                font-weight: 700;
                color: #FFFFFF;
            }
        """)

        self.logo.setWordWrap(True)

        self.version = QLabel(
            "VERSION " + APP_VERSION.upper()
        )

        self.version.setObjectName(
            "Subtitle"
        )

        self.version.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                color: #949EAD;
                font-size: 12px;
            }
        """)

        # Compact brand mark alongside the existing app name.
        self.logo_image = QLabel()
        self.logo_image.setObjectName("BrandLogoImage")
        self.logo_image.setFixedSize(62, 62)
        self.logo_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_image.setStyleSheet("background: transparent; border: none;")
        if LOGO_PATH.is_file():
            pixmap = QPixmap(str(LOGO_PATH))
            if not pixmap.isNull():
                # Transparent rounded mask removes square/black outside corners.
                target = QPixmap(60, 60)
                target.fill(Qt.GlobalColor.transparent)
                painter = QPainter(target)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                clip_path = QPainterPath()
                clip_path.addRoundedRect(0, 0, 60, 60, 12, 12)
                painter.setClipPath(clip_path)
                painter.drawPixmap(0, 0, pixmap.scaled(
                    60, 60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
                painter.end()
                self.logo_image.setPixmap(target)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        brand_row.addWidget(self.logo_image)
        brand_row.addWidget(self.logo, 1)
        side_layout.addLayout(brand_row)

        side_layout.addWidget(
            self.version
        )

        # Read-only game discovery runs after initial paint; it never changes
        # files or scans every drive. Manual folder selection remains available.
        self.game_status = QLabel("Поиск War Thunder...")
        self.game_status.setObjectName("Subtitle")
        self.game_status.setWordWrap(True)
        self.game_status.setToolTip(
            "Проверяются только стандартные папки игры и локальные Steam-библиотеки."
        )
        self.game_detect_button = QPushButton("Проверить игру")
        self.game_detect_button.setToolTip("Повторить безопасный поиск установок.")
        self.game_detect_button.clicked.connect(self.refresh_game_detection)
        side_layout.addWidget(self.game_status)
        side_layout.addWidget(self.game_detect_button)
        side_layout.addSpacing(16)

        # ==================================
        # PAGE STACK
        # ==================================

        self.pages = QStackedWidget()

        self.pages.setObjectName(
            "MainPages"
        )

        self.nav_buttons = []

        self.sections = [
            "Прицелы",
            "Камуфляжи",
            "Звуки",
            "Конфигурации",
            "Настройки",
            "Загрузки",
        ]

        # ==================================
        # NAVIGATION BUTTONS
        # ==================================

        for index, name in enumerate(
            self.sections
        ):
            button = QPushButton(name)

            button.setObjectName(
                "Nav"
            )

            icon_names = {
                "Прицелы": "sights",
                "Камуфляжи": "camouflages",
                "Звуки": "sounds",
                "Конфигурации": "configurations",
                "Настройки": "settings",
            }
            icon_name = icon_names.get(name)
            if icon_name:
                apply_icon(button, icon_name, self.settings, 20)


            button.setCheckable(True)

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )

            button.clicked.connect(
                lambda checked=False, i=index:
                    self.pages.setCurrentIndex(i)
            )

            self.nav_buttons.append(
                button
            )

            side_layout.addWidget(
                button
            )

        # ==================================
        # PAGE 1 — SIGHTS
        # ==================================

        self.sights_page = SightsPage()

        self.pages.addWidget(
            self.sights_page
        )

        # ==================================
        # PAGE 2 — CAMOUFLAGES
        # ==================================

        self.camouflages_page = (
            CamouflagesPage()
        )

        self.pages.addWidget(
            self.camouflages_page
        )

        # ==================================
        # PAGE 3 — SOUNDS
        # ==================================

        self.sounds_page = SoundsPage()

        self.pages.addWidget(
            self.sounds_page
        )

        # ==================================
        # PAGE 4 — CONFIGURATIONS
        # ==================================

        self.configs_page = (
            self.build_placeholder_page(
                "Профили и конфигурации",
                "Здесь можно будет создавать, "
                "сохранять, загружать и удалять "
                "пользовательские конфигурации.",
            )
        )

        self.pages.addWidget(
            self.configs_page
        )

        # ==================================
        # PAGE 5 — SETTINGS
        # ==================================

        self.settings_page = SettingsPage()

        self.pages.addWidget(
            self.settings_page
        )

        # Online downloads are appended to preserve all existing tab indices.
        self.online_page = OnlinePage()
        self.pages.addWidget(self.online_page)
        self.online_page.account_changed.connect(self.refresh_online_assets)
        self.online_page.assets_changed.connect(self.refresh_online_assets)
        self.online_page.check_update_requested.connect(self.check_update_requested)
        self.online_page.rollback_update_requested.connect(self.rollback_update_requested)

        # ==================================
        # SETTINGS SIGNAL
        # ==================================

        self.settings_page.settings_changed.connect(
            self.apply_settings
        )

        # ==================================
        # NAVIGATION SIGNAL
        # ==================================

        self.pages.currentChanged.connect(
            self.update_navigation
        )

        # ==================================
        # LAST OPENED TAB
        # ==================================

        start_tab = 0

        if self.settings.get(
            "remember_last_tab",
            True,
        ):
            start_tab = self.settings.get(
                "last_tab",
                0,
            )

        try:
            start_tab = int(start_tab)

        except (
            TypeError,
            ValueError,
        ):
            start_tab = 0

        start_tab = max(
            0,
            min(
                start_tab,
                self.pages.count() - 1,
            ),
        )

        self.pages.setCurrentIndex(
            start_tab
        )

        self.update_navigation(
            start_tab
        )

        # Keep navigation anchored at the top; no status footer.
        side_layout.addStretch()

        # ==================================
        # COMPLETE WINDOW LAYOUT
        # ==================================

        layout.addWidget(
            self.sidebar
        )

        layout.addWidget(
            self.pages,
            1,
        )

        self._layout_ready = True

        # ==================================
        # RESPONSIVE SIDEBAR
        # ==================================

        self.update_responsive_layout()

        # ==================================
        # INITIAL SOUND VOLUME
        # ==================================

        self.sounds_page.set_volume(
            self.settings.get(
                "preview_volume",
                70,
            )
        )

        # ==================================
        # PAGE ANIMATION SIGNAL
        # ==================================

        self.pages.currentChanged.connect(
            self.animate_page_transition
        )

        # ==================================
        # INITIAL PERSONALIZATION
        # ==================================

        self.apply_personalization()

        # ==================================
        # SYSTEM APPEARANCE CHANGES
        # ==================================

        app = QApplication.instance()

        if app is not None:
            try:
                app.styleHints().colorSchemeChanged.connect(
                    self.on_system_color_scheme_changed
                )

            except AttributeError:
                pass

        # ==================================
        # DYNAMIC TRANSLATIONS
        # ==================================

        for widget in self.findChildren(
            QPushButton
        ):
            if self.settings_page.isAncestorOf(widget):
                continue

            widget.clicked.connect(
                self.schedule_translation
            )

        for page in (
            self.sights_page,
            self.camouflages_page,
            self.sounds_page,
        ):
            for list_widget in page.findChildren(
                QListWidget
            ):
                list_widget.itemSelectionChanged.connect(
                    self.schedule_translation
                )

        self.sounds_page.player.playbackStateChanged.connect(
            self.schedule_translation
        )
        QTimer.singleShot(0, self.refresh_game_detection)

    def refresh_game_detection(self):
        """Show a local installation hint; do not modify or launch the game."""
        try:
            roots = find_game_roots()
            profiles = find_sight_folders()
            if len(roots) == 1:
                status = "War Thunder найден"
            elif len(roots) > 1:
                status = f"Найдено установок War Thunder: {len(roots)}"
            elif profiles:
                status = "Найдены сохранения War Thunder"
            else:
                status = "Папка игры не найдена"
            self.game_status.setText(status)
            self.game_status.setToolTip(
                "Автопоиск не меняет файлы игры. "
                "При установке удерживай Ctrl, чтобы выбрать папку вручную."
            )
        except OSError:
            self.game_status.setText("Автопоиск недоступен; выберите папку вручную")

    def refresh_online_assets(self, category=None):
        """Refresh only affected lists in one Qt paint transaction, with no window restart."""
        pages = {
            "sights": (self.sights_page, "load_sights"),
            "sounds": (self.sounds_page, "load_sounds"),
            "camouflage": (self.camouflages_page, "refresh_files"),
        }
        selected = pages if category not in pages else {category: pages[category]}
        for widget, method_name in selected.values():
            widget.setUpdatesEnabled(False)
            try:
                getattr(widget, method_name)()
            finally:
                widget.setUpdatesEnabled(True)

    # ======================================
    # APPLY PERSONALIZATION
    # ======================================

    def apply_personalization(self, force=False):
        """Apply the palette to every page without displaying partial repaints.

        Original styles are stored once. Recoloring a previously recolored QSS
        would accumulate damage; this method always starts from the original.
        Checkbox and volume updates do not call it, preventing visual flicker.
        """
        settings = self.settings
        signature = (
            settings.get("theme", "blue"),
            settings.get("appearance_mode", "black"),
            effective_mode(settings),
            settings.get("font_family", "Segoe UI"),
            settings.get("custom_hex", "#4777BA"),
            settings.get("theme_intensity", 60),
            settings.get("accent_enabled", False),
        )
        if not force and signature == self._last_theme_signature:
            return

        # Full-window updates are presented once, after all QSS is updated.
        self.setUpdatesEnabled(False)
        try:
            palette = theme_palette(settings)
            # Refresh sidebar icons when colors or system mode change.
            for name, button in zip(self.sections, self.nav_buttons):
                icon_name = {
                    "Прицелы": "sights",
                    "Камуфляжи": "camouflages",
                    "Звуки": "sounds",
                    "Конфигурации": "configurations",
                    "Настройки": "settings",
                }.get(name)
                if icon_name:
                    apply_icon(button, icon_name, settings, 20)
            # Match audio transport icons to the active dark/light theme.
            self.sounds_page.apply_transport_icons(settings)
            self.apply_native_palette(palette)
            accent = palette["accent"]
            font_name = settings.get("font_family", "Segoe UI")
            if font_name not in SUPPORTED_FONTS:
                font_name = "Segoe UI"

            main_css = theme_stylesheet(STYLE, settings)
            if self.styleSheet() != main_css:
                self.setStyleSheet(main_css)
            if self.font().family() != font_name:
                self.setFont(QFont(font_name, 10))

            # The main window's QSS is inherited by all pages. Widgets that
            # declare their own stylesheets must be updated separately.
            for widget in self.findChildren(QWidget):
                if widget is self.settings_page or self.settings_page.isAncestorOf(widget):
                    continue
                current = widget.styleSheet()
                original = widget.property("_wt_original_qss")
                last_applied = widget.property("_wt_last_qss")

                # Widgets may change their own local QSS dynamically, e.g.
                # on selection; capture such updates as the next source.
                if original is None or (current and current != last_applied):
                    original = current
                    widget.setProperty("_wt_original_qss", original)

                if original:
                    updated = theme_stylesheet(original, settings)
                    if current != updated:
                        widget.setStyleSheet(updated)
                    widget.setProperty("_wt_last_qss", updated)

                # QPainter widgets ignore stylesheets for their tracks.
                if hasattr(widget, "progress_color"):
                    widget.progress_color = QColor(accent)
                    if hasattr(widget, "track_color"):
                        widget.track_color = QColor(palette["surface"])
                    if hasattr(widget, "handle_color"):
                        widget.handle_color = QColor(
                            "#FFFFFF" if palette["mode"] == "white" else "#E5EDF8"
                        )
                    widget.update()

                if hasattr(widget, "set_accent") and callable(widget.set_accent):
                    widget.set_accent(accent)

            # A page owns its controls, so it is responsible for its own QSS.
            # The same settings dictionary may already have been saved by
            # SettingsPage, in which case force applying appearance is needed
            # for OS theme changes even though its data remains unchanged.
            if hasattr(self.settings_page, "apply_external_settings"):
                self.settings_page.apply_external_settings(settings)
            if hasattr(self.settings_page, "apply_appearance"):
                self.settings_page.apply_appearance()

            self._last_theme_signature = signature
        finally:
            self.setUpdatesEnabled(True)
            self.update()

        self._current_language = settings.get("language", "ru")
        self.refresh_translations()

    # ======================================
    # LIVE INTENSITY PREVIEW (NO DISK WRITES)
    # ======================================

    def preview_theme_intensity(self, value):
        """Recolor all pages while the user is moving the slider.

        The settings page owns the in-progress control value and must not be
        resynchronized from saved settings during the preview.
        """
        try:
            value = max(0, min(100, int(value)))
        except (TypeError, ValueError, OverflowError):
            return
        if self.settings.get("theme_intensity") == value:
            return
        self.settings["theme_intensity"] = value
        self.settings_page.settings["theme_intensity"] = value
        self.apply_personalization()

    # ======================================
    # NATIVE QT COLOR PALETTE
    # ======================================

    def apply_native_palette(self, colors):
        """Synchronize Qt's native controls with the selected theme.

        Certain child widgets, multimedia surfaces and popup controls use
        QPalette rather than QSS. A local palette is installed on the manager
        so that it propagates to those widgets as well. This does not change
        the palette of unrelated applications or of the whole QApplication.
        """
        palette = QPalette(self.palette())
        palette.setColor(QPalette.ColorRole.Window, QColor(colors["window"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors["card"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["surface"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors["surface"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["accent_deep"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["selection_text"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["card"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors["text_muted"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(colors["accent"]))
        self.setPalette(palette)

    # ======================================
    # THEME SAFETY / REPAINT HELPERS
    # ======================================

    def refresh_current_page(self):
        """Recolor any new local QSS created after initial page setup.

        Called only on user navigation, never by a timer. This avoids
        repeated global repolishing when animated switches change state.
        """
        page = self.pages.currentWidget()
        if page is None or page is self.settings_page:
            return
        for widget in [page] + page.findChildren(QWidget):
            current = widget.styleSheet()
            if not current:
                continue
            last = widget.property("_wt_last_qss")
            if last == current:
                continue
            # New stylesheet from a page after media/file selection.
            widget.setProperty("_wt_original_qss", current)
            themed = theme_stylesheet(current, self.settings)
            if themed != current:
                widget.setStyleSheet(themed)
            widget.setProperty("_wt_last_qss", themed)

    # ======================================
    # TRANSLATE INTERFACE TEXT
    # ======================================

    def refresh_translations(self):
        """
        Переводит элементы главного окна,
        прицелов, камуфляжей и звуков.

        Пользовательские имена файлов
        не изменяются.
        """

        language = self.settings.get(
            "language",
            "ru",
        )

        for widget in self.findChildren(
            QWidget
        ):
            # Вкладка настроек переводит
            # собственные компоненты самостоятельно.

            if (
                widget is self.settings_page
                or self.settings_page.isAncestorOf(widget)
            ):
                continue

            if not isinstance(
                widget,
                (
                    QLabel,
                    QPushButton,
                ),
            ):
                continue

            current = widget.text()

            last_applied = widget.property(
                "_wt_last_translation"
            )

            source = widget.property(
                "_wt_source_ru"
            )

            # Если надпись поменялась во время
            # работы программы, запоминаем её
            # как новое исходное значение.

            if (
                source is None
                or current != last_applied
            ):
                source = current

                widget.setProperty(
                    "_wt_source_ru",
                    source,
                )

            translated = translate_ui(
                source,
                language,
            )

            if current != translated:
                widget.setText(
                    translated
                )

            widget.setProperty(
                "_wt_last_translation",
                translated,
            )

    # ======================================
    # PAGE TRANSITION ANIMATION
    # ======================================

    def animate_page_transition(self, selected_index):
        """Lightweight title-only transition, not a costly full-page effect.

        A large QGraphicsOpacityEffect on a page with scroll areas caused
        flicker, so the only animated object is one small heading QLabel.
        The speed slider adjusts duration; disabling animations is immediate.
        """
        if selected_index < 0:
            return
        if self._title_animation is not None:
            old_target = self._title_animation.targetObject()
            self._title_animation.stop()
            if isinstance(old_target, QGraphicsOpacityEffect):
                old_target.setOpacity(1.0)
            self._title_animation = None
        if self._page_animation is not None:
            self._page_animation.stop()
            self._page_animation = None
        self.refresh_current_page()
        self.schedule_translation()
        if not self.settings.get("animations_enabled", True):
            return
        page = self.pages.widget(selected_index)
        if page is None or page is self.settings_page:
            return
        title = next(iter(page.findChildren(QLabel, "Title")), None)
        if title is None:
            return
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
        self._title_animation = animation
        animation.start()

    # ======================================
    # WINDOWS SYSTEM COLOR SCHEME
    # ======================================

    def on_system_color_scheme_changed(
        self,
        *_args,
    ):
        """
        Обновляет приложение при смене
        системной светлой/тёмной темы.
        """

        if self.settings.get("appearance_mode", "black") == "system":
            # The selected setting remains 'system'; effective_mode changes.
            self.apply_personalization(force=True)

    # ======================================
    # NO-FLICKER ALWAYS-ON-TOP
    # ======================================

    def set_always_on_top(
        self,
        enabled,
    ):
        """
        Windows:
        переключение поверх окон без
        пересоздания главного окна.

        Это устраняет одно из возможных
        источников мерцания.
        """

        if (
            sys.platform == "win32"
            and self.isVisible()
        ):
            try:
                hwnd = int(
                    self.winId()
                )

                # HWND_TOPMOST = -1
                # HWND_NOTOPMOST = -2

                insert_after = (
                    -1 if enabled else -2
                )

                SWP_NOSIZE = 0x0001
                SWP_NOMOVE = 0x0002
                SWP_NOACTIVATE = 0x0010

                flags = (
                    SWP_NOSIZE
                    | SWP_NOMOVE
                    | SWP_NOACTIVATE
                )

                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    insert_after,
                    0,
                    0,
                    0,
                    0,
                    flags,
                )

                return

            except (
                AttributeError,
                OSError,
                ValueError,
            ):
                pass

        # ==================================
        # OTHER PLATFORMS
        # ==================================

        was_visible = self.isVisible()

        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            bool(enabled),
        )

        if was_visible:
            self.show()

    # ======================================
    # SCHEDULE TEXT TRANSLATION
    # ======================================

    def schedule_translation(
        self,
        *unused,
    ):
        """
        Позволяет обновить перевод после
        действий, которые изменяют надписи.
        """

        QTimer.singleShot(
            0,
            self.refresh_translations,
        )

    # ======================================
    # NAVIGATION
    # ======================================

    def update_navigation(
        self,
        selected_index,
    ):
        """
        Подсветка выбранного раздела
        и сохранение последней вкладки.
        """

        if selected_index < 0:
            return

        for index, button in enumerate(
            self.nav_buttons
        ):
            button.setChecked(
                index == selected_index
            )

        if self.settings.get(
            "remember_last_tab",
            True,
        ):
            save_settings({
                "last_tab": selected_index
            })

    # ======================================
    # APPLY SETTINGS
    # ======================================

    def apply_settings(
        self,
        settings,
    ):
        """
        Применяет изменения настроек.

        Полное обновление темы выполняется
        только при смене визуальных настроек.
        """

        old_settings = (
            self.settings.copy()
        )

        self.settings = (
            settings.copy()
        )

        # ==================================
        # CHECK VISUAL CHANGES
        # ==================================

        visuals_changed = any(
            old_settings.get(key)
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

        language_changed = (
            old_settings.get("language")
            != self.settings.get("language")
        )

        # ==================================
        # APPLY ONLY NECESSARY CHANGES
        # ==================================

        if visuals_changed:
            self.apply_personalization()

        elif language_changed:
            # SettingsPage owns its translation keys.
            if hasattr(self.settings_page, "apply_external_settings"):
                self.settings_page.apply_external_settings(self.settings)
            self.refresh_translations()

        # ==================================
        # AUDIO VOLUME
        # ==================================

        if hasattr(
            self,
            "sounds_page",
        ):
            new_volume = self.settings.get(
                "preview_volume",
                70,
            )

            current_volume = (
                self.sounds_page
                .volume_slider
                .value()
            )

            if current_volume != new_volume:
                self.sounds_page.set_volume(
                    new_volume
                )

        # ==================================
        # ALWAYS ON TOP
        # ==================================

        old_top = old_settings.get(
            "always_on_top",
            False,
        )

        new_top = self.settings.get(
            "always_on_top",
            False,
        )

        if old_top != new_top:
            self.set_always_on_top(
                new_top
            )

        # ==================================
        # LAST OPENED TAB
        # ==================================

        if (
            self.settings.get("remember_last_tab", True)
            and not old_settings.get("remember_last_tab", True)
        ):
            save_settings({"last_tab": self.pages.currentIndex()})

    # ======================================
    # RESPONSIVE SIDEBAR
    # ======================================

    def update_responsive_layout(self):
        """
        Изменяет ширину боковой панели
        в зависимости от размера окна.
        """

        if not hasattr(
            self,
            "sidebar",
        ):
            return

        window_width = (
            self.width()
        )

        if window_width < 780:
            sidebar_width = 155

        elif window_width < 1000:
            sidebar_width = 190

        else:
            sidebar_width = 235

        if (
            self.sidebar.width()
            != sidebar_width
        ):
            self.sidebar.setFixedWidth(
                sidebar_width
            )

        # ==================================
        # RESPONSIVE LOGO
        # ==================================

        if sidebar_width <= 155:
            self.logo.setText(
                "WT MANAGER"
            )

        else:
            self.logo.setText(
                "WT MOD MANAGER"
            )

    # ======================================
    # RESIZE EVENT
    # ======================================

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if getattr(
            self,
            "_layout_ready",
            False,
        ):
            self.update_responsive_layout()

    # ======================================
    # SHOW EVENT
    # ======================================

    def showEvent(self, event):
        super().showEvent(event)

        if getattr(
            self,
            "_layout_ready",
            False,
        ):
            QTimer.singleShot(
                0,
                self.update_responsive_layout,
            )

    # ======================================
    # STOP AUDIO
    # ======================================

    def stop_audio(self):
        """
        Останавливает воспроизведение
        звукового файла.
        """

        if hasattr(
            self,
            "sounds_page",
        ):
            self.sounds_page.player.stop()

    # ======================================
    # SAVE CURRENT TAB
    # ======================================

    def save_current_tab(self):
        """
        Сохраняет текущую вкладку,
        если настройка включена.
        """

        if self.settings.get(
            "remember_last_tab",
            True,
        ):
            save_settings({
                "last_tab":
                    self.pages.currentIndex(),
            })

    # ======================================
    # WINDOW CLOSE EVENT
    # ======================================

    def closeEvent(self, event):
        """
        Обработка закрытия окна.

        При включённой настройке
        приложение скрывается в трее.

        При обычном закрытии
        сохраняет последнюю вкладку
        и останавливает аудио.
        """

        self.save_current_tab()

        self.stop_audio()

        minimize_to_tray = (
            self.settings.get(
                "minimize_to_tray_on_close",
                False,
            )
        )

        tray_available = (
            QSystemTrayIcon.isSystemTrayAvailable()
        )

        if (
            minimize_to_tray
            and tray_available
            and not self._force_close
        ):
            self.hide()

            event.ignore()

            return

        super().closeEvent(
            event
        )

    # ======================================
    # FORCE CLOSE
    # ======================================

    def force_close(self):
        """
        Принудительно закрывает окно
        без сворачивания в трей.
        """

        self._force_close = True

        self.close()

    # ======================================
    # RESTORE WINDOW
    # ======================================

    def restore_window(self):
        """
        Восстанавливает главное окно
        и переводит его на передний план.
        """

        if self.isMinimized():
            self.showNormal()

        else:
            self.show()

        self.raise_()

        self.activateWindow()

    # ======================================
    # TEMPORARY CONFIGURATION PAGE
    # ======================================

    @staticmethod
    def build_placeholder_page(
        heading,
        subtitle_text,
    ):
        """
        Создаёт временную страницу
        для ещё не реализованных разделов.
        """

        page = QWidget()

        page_layout = QVBoxLayout(
            page
        )

        page_layout.setContentsMargins(
            35,
            35,
            35,
            35,
        )

        page_layout.setSpacing(16)

        title = QLabel(
            heading
        )

        title.setObjectName(
            "Title"
        )

        subtitle = QLabel(
            subtitle_text
        )

        subtitle.setObjectName(
            "Subtitle"
        )

        subtitle.setWordWrap(True)

        page_layout.addWidget(
            title
        )

        page_layout.addWidget(
            subtitle
        )

        page_layout.addStretch()

        return page
