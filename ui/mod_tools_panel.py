"""Opt-in local mod manager tools. No remote calls or automatic file changes."""
from __future__ import annotations
import json
from pathlib import Path
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QGroupBox, QGridLayout, QVBoxLayout, QLabel, QPushButton, QMessageBox,
    QFileDialog, QInputDialog, QPlainTextEdit, QDialog, QApplication
)
from src.profile_paths import DATA_DIR, save_mod_profile
from src.mod_suite import (
    installed_integrity, history, compatibility, modpack_manifest, read_modpack
)


class IntegrityWorker(QThread):
    completed = Signal(object, str)

    def run(self):
        try:
            self.completed.emit(installed_integrity(), "")
        except (OSError, ValueError, TypeError) as error:
            self.completed.emit([], "Не удалось проверить локальные файлы.")


class ModToolsPanel(QGroupBox):
    def __init__(self, get_account, get_library, reload_profiles, parent=None):
        super().__init__("WT Mod Suite — локальные инструменты", parent)
        self.get_account = get_account
        self.get_library = get_library
        self.reload_profiles = reload_profiles
        self.worker = None
        outer = QVBoxLayout(self)
        description = QLabel(
            "Предпросмотр установок и откат — в окнах установки модов. "
            "Здесь доступны история, проверка целостности, совместимость и "
            "обмен наборами. Импорт JSON никогда не скачивает и не запускает файлы."
        )
        description.setWordWrap(True)
        outer.addWidget(description)
        buttons = QGridLayout()
        buttons.setSpacing(8)
        self.integrity_button = QPushButton("Проверить целостность")
        self.integrity_button.clicked.connect(self.inspect_integrity)
        buttons.addWidget(self.integrity_button, 0, 0)
        self.timeline_button = QPushButton("История установки")
        self.timeline_button.clicked.connect(self.show_history)
        buttons.addWidget(self.timeline_button, 0, 1)
        self.export_button = QPushButton("Экспорт набора JSON")
        self.export_button.clicked.connect(self.export_modpack)
        buttons.addWidget(self.export_button, 1, 0)
        self.import_button = QPushButton("Импорт набора JSON")
        self.import_button.clicked.connect(self.import_modpack)
        buttons.addWidget(self.import_button, 1, 1)
        self.compatibility_button = QPushButton("Совместимость с игрой")
        self.compatibility_button.clicked.connect(self.check_compatibility)
        buttons.addWidget(self.compatibility_button, 2, 0, 1, 2)
        outer.addLayout(buttons)
        self.result = QLabel("Проверки выполняются только после нажатия кнопки.")
        self.result.setWordWrap(True)
        self.result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(self.result)
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.stop)

    def _show_text(self, title: str, message: str):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(680, 420)
        layout = QVBoxLayout(dialog)
        pane = QPlainTextEdit()
        pane.setReadOnly(True)
        pane.setPlainText(message)
        layout.addWidget(pane)
        close = QPushButton("Закрыть")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

    def inspect_integrity(self):
        if self.worker is not None:
            return
        self.integrity_button.setEnabled(False)
        self.result.setText("Проверяем установленные моды в фоне…")
        worker = IntegrityWorker(self)
        self.worker = worker
        worker.completed.connect(self._integrity_done)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._worker_done)
        worker.start()

    def _integrity_done(self, entries, error):
        if error:
            self.result.setText(error)
            return
        counts = {key: sum(r["status"] == key for r in entries)
                  for key in ("ok", "changed", "missing", "link", "unavailable", "unknown")}
        self.result.setText(
            f"Проверено файлов: {len(entries)}. Совпадают: {counts['ok']}; "
            f"изменены: {counts['changed']}; отсутствуют: {counts['missing']}; "
            f"прочие ошибки: {counts['link'] + counts['unavailable']}."
        )
        lines = [f"{r['status']:12}  {r['file']}" for r in entries]
        self._show_text("WT Mod Integrity Monitor", "\n".join(lines) or
                        "Истории локальных установок пока нет.")

    def _worker_done(self):
        self.worker = None
        self.integrity_button.setEnabled(True)

    def show_history(self):
        entries = history()
        lines = [f"{r['time_utc'][:19]} • {r['event']} • {r['files']} файлов • "
                 f"ID {r['transaction'][:12]}" for r in reversed(entries)]
        self._show_text("WT Timeline — история изменений", "\n".join(lines) or
                        "История ещё пуста. Будущие установки будут записываться локально.")

    def export_modpack(self):
        account = self.get_account()
        if not account:
            QMessageBox.information(self, "Модпаки", "Сначала свяжи аккаунт сайта.")
            return
        entries = self.get_library()
        if not entries:
            QMessageBox.information(self, "Модпаки", "Нет импортированных модов.")
            return
        name, ok = QInputDialog.getText(self, "Экспорт модпака",
                                        "Название набора модов:", text="Мой набор")
        if not ok:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить список модов (без файлов)",
            str(Path.home() / "WTMM-modpack.json"), "WT Modpack JSON (*.json)"
        )
        if not filename:
            return
        try:
            from src.profile_paths import _account_path
            pack = modpack_manifest(_account_path(account), list(entries), name)
            target = Path(filename)
            if target.is_symlink():
                raise OSError("Отказ записи по символической ссылке.")
            target.write_text(json.dumps(pack, ensure_ascii=False, indent=2),
                              encoding="utf-8")
            self.result.setText(f"Сохранён список из {len(pack['mods'])} модов. "
                                "Файлы и токены не экспортировались.")
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Модпак", str(error))

    def import_modpack(self):
        account = self.get_account()
        if not account:
            QMessageBox.information(self, "Модпаки", "Сначала свяжи аккаунт сайта.")
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Импорт списка модов", str(Path.home()), "WT Modpack JSON (*.json)"
        )
        if not filename:
            return
        try:
            source = Path(filename)
            if source.is_symlink() or source.stat().st_size > 128 * 1024:
                raise ValueError("Файл слишком большой или является ссылкой.")
            pack = json.loads(source.read_text("utf-8"))
            available = set(self.get_library())
            found = read_modpack(pack, available)
            total = len(pack["mods"])
            if not found:
                QMessageBox.information(
                    self, "Импорт", "В этом наборе нет модов, уже импортированных "
                    "в подключённый аккаунт. Ничего не скачивалось."
                )
                return
            name, ok = QInputDialog.getText(
                self, "Импорт модпака", "Сохранить как набор:",
                text=str(pack.get("name", "Импортированный набор"))[:40]
            )
            if not ok:
                return
            save_mod_profile(account, name, found)
            self.reload_profiles()
            self.result.setText(
                f"Импортировано {len(found)} из {total} известных модов в новый "
                "профиль. Файлы игры не изменялись."
            )
        except (ValueError, OSError, UnicodeError, TypeError) as error:
            QMessageBox.warning(self, "Ошибка импорта", str(error))

    def check_compatibility(self):
        account = self.get_account()
        if not account:
            QMessageBox.information(self, "Совместимость",
                                    "Привяжи аккаунт с импортированными модами.")
            return
        actual, ok = QInputDialog.getText(
            self, "Версия игры", "Введи фактическую версию War Thunder "
            "из меню самой игры (например 2.45.0):"
        )
        if not ok:
            return
        entries = self.get_library()
        lines = []
        for name, entry in list(entries.items())[:100]:
            verdict = compatibility(entry, actual.strip())
            lines.append(
                str(entry.get("title", "Мод"))[:60] + " — " +
                verdict["status"] + ": " + verdict["reason"]
            )
        self._show_text("WT Compatibility Checker",
                        "\n".join(lines) or "Нет импортированных модов.")

    def stop(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait(15000)
