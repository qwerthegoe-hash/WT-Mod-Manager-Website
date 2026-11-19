"""Account-specific online mod downloads inside WT Mod Manager."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QScrollArea,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QApplication, QTabWidget, QLineEdit, QComboBox, QInputDialog,
    QAbstractItemView, QCheckBox, QPlainTextEdit
)

from src.desktop_sync import DesktopSync, imported_library, restore_previous_mod, PackageError, UUID
from src.update_notifications import load_notifications, mark_all_read
from src.diagnostics import inspect_local, format_report, repair_safe_folders
from src.update_checker import VERSION, is_installed_app, update_channel, set_update_channel
from src.portable_updater import previous_exe_available
from ui.security_panel import SecurityPanel
from ui.trust_panel import TrustPanel
from ui.mod_tools_panel import ModToolsPanel
from src.offline_mode import is_offline, set_offline
from src.release_rollout import early_access, set_early_access
from src.crash_recovery import latest_report_summary
from src.profile_paths import (
    DATA_DIR, set_active_online_account, load_mod_profiles,
    save_mod_profile, set_active_mod_profile, delete_mod_profile
)


class OnlinePage(QWidget):
    assets_changed = Signal(str)
    account_changed = Signal()
    check_update_requested = Signal()
    install_update_requested = Signal()
    rollback_update_requested = Signal()
    auto_check_changed = Signal(bool)
    account_new_notice = Signal(str, str)

    def __init__(self):
        super().__init__()

        # The content scrolls as a whole on smaller Windows displays.
        # Nothing is positioned with absolute coordinates or overlap hacks.
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        scroller = QScrollArea(self)
        scroller.setWidgetResizable(True)
        scroller.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(scroller)
        body = QWidget()
        body.setObjectName("DownloadsBody")
        scroller.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Загрузки и синхронизация")
        title.setObjectName("Title")
        layout.addWidget(title)
        subtitle = QLabel(
            "Моды сайта подключаются только по твоему запросу. "
            "Локальные моды работают независимо от аккаунта."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        def card(label):
            frame = QFrame()
            frame.setObjectName("ContentCard")
            col = QVBoxLayout(frame)
            col.setContentsMargins(16, 14, 16, 16)
            col.setSpacing(10)
            caption = QLabel(label)
            caption.setObjectName("CardTitle")
            col.addWidget(caption)
            return frame, col

        top = QGridLayout()
        top.setHorizontalSpacing(14)
        top.setVerticalSpacing(14)
        top.setColumnStretch(0, 1)
        top.setColumnStretch(1, 1)
        layout.addLayout(top)

        account_card, account = card("АККАУНТ САЙТА")
        top.addWidget(account_card, 0, 0)
        self.status = QLabel("Аккаунт не подключён.")
        self.status.setObjectName("Subtitle")
        self.status.setWordWrap(True)
        self.status.setMinimumHeight(48)
        account.addWidget(self.status)

        self.link_button = QPushButton("Связать аккаунт сайта")
        self.link_button.setObjectName("Primary")
        self.link_button.clicked.connect(self.connect_account)
        self.refresh_button = QPushButton("Синхронизировать")
        self.refresh_button.clicked.connect(self.check_now)
        self.folder_button = QPushButton("Открыть мои файлы")
        self.folder_button.clicked.connect(self.open_folder)
        self.unlink_button = QPushButton("Отключить аккаунт")
        self.unlink_button.clicked.connect(self.disconnect_account)
        account_actions = QGridLayout()
        account_actions.setSpacing(8)
        account_actions.addWidget(self.link_button, 0, 0, 1, 2)
        account_actions.addWidget(self.refresh_button, 1, 0)
        account_actions.addWidget(self.folder_button, 1, 1)
        account_actions.addWidget(self.unlink_button, 2, 0, 1, 2)
        account.addLayout(account_actions)
        self.offline_switch = QCheckBox("WT Offline Mode — без сети")
        self.offline_switch.setChecked(is_offline())
        self.offline_switch.setToolTip(
            "Локальные моды и настройки работают как обычно. "
            "Синхронизация, VirusTotal и обновления выключены."
        )
        self.offline_switch.toggled.connect(self.set_offline_mode)
        account.addWidget(self.offline_switch)
        account.addStretch(1)

        updates_card, updates = card("ОБНОВЛЕНИЯ")
        top.addWidget(updates_card, 0, 1)
        self._header_grid = top
        self._account_card = account_card
        self._updates_card = updates_card
        self._compact_header = False
        self.update_summary = QLabel(
            "Текущая версия: " + VERSION + ". Новые версии проверяются в фоне."
        )
        self.update_summary.setWordWrap(True)
        updates.addWidget(self.update_summary)
        update_actions = QGridLayout()
        update_actions.setSpacing(8)
        self.update_button = QPushButton("Проверить обновления")
        self.update_button.clicked.connect(self.check_update_requested.emit)
        update_actions.addWidget(self.update_button, 0, 0)
        self.install_update_button = QPushButton("Скачать обновление")
        self.install_update_button.setEnabled(False)
        self.install_update_button.hide()
        self.install_update_button.clicked.connect(self.install_update_requested.emit)
        update_actions.addWidget(self.install_update_button, 1, 0)
        updates.addLayout(update_actions)
        self.update_auto_checkbox = QCheckBox("Автопроверка каждые 10 минут")
        self.update_auto_checkbox.setChecked(load_notifications()["auto_check"])
        self.update_auto_checkbox.toggled.connect(self.auto_check_changed.emit)
        updates.addWidget(self.update_auto_checkbox)
        channel_row = QHBoxLayout()
        channel_row.addWidget(QLabel("Канал обновлений:"))
        self.channel_picker = QComboBox()
        self.channel_picker.addItem("Stable — проверенные версии", "stable")
        self.channel_picker.addItem("Beta — новые функции", "beta")
        self.channel_picker.setCurrentIndex(0 if update_channel() == "stable" else 1)
        channel_row.addWidget(self.channel_picker, 1)
        updates.addLayout(channel_row)
        self.channel_picker.currentIndexChanged.connect(self._save_channel)
        self.early_beta_checkbox = QCheckBox("Участвовать в раннем тестировании Beta")
        self.early_beta_checkbox.setChecked(early_access())
        self.early_beta_checkbox.setToolTip(
            "Необязательный ранний доступ к тестовым версиям. "
            "Процент допуска управляется прозрачной политикой GitHub."
        )
        self.early_beta_checkbox.toggled.connect(self._save_early_beta)
        updates.addWidget(self.early_beta_checkbox)
        self.rollback_exe_button = QPushButton("Вернуть предыдущую версию приложения")
        self.rollback_exe_button.clicked.connect(self.rollback_update_requested.emit)
        self.rollback_exe_button.setToolTip(
            "Откат доступен только когда сохранена проверенная предыдущая portable-версия."
        )
        self.rollback_exe_button.setVisible(
            not is_installed_app() and previous_exe_available()
        )
        updates.addWidget(self.rollback_exe_button)
        updates.addStretch(1)

        inbox_card, inbox = card("УВЕДОМЛЕНИЯ")
        layout.addWidget(inbox_card)
        notice_grid = QGridLayout()
        notice_grid.setHorizontalSpacing(14)
        notice_grid.setVerticalSpacing(6)
        notice_grid.setColumnStretch(0, 1)
        notice_grid.setColumnStretch(1, 1)
        inbox.addLayout(notice_grid)
        notice_grid.addWidget(QLabel("Обновления приложения"), 0, 0)
        notice_grid.addWidget(QLabel("Аккаунт и моды"), 0, 1)
        self.updates_inbox = QListWidget()
        self.updates_inbox.setMaximumHeight(90)
        self.updates_inbox.setToolTip("История уведомлений этого профиля Windows")
        notice_grid.addWidget(self.updates_inbox, 1, 0)
        self.remote_notifications = QListWidget()
        self.remote_notifications.setMaximumHeight(90)
        self.remote_notifications.addItem("Нет уведомлений аккаунта.")
        self.remote_notifications.setToolTip(
            "Уведомления сайта, модерации и сообщества"
        )
        notice_grid.addWidget(self.remote_notifications, 1, 1)
        self.read_notices_button = QPushButton("Прочитать обновления")
        self.read_notices_button.clicked.connect(self.mark_update_notices_read)
        notice_grid.addWidget(self.read_notices_button, 2, 0)
        site_notice_actions = QHBoxLayout()
        self.notices_refresh = QPushButton("Обновить")
        self.notices_refresh.clicked.connect(self.check_account_notifications)
        site_notice_actions.addWidget(self.notices_refresh)
        self.notices_mark_read = QPushButton("Прочитать")
        self.notices_mark_read.clicked.connect(self.mark_account_notifications_read)
        site_notice_actions.addWidget(self.notices_mark_read)
        notice_grid.addLayout(site_notice_actions, 2, 1)
        self._seen_account_notices = None
        self.refresh_update_notices()

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMinimumHeight(410)
        layout.addWidget(self.tabs)

        # 1. Downloaded mods. Presets belong above the list, not beneath it.
        offline_tab = QWidget()
        offline_layout = QVBoxLayout(offline_tab)
        offline_layout.setContentsMargins(12, 14, 12, 12)
        offline_layout.setSpacing(10)
        presets = QHBoxLayout()
        presets.setSpacing(8)
        self.profile_picker = QComboBox()
        self.profile_picker.setMinimumWidth(140)
        presets.addWidget(self.profile_picker, 1)
        self.profile_apply = QPushButton("Применить")
        self.profile_apply.clicked.connect(self.apply_selected_profile)
        presets.addWidget(self.profile_apply)
        self.profile_save = QPushButton("Сохранить набор")
        self.profile_save.clicked.connect(self.save_selected_profile)
        presets.addWidget(self.profile_save)
        self.profile_delete = QPushButton("Удалить")
        self.profile_delete.clicked.connect(self.remove_selected_profile)
        presets.addWidget(self.profile_delete)
        offline_layout.addLayout(presets)
        self.list_title = QLabel("Импортированные моды этого аккаунта")
        offline_layout.addWidget(self.list_title)
        self.library = QListWidget()
        self.library.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        offline_layout.addWidget(self.library, 1)
        self.rollback_button = QPushButton("Восстановить выбранный мод")
        self.rollback_button.setEnabled(False)
        self.rollback_button.clicked.connect(self.restore_selected_version)
        self.library.itemSelectionChanged.connect(self.update_rollback_control)
        offline_layout.addWidget(self.rollback_button)
        self.mod_tools_panel = ModToolsPanel(
            lambda: self.bridge.user_id,
            lambda: imported_library(self.bridge.user_id),
            self.refresh_profile_controls,
        )
        offline_layout.addWidget(self.mod_tools_panel)
        self.tabs.addTab(offline_tab, "Мои моды")

        # 2. The public catalogue retains its own search and actions.
        catalog_tab = QWidget()
        catalog_layout = QVBoxLayout(catalog_tab)
        catalog_layout.setContentsMargins(12, 14, 12, 12)
        self.catalog_note = QLabel(
            "Показываются одобренные моды. Передача модов в приложение "
            "происходит только через подтверждение на сайте."
        )
        self.catalog_note.setWordWrap(True)
        catalog_layout.addWidget(self.catalog_note)
        search_controls = QHBoxLayout()
        self.catalog_search = QLineEdit()
        self.catalog_search.setPlaceholderText("Поиск: название, описание, категория, версия")
        self.catalog_search.setClearButtonEnabled(True)
        self.catalog_search.textChanged.connect(self.render_catalog)
        search_controls.addWidget(self.catalog_search, 1)
        self.catalog_clear = QPushButton("Очистить")
        self.catalog_clear.setToolTip("Сбросить поиск без повторной загрузки каталога")
        self.catalog_clear.clicked.connect(self.catalog_search.clear)
        self.catalog_clear.setEnabled(False)
        search_controls.addWidget(self.catalog_clear)
        catalog_layout.addLayout(search_controls)
        self.catalog_count = QLabel("Каталог ещё не загружен")
        self.catalog_count.setObjectName("Subtitle")
        catalog_layout.addWidget(self.catalog_count)
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

        # 3. Diagnostics and optional file/VT checks, hidden until selected.
        diagnostics_tab = QWidget()
        diag_root = QVBoxLayout(diagnostics_tab)
        diag_root.setContentsMargins(7, 7, 7, 7)
        diagnostic_scroll = QScrollArea()
        diagnostic_scroll.setWidgetResizable(True)
        diagnostic_scroll.setFrameShape(QFrame.Shape.NoFrame)
        diag_root.addWidget(diagnostic_scroll)
        diag_body = QWidget()
        diagnostic_scroll.setWidget(diag_body)
        diagnostic_layout = QVBoxLayout(diag_body)
        diagnostic_layout.setContentsMargins(8, 8, 8, 8)
        diagnostic_layout.setSpacing(10)
        diagnostic_layout.addWidget(QLabel("Диагностика программы"))
        diagnostic_description = QLabel(
            "Проверка настроек, папок модов, обновлений и привязки аккаунта. "
            "Личные файлы не отправляются."
        )
        diagnostic_description.setWordWrap(True)
        diagnostic_layout.addWidget(diagnostic_description)
        self.diagnostic_output = QPlainTextEdit()
        self.diagnostic_output.setReadOnly(True)
        self.diagnostic_output.setMaximumHeight(130)
        self.diagnostic_output.setPlaceholderText("D001–D009: проверка не выполнена.")
        diagnostic_layout.addWidget(self.diagnostic_output)
        diagnostic_actions = QHBoxLayout()
        self.diagnostic_scan = QPushButton("Запустить диагностику")
        self.diagnostic_scan.clicked.connect(self.run_diagnostics)
        diagnostic_actions.addWidget(self.diagnostic_scan)
        self.diagnostic_copy = QPushButton("Копировать результат")
        self.diagnostic_copy.clicked.connect(self.copy_diagnostics)
        diagnostic_actions.addWidget(self.diagnostic_copy)
        self.diagnostic_repair = QPushButton("Исправить безопасные проблемы")
        self.diagnostic_repair.clicked.connect(self.repair_diagnostic_folders)
        diagnostic_actions.addWidget(self.diagnostic_repair)
        diagnostic_layout.addLayout(diagnostic_actions)
        self.trust_panel = TrustPanel()
        diagnostic_layout.addWidget(self.trust_panel)
        self.security_panel = SecurityPanel()
        diagnostic_layout.addWidget(self.security_panel)
        diagnostic_layout.addStretch(1)
        self.tabs.addTab(diagnostics_tab, "Диагностика и безопасность")

        self.bridge = DesktopSync(self)
        self.bridge.status_changed.connect(self._on_sync_status)
        self.bridge.account_changed.connect(self.on_account)
        self.bridge.files_changed.connect(self.on_import)
        self.bridge.catalog_changed.connect(self.on_catalog)
        self.bridge.notifications_changed.connect(self.on_account_notifications)
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.bridge.stop)
        self.refresh_library()
        self.refresh_profile_controls()
        self._refresh_account_actions()
        self._refresh_offline_controls()
        self.profile_picker.currentIndexChanged.connect(
            lambda _: self.profile_delete.setEnabled(
                bool(self.bridge.user_id and self.profile_picker.currentData())
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_header_grid"):
            compact = self.width() < 810
            if compact != self._compact_header:
                self._compact_header = compact
                self._header_grid.removeWidget(self._account_card)
                self._header_grid.removeWidget(self._updates_card)
                self._header_grid.addWidget(self._account_card, 0, 0)
                self._header_grid.addWidget(
                    self._updates_card, 1 if compact else 0,
                    0 if compact else 1
                )
                self._header_grid.setColumnStretch(1, 0 if compact else 1)

    def set_offline_mode(self, checked):
        try:
            set_offline(bool(checked))
            self._refresh_offline_controls()
        except (OSError, ValueError):
            QMessageBox.warning(self, "WT Offline Mode",
                                "Не удалось сохранить настройку офлайн-режима.")
            self.offline_switch.blockSignals(True)
            self.offline_switch.setChecked(is_offline())
            self.offline_switch.blockSignals(False)

    def _refresh_offline_controls(self):
        offline = is_offline()
        for button in (
            self.link_button, self.refresh_button, self.unlink_button,
            self.update_button, self.catalog_refresh, self.notices_refresh,
            self.catalog_open, self.community_open
        ):
            button.setEnabled(not offline)
        if offline:
            self.status.setText(
                "WT Offline Mode активен. Локальная библиотека и настройки "
                "доступны, сетевые действия приостановлены."
            )

    def _save_early_beta(self, enabled):
        try:
            set_early_access(bool(enabled))
        except (ValueError, OSError):
            self.early_beta_checkbox.blockSignals(True)
            self.early_beta_checkbox.setChecked(early_access())
            self.early_beta_checkbox.blockSignals(False)
            QMessageBox.warning(self, "Beta", "Не удалось сохранить ранний доступ.")

    def _save_channel(self, _index):
        selected = self.channel_picker.currentData()
        try:
            set_update_channel(selected)
        except (ValueError, OSError):
            QMessageBox.warning(
                self, "Канал обновлений",
                "Не удалось сохранить выбранный канал обновлений."
            )
            self.channel_picker.blockSignals(True)
            self.channel_picker.setCurrentIndex(
                0 if update_channel() == "stable" else 1
            )
            self.channel_picker.blockSignals(False)
            return
        self.update_summary.setText(
            "Канал: " + ("Stable" if selected == "stable" else "Beta") +
            ". Проверка новых релизов доступна по кнопке выше."
        )

    def _on_sync_status(self, message):
        text = str(message or "")
        if "409" in text and ("Server" in text or "HTTP" in text):
            text = (
                "Конфликт синхронизации (HTTP 409). Проверь привязку аккаунта "
                "и нажми «Синхронизировать». Локальные моды не затронуты."
            )
        self.status.setText(text[:350])

    def _refresh_account_actions(self):
        linked = bool(self.bridge.user_id)
        self.link_button.setVisible(not linked)
        self.unlink_button.setVisible(linked)
        self.refresh_button.setEnabled(linked)
        self.notices_refresh.setEnabled(linked)
        self.notices_mark_read.setEnabled(linked)

    def check_account_notifications(self):
        self.bridge.refresh_notifications()

    def mark_account_notifications_read(self):
        self.bridge.mark_notifications_read()

    def on_account_notifications(self, rows):
        notices = [x for x in rows if isinstance(x, dict)][:60]
        ids = {str(x.get("id", "")) for x in notices}
        if self._seen_account_notices is not None:
            new = [x for x in notices
                   if str(x.get("id", "")) not in self._seen_account_notices
                   and x.get("read_at") is None]
            if new:
                latest = new[0]
                self.account_new_notice.emit(
                    str(latest.get("title", "Уведомление"))[:100],
                    str(latest.get("body", ""))[:200]
                )
        self._seen_account_notices = ids
        self.remote_notifications.clear()
        for item in notices:
            mark = "● " if item.get("read_at") is None else "  "
            self.remote_notifications.addItem(
                mark + str(item.get("title") or "Сообщение")[:100] +
                " — " + str(item.get("body") or "")[:280]
            )
        if not notices:
            self.remote_notifications.addItem(
                "Нет уведомлений для этого аккаунта."
            )

    def run_diagnostics(self):
        try:
            result = format_report(inspect_local())
        except Exception:
            result = ("D000 [ERROR]: Не удалось завершить локальную диагностику.\n"
                      "Скопируй код D000 для технической поддержки.")
        self.diagnostic_output.setPlainText(result + "\n" +
                                            latest_report_summary())

    def repair_diagnostic_folders(self):
        choice = QMessageBox.question(
            self, "WT Diagnostics Pro",
            "Создать только отсутствующие папки локальной библиотеки? "
            "Программа не изменит игру, настройки и существующие файлы.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        try:
            created = repair_safe_folders()
            self.run_diagnostics()
            QMessageBox.information(
                self, "WT Diagnostics Pro",
                "Создано новых папок: " + str(len(created)) +
                ". Другие файлы не изменялись."
            )
        except OSError as error:
            QMessageBox.warning(self, "WT Diagnostics Pro", str(error))

    def copy_diagnostics(self):
        result = self.diagnostic_output.toPlainText()
        if result:
            QApplication.clipboard().setText(result)
            self.status.setText("Диагностика скопирована без личных данных.")

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
        self.install_update_button.show()
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
        self._seen_account_notices = None
        self.remote_notifications.clear()
        self.catalog_rows = []
        self.render_catalog()
        self.account_changed.emit()
        self.refresh_library()
        self.refresh_profile_controls()
        self._refresh_account_actions()

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
        # The bridge supplies the already-approved, account-scoped catalogue.
        # Filtering remains strictly local; typing does not trigger new requests.
        query = self.catalog_search.text().strip().casefold()
        self.catalog_clear.setEnabled(bool(self.catalog_search.text()))
        self.catalog_list.clear()
        labels = {
            "sights": "Прицелы", "camouflage": "Камуфляжи",
            "sounds": "Звуки", "visuals": "Графика",
            "interface": "Интерфейс", "other": "Другое"
        }
        valid_total = 0
        matches = 0
        for row in self.catalog_rows:
            ident = str(row.get("id") or "")
            if not UUID.fullmatch(ident):
                continue
            if row.get("status") not in (None, "approved"):
                continue
            valid_total += 1
            title = str(row.get("title") or "")[:90]
            category = labels.get(row.get("category"), "Мод")
            version = str(row.get("version") or "")[:32]
            description = str(row.get("description") or "")[:400]
            if query and query not in (
                title + " " + category + " " + description + " " + version
            ).casefold():
                continue
            item = QListWidgetItem(category + " • " + title + " • v" + version)
            item.setData(Qt.ItemDataRole.UserRole, ident)
            self.catalog_list.addItem(item)
            matches += 1
        self.catalog_count.setText(
            f"Найдено: {matches} из {valid_total}" if query
            else f"Модов в каталоге: {valid_total}"
        )
        if matches == 0:
            self.catalog_list.addItem(
                "Поиск не дал результатов — очисти запрос" if query
                else "Нет опубликованных модов"
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
        target = (DATA_DIR / "accounts" / self.bridge.user_id / "mods"
                  if self.bridge.user_id else DATA_DIR / "mods")
        target.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def disconnect_account(self):
        if is_offline():
            QMessageBox.information(
                self, "WT Offline Mode",
                "Чтобы безопасно отключить устройство от сервера, "
                "сначала выключи офлайн-режим и повтори действие."
            )
            return
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
