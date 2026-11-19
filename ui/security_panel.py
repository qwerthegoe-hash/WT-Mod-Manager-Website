"""Opt-in file safety checks for the desktop Downloads / Diagnostics page.

Local scanning does not execute or extract downloaded mods. VirusTotal only
receives SHA-256 after an explicit click; no file is uploaded automatically.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
)

from src.mod_security import (
    SecurityError, VirusTotalError, inspect_mod_file, lookup_vt_sha256,
    has_vt_key, save_vt_key, remove_vt_key
)


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
            self.result_ready.emit(lookup_vt_sha256(self.digest), "")
        except (VirusTotalError, OSError) as error:
            self.result_ready.emit(None, str(error))


class SecurityPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ""
        self._digest = ""
        self._worker = None
        self._vt_worker = None
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._stop_workers)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 8, 2, 4)
        layout.setSpacing(12)

        local = QGroupBox("Проверка модов и ZIP")
        local_layout = QVBoxLayout(local)
        note = QLabel(
            "Локальная проверка путей, формата, CRC, ограничений распаковки "
            "и SHA-256. Это НЕ антивирусное заключение."
        )
        note.setWordWrap(True)
        local_layout.addWidget(note)
        actions = QHBoxLayout()
        self.choose_button = QPushButton("Выбрать ZIP или файл мода")
        self.choose_button.clicked.connect(self.choose_file)
        actions.addWidget(self.choose_button, 1)
        self.scan_button = QPushButton("Проверить локально")
        self.scan_button.setEnabled(False)
        self.scan_button.clicked.connect(self.scan_file)
        actions.addWidget(self.scan_button)
        local_layout.addLayout(actions)
        self.path_label = QLabel("Файл не выбран")
        self.path_label.setWordWrap(True)
        local_layout.addWidget(self.path_label)
        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        self.result.setMaximumHeight(110)
        self.result.setPlaceholderText("Результаты проверки появятся здесь.")
        local_layout.addWidget(self.result)
        layout.addWidget(local)

        vt_group = QGroupBox("VirusTotal — дополнительная проверка по хешу")
        vt_layout = QVBoxLayout(vt_group)
        guidance = QLabel(
            "Нужен личный API-ключ VirusTotal Community. Бесплатный тариф "
            "имеет лимиты и разрешён только для некоммерческого использования. "
            "Файлы на сервер не загружаются; передаётся только SHA-256."
        )
        guidance.setWordWrap(True)
        vt_layout.addWidget(guidance)
        grid = QGridLayout()
        self.key_entry = QLineEdit()
        self.key_entry.setPlaceholderText("Личный API-ключ (не показывается)")
        self.key_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_entry.setMinimumWidth(160)
        grid.addWidget(self.key_entry, 0, 0, 1, 2)
        self.save_button = QPushButton("Сохранить ключ")
        self.save_button.clicked.connect(self.save_key)
        grid.addWidget(self.save_button, 1, 0)
        self.remove_button = QPushButton("Удалить ключ")
        self.remove_button.clicked.connect(self.remove_key)
        grid.addWidget(self.remove_button, 1, 1)
        vt_layout.addLayout(grid)
        self.key_status = QLabel("")
        self.key_status.setWordWrap(True)
        vt_layout.addWidget(self.key_status)
        self.lookup_button = QPushButton("Проверить SHA-256 в VirusTotal")
        self.lookup_button.setEnabled(False)
        self.lookup_button.clicked.connect(self.check_virustotal)
        vt_layout.addWidget(self.lookup_button)
        self.vt_result = QLabel("Отчёт ещё не запрашивался.")
        self.vt_result.setWordWrap(True)
        self.vt_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        vt_layout.addWidget(self.vt_result)
        layout.addWidget(vt_group)
        self._refresh_key_status()

    def _refresh_key_status(self):
        self.key_status.setText(
            "API-ключ сохранён в защищённом профиле Windows (DPAPI)."
            if has_vt_key() else "API-ключ не подключён. Локальная проверка доступна без него."
        )
        self.lookup_button.setEnabled(bool(self._digest and has_vt_key()) and
                                      self._vt_worker is None)

    def choose_file(self):
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
            self.vt_result.setText("Новый файл ещё не проверялся через VirusTotal.")
            self.scan_button.setEnabled(True)
            self._refresh_key_status()

    def scan_file(self):
        if not self._path or self._worker is not None:
            return
        self.scan_button.setEnabled(False)
        self.choose_button.setEnabled(False)
        self.result.setPlainText("Проверяем файл, не распаковывая его на диск…")
        worker = LocalInspection(self._path, self)
        self._worker = worker
        worker.result_ready.connect(self._on_scan_complete)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._on_worker_finished)
        worker.start()

    def _on_worker_finished(self):
        self._worker = None
        self.choose_button.setEnabled(self._vt_worker is None)
        self.scan_button.setEnabled(bool(self._path) and self._vt_worker is None)

    def _on_scan_complete(self, report, error):
        if error or not report:
            self._digest = ""
            self.result.setPlainText("Проверка не пройдена: " + (error or "ошибка"))
        else:
            self._digest = report["sha256"]
            self.result.setPlainText(
                report["message"] + "\n"
                + "Файлов: " + str(report["files"]) + "\n"
                + "Размер: " + str(report["bytes"]) + " байт\n"
                + "SHA-256: " + report["sha256"]
            )
        self._refresh_key_status()

    def save_key(self):
        key = self.key_entry.text().strip()
        try:
            save_vt_key(key)
        except VirusTotalError as error:
            QMessageBox.warning(self, "VirusTotal", str(error))
            return
        self.key_entry.clear()
        self._refresh_key_status()

    def remove_key(self):
        try:
            remove_vt_key()
        except VirusTotalError as error:
            QMessageBox.warning(self, "VirusTotal", str(error))
        self.key_entry.clear()
        self._refresh_key_status()

    def check_virustotal(self):
        if not self._digest or self._vt_worker is not None:
            return
        digest = self._digest
        self.lookup_button.setEnabled(False)
        self.choose_button.setEnabled(False)
        self.scan_button.setEnabled(False)
        self.vt_result.setText("Запрос отчёта VirusTotal по SHA-256…")
        worker = VirusTotalLookup(digest, self)
        self._vt_worker = worker
        worker.result_ready.connect(self._on_vt_result)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._on_vt_finished)
        worker.start()

    def _on_vt_finished(self):
        self._vt_worker = None
        self.choose_button.setEnabled(self._worker is None)
        self.scan_button.setEnabled(bool(self._path) and self._worker is None)
        self._refresh_key_status()

    def _on_vt_result(self, report, error):
        if error or not report:
            self.vt_result.setText(error or "Не удалось получить отчёт VirusTotal.")
        elif not report.get("known"):
            self.vt_result.setText(
                "VirusTotal пока не знает этот SHA-256. Это НЕ подтверждение безопасности."
            )
        else:
            malicious = report["malicious"]
            suspicious = report["suspicious"]
            total = sum(report[x] for x in ("malicious", "suspicious", "harmless", "undetected"))
            summary = (
                "Есть предупреждения от отдельных движков. Требуется ручная проверка."
                if malicious or suspicious else
                "Известные движки не сообщили угроз; это не гарантирует безопасность."
            )
            self.vt_result.setText(
                "VirusTotal: " + str(malicious) + " вредоносных, "
                + str(suspicious) + " подозрительных из "
                + str(total) + " результатов.\n" + summary
            )

    def _stop_workers(self):
        # The native QThread objects are owned by this widget. Do not destroy
        # them while a bounded local check or network lookup is still running.
        for worker in (self._worker, self._vt_worker):
            if worker is not None and worker.isRunning():
                worker.wait(20000)
