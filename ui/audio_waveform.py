"""A compact real WAV waveform with direct click-to-seek interaction."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget


class AudioWaveform(QWidget):
    seek_fraction = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._peaks = None
        self._progress = 0.0
        self.setMinimumHeight(46)
        self.setMaximumHeight(70)
        self.setToolTip("Нажми на волну WAV для перемотки.")

    def set_peaks(self, peaks):
        self._peaks = list(peaks) if peaks else None
        self.update()

    def set_progress(self, progress):
        value = max(0.0, min(float(progress), 1.0))
        if abs(value - self._progress) > 0.002:
            self._progress = value
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        width = max(1, self.width() - 8)
        height = max(1, self.height() - 8)
        center = self.height() / 2
        if not self._peaks:
            painter.setPen(QPen(QColor("#566274"), 1))
            painter.drawLine(4, int(center), self.width() - 4, int(center))
            painter.setPen(QColor("#97A9C2"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "Волновая форма доступна для PCM WAV")
            return
        n = len(self._peaks)
        for index, value in enumerate(self._peaks):
            x = 4.0 + (index + 0.5) * width / n
            half = max(1.2, min(height / 2, value * height / 2))
            painter.setPen(QPen(
                QColor("#A8D8FF") if (index / n) <= self._progress
                else QColor("#4777BA"), max(1.2, width / n * 0.65)
            ))
            painter.drawLine(int(x), int(center - half), int(x), int(center + half))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._peaks:
            fraction = (event.position().x() - 4) / max(1, self.width() - 8)
            self.seek_fraction.emit(max(0.0, min(float(fraction), 1.0)))
            event.accept()
        else:
            super().mousePressEvent(event)
