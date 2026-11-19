
from pathlib import Path
from src.profile_paths import MODS_DIR, online_visible_files
from ui.game_install_ui import install_sight_dialog, restore_last_game_install
import shutil

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QFrame,
)


ROOT = Path(__file__).resolve().parent.parent
SIGHTS_DIR = MODS_DIR / "sights"

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".webp",
}


class SightsPage(QWidget):
    def __init__(self):
        super().__init__()

        SIGHTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.current_file = None
        self.original_pixmap = None

        self.build_ui()
        self.load_sights()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(35, 35, 35, 35)
        root.setSpacing(18)

        # Заголовок страницы
        title = QLabel("Пользовательские прицелы")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Загружай изображения прицелов, "
            "выбирай их и смотри предпросмотр."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(18)

        # =====================================
        # ЛЕВАЯ КАРТОЧКА
        # =====================================

        left_panel = QFrame()
        left_panel.setObjectName("SightLeftPanel")

        left_panel.setStyleSheet("""
            QFrame#SightLeftPanel {
                background-color: #1D2026;
                border: 1px solid #353A43;
                border-radius: 14px;
            }

            QFrame#SightLeftPanel QLabel {
                background-color: transparent;
                border: none;
            }
        """)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(
            16, 16, 16, 16
        )
        left_layout.setSpacing(12)

        list_title = QLabel("Список прицелов")
        list_title.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E9EDF3;
            font-size: 14px;
            font-weight: 600;
        """)

        self.sight_list = QListWidget()

        self.sight_list.setStyleSheet("""
            QListWidget {
                background-color: #15171B;
                border: 1px solid #353A43;
                border-radius: 10px;
                padding: 6px;
                outline: none;
            }

            QListWidget::item {
                padding: 9px;
                border-radius: 6px;
                color: #E9EDF3;
            }

            QListWidget::item:selected {
                background-color: #365F9C;
                color: white;
            }

            QListWidget::item:hover:!selected {
                background-color: #2C313A;
            }
        """)

        self.sight_list.itemSelectionChanged.connect(
            self.on_selection_changed
        )

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)

        add_button = QPushButton("Добавить")
        add_button.setObjectName("Primary")
        add_button.clicked.connect(self.add_sight)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_sights)

        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.delete_selected)

        buttons_row.addWidget(add_button)
        buttons_row.addWidget(refresh_button)
        buttons_row.addWidget(delete_button)

        left_layout.addWidget(list_title)
        left_layout.addWidget(self.sight_list, 1)
        left_layout.addLayout(buttons_row)
        game_button = QPushButton("Установить игровой .blk")
        game_button.setToolTip("PNG — только предпросмотр; для игры нужен .blk. Ctrl+клик — ручной выбор папки.")
        game_button.clicked.connect(lambda: install_sight_dialog(self))
        restore_button = QPushButton("Откатить установку в игре")
        restore_button.clicked.connect(lambda: restore_last_game_install(self))
        left_layout.addWidget(game_button)
        left_layout.addWidget(restore_button)

        # =====================================
        # ПРАВАЯ КАРТОЧКА
        # =====================================

        right_panel = QFrame()
        right_panel.setObjectName("SightRightPanel")

        right_panel.setStyleSheet("""
            QFrame#SightRightPanel {
                background-color: #1D2026;
                border: 1px solid #353A43;
                border-radius: 14px;
            }

            QFrame#SightRightPanel QLabel {
                background-color: transparent;
                border: none;
            }
        """)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(
            16, 16, 16, 16
        )
        right_layout.setSpacing(12)

        preview_title = QLabel("Предпросмотр")
        preview_title.setStyleSheet("""
            background-color: transparent;
            border: none;
            color: #E9EDF3;
            font-size: 14px;
            font-weight: 600;
        """)

        self.preview_name = QLabel("Файл не выбран")
        self.preview_name.setObjectName("Subtitle")
        self.preview_name.setWordWrap(True)

        self.preview_box = QLabel(
            "Здесь будет предпросмотр прицела"
        )

        self.preview_box.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.preview_box.setMinimumSize(
            260, 220
        )

        self.preview_box.setStyleSheet("""
            QLabel {
                background-color: #111317;
                border: 1px solid #353A43;
                border-radius: 14px;
                color: #7E8795;
                font-size: 13px;
                padding: 10px;
            }
        """)

        self.current_label = QLabel(
            "Текущий выбранный прицел: нет"
        )
        self.current_label.setObjectName("Subtitle")
        self.current_label.setWordWrap(True)

        self.file_info = QLabel("")
        self.file_info.setObjectName("Subtitle")
        self.file_info.setWordWrap(True)

        right_layout.addWidget(preview_title)
        right_layout.addWidget(self.preview_name)
        right_layout.addWidget(
            self.preview_box, 1
        )
        right_layout.addWidget(self.file_info)
        right_layout.addWidget(self.current_label)

        content.addWidget(left_panel, 1)
        content.addWidget(right_panel, 2)

        root.addLayout(content, 1)

    # =====================================
    # ЗАГРУЗКА СПИСКА ПРИЦЕЛОВ
    # =====================================

    def load_sights(self):
        old_name = (
            self.current_file.name
            if self.current_file else None
        )

        self.sight_list.blockSignals(True)
        self.sight_list.clear()

        image_files = sorted(
            [
                file_path
                for file_path in (list(SIGHTS_DIR.iterdir()) + online_visible_files("sights"))
                if file_path.is_file()
                and file_path.suffix.lower()
                in IMAGE_EXTENSIONS
            ],
            key=lambda file_path:
                file_path.name.lower()
        )

        for file_path in image_files:
            item = QListWidgetItem(
                file_path.name
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                str(file_path)
            )

            self.sight_list.addItem(item)

        self.sight_list.blockSignals(False)

        if old_name:
            self.select_file(old_name)

            if self.sight_list.selectedItems():
                return

        self.clear_preview()

        if not image_files:
            self.preview_box.setText(
                "Папка mods/sights пуста"
            )

            self.preview_name.setText(
                "Нет доступных прицелов"
            )

    # =====================================
    # ОЧИСТКА ПРЕДПРОСМОТРА
    # =====================================

    def clear_preview(self):
        self.current_file = None
        self.original_pixmap = None

        self.preview_box.clear()

        self.preview_box.setText(
            "Здесь будет предпросмотр прицела"
        )

        self.preview_name.setText(
            "Файл не выбран"
        )

        self.current_label.setText(
            "Текущий выбранный прицел: нет"
        )

        self.file_info.setText("")

    # =====================================
    # ВЫБОР ПРИЦЕЛА
    # =====================================

    def on_selection_changed(self):
        selected = self.sight_list.selectedItems()

        if not selected:
            return

        item = selected[0]

        file_path = Path(
            item.data(
                Qt.ItemDataRole.UserRole
            )
        )

        self.current_file = file_path

        self.preview_name.setText(
            file_path.name
        )

        self.current_label.setText(
            f"Текущий выбранный прицел: "
            f"{file_path.name}"
        )

        self.show_preview(file_path)

    # =====================================
    # ПРЕДПРОСМОТР ИЗОБРАЖЕНИЯ
    # =====================================

    def show_preview(self, file_path: Path):
        pixmap = QPixmap(
            str(file_path)
        )

        if pixmap.isNull():
            self.original_pixmap = None
            self.preview_box.clear()

            self.preview_box.setText(
                "Не удалось загрузить изображение"
            )

            self.file_info.setText(
                "Неподдерживаемый или повреждённый файл"
            )

            return

        self.original_pixmap = pixmap

        width = pixmap.width()
        height = pixmap.height()

        size_kb = (
            file_path.stat().st_size / 1024
        )

        self.file_info.setText(
            f"Разрешение: {width} × {height} px"
            f"  |  Размер: {size_kb:.1f} KB"
        )

        self.update_preview()

    # =====================================
    # МАСШТАБИРОВАНИЕ ИЗОБРАЖЕНИЯ
    # =====================================

    def update_preview(self):
        if self.original_pixmap is None:
            return

        available = (
            self.preview_box.contentsRect().size()
        )

        if (
            available.width() <= 0
            or available.height() <= 0
        ):
            return

        scaled = self.original_pixmap.scaled(
            available,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.preview_box.setPixmap(
            scaled
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.update_preview()

    # =====================================
    # ДОБАВЛЕНИЕ ПРИЦЕЛА
    # =====================================

    def add_sight(self):
        file_path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Выбрать изображение прицела",
                "",
                "Images (*.png *.jpg *.jpeg "
                "*.bmp *.webp)"
            )
        )

        if not file_path:
            return

        source = Path(file_path)
        target = SIGHTS_DIR / source.name

        # Проверяем изображение
        test_pixmap = QPixmap(
            str(source)
        )

        if test_pixmap.isNull():
            QMessageBox.warning(
                self,
                "Ошибка",
                "Файл не является "
                "поддерживаемым изображением."
            )
            return

        try:
            # Если файл уже в папке mods/sights,
            # повторное копирование не требуется.
            if (
                source.resolve()
                != target.resolve()
            ):
                if target.exists():
                    answer = QMessageBox.question(
                        self,
                        "Замена файла",
                        f"Прицел {target.name} "
                        "уже существует.\n"
                        "Заменить его?"
                    )

                    if (
                        answer
                        != QMessageBox.StandardButton.Yes
                    ):
                        return

                shutil.copy2(
                    source,
                    target
                )

            self.current_file = target

            self.load_sights()
            self.select_file(target.name)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось добавить файл:\n"
                f"{error}"
            )

    # =====================================
    # УДАЛЕНИЕ ПРИЦЕЛА
    # =====================================

    def delete_selected(self):
        selected = (
            self.sight_list.selectedItems()
        )

        if not selected:
            QMessageBox.information(
                self,
                "Удаление",
                "Сначала выбери прицел из списка."
            )
            return

        item = selected[0]

        file_path = Path(
            item.data(
                Qt.ItemDataRole.UserRole
            )
        )

        answer = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить прицел {file_path.name} "
            "из библиотеки менеджера?"
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            if file_path.exists():
                file_path.unlink()

            self.current_file = None

            self.load_sights()
            self.clear_preview()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось удалить файл:\n"
                f"{error}"
            )

    # =====================================
    # ВЫБОР ФАЙЛА ПО ИМЕНИ
    # =====================================

    def select_file(self, filename: str):
        for index in range(
            self.sight_list.count()
        ):
            item = self.sight_list.item(
                index
            )

            if item.text() == filename:
                self.sight_list.setCurrentItem(
                    item
                )
                break
