from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.time import format_time


class ThumbnailButton(QPushButton):

    def __init__(self, shot_index, shot, parent=None):
        super().__init__(parent)

        self.setFixedSize(190, 145)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(
            f"SHOT {shot_index + 1:03d}\n"
            f"{format_time(shot.time_ms)}"
        )


class ThumbnailTimeline(QWidget):
    """Horizontally scrollable thumbnails that notify their selected shot."""

    shot_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel("🖼️ 縮圖時間軸"))

        self.count_label = QLabel("尚未產生縮圖")
        header.addWidget(self.count_label)
        header.addStretch()
        layout.addLayout(header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.container = QWidget()
        self.thumbnail_layout = QHBoxLayout(self.container)
        self.thumbnail_layout.setAlignment(Qt.AlignLeft)
        self.thumbnail_layout.setSpacing(12)

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area, 1)

    def set_shots(self, shots):
        self.clear()

        for index, shot in enumerate(shots):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(2, 2, 2, 2)

            button = ThumbnailButton(index, shot)
            button.clicked.connect(
                lambda checked=False, i=index: self.shot_selected.emit(i)
            )
            self._set_thumbnail(button, shot.thumbnail)
            layout.addWidget(button)

            time_label = QLabel(
                f"SHOT {index + 1:03d}\n{format_time(shot.time_ms)}"
            )
            time_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(time_label)

            self.thumbnail_layout.addWidget(container)

        self.set_count(len(shots))

    def clear(self):
        while self.thumbnail_layout.count() > 0:
            item = self.thumbnail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def set_count(self, count):
        self.count_label.setText(
            f"{count} 張縮圖" if count else "尚未產生縮圖"
        )

    @staticmethod
    def _set_thumbnail(button, thumbnail_path):
        if not thumbnail_path or not Path(thumbnail_path).exists():
            return

        pixmap = QPixmap(thumbnail_path)
        if pixmap.isNull():
            return

        button.setIcon(
            pixmap.scaled(
                180,
                105,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        button.setIconSize(QSize(180, 105))
