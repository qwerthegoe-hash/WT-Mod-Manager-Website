"""Local ZIP inspection and automatic server-mediated VirusTotal hash report.

No personal API key is entered or bundled into the desktop application.
The user's DPAPI-protected WTMM account pairing authenticates server requests.
Only a hash, never original mod contents, goes to the server and VirusTotal.
"""
from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
)
from src.mod_security import inspect_mod_file, SecurityError, VirusTotalError
from src.vt_backend import lookup_shared_vt_hash


class LocalInspection(QThread):
    result_ready = Signal(object, str)

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = path

    def run(self):
        try:
            self.result_ready.emit(inspect_mod_file(self.path), "")
        except (SecurityError, OSError, ValueError) as error:
            self.result_ready.emit(None, str(error))


class VirusTotalLookup(QThread):
    result_ready = Signal(object, str)

    def __init__(self, digest: str, parent=None):
        super().__init__(parent)
        self.digest = digest

    def run(self):
        try:
            self.result_ready.emit(lookup_shared_vt_hash(self.digest), "")
        except (VirusTotalError, OSError, ValueError) as error:
            self.result_ready.emit(None, str(error))


class SecurityPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ""
        self._digest = ""
        self._worker = None
        self._vt_worker = None
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self._stop_workers)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 8, 2, 4)
        layout.setSpacing(12)
        local = QGroupBox("Проверка ZIP и файлов модов")
        local_layout = QVBoxLayout(local)
        info = QLabel(
            "Сначала проверяется структура и SHA-256 файла на компьютере. "
            "После успешной локальной проверки автоматически запрашивается "
            "отчёт VirusTotal через защищённый сервер WT Mod Manager."
        )
        info.setWordWrap(True)
        local_layout.addWidget(info)
        actions = QHBoxLayout()
        self.choose_button = QPushButton("Выбрать ZIP или файл мода")
        self.choose_button.clicked.connect(self.choose_file)
        actions.addWidget(self.choose_button, 1)
        self.scan_button = QPushButton("Проверить файл")
        self.scan_button.setEnabled(False)
        self.scan_button.clicked.connect(self.scan_file)
        actions.addWidget(self.scan_button)
        local_layout.addLayout(actions)
        self.path_label = QLabel("Файл не выбран")
        self.path_label.setWordWrap(True)
        local_layout.addWidget(self.path_label)
        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        self.result.setMaximumHeight(105)
        self.result.setPlaceholderText("Результат локальной проверки")
        local_layout.addWidget(self.result)
        layout.addWidget(local)

        remote = QGroupBox("VirusTotal — через сервер проекта")
        remote_layout = QVBoxLayout(remote)
        note = QLabel(
            "API-ключ уже настроен на сервере — вводить его не нужно. "
            "Для доступа требуется связанный с сайтом аккаунт. "
            "На сервер и в VirusTotal передаётся только SHA-256, не сам ZIP. "
            "Бесплатный тариф имеет ограничения; отсутствие обнаружений "
            "не является гарантией безопасности."
        )
        note.setWordWrap(True)
        remote_layout.addWidget(note)
        self.vt_result = QLabel("Проверка VirusTotal ещё не выполнялась.")
        self.vt_result.setWordWrap(True)
        self.vt_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        remote_layout.addWidget(self.vt_result)
        self.lookup_button = QPushButton("Повторить проверку VirusTotal")
        self.lookup_button.setEnabled(False)
        self.lookup_button.clicked.connect(self.check_virustotal)
        remote_layout.addWidget(self.lookup_button)
        layout.addWidget(remote)

    def choose_file(self):
        if self._worker is not None or self._vt_worker is not None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать мод для проверки", "",
            "Моды (*.zip *.png *.jpg *.jpeg *.webp *.bmp *.dds *.tga "
            "*.wav *.mp3 *.ogg *.flac *.blk *.cfg *.txt *.json *.xml)"
        )
        if path:
            self._path = path
            self._digest = ""
            self.path_label.setText("Файл: " + Path(path).name)
            self.result.clear()
            self.vt_result.setText("Файл ещё не проверялся через VirusTotal.")
            self.scan_button.setEnabled(True)
            self.lookup_button.setEnabled(False)

    def scan_file(self):
        if not self._path or self._worker is not None or self._vt_worker is not None:
            return
        self.choose_button.setEnabled(False)
        self.scan_button.setEnabled(False)
        self.lookup_button.setEnabled(False)
        self.result.setPlainText("Проверяем локально без распаковки на диск…")
        worker = LocalInspection(self._path, self)
        self._worker = worker
        worker.result_ready.connect(self._on_scan_complete)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._on_scan_finished)
        worker.start()

    def _on_scan_complete(self, report, error):
        if error or not report:
            self._digest = ""
            self.result.setPlainText("Локальная проверка не пройдена: " +
                                     (error or "ошибка"))
            self.vt_result.setText("Проверка VirusTotal не запускалась.")
            return
        self._digest = report["sha256"]
        self.result.setPlainText(
            report["message"] + "\n"
            + "Файлов: " + str(report["files"]) + "\n"
            + "Размер: " + str(report["bytes"]) + " байт\n"
            + "SHA-256: " + report["sha256"]
        )
        # The user explicitly selected this file for inspection. Automatically
        # request the existing VT hash report after local validation succeeds.
        self.check_virustotal()

    def _on_scan_finished(self):
        self._worker = None
        self.choose_button.setEnabled(self._vt_worker is None)
        self.scan_button.setEnabled(bool(self._path) and self._vt_worker is None)

    def check_virustotal(self):
        if not self._digest or self._vt_worker is not None:
            return
        self.choose_button.setEnabled(False)
        self.scan_button.setEnabled(False)
        self.lookup_button.setEnabled(False)
        self.vt_result.setText("Запрашиваем отчёт VirusTotal по SHA-256…")
        worker = VirusTotalLookup(self._digest, self)
        self._vt_worker = worker
        worker.result_ready.connect(self._on_vt_result)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._on_vt_finished)
        worker.start()

    def _on_vt_finished(self):
        self._vt_worker = None
        self.choose_button.setEnabled(self._worker is None)
        self.scan_button.setEnabled(bool(self._path) and self._worker is None)
        self.lookup_button.setEnabled(bool(self._digest) and self._worker is None)

    def _on_vt_result(self, report, error):
        if error or not report:
            self.vt_result.setText(error or "Не удалось получить отчёт VirusTotal.")
        elif not report.get("known"):
            self.vt_result.setText(
                "VirusTotal не знает этот SHA-256. Это не подтверждает безопасность."
            )
        else:
            malicious = report["malicious"]
            suspicious = report["suspicious"]
            total = sum(report[k] for k in (
                "malicious", "suspicious", "harmless", "undetected"
            ))
            summary = (
                "Найдены предупреждения. Не устанавливай файл до ручной проверки."
                if malicious or suspicious else
                "Угрозы не обнаружены проверившими движками. "
                "Это не гарантирует безопасность."
            )
            self.vt_result.setText(
                f"VirusTotal: {malicious} вредоносных, {suspicious} "
                f"подозрительных из {total} результатов.\n" + summary
            )

    def _stop_workers(self):
        for worker in (self._worker, self._vt_worker):
            if worker is not None and worker.isRunning():
                worker.wait(20000)
