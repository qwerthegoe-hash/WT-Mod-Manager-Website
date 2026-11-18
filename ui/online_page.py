"""Account-specific online mod downloads inside WT Mod Manager."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QApplication, QTabWidget, QLineEdit
)

from src.desktop_sync import DesktopSync, imported_library, restore_previous_mod, PackageError, UUID
from src.profile_paths import DATA_DIR, set_active_online_account


class OnlinePage(QWidget):
    assets_changed = Signal(str)
    account_changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(15)

        heading = QLabel("Скачанные моды и синхронизация")
        heading.setObjectName("Title")
        description = QLabel(
            "Свяжи аккаунт сайта, чтобы моды из раздела «Скачанные» "
            "появлялись только после нажатия «Добавить в приложение». "
            "Локальные файлы с твоего ПК продолжат работать независимо от сайта."
        )
        description.setObjectName("Subtitle")
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)

        self.status = QLabel("Аккаунт не подключён.")
        self.status.setWordWrap(True)
        self.status.setObjectName("Subtitle")
        layout.addWidget(self.status)

        controls = QHBoxLayout()
        self.link_button = QPushButton("Связать аккаунт сайта")
        self.link_button.setObjectName("Primary")
        self.link_button.clicked.connect(self.connect_account)
        self.refresh_button = QPushButton("Проверить сейчас")
        self.refresh_button.clicked.connect(self.check_now)
        self.folder_button = QPushButton("Открыть мои файлы")
        self.folder_button.clicked.connect(self.open_folder)
        self.unlink_button = QPushButton("Отключить аккаунт")
        self.unlink_button.clicked.connect(self.disconnect_account)
        for button in (self.link_button, self.refresh_button, self.folder_button, self.unlink_button):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            controls.addWidget(button)
        layout.addLayout(controls)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        offline_tab = QWidget()
        offline_layout = QVBoxLayout(offline_tab)
        self.list_title = QLabel("Импортированные моды этого аккаунта")
        offline_layout.addWidget(self.list_title)
        self.library = QListWidget()
        offline_layout.addWidget(self.library, 1)
        self.rollback_button = QPushButton("Восстановить предыдущую версию")
        self.rollback_button.setEnabled(False)
        self.rollback_button.clicked.connect(self.restore_selected_version)
        self.library.itemSelectionChanged.connect(self.update_rollback_control)
        offline_layout.addWidget(self.rollback_button)
        self.tabs.addTab(offline_tab, "Мои загрузки")

        catalog_tab = QWidget()
        catalog_layout = QVBoxLayout(catalog_tab)
        self.catalog_note = QLabel(
            "Каталог сайта отображает только одобренные моды. Для загрузки "
            "и передачи открой мод на сайте — автоматической установки нет."
        )
        self.catalog_note.setWordWrap(True)
        catalog_layout.addWidget(self.catalog_note)
        self.catalog_search = QLineEdit()
        self.catalog_search.setPlaceholderText("Поиск по названию или категории")
        self.catalog_search.textChanged.connect(self.render_catalog)
        catalog_layout.addWidget(self.catalog_search)
        self.catalog_list = QListWidget()
        self.catalog_list.itemDoubleClicked.connect(self.open_selected_mod)
        catalog_layout.addWidget(self.catalog_list, 1)
        catalog_controls = QHBoxLayout()
        self.catalog_refresh = QPushButton("Обновить каталог")
        self.catalog_refresh.clicked.connect(self.refresh_remote_catalog)
        catalog_controls.addWidget(self.catalog_refresh)
        self.catalog_open = QPushButton("Подробнее на сайте")
        self.catalog_open.clicked.connect(self.open_selected_mod)
        catalog_controls.addWidget(self.catalog_open)
        self.community_open = QPushButton("Сообщество")
        self.community_open.clicked.connect(self.open_community)
        catalog_controls.addWidget(self.community_open)
        catalog_layout.addLayout(catalog_controls)
        self.tabs.addTab(catalog_tab, "Каталог сайта")
        self.catalog_rows = []

        self.bridge = DesktopSync(self)
        self.bridge.status_changed.connect(self.status.setText)
        self.bridge.account_changed.connect(self.on_account)
        self.bridge.files_changed.connect(self.on_import)
        self.bridge.catalog_changed.connect(self.on_catalog)
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.bridge.stop)
        self.refresh_library()

    def connect_account(self):
        self.bridge.link_account()

    def check_now(self):
        self.bridge.sync_now()
        self.bridge.refresh_catalog()
        self.refresh_library()

    def on_account(self, account_id):
        set_active_online_account(account_id or None)
        self.catalog_rows = []
        self.render_catalog()
        self.account_changed.emit()
        self.refresh_library()

    def on_import(self, category):
        self.refresh_library()
        self.assets_changed.emit(category)
        self.status.setText("Новые файлы добавлены без перезапуска WT Mod Manager.")

    def refresh_remote_catalog(self):
        if not self.bridge.user_id:
            self.status.setText("Привяжи аккаунт сайта, чтобы открыть онлайн-каталог.")
            return
        self.bridge.refresh_catalog()

    def on_catalog(self, rows):
        self.catalog_rows = [row for row in rows if isinstance(row, dict)]
        self.render_catalog()

    def render_catalog(self, *_):
        query = self.catalog_search.text().strip().casefold()
        self.catalog_list.clear()
        labels = {
            "sights": "Прицелы", "camouflage": "Камуфляжи",
            "sounds": "Звуки", "visuals": "Графика",
            "interface": "Интерфейс", "other": "Другое"
        }
        for row in self.catalog_rows:
            title = str(row.get("title", ""))[:90]
            category = labels.get(row.get("category"), "Мод")
            version = str(row.get("version", ""))[:32]
            if query and query not in (title + " " + category).casefold():
                continue
            ident = str(row.get("id", ""))
            if not UUID.fullmatch(ident):
                continue
            item = QListWidgetItem(category + " • " + title + " • v" + version)
            item.setData(Qt.ItemDataRole.UserRole, ident)
            self.catalog_list.addItem(item)
        if not self.catalog_list.count():
            self.catalog_list.addItem(
                "Нет опубликованных модов" if not self.catalog_rows else
                "Поиск не дал результатов"
            )

    def open_selected_mod(self, *_):
        item = self.catalog_list.currentItem()
        ident = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not ident or not UUID.fullmatch(str(ident)):
            return
        url = ("https://qwerthegoe-hash.github.io/WT-Mod-Manager-Website/"
               "mods/mods.html?mod=" + str(ident))
        QDesktopServices.openUrl(QUrl(url))

    def open_community(self):
        QDesktopServices.openUrl(QUrl(
            "https://qwerthegoe-hash.github.io/WT-Mod-Manager-Website/"
            "community/community.html"
        ))

    def refresh_library(self):
        entries = imported_library(self.bridge.user_id)
        self.library.clear()
        category_names = {
            "sights": "Прицелы", "sounds": "Звуки", "camouflage": "Камуфляжи"
        }
        for mod_id, item in sorted(
            entries.items(),
            key=lambda entry: entry[1].get("imported_at", 0)
                if isinstance(entry[1], dict) else 0,
            reverse=True
        ):
            if not isinstance(item, dict):
                continue
            category = category_names.get(item.get("category"), "Мод")
            name = str(item.get("title") or "Без названия")
            version = str(item.get("version") or "")
            count = len(item.get("files", []))
            has_history = isinstance(item.get("previous"), dict)
            label = (category + " • " + name + " • v" + version
                     + " • файлов: " + str(count)
                     + (" • предыдущая версия сохранена" if has_history else ""))
            row = QListWidgetItem(label)
            row.setData(Qt.ItemDataRole.UserRole, mod_id)
            self.library.addItem(row)
        if not self.library.count():
            self.library.addItem("Пока нет переданных модов. Локальная библиотека остаётся доступной.")
        self.update_rollback_control()

    def update_rollback_control(self):
        item = self.library.currentItem()
        mod_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        entries = imported_library(self.bridge.user_id)
        entry = entries.get(mod_id) if mod_id else None
        self.rollback_button.setEnabled(
            isinstance(entry, dict) and isinstance(entry.get("previous"), dict)
        )

    def restore_selected_version(self):
        item = self.library.currentItem()
        mod_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not mod_id or not self.bridge.user_id:
            return
        entry = imported_library(self.bridge.user_id).get(mod_id)
        if not isinstance(entry, dict) or not isinstance(entry.get("previous"), dict):
            QMessageBox.information(self, "История", "Для этого мода нет предыдущей версии.")
            return
        previous = entry["previous"]
        answer = QMessageBox.question(
            self, "Восстановление",
            "Восстановить предыдущую версию "
            + str(previous.get("version", "")) + " мода «"
            + str(entry.get("title", "")) + "»? Текущая версия будет заменена."
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            count, category = restore_previous_mod(self.bridge.user_id, mod_id)
            self.refresh_library()
            self.assets_changed.emit(category)
            self.status.setText("Предыдущая версия восстановлена (файлов: " + str(count) + ").")
        except (PackageError, OSError, ValueError) as error:
            QMessageBox.warning(self, "Ошибка восстановления", str(error))

    def open_folder(self):
        if not self.bridge.user_id:
            QMessageBox.information(self, "Аккаунт", "Сначала свяжи аккаунт сайта.")
            return
        target = DATA_DIR / "accounts" / self.bridge.user_id / "mods"
        target.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def disconnect_account(self):
        choice = QMessageBox.question(
            self, "Отключить аккаунт",
            "Отключить синхронизацию? Локальные и ранее скачанные файлы сохранятся."
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.bridge.unlink_account()
            set_active_online_account(None)
            self.account_changed.emit()
            self.refresh_library()
