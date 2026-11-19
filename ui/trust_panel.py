"""Small, on-demand Trust Center widget for the Downloads diagnostics page."""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QGroupBox, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QVBoxLayout
)

from src.trust_center import local_executable_trust, format_local_trust
from src.crash_recovery import latest_report_summary


class TrustWorker(QThread):
    result_ready = Signal(str)

    def run(self):
        try:
            report = local_executable_trust()
            self.result_ready.emit(format_local_trust(report))
        except (OSError, ValueError, RuntimeError):
            self.result_ready.emit(
                "Не удалось завершить локальную проверку. "
                "Попробуй снова или открой GitHub Releases."
            )


class TrustPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("WT Trust Center — доверие и восстановление", parent)
        self.worker = None
        col = QVBoxLayout(self)
        explanation = QLabel(
            "Локальная проверка EXE и цифровой подписи Windows. "
            "Она не заменяет антивирус и не отправляет твои файлы."
        )
        explanation.setWordWrap(True)
        col.addWidget(explanation)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(190)
        self.output.setPlaceholderText(
            "Нажми «Проверить установленную версию». "
            "SHA-256 можно будет сравнить с официальным релизом."
        )
        col.addWidget(self.output)
        actions = QHBoxLayout()
        self.inspect_button = QPushButton("Проверить установленную версию")
        self.inspect_button.clicked.connect(self.inspect)
        actions.addWidget(self.inspect_button)
        self.site_button = QPushButton("Проверить релиз на сайте")
        self.site_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(
                "https://qwerthegoe-hash.github.io/WT-Mod-Manager-Website/trust.html"
            ))
        )
        actions.addWidget(self.site_button)
        col.addLayout(actions)
        self.recovery_note = QLabel(latest_report_summary())
        self.recovery_note.setWordWrap(True)
        col.addWidget(self.recovery_note)
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.stop)

    def inspect(self):
        if self.worker is not None:
            return
        self.inspect_button.setEnabled(False)
        self.output.setPlainText("Проверяем локальный файл и подпись…")
        worker = TrustWorker(self)
        self.worker = worker
        worker.result_ready.connect(self.output.setPlainText)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._done)
        worker.start()

    def _done(self):
        self.worker = None
        self.inspect_button.setEnabled(True)

    def stop(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait(15000)
