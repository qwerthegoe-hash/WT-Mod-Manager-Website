"""Live, non-blocking Windows EXE update checks and account-local notices.

Checking for a new release never closes the app. After the user accepts,
a verified EXE is downloaded in the background; only the final installation
requires the safe short restart handled by portable_updater.py.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QThread, Signal, Slot, QTimer
from PySide6.QtWidgets import QMessageBox

from src.update_checker import find_update, download_verified, repository, _sha256
from src.portable_updater import launch_verified_update, launch_verified_rollback, previous_exe_available
from src.update_notifications import (
    load_notifications, record_event, set_auto_check, ignore_version
)

CHECK_INTERVAL_MS = 10 * 60 * 1000


class UpdateWorker(QObject):
    finished = Signal(object, str)

    def __init__(self, download_info=None):
        super().__init__()
        self.download_info = download_info

    @Slot()
    def run(self):
        try:
            if self.download_info is not None:
                path = download_verified(self.download_info)
                value = {"path": path, "release": self.download_info}
            else:
                value = find_update()
            self.finished.emit(value, "")
        except Exception as error:
            self.finished.emit(None, str(error)[:250])


class UpdateController(QObject):
    update_available = Signal(object)
    notifications_changed = Signal()
    tray_notification = Signal(str, str)

    def __init__(self, parent=None, on_install_ready=None):
        super().__init__(parent if isinstance(parent, QObject) else None)
        self.parent_window = parent if hasattr(parent, "windowTitle") else None
        self.on_install_ready = on_install_ready
        self.thread = None
        self.worker = None
        self._queued_download = None
        self._manual_check = False
        self.current_update = None
        self._timer = QTimer(self)
        self._timer.setInterval(CHECK_INTERVAL_MS)
        self._timer.timeout.connect(self.check)
        self._timer.start()

    def automatic_checks_enabled(self):
        return load_notifications()["auto_check"]

    def set_automatic_checks_enabled(self, enabled):
        set_auto_check(enabled)
        if enabled:
            self.check()
        self.notifications_changed.emit()

    def check(self):
        """Periodic/startup check when running, including in the system tray."""
        if (not self.automatic_checks_enabled() or
                repository() is None or self.thread is not None):
            return
        self._start(None)

    def check_manual(self):
        """Manual checks bypass the automatic-check preference."""
        if self.thread is not None:
            self.tray_notification.emit(
                "WT Mod Manager", "Проверка или скачивание обновления уже выполняется."
            )
            return
        if repository() is None:
            QMessageBox.warning(
                self.parent_window, "Обновления", "Источник обновлений пока не настроен."
            )
            return
        self._manual_check = True
        self._start(None)

    def request_rollback(self):
        if self.thread is not None:
            QMessageBox.information(
                self.parent_window, "Откат версии",
                "Во время проверки или скачивания обновления откат недоступен."
            )
            return
        if not previous_exe_available():
            QMessageBox.information(
                self.parent_window, "Откат версии",
                "Нет сохранённой предыдущей версии с подтверждённой SHA-256. "
                "Резервная копия создаётся при следующем обновлении через новый механизм."
            )
            return
        choice = QMessageBox.question(
            self.parent_window, "Вернуть предыдущую версию",
            "Вернуть предыдущий проверенный EXE WT Mod Manager?\n"
            "Текущая версия будет сохранена отдельно, а приложение перезапустится. "
            "Моды и настройки останутся на месте.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        try:
            launch_verified_rollback()
        except (ValueError, OSError, RuntimeError) as error:
            QMessageBox.warning(self.parent_window, "Ошибка отката", str(error))
            return
        if callable(self.on_install_ready):
            QTimer.singleShot(0, self.on_install_ready)

    def request_install(self):
        """An explicit user action. No forced app close on a mere notification."""
        info = self.current_update
        if info is None:
            self.check_manual()
            return
        if self.thread is not None:
            return
        choice = QMessageBox.question(
            self.parent_window, "Скачать обновление",
            "Доступна " + str(info["version"]) +
            ". Скачать официальный файл WTModManager.exe и проверить SHA-256?"
            "\nПриложение продолжит работать во время скачивания.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if choice == QMessageBox.StandardButton.Yes:
            self._start(info)

    def ignore_current_version(self):
        if self.current_update:
            ignore_version(str(self.current_update["version"]))
            self.notifications_changed.emit()

    def _start(self, info):
        if self.thread is not None:
            if info is not None:
                self._queued_download = info
            return
        self.thread = QThread(self)
        self.worker = UpdateWorker(info)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(
            lambda result, error, is_download=info is not None:
                self._finished(result, error, is_download)
        )
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear)
        self.thread.start()

    def _clear(self):
        self.thread = None
        self.worker = None
        if self._queued_download is not None:
            queued = self._queued_download
            self._queued_download = None
            QTimer.singleShot(0, lambda: self._start(queued))

    def _finished(self, result, error, downloaded):
        manual = self._manual_check
        self._manual_check = False
        if error:
            if downloaded:
                record_event(
                    "update_failed", "Не удалось скачать обновление",
                    "Скачивание или проверка не прошли: " + error,
                    event_id="failed-download-" + str(self.current_update and
                                                     self.current_update.get("version")) +
                                                     "-" + str(__import__("time").time_ns())
                )
                self.notifications_changed.emit()
                QMessageBox.warning(self.parent_window, "Обновление", error)
            elif manual:
                QMessageBox.warning(self.parent_window, "Обновление", error)
            # A temporary network outage must not close the open application.
            return
        if result is None:
            if manual and not downloaded:
                QMessageBox.information(
                    self.parent_window, "Обновления", "Новых версий пока нет."
                )
            return
        if not downloaded:
            self.current_update = result
            newly_recorded = record_event(
                "update_available", "Доступна новая версия WT Mod Manager",
                "Версия " + str(result["version"]) + " готова к скачиванию.",
                str(result["version"]), "update-available:" + str(result["version"])
            )
            self.update_available.emit(result)
            if newly_recorded:
                self.notifications_changed.emit()
            if (newly_recorded and
                    load_notifications()["ignored_version"] != result["version"]):
                self.tray_notification.emit(
                    "Обновление WT Mod Manager",
                    "Новая версия " + str(result["version"]) +
                    " доступна. Открой приложение, чтобы установить её."
                )
            if manual:
                QMessageBox.information(
                    self.parent_window, "Найдена новая версия",
                    "Доступна " + str(result["version"]) +
                    ". Открой вкладку «Загрузки», чтобы скачать и установить."
                )
            return

        info = result["release"]
        staged = result["path"]
        # Re-check the staged file immediately before handing it to the
        # installer, even though the download worker already verified it.
        if _sha256(staged) != info["digest"]:
            QMessageBox.warning(
                self.parent_window, "Ошибка обновления",
                "Загруженный файл изменился после проверки. Установка отменена."
            )
            return
        record_event(
            "update_ready", "Обновление скачано",
            "Версия " + str(info["version"]) +
            " проверена по SHA-256; нужна перезагрузка программы.",
            str(info["version"]), "update-ready:" + str(info["version"])
        )
        self.notifications_changed.emit()

        choice = QMessageBox.question(
            self.parent_window, "Установить обновление",
            "WT Mod Manager " + str(info["version"]) +
            " скачан и проверен.\n"
            "Завершить работу приложения, сохранить прежний EXE в резервной "
            "копии и автоматически открыть новую версию?\n"
            "Текущие моды и настройки не удаляются.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        if sys.platform != "win32" or not getattr(sys, "frozen", False):
            QMessageBox.information(
                self.parent_window, "Обновление",
                "Замена приложения доступна только в готовом Windows EXE."
            )
            return
        try:
            launch_verified_update(staged, info["digest"])
        except (OSError, ValueError, RuntimeError) as problem:
            QMessageBox.warning(self.parent_window, "Ошибка обновления", str(problem))
            return
        if callable(self.on_install_ready):
            QTimer.singleShot(0, self.on_install_ready)
