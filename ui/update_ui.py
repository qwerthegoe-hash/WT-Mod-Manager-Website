"""Non-blocking, explicitly confirmed updates of the portable Windows EXE."""
from __future__ import annotations

import sys
from PySide6.QtCore import QObject, QThread, Signal, Slot, QTimer
from PySide6.QtWidgets import QMessageBox

from src.update_checker import find_update, download_verified, repository
from src.portable_updater import launch_verified_update


class UpdateWorker(QObject):
    finished = Signal(object, str)

    def __init__(self, download_info=None):
        super().__init__()
        self.download_info = download_info

    @Slot()
    def run(self):
        try:
            value = download_verified(self.download_info) if self.download_info else find_update()
            self.finished.emit(value, "")
        except Exception as error:
            self.finished.emit(None, str(error))


class UpdateController(QObject):
    def __init__(self, parent=None, on_install_ready=None):
        super().__init__(parent if isinstance(parent, QObject) else None)
        self.parent_window = parent if hasattr(parent, "windowTitle") else None
        self.on_install_ready = on_install_ready
        self.thread = None
        self.worker = None
        self._queued_download = None
        self._manual_check = False

    def check(self):
        if repository() is None or self.thread is not None:
            return
        self._start(None)

    def check_manual(self):
        if self.thread is not None:
            return
        if repository() is None:
            QMessageBox.warning(self.parent_window, "Обновления", "Проверка обновлений пока не настроена.")
            return
        self._manual_check = True
        self._start(None)

    def _start(self, info):
        if self.thread is not None:
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
            next_download = self._queued_download
            self._queued_download = None
            QTimer.singleShot(0, lambda: self._start(next_download))

    def _finished(self, result, error, downloaded):
        manual = self._manual_check
        self._manual_check = False
        if error:
            if downloaded or manual:
                QMessageBox.warning(self.parent_window, "Ошибка обновления", error)
            return
        if result is None:
            if manual and not downloaded:
                QMessageBox.information(self.parent_window, "Обновления", "Новых версий пока нет.")
            return
        if not downloaded:
            answer = QMessageBox.question(
                self.parent_window, "Обновление WT Mod Manager",
                "Доступна версия " + str(result["version"]) +
                ". Скачать проверенный Windows EXE в фоне? После проверки "
                "будет предложено закрыть и обновить приложение.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._queued_download = result
        else:
            answer = QMessageBox.question(
                self.parent_window, "Обновление готово",
                "Новая версия загружена, её SHA-256 и размер проверены. "
                "Сохранённые настройки и моды останутся на месте.\n"
                "Перезапустить WT Mod Manager, заменив EXE?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            if sys.platform != "win32" or not getattr(sys, "frozen", False):
                QMessageBox.information(
                    self.parent_window, "Обновление",
                    "Самообновление доступно только из собранного WTModManager.exe."
                )
                return
            try:
                launch_verified_update(result)
            except (OSError, ValueError, RuntimeError) as error:
                QMessageBox.warning(self.parent_window, "Ошибка самообновления", str(error))
                return
            if callable(self.on_install_ready):
                QTimer.singleShot(0, self.on_install_ready)
