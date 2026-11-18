
import sys
from pathlib import Path

import psutil

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QStyle,
)

ROOT = (Path(sys._MEIPASS) if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
        else Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(ROOT))

from ui.main_window import LaunchPrompt, ManagerWindow
from src.settings_store import load_settings
from ui.i18n import translate_ui
from ui.update_ui import UpdateController


# ==========================================
# APPLICATION LOGO
# ==========================================

LOGO_PATH = (
    ROOT
    / "assets"
    / "icons"
    / "Logotip"
    / "LogotipProject.png"
)


def load_application_icon(app=None):
    """
    Загружает пользовательский логотип приложения.

    Если PNG отсутствует или повреждён,
    используется стандартная иконка Windows.
    """

    if LOGO_PATH.is_file():
        icon = QIcon(str(LOGO_PATH))

        if not icon.isNull():
            return icon

    print(
        "[WT] Логотип не найден или не загружен:",
        LOGO_PATH
    )

    if app is None:
        app = QApplication.instance()

    if app is not None:
        return app.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )

    return QIcon()


# ==========================================
# GAME PROCESS DETECTION
# ==========================================

GAME_PROCESSES = {
    "aces.exe",
    "aces64.exe",
}


def is_game_running():
    for process in psutil.process_iter(["name"]):
        try:
            name = (process.info["name"] or "").lower()

            if name in GAME_PROCESSES:
                return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    return False


# ==========================================
# WT MOD MANAGER APPLICATION
# ==========================================

class WTManagerApp:

    def __init__(self, app):
        self.app = app

        self.app.setQuitOnLastWindowClosed(False)

        # ==================================
        # APPLICATION ICON
        # ==================================

        self.application_icon = load_application_icon(
            self.app
        )

        self.app.setWindowIcon(
            self.application_icon
        )

        # ==================================
        # APPLICATION STATE
        # ==================================

        self.game_was_running = False

        self.prompt = None
        self.manager = None

        # ==================================
        # GAME DETECTION TIMER
        # ==================================

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.check_game
        )

        self.timer.start(2000)

        # ==================================
        # SYSTEM TRAY
        # ==================================

        self.tray = QSystemTrayIcon()

        self.tray.setIcon(
            self.application_icon
        )

        self.tray.setToolTip(
            "WT Mod Manager"
        )

        # ==================================
        # TRAY CONTEXT MENU
        # ==================================

        menu = QMenu()

        self.open_action = menu.addAction(
            "Открыть менеджер",
            self.open_manager
        )

        self.hide_action = menu.addAction(
            "Скрыть менеджер",
            self.hide_manager
        )

        menu.addSeparator()

        self.exit_action = menu.addAction(
            "Выход",
            self.exit_app
        )

        menu.aboutToShow.connect(
            self.translate_tray_menu
        )

        self.tray.setContextMenu(menu)

        self.tray.activated.connect(
            self.on_tray_activated
        )

        # ==================================
        # SHOW SYSTEM TRAY
        # ==================================

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

        # ==================================
        # INITIAL GAME CHECK
        # ==================================

        self.check_game()

        # Non-blocking optional update check; no network use until repo is configured.
        self.updater = UpdateController(None, on_install_ready=self.exit_app)
        QTimer.singleShot(3000, self.updater.check)

    # ======================================
    # TRAY TRANSLATIONS
    # ======================================

    def translate_tray_menu(self):
        language = load_settings().get(
            "language",
            "ru"
        )

        self.open_action.setText(
            translate_ui(
                "Открыть менеджер",
                language
            )
        )

        self.hide_action.setText(
            translate_ui(
                "Скрыть менеджер",
                language
            )
        )

        self.exit_action.setText(
            translate_ui(
                "Выход",
                language
            )
        )

    # ======================================
    # TRAY ACTIVATION
    # ======================================

    def on_tray_activated(self, reason):

        if (
            reason
            == QSystemTrayIcon.ActivationReason.DoubleClick
        ):
            self.open_manager()

    # ======================================
    # TRAY NOTIFICATIONS
    # ======================================

    def show_tray_message(self, title, message):
        settings = load_settings()

        if not settings.get(
            "enable_tray_notifications",
            True
        ):
            return

        if QSystemTrayIcon.isSystemTrayAvailable():

            self.tray.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    # ======================================
    # WAR THUNDER DETECTION
    # ======================================

    def check_game(self):
        running = is_game_running()

        if running and not self.game_was_running:

            print(
                "[WT] War Thunder обнаружен"
            )

            settings = load_settings()

            self.show_tray_message(
                "WT Mod Manager",
                "War Thunder обнаружен."
            )

            if settings.get(
                "auto_open_manager_on_detect",
                False
            ):
                self.open_manager()

            elif settings.get(
                "show_launch_prompt",
                True
            ):
                self.show_launch_prompt()

        if not running and self.game_was_running:

            print(
                "[WT] War Thunder закрыт"
            )

        self.game_was_running = running

    # ======================================
    # LAUNCH PROMPT
    # ======================================

    def show_launch_prompt(self):

        if self.prompt is not None:
            return

        self.prompt = LaunchPrompt()

        # Apply custom application logo
        self.prompt.setWindowIcon(
            self.application_icon
        )

        self.prompt.accepted.connect(
            self.open_manager
        )

        self.prompt.finished.connect(
            self.clear_prompt
        )

        self.prompt.show()
        self.prompt.raise_()
        self.prompt.activateWindow()

    # ======================================
    # CLEAR LAUNCH PROMPT
    # ======================================

    def clear_prompt(self, result):
        self.prompt = None

    # ======================================
    # OPEN MAIN WINDOW
    # ======================================

    def open_manager(self):

        if self.manager is None:

            self.manager = ManagerWindow()
            self.manager.check_update_requested.connect(self.updater.check_manual)

            # Apply custom application logo
            self.manager.setWindowIcon(
                self.application_icon
            )

        self.manager.show()
        self.manager.raise_()
        self.manager.activateWindow()

    # ======================================
    # HIDE MAIN WINDOW
    # ======================================

    def hide_manager(self):

        if self.manager is not None:
            self.manager.hide()

    # ======================================
    # EXIT APPLICATION
    # ======================================

    def exit_app(self):

        if self.manager is not None:
            self.manager.force_close()

        if self.prompt is not None:
            self.prompt.close()

        self.tray.hide()

        self.app.quit()


# ==========================================
# MAIN ENTRY POINT
# ==========================================

def main():

    app = QApplication(sys.argv)

    app.setApplicationName(
        "WT Mod Manager"
    )

    # Set the application logo globally
    app.setWindowIcon(
        load_application_icon(app)
    )

    # Start the application controller
    controller = WTManagerApp(app)

    # Demonstration mode
    if "--demo" in sys.argv:

        QTimer.singleShot(
            200,
            controller.show_launch_prompt
        )

    sys.exit(
        app.exec()
    )


# ==========================================
# APPLICATION START
# ==========================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--apply-update":
        from src.portable_updater import apply_verified_update
        sys.exit(apply_verified_update(sys.argv[2:]))
    main()
