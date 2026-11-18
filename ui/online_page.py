"""Account-specific online mod downloads inside WT Mod Manager."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QApplication, QTabWidget, QLineEdit,
    QComboBox, QInputDialog, QAbstractItemView, QCheckBox
)

from src.desktop_sync import DesktopSync, imported_library, restore_previous_mod, PackageError, UUID
from src.update_notifications import load_notifications, mark_all_read
from src.profile_paths import (
    DATA_DIR, set_active_online_account, load_mod_profiles,
    save_mod_profile, set_active_mod_profile, delete_mod_profile
)


class OnlinePage(QWidget):
    assets_changed = Signal(str)
    account_changed = Signal()
    check_update_requested = Signal()
    install_update_requested = Signal()
    auto_check_changed = Signal(bool)

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
        update_controls = QHBoxLayout()
        self.update_button = QPushButton("Проверить обновления")
        self.update_button.clicked.connect(self.check_update_requested.emit)
        self.install_update_button = QPushButton("Скачать обновление")
        self.install_update_button.setEnabled(False)
        self.install_update_button.clicked.connect(self.install_update_requested.emit)
        self.update_auto_checkbox = QCheckBox("Автопроверка каждые 10 минут")
        self.update_auto_checkbox.setChecked(load_notifications()["auto_check"])
        self.update_auto_checkbox.toggled.connect(self.auto_check_changed.emit)
        update_controls.addWidget(self.update_button)
        update_controls.addWidget(self.install_update_button)
        update_controls.addWidget(self.update_auto_checkbox)
        layout.addLayout(update_controls)
        self.update_summary = QLabel("Проверка новых выпусков работает и при свёрнутом окне.")
        self.update_summary.setWordWrap(True)
        layout.addWidget(self.update_summary)

        self.updates_inbox = QListWidget()
        self.updates_inbox.setMaximumHeight(105)
        self.updates_inbox.setToolTip("История уведомлений об обновлениях в этом профиле Windows")
        layout.addWidget(self.updates_inbox)
        self.read_notices_button = QPushButton("Отметить уведомления прочитанными")
        self.read_notices_button.clicked.connect(self.mark_update_notices_read)
        layout.addWidget(self.read_notices_button)
        self.refresh_update_notices()

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        offline_tab = QWidget()
        offline_layout = QVBoxLayout(offline_tab)
        self.list_title = QLabel("Импортированные моды этого аккаунта")
        offline_layout.addWidget(self.list_title)
        self.library = QListWidget()
        self.library.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        offline_layout.addWidget(self.library, 1)
        self.rollback_button = QPushButton("Восстановить предыдущую версию")
        self.rollback_button.setEnabled(False)
        self.rollback_button.clicked.connect(self.restore_selected_version)
        self.library.itemSelectionChanged.connect(self.update_rollback_control)
        offline_layout.addWidget(self.rollback_button)
        presets = QHBoxLayout()
        self.profile_picker = QComboBox()
        presets.addWidget(self.profile_picker, 1)
        self.profile_save = QPushButton("Сохранить набор")
        self.profile_save.clicked.connect(self.save_selected_profile)
        presets.addWidget(self.profile_save)
        self.profile_apply = QPushButton("Применить")
        self.profile_apply.clicked.connect(self.apply_selected_profile)
        presets.addWidget(self.profile_apply)
        self.profile_delete = QPushButton("Удалить")
        self.profile_delete.clicked.connect(self.remove_selected_profile)
        presets.addWidget(self.profile_delete)
        offline_layout.addLayout(presets)
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
        self.refresh_profile_controls()
        self.profile_picker.currentIndexChanged.connect(
            lambda _: self.profile_delete.setEnabled(
                bool(self.bridge.user_id and self.profile_picker.currentData())
            )
        )

    def set_available_update(self, info):
        if not isinstance(info, dict):
            return
        version = str(info.get("version", ""))[:50]
        self.update_summary.setText(
            "Доступен WT Mod Manager " + version +
            ". Обновление можно скачать и установить без удаления модов и настроек."
        )
        self.install_update_button.setText("Скачать и установить " + version)
        self.install_update_button.setEnabled(True)
        self.refresh_update_notices()

    def refresh_update_notices(self):
        state = load_notifications()
        self.updates_inbox.clear()
        for event in reversed(state["events"][-12:]):
            marker = "● " if not event["read"] else "  "
            self.updates_inbox.addItem(
                marker + str(event["title"]) + " — " + str(event["message"])
            )
        if not self.updates_inbox.count():
            self.updates_inbox.addItem("Уведомлений пока нет.")

    def mark_update_notices_read(self):
        mark_all_read()
        self.refresh_update_notices()

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
        self.refresh_profile_controls()

    def on_import(self, category):
        self.refresh_library()
        self.refresh_profile_controls()
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

    def refresh_profile_controls(self):
        self.profile_picker.blockSignals(True)
        self.profile_picker.clear()
        self.profile_picker.addItem("Все скачанные", None)
        if self.bridge.user_id:
            state = load_mod_profiles(self.bridge.user_id)
            for name in sorted(state["profiles"], key=str.casefold):
                self.profile_picker.addItem(name, name)
            idx = self.profile_picker.findData(state["active"])
            if idx >= 0:
                self.profile_picker.setCurrentIndex(idx)
        self.profile_picker.blockSignals(False)
        active = bool(self.bridge.user_id)
        self.profile_picker.setEnabled(active)
        self.profile_save.setEnabled(active)
        self.profile_apply.setEnabled(active)
        self.profile_delete.setEnabled(active and self.profile_picker.currentData() is not None)

    def save_selected_profile(self):
        if not self.bridge.user_id:
            return
        name, ok = QInputDialog.getText(self, "Набор модов", "Название набора:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in load_mod_profiles(self.bridge.user_id)["profiles"]:
            if QMessageBox.question(self, "Заменить набор", "Обновить существующий набор «" + name + "»?") != QMessageBox.StandardButton.Yes:
                return
        ids = [str(item.data(Qt.ItemDataRole.UserRole))
               for item in self.library.selectedItems()
               if UUID.fullmatch(str(item.data(Qt.ItemDataRole.UserRole) or ""))]
        try:
            count = save_mod_profile(self.bridge.user_id, name, ids)
            self.refresh_profile_controls()
            index = self.profile_picker.findData(name)
            if index >= 0:
                self.profile_picker.setCurrentIndex(index)
            self.status.setText("Набор «" + name + "» сохранён (модов: " + str(count) + ").")
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Ошибка набора", str(error))

    def apply_selected_profile(self):
        if not self.bridge.user_id:
            return
        name = self.profile_picker.currentData()
        try:
            set_active_mod_profile(self.bridge.user_id, name)
            self.account_changed.emit()
            self.status.setText("Включён набор «" + name + "»." if name else
                                "Показаны все моды этого аккаунта.")
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Ошибка переключения", str(error))

    def remove_selected_profile(self):
        name = self.profile_picker.currentData()
        if not self.bridge.user_id or not name:
            return
        if QMessageBox.question(self, "Удалить набор", "Удалить «" + name + "» без удаления файлов?") != QMessageBox.StandardButton.Yes:
            return
        delete_mod_profile(self.bridge.user_id, name)
        self.refresh_profile_controls()
        self.account_changed.emit()
        self.status.setText("Набор удалён; файлы сохранены.")

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
            self.refresh_profile_controls()
