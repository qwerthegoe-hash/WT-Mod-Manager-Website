"""Non-blocking update notices; installer is only run after user confirmation."""
import subprocess
import sys
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QMessageBox
from src.update_checker import find_update, download_verified, repository

class UpdateWorker(QObject):
    finished = Signal(object, str)
    def __init__(self, download_info=None):
        super().__init__()
        self.download_info = download_info
    @Slot()
    def run(self):
        try:
            result = download_verified(self.download_info) if self.download_info else find_update()
            self.finished.emit(result, "")
        except Exception as exc:
            self.finished.emit(None, str(exc))

class UpdateController(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.thread = None
        self.worker = None

    def check(self):
        if repository() is None or self.thread is not None:
            return
        self._start(None)

    def _start(self, info):
        self.thread = QThread(self)
        self.worker = UpdateWorker(info)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda result, error, downloaded=info is not None:
            self._finished(result,error,downloaded))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear)
        self.thread.start()

    def _clear(self):
        self.thread = None
        self.worker = None

    def _finished(self,result,error,downloaded):
        if error:
            # Network errors should not interrupt normal app operation.
            print("[UPDATE]",error)
            if downloaded:
                QMessageBox.warning(self.parent_window,"Ошибка обновления",error)
            return
        if result is None:
            return
        if not downloaded:
            answer = QMessageBox.question(
                self.parent_window,"Обновление WT Mod Manager",
                f"Доступна версия {result['version']}. Скачать проверенный установщик?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer == QMessageBox.StandardButton.Yes:
                # Start when previous thread has finished and been destroyed.
                from PySide6.QtCore import QTimer
                QTimer.singleShot(200,lambda: self._start(result) if self.thread is None else None)
        else:
            answer = QMessageBox.question(
                self.parent_window,"Обновление загружено",
                "SHA256 проверен. Закройте приложение перед установкой. Запустить установщик?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer == QMessageBox.StandardButton.Yes and sys.platform == "win32":
                # User must close WT Mod Manager to complete installation.
                subprocess.Popen([str(result)], close_fds=True)
