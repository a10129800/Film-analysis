from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget
from PySide6.QtMultimediaWidgets import QVideoWidget

from core.time import format_time


class VideoPanel(QWidget):
    """Video display and transport controls, independent from playback logic."""

    play_requested = Signal()
    speed_changed = Signal(float)
    seek_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget, 1)

        self.preview_label = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: black;")
        self.preview_label.hide()

        controls = QHBoxLayout()
        self.play_button = QPushButton("▶ 播放")
        self.play_button.clicked.connect(self.play_requested)
        controls.addWidget(self.play_button)

        self.speed_label = QLabel("速度：")

        self.speed_combo = QComboBox()
        self.speed_combo.addItems([
            "0.5",
            "1",
            "2",
            "4",
            "8",
        ])
        self.speed_combo.setCurrentText("1")
        self.speed_combo.currentTextChanged.connect(
            lambda text: self.speed_changed.emit(float(text))
        )

        controls.addWidget(self.speed_label)
        controls.addWidget(self.speed_combo)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.seek_requested)
        controls.addWidget(self.position_slider, 1)

        self.time_label = QLabel("00:00:00.000 / 00:00:00.000")
        controls.addWidget(self.time_label)
        layout.addLayout(controls)

        self.video_name_label = QLabel("尚未開啟影片")
        layout.addWidget(self.video_name_label)

    def set_playing(self, is_playing):
        self.play_button.setText(" 暫停" if is_playing else " 播放")

    def set_position(self, position_ms, duration_ms):
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position_ms)
        self.position_slider.blockSignals(False)
        self.time_label.setText(
            f"{format_time(position_ms)} / {format_time(duration_ms)}"
        )

    def set_duration(self, duration_ms):
        self.position_slider.setRange(0, duration_ms)

    def set_video_name(self, name):
        self.video_name_label.setText(name)

    def reset(self):
        self.set_duration(0)
        self.set_position(0, 0)
        self.set_video_name("尚未開啟影片")
        self.set_playing(False)
        self.preview_label.hide()

    def show_preview(self, pixmap):
        self.preview_label.setGeometry(self.video_widget.geometry())
        self.preview_label.setPixmap(
            pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        self.preview_label.show()
        self.preview_label.raise_()
        self.preview_label.repaint()

    def hide_preview(self):
        self.preview_label.hide()
        self.video_widget.show()

    def refresh_video_frame(self):
        self.video_widget.update()



