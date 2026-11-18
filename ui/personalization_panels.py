
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
)

from ui.appearance import (
    THEMES,
    FONTS,
)

from src.settings_store import (
    load_settings,
    save_settings,
)


class PersonalizationDialog(QDialog):
    """
    Two dialog modes:
        customize - colors and fonts
        language  - Russian and English
    """

    def __init__(
        self,
        parent=None,
        mode="customize",
        on_change=None,
    ):
        super().__init__(parent)

        self.mode = mode
        self.on_change = on_change

        self.setMinimumSize(390, 270)
        self.setWindowTitle("WT Mod Manager")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        self.title = QLabel()
        self.title.setObjectName("Title")
        root.addWidget(self.title)

        self.subtitle = QLabel()
        self.subtitle.setObjectName("Subtitle")
        self.subtitle.setWordWrap(True)
        root.addWidget(self.subtitle)

        self.controls = QVBoxLayout()
        self.controls.setSpacing(12)
        root.addLayout(self.controls)

        root.addStretch()

        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.accept)
        root.addWidget(self.close_button)

        self.build_controls()
        self.retranslate()

    def build_controls(self):
        settings = load_settings()

        if self.mode == "customize":
            self.theme_label = QLabel()
            self.controls.addWidget(self.theme_label)

            self.theme_combo = QComboBox()

            for key, theme in THEMES.items():
                self.theme_combo.addItem(
                    theme[0], key
                )

            index = self.theme_combo.findData(
                settings.get("theme", "blue")
            )
            self.theme_combo.setCurrentIndex(
                max(0, index)
            )

            self.controls.addWidget(self.theme_combo)

            self.font_label = QLabel()
            self.controls.addWidget(self.font_label)

            self.font_combo = QComboBox()

            for font in FONTS:
                self.font_combo.addItem(font, font)

            index = self.font_combo.findData(
                settings.get(
                    "font_family", "Segoe UI"
                )
            )
            self.font_combo.setCurrentIndex(
                max(0, index)
            )

            self.controls.addWidget(self.font_combo)

            self.theme_combo.currentIndexChanged.connect(
                lambda _:
                    self.save(
                        "theme",
                        self.theme_combo.currentData(),
                    )
            )

            self.font_combo.currentIndexChanged.connect(
                lambda _:
                    self.save(
                        "font_family",
                        self.font_combo.currentData(),
                    )
            )

        else:
            self.language_label = QLabel()
            self.controls.addWidget(self.language_label)

            self.language_combo = QComboBox()
            self.language_combo.addItem("Русский", "ru")
            self.language_combo.addItem("English", "en")

            index = self.language_combo.findData(
                settings.get("language", "ru")
            )
            self.language_combo.setCurrentIndex(
                max(0, index)
            )

            self.controls.addWidget(self.language_combo)

            self.language_combo.currentIndexChanged.connect(
                lambda _:
                    self.save(
                        "language",
                        self.language_combo.currentData(),
                    )
            )

    def save(self, key, value):
        settings = save_settings({
            key: value
        })

        if self.on_change is not None:
            self.on_change(settings)

        self.retranslate()

    def retranslate(self):
        english = (
            load_settings().get("language") == "en"
        )

        if self.mode == "customize":
            self.setWindowTitle(
                "Customization" if english
                else "Кастомизация"
            )

            self.title.setText(
                "Customization" if english
                else "Кастомизация"
            )

            self.subtitle.setText(
                "Change the accent color and font."
                if english
                else "Выберите цветовую тему и шрифт."
            )

            self.theme_label.setText(
                "Color theme" if english
                else "Цветовая тема"
            )

            self.font_label.setText(
                "Font" if english else "Шрифт"
            )

        else:
            self.setWindowTitle(
                "Language" if english
                else "Смена языка"
            )

            self.title.setText(
                "Language" if english
                else "Смена языка"
            )

            self.subtitle.setText(
                "Choose the application language."
                if english
                else "Выберите язык приложения."
            )

            self.language_label.setText(
                "Application language"
                if english
                else "Язык приложения"
            )

        self.close_button.setText(
            "Close" if english
            else "Закрыть"
        )
