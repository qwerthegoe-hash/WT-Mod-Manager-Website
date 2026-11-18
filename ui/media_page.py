
from pathlib import Path
import shutil

from PIL import Image
from PIL.ImageQt import ImageQt

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QVBoxLayout, QHBoxLayout
)


ROOT = Path(__file__).resolve().parent.parent

EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp",
    ".webp", ".dds", ".tga"
}

CARD_STYLE = """
QFrame#MediaCard {
    background-color: #1D2026;
    border: 1px solid #353A43;
    border-radius: 14px;
}

QFrame#MediaCard QLabel {
    background: transparent;
    border: none;
}

QLabel#MediaHeading {
    color: #F0F2F6;
    font-size: 15px;
    font-weight: 600;
}

QLabel#MediaInfo {
    color: #98A2B3;
    font-size: 12px;
}

QFrame#PreviewSurface {
    background-color: #111317;
    border: 1px solid #303640;
    border-radius: 12px;
}

QFrame#PreviewSurface QLabel {
    background: transparent;
    border: none;
    color: #8290A3;
}

QListWidget {
    background-color: #14171C;
    border: 1px solid #353A43;
    border-radius: 10px;
    padding: 6px;
    outline: none;
}

QListWidget::item {
    padding: 10px;
    border-radius: 7px;
    color: #DFE4EC;
}

QListWidget::item:selected {
    background-color: #365F9C;
    color: #FFFFFF;
}

QListWidget::item:hover:!selected {
    background-color: #303640;
}
"""


class MediaPage(QWidget):
    def __init__(self, title, description, folder, item_name):
        super().__init__()

        self.folder = ROOT / "mods" / folder
        self.folder.mkdir(parents=True, exist_ok=True)

        self.item_name = item_name
        self.current_file = None
        self.original_pixmap = None

        self.build_ui(title, description)
        self.refresh_files()

    def build_ui(self, title, description):
        main = QVBoxLayout(self)
        main.setContentsMargins(28, 28, 28, 28)
        main.setSpacing(18)

        heading = QLabel(title)
        heading.setObjectName("Title")

        subtitle = QLabel(description)
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)

        main.addWidget(heading)
        main.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(18)

        # LEFT CARD
        left = QFrame()
        left.setObjectName("MediaCard")
        left.setStyleSheet(CARD_STYLE)

        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 18, 16, 16)
        left_layout.setSpacing(14)

        list_title = QLabel(f"Список: {self.item_name}")
        list_title.setObjectName("MediaHeading")

        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(
            self.on_selection_changed
        )

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        add_btn = QPushButton("Добавить")
        add_btn.setObjectName("Primary")
        add_btn.clicked.connect(self.add_file)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh_files)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_file)

        buttons.addWidget(add_btn)
        buttons.addWidget(refresh_btn)
        buttons.addWidget(delete_btn)

        left_layout.addWidget(list_title)
        left_layout.addWidget(self.file_list, 1)
        left_layout.addLayout(buttons)

        # RIGHT CARD
        right = QFrame()
        right.setObjectName("MediaCard")
        right.setStyleSheet(CARD_STYLE)

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 18, 16, 16)
        right_layout.setSpacing(14)

        preview_title = QLabel("Предпросмотр")
        preview_title.setObjectName("MediaHeading")

        self.file_name = QLabel("Файл не выбран")
        self.file_name.setObjectName("MediaInfo")
        self.file_name.setWordWrap(True)

        preview_surface = QFrame()
        preview_surface.setObjectName("PreviewSurface")

        surface_layout = QVBoxLayout(preview_surface)
        surface_layout.setContentsMargins(14, 14, 14, 14)

        self.preview_label = QLabel(
            "Выберите файл для предпросмотра"
        )
        self.preview_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.preview_label.setMinimumHeight(180)

        surface_layout.addWidget(self.preview_label)

        self.details = QLabel("Файл не выбран")
        self.details.setObjectName("MediaInfo")
        self.details.setWordWrap(True)

        right_layout.addWidget(preview_title)
        right_layout.addWidget(self.file_name)
        right_layout.addWidget(preview_surface, 1)
        right_layout.addWidget(self.details)

        content.addWidget(left, 4)
        content.addWidget(right, 6)

        main.addLayout(content, 1)

    def refresh_files(self):
        selected_name = (
            self.current_file.name
            if self.current_file else None
        )

        self.file_list.clear()

        files = sorted(
            (
                file for file in self.folder.iterdir()
                if file.is_file()
                and file.suffix.lower() in EXTENSIONS
            ),
            key=lambda file: file.name.lower()
        )

        for file in files:
            item = QListWidgetItem(file.name)
            item.setData(
                Qt.ItemDataRole.UserRole, str(file)
            )
            self.file_list.addItem(item)

        for index in range(self.file_list.count()):
            item = self.file_list.item(index)

            if item.text() == selected_name:
                self.file_list.setCurrentItem(item)
                return

        self.clear_preview()

    def clear_preview(self):
        self.current_file = None
        self.original_pixmap = None

        self.file_name.setText("Файл не выбран")
        self.details.setText("Нет выбранного файла")

        self.preview_label.clear()
        self.preview_label.setText(
            "Выберите файл для предпросмотра"
        )

    def on_selection_changed(self):
        items = self.file_list.selectedItems()

        if not items:
            self.clear_preview()
            return

        path = Path(
            items[0].data(Qt.ItemDataRole.UserRole)
        )

        self.current_file = path
        self.file_name.setText(path.name)

        try:
            with Image.open(path) as image:
                image.load()

                width, height = image.size
                rgba = image.convert("RGBA")

                qimage = ImageQt(rgba)
                self.original_pixmap = QPixmap.fromImage(
                    qimage.copy()
                )

            size_kb = path.stat().st_size / 1024

            self.details.setText(
                f"{width} × {height} px  |  "
                f"{size_kb:.1f} KB  |  "
                f"{path.suffix.upper()}"
            )

            self.update_preview()

        except Exception as error:
            self.original_pixmap = None
            self.preview_label.clear()
            self.preview_label.setText(
                "Не удалось открыть изображение"
            )
            self.details.setText(str(error))

    def update_preview(self):
        if self.original_pixmap is None:
            return

        size = self.preview_label.size()

        if size.width() < 2 or size.height() < 2:
            return

        scaled = self.original_pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()

    def add_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            str(Path.home()),
            "Изображения (*.png *.jpg *.jpeg "
            "*.bmp *.webp *.dds *.tga)"
        )

        if not filename:
            return

        source = Path(filename)
        target = self.folder / source.name

        try:
            # Проверяем, что файл можно прочитать
            with Image.open(source) as image:
                image.verify()

            if source.resolve() != target.resolve():
                if target.exists():
                    answer = QMessageBox.question(
                        self,
                        "Замена файла",
                        f"Файл {target.name} уже существует.\n"
                        "Заменить его?"
                    )

                    if answer != QMessageBox.StandardButton.Yes:
                        return

                shutil.copy2(source, target)

            self.current_file = target
            self.refresh_files()

            for index in range(self.file_list.count()):
                item = self.file_list.item(index)

                if item.text() == target.name:
                    self.file_list.setCurrentItem(item)
                    break

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка импорта",
                str(error)
            )

    def delete_file(self):
        if self.current_file is None:
            QMessageBox.information(
                self,
                "Удаление",
                "Сначала выберите файл."
            )
            return

        answer = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить {self.current_file.name} "
            "из библиотеки менеджера?"
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.current_file.unlink()
            self.refresh_files()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка удаления",
                str(error)
            )
