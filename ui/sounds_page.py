
from pathlib import Path
import shutil
from src.profile_paths import MODS_DIR

from PySide6.QtCore import (
    Qt,
    QUrl,
    QPointF,
    QRectF,
    QSize
)

from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush
)

from PySide6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput
)

from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QBoxLayout,
    QSlider,
    QSizePolicy
)

from ui.icon_assets import apply_icon

from src.settings_store import (
    load_settings,
    save_settings
)


# ==========================================
# PROJECT PATHS
# ==========================================

ROOT = Path(__file__).resolve().parent.parent
SOUNDS_DIR = MODS_DIR / "sounds"

EXTENSIONS = {
    ".wav",
    ".mp3",
    ".ogg",
    ".flac"
}

SOUNDS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# DESIGN
# ==========================================

SOUND_STYLE = """
QFrame#SoundCard {
    background-color: #1D2026;
    border: 1px solid #353A43;
    border-radius: 14px;
}

QFrame#SoundCard QLabel {
    background-color: transparent;
    border: none;
}

QFrame#PlayerSurface {
    background-color: #13161B;
    border: 1px solid #353A43;
    border-radius: 12px;
}

QFrame#PlayerSurface QLabel {
    background-color: transparent;
    border: none;
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
    color: #E7EBF2;
}

QListWidget::item:selected {
    background-color: #365F9C;
    color: #FFFFFF;
}

QListWidget::item:hover:!selected {
    background-color: #303640;
}

QPushButton#SoundPrimary {
    background-color: #365F9C;
    border: 1px solid #4777BA;
    border-radius: 9px;
    color: white;
    padding: 10px 13px;
    font-weight: 600;
}

QPushButton#SoundPrimary:hover {
    background-color: #4675B5;
}

QPushButton#SoundSecondary {
    background-color: #292E36;
    border: 1px solid #3A424D;
    border-radius: 9px;
    color: #E7EBF2;
    padding: 10px 13px;
}

QPushButton#SoundSecondary:hover {
    background-color: #343C47;
}
"""


# ==========================================
# HELPERS
# ==========================================

def format_time(milliseconds):
    """
    Converts milliseconds into MM:SS.
    """

    seconds = max(
        0,
        int(milliseconds) // 1000
    )

    minutes, seconds = divmod(
        seconds,
        60
    )

    return f"{minutes:02d}:{seconds:02d}"


def format_file_size(size_bytes):
    """
    Returns a readable file size.
    """

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"

    return (
        f"{size_bytes / (1024 * 1024):.2f} MB"
    )


# ==========================================
# CUSTOM PROCEDURAL SLIDER
# ==========================================

class RoundedSlider(QSlider):
    """
    Custom painted slider.

    Features:
    - Rounded track
    - Rounded progress
    - Smooth circular handle
    - Correct endpoints
    - Mouse dragging
    - Keyboard support
    """

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

        self.setMinimumHeight(30)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        self.track_height = 7
        self.handle_radius = 9

        self.track_color = QColor("#303742")
        self.progress_color = QColor("#4777BA")
        self.handle_color = QColor("#E5EDF8")

        self._dragging = False

    def sizeHint(self):
        return QSize(180, 30)

    def _slider_geometry(self):
        radius = self.handle_radius

        left = radius + 2
        right = max(
            left,
            self.width() - radius - 2
        )

        center_y = self.height() / 2

        return left, right, center_y

    def _handle_position(self):
        left, right, center_y = (
            self._slider_geometry()
        )

        minimum = self.minimum()
        maximum = self.maximum()

        if maximum <= minimum:
            ratio = 0.0
        else:
            ratio = (
                (self.value() - minimum)
                / (maximum - minimum)
            )

        x = left + (right - left) * ratio

        return x, center_y

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        left, right, cy = (
            self._slider_geometry()
        )

        radius = self.track_height / 2

        track = QRectF(
            left,
            cy - radius,
            max(0, right - left),
            self.track_height
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            QBrush(self.track_color)
        )

        painter.drawRoundedRect(
            track,
            radius,
            radius
        )

        hx, hy = self._handle_position()

        progress_width = max(
            0,
            hx - left
        )

        if progress_width > 0:
            progress = QRectF(
                left,
                cy - radius,
                progress_width,
                self.track_height
            )

            painter.setBrush(
                QBrush(self.progress_color)
            )

            painter.drawRoundedRect(
                progress,
                radius,
                radius
            )

        if self.isEnabled():
            handle_color = self.handle_color
        else:
            handle_color = QColor("#788394")

        painter.setBrush(
            QBrush(handle_color)
        )

        painter.setPen(
            QPen(
                QColor("#15191F"),
                1.5
            )
        )

        painter.drawEllipse(
            QPointF(hx, hy),
            self.handle_radius,
            self.handle_radius
        )

        painter.end()

    def _set_value_from_x(self, x):
        left, right, _ = (
            self._slider_geometry()
        )

        if right <= left:
            return

        ratio = (
            (x - left)
            / (right - left)
        )

        ratio = max(
            0.0,
            min(1.0, ratio)
        )

        value = (
            self.minimum()
            + ratio
            * (self.maximum() - self.minimum())
        )

        self.setValue(
            round(value)
        )

        self.update()

    def mousePressEvent(self, event):
        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):
            self._dragging = True
            self.setSliderDown(True)
            self._set_value_from_x(
                event.position().x()
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._set_value_from_x(
                event.position().x()
            )
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            event.button()
            == Qt.MouseButton.LeftButton
            and self._dragging
        ):
            self._set_value_from_x(
                event.position().x()
            )
            self._dragging = False
            self.setSliderDown(False)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.update()


# ==========================================
# SOUNDS PAGE
# ==========================================

class SoundsPage(QWidget):

    def __init__(self):
        super().__init__()

        SOUNDS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.current_file = None

        self.player = QMediaPlayer(self)

        self.audio_output = QAudioOutput(self)

        self.player.setAudioOutput(
            self.audio_output
        )

        settings = load_settings()

        self.audio_output.setVolume(
            settings["preview_volume"] / 100.0
        )

        self.build_ui()
        self.apply_transport_icons(settings)

        self.connect_player()

        self.load_sounds()

    # ======================================
    # BUILD INTERFACE
    # ======================================

    def build_ui(self):
        root = QVBoxLayout(self)

        root.setContentsMargins(
            24, 24, 24, 24
        )

        root.setSpacing(14)

        title = QLabel(
            "Звуковые модификации"
        )

        title.setObjectName("Title")

        description = QLabel(
            "Добавляйте звуковые файлы, "
            "прослушивайте их и управляйте "
            "своей библиотекой."
        )

        description.setObjectName("Subtitle")
        description.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(description)

        self.content = QBoxLayout(
            QBoxLayout.Direction.LeftToRight
        )

        self.content.setSpacing(16)

        # ==================================
        # LEFT CARD
        # ==================================

        left = QFrame()
        left.setObjectName("SoundCard")
        left.setStyleSheet(SOUND_STYLE)

        left_layout = QVBoxLayout(left)

        left_layout.setContentsMargins(
            16, 16, 16, 16
        )

        left_layout.setSpacing(12)

        list_title = QLabel(
            "Библиотека звуков"
        )

        list_title.setStyleSheet("""
            background: transparent;
            border: none;
            font-size: 15px;
            font-weight: 600;
        """)

        self.sound_list = QListWidget()

        self.sound_list.setMinimumHeight(110)

        self.sound_list.itemSelectionChanged.connect(
            self.on_selection_changed
        )

        self.sound_list.itemDoubleClicked.connect(
            lambda _: self.play_audio()
        )

        buttons = QHBoxLayout()
        buttons.setSpacing(7)

        add_button = QPushButton(
            "Добавить"
        )

        add_button.setObjectName(
            "SoundPrimary"
        )

        add_button.clicked.connect(
            self.add_sound
        )

        refresh_button = QPushButton(
            "Обновить"
        )

        refresh_button.setObjectName(
            "SoundSecondary"
        )

        refresh_button.clicked.connect(
            self.load_sounds
        )

        delete_button = QPushButton(
            "Удалить"
        )

        delete_button.setObjectName(
            "SoundSecondary"
        )

        delete_button.clicked.connect(
            self.delete_sound
        )

        for button in (
            add_button,
            refresh_button,
            delete_button
        ):
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            buttons.addWidget(button)

        left_layout.addWidget(list_title)

        left_layout.addWidget(
            self.sound_list,
            1
        )

        left_layout.addLayout(buttons)

        # ==================================
        # RIGHT CARD
        # ==================================

        right = QFrame()
        right.setObjectName("SoundCard")
        right.setStyleSheet(SOUND_STYLE)

        right_layout = QVBoxLayout(right)

        right_layout.setContentsMargins(
            18, 18, 18, 18
        )

        right_layout.setSpacing(14)

        player_title = QLabel(
            "Предпросмотр аудио"
        )

        player_title.setStyleSheet("""
            background: transparent;
            border: none;
            font-size: 15px;
            font-weight: 600;
        """)

        self.filename_label = QLabel(
            "Выберите файл для прослушивания"
        )

        self.filename_label.setWordWrap(True)

        self.filename_label.setStyleSheet("""
            color: #AEB9C9;
            background: transparent;
            border: none;
        """)

        # ==================================
        # PLAYER SURFACE
        # ==================================

        surface = QFrame()
        surface.setObjectName("PlayerSurface")
        surface.setStyleSheet(SOUND_STYLE)

        surface_layout = QVBoxLayout(surface)

        surface_layout.setContentsMargins(
            16, 16, 16, 16
        )

        surface_layout.setSpacing(10)

        self.audio_symbol = QLabel("♫")

        self.audio_symbol.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.audio_symbol.setStyleSheet("""
            font-size: 64px;
            color: #91A9CC;
            background: transparent;
            border: none;
        """)

        self.playback_status = QLabel(
            "Аудио не выбрано"
        )

        self.playback_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.playback_status.setWordWrap(True)

        self.playback_status.setStyleSheet("""
            color: #9AA5B5;
            background: transparent;
            border: none;
        """)

        surface_layout.addStretch()
        surface_layout.addWidget(
            self.audio_symbol
        )
        surface_layout.addWidget(
            self.playback_status
        )
        surface_layout.addStretch()

        # ==================================
        # SEEK SLIDER
        # ==================================

        self.seek_slider = RoundedSlider(
            Qt.Orientation.Horizontal
        )

        self.seek_slider.setRange(0, 0)

        timeline = QHBoxLayout()
        timeline.setSpacing(10)

        self.current_time = QLabel("00:00")
        self.total_time = QLabel("00:00")

        for label in (
            self.current_time,
            self.total_time
        ):
            label.setStyleSheet("""
                color: #AEB9C9;
                background: transparent;
                border: none;
            """)

        timeline.addWidget(
            self.current_time
        )

        timeline.addWidget(
            self.seek_slider,
            1
        )

        timeline.addWidget(
            self.total_time
        )

        # ==================================
        # PLAYER BUTTONS
        # ==================================

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.play_button = QPushButton(
            "▶ Играть"
        )

        self.play_button.setObjectName(
            "SoundPrimary"
        )

        self.play_button.clicked.connect(
            self.toggle_playback
        )

        self.pause_button = QPushButton(
            "Ⅱ Пауза"
        )

        self.pause_button.setObjectName(
            "SoundSecondary"
        )

        self.pause_button.clicked.connect(
            self.player.pause
        )

        self.stop_button = QPushButton(
            "■ Стоп"
        )

        self.stop_button.setObjectName(
            "SoundSecondary"
        )

        self.stop_button.clicked.connect(
            self.player.stop
        )

        for button in (
            self.play_button,
            self.pause_button,
            self.stop_button
        ):
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )
            controls.addWidget(button)

        # ==================================
        # VOLUME
        # ==================================

        volume_row = QHBoxLayout()
        volume_row.setSpacing(10)

        volume_title = QLabel(
            "Громкость"
        )

        volume_title.setStyleSheet("""
            color: #D9E0EB;
            background: transparent;
            border: none;
        """)

        self.volume_value = QLabel("70%")
        self.volume_value.setMinimumWidth(42)

        self.volume_value.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.volume_slider = RoundedSlider(
            Qt.Orientation.Horizontal
        )

        self.volume_slider.setRange(0, 100)

        self.volume_slider.setValue(
            load_settings()["preview_volume"]
        )

        self.volume_value.setText(
            f"{self.volume_slider.value()}%"
        )

        volume_row.addWidget(volume_title)
        volume_row.addWidget(
            self.volume_slider,
            1
        )
        volume_row.addWidget(
            self.volume_value
        )

        # ==================================
        # FILE INFO
        # ==================================

        self.file_info = QLabel(
            "Поддерживаемые форматы: "
            "WAV, MP3, OGG, FLAC"
        )

        self.file_info.setWordWrap(True)

        self.file_info.setStyleSheet("""
            color: #8491A3;
            font-size: 12px;
            background: transparent;
            border: none;
        """)

        # ==================================
        # ASSEMBLE RIGHT PANEL
        # ==================================

        right_layout.addWidget(
            player_title
        )

        right_layout.addWidget(
            self.filename_label
        )

        right_layout.addWidget(
            surface,
            1
        )

        right_layout.addLayout(
            timeline
        )

        right_layout.addLayout(
            controls
        )

        right_layout.addLayout(
            volume_row
        )

        right_layout.addWidget(
            self.file_info
        )

        # ==================================
        # ASSEMBLE CONTENT
        # ==================================

        self.content.addWidget(left, 4)
        self.content.addWidget(right, 6)

        root.addLayout(
            self.content,
            1
        )

        # ==================================
        # CONNECT SLIDERS
        # ==================================

        self.seek_slider.valueChanged.connect(
            self.on_seek_slider_changed
        )

        self.volume_slider.valueChanged.connect(
            self.change_volume
        )

    # ======================================
    # PLAYER SIGNALS
    # ======================================

    def connect_player(self):
        self.player.durationChanged.connect(
            self.on_duration_changed
        )

        self.player.positionChanged.connect(
            self.on_position_changed
        )

        self.player.playbackStateChanged.connect(
            self.on_state_changed
        )

        self.player.errorOccurred.connect(
            self.on_player_error
        )

    # ======================================
    # LOAD SOUND LIBRARY
    # ======================================

    def load_sounds(self):
        old_name = (
            self.current_file.name
            if self.current_file
            else None
        )

        self.sound_list.blockSignals(True)
        self.sound_list.clear()

        files = sorted(
            (
                path
                for path in SOUNDS_DIR.iterdir()
                if path.is_file()
                and path.suffix.lower()
                in EXTENSIONS
            ),
            key=lambda path:
                path.name.lower()
        )

        for path in files:
            item = QListWidgetItem(
                path.name
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                str(path)
            )

            self.sound_list.addItem(item)

        self.sound_list.blockSignals(False)

        if old_name:
            for index in range(
                self.sound_list.count()
            ):
                item = self.sound_list.item(
                    index
                )

                if item.text() == old_name:
                    self.sound_list.setCurrentItem(
                        item
                    )
                    return

        self.player.stop()

        self.player.setSource(
            QUrl()
        )

        self.current_file = None

        self.filename_label.setText(
            "Выберите файл для прослушивания"
        )

        self.playback_status.setText(
            "Аудио не выбрано"
        )

        self.file_info.setText(
            f"Найдено звуков: {len(files)}"
        )

        self.current_time.setText("00:00")
        self.total_time.setText("00:00")

        self.seek_slider.blockSignals(True)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setValue(0)
        self.seek_slider.blockSignals(False)

    # ======================================
    # FILE SELECTION
    # ======================================

    def on_selection_changed(self):
        selected = (
            self.sound_list.selectedItems()
        )

        if not selected:
            return

        path = Path(
            selected[0].data(
                Qt.ItemDataRole.UserRole
            )
        )

        if not path.exists():
            QMessageBox.warning(
                self,
                "Файл не найден",
                "Выбранный файл больше не существует."
            )
            self.load_sounds()
            return

        self.player.stop()

        self.current_file = path

        self.player.setSource(
            QUrl.fromLocalFile(
                str(path.resolve())
            )
        )

        self.filename_label.setText(
            path.name
        )

        self.playback_status.setText(
            "Готово к воспроизведению"
        )

        self.file_info.setText(
            f"Формат: {path.suffix.upper()}  |  "
            f"Размер: "
            f"{format_file_size(path.stat().st_size)}"
        )

    # ======================================
    # PLAY AUDIO
    # ======================================

    def play_audio(self):
        if self.current_file is None:
            return

        if not self.current_file.exists():
            self.playback_status.setText(
                "Аудиофайл не найден"
            )
            return

        self.player.play()

    # ======================================
    # PLAY / PAUSE TOGGLE
    # ======================================

    def toggle_playback(self):
        if self.current_file is None:
            QMessageBox.information(
                self,
                "Аудио",
                "Сначала выберите звуковой файл."
            )
            return

        state = self.player.playbackState()

        if (
            state
            == QMediaPlayer.PlaybackState.PlayingState
        ):
            self.player.pause()
        else:
            self.play_audio()

    # ======================================
    # AUDIO TRANSPORT ICONS
    # ======================================

    def apply_transport_icons(self, settings=None):
        """Use PNGs from assets/icons/White or Black, based on UI mode.

        The Play button doubles as Pause while audio is playing.
        Keep labels, keyboard behavior, tooltips, and signals unchanged.
        """
        if settings is None:
            settings = load_settings()

        playing = (
            self.player.playbackState()
            == QMediaPlayer.PlaybackState.PlayingState
        )
        apply_icon(
            self.play_button,
            "pause" if playing else "play",
            settings,
            19,
        )
        apply_icon(self.pause_button, "pause", settings, 19)
        apply_icon(self.stop_button, "stop", settings, 19)

    # ======================================
    # PLAYBACK STATE
    # ======================================

    def on_state_changed(self, state):
        # Keep the transport icon synchronized with Play/Pause state.
        self.apply_transport_icons()
        if (
            state
            == QMediaPlayer.PlaybackState.PlayingState
        ):
            self.playback_status.setText(
                "Воспроизводится"
            )

            self.play_button.setText(
                "Ⅱ Пауза"
            )

        elif (
            state
            == QMediaPlayer.PlaybackState.PausedState
        ):
            self.playback_status.setText(
                "Пауза"
            )

            self.play_button.setText(
                "▶ Продолжить"
            )

        else:
            self.play_button.setText(
                "▶ Играть"
            )

            if self.current_file:
                self.playback_status.setText(
                    "Воспроизведение остановлено"
                )

    # ======================================
    # DURATION
    # ======================================

    def on_duration_changed(self, duration):
        self.seek_slider.blockSignals(True)

        self.seek_slider.setRange(
            0,
            max(0, duration)
        )

        self.seek_slider.blockSignals(False)

        self.total_time.setText(
            format_time(duration)
        )

    # ======================================
    # POSITION
    # ======================================

    def on_position_changed(self, position):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.blockSignals(True)

            self.seek_slider.setValue(
                position
            )

            self.seek_slider.blockSignals(False)

        self.current_time.setText(
            format_time(position)
        )

    # ======================================
    # SEEK
    # ======================================

    def on_seek_slider_changed(self, position):
        if self.current_file is None:
            return

        if self.seek_slider.isSliderDown():
            self.player.setPosition(
                position
            )

            self.current_time.setText(
                format_time(position)
            )

    # ======================================
    # PLAYER ERROR
    # ======================================

    def on_player_error(self, error, message):
        if error == QMediaPlayer.Error.NoError:
            return

        self.playback_status.setText(
            "Ошибка воспроизведения"
        )

        QMessageBox.warning(
            self,
            "Ошибка аудио",
            message
            or "Не удалось воспроизвести файл."
        )

    # ======================================
    # VOLUME CHANGED
    # ======================================

    def change_volume(self, value):
        value = max(
            0,
            min(100, int(value))
        )

        self.audio_output.setVolume(
            value / 100.0
        )

        self.volume_value.setText(
            f"{value}%"
        )

        save_settings({
            "preview_volume": value
        })

    # ======================================
    # SET VOLUME FROM SETTINGS
    # ======================================

    def set_volume(self, value):
        value = max(
            0,
            min(100, int(value))
        )

        self.volume_slider.blockSignals(True)

        self.volume_slider.setValue(
            value
        )

        self.volume_slider.blockSignals(False)

        self.audio_output.setVolume(
            value / 100.0
        )

        self.volume_value.setText(
            f"{value}%"
        )

    # ======================================
    # ADD AUDIO FILE
    # ======================================

    def add_sound(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите аудиофайл",
            str(Path.home()),
            "Аудиофайлы "
            "(*.wav *.mp3 *.ogg *.flac)"
        )

        if not filename:
            return

        source = Path(filename)
        target = SOUNDS_DIR / source.name

        if not source.is_file():
            QMessageBox.warning(
                self,
                "Ошибка",
                "Исходный файл не найден."
            )
            return

        if source.suffix.lower() not in EXTENSIONS:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Неподдерживаемый формат аудио."
            )
            return

        try:
            if (
                source.resolve()
                != target.resolve()
            ):
                if target.exists():
                    answer = QMessageBox.question(
                        self,
                        "Замена файла",
                        f"Звук {target.name} уже существует.\n"
                        "Заменить его?"
                    )

                    if (
                        answer
                        != QMessageBox.StandardButton.Yes
                    ):
                        return

                if (
                    self.current_file is not None
                    and self.current_file == target
                ):
                    self.player.stop()

                    self.player.setSource(
                        QUrl()
                    )

                shutil.copy2(
                    source,
                    target
                )

            self.current_file = None
            self.load_sounds()

            for index in range(
                self.sound_list.count()
            ):
                item = self.sound_list.item(
                    index
                )

                if item.text() == target.name:
                    self.sound_list.setCurrentItem(
                        item
                    )
                    break

        except OSError as error:
            QMessageBox.critical(
                self,
                "Ошибка импорта",
                str(error)
            )

    # ======================================
    # DELETE AUDIO FILE
    # ======================================

    def delete_sound(self):
        if self.current_file is None:
            QMessageBox.information(
                self,
                "Удаление",
                "Сначала выберите звук."
            )
            return

        path = self.current_file

        answer = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить файл {path.name} "
            "из библиотеки менеджера?"
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            self.player.stop()

            self.player.setSource(
                QUrl()
            )

            if path.exists():
                path.unlink()

            self.current_file = None
            self.load_sounds()

        except OSError as error:
            QMessageBox.critical(
                self,
                "Ошибка удаления",
                str(error)
            )

    # ======================================
    # RESPONSIVE LAYOUT
    # ======================================

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not hasattr(self, "content"):
            return

        if self.width() >= 850:
            direction = (
                QBoxLayout.Direction.LeftToRight
            )
        else:
            direction = (
                QBoxLayout.Direction.TopToBottom
            )

        if self.content.direction() != direction:
            self.content.setDirection(
                direction
            )

    # ======================================
    # STOP AUDIO WHEN WINDOW CLOSES
    # ======================================

    def closeEvent(self, event):
        self.player.stop()
        super().closeEvent(event)
