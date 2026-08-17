from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.time import format_time


class ShotPanel(QWidget):
    """View component for selecting and annotating shots."""

    shot_selected = Signal(int)
    add_requested = Signal()
    delete_requested = Signal()
    shot_size_changed = Signal(str)
    note_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🎞️ SHOT"))

        self.shot_list = QListWidget()
        self.shot_list.currentRowChanged.connect(self.shot_selected)
        layout.addWidget(self.shot_list, 1)

        buttons = QHBoxLayout()
        self.add_shot_button = QPushButton("✂️ 目前時間新增")
        self.add_shot_button.clicked.connect(self.add_requested)
        buttons.addWidget(self.add_shot_button)

        self.delete_shot_button = QPushButton("🗑️ 刪除")
        self.delete_shot_button.clicked.connect(self.delete_requested)
        buttons.addWidget(self.delete_shot_button)
        layout.addLayout(buttons)

        self.shot_label = QLabel("尚未選擇 SHOT")
        layout.addWidget(self.shot_label)

        layout.addWidget(QLabel(" 景別"))
        sizes = ["大特寫", "特寫", "中景", "全景", "大全景"]
        self.shot_size_buttons = []
        size_layout = QHBoxLayout()
        for text in sizes:
            button = QPushButton(text)
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, value=text: self.shot_size_changed.emit(value)
            )
            self.shot_size_buttons.append(button)
            size_layout.addWidget(button)
        layout.addLayout(size_layout)

        self.note_editor = QTextEdit()
        self.note_editor.setPlaceholderText("在這裡寫你的拉片觀察……")
        self.note_editor.textChanged.connect(self.note_changed)
        layout.addWidget(self.note_editor, 1)

    def set_shots(self, shots):
        self.shot_list.blockSignals(True)
        self.shot_list.clear()

        for index, shot in enumerate(shots):
            text = f"SHOT {index + 1:03d}   {format_time(shot.time_ms)}"
            if shot.note.strip():
                text += "   📝"
            self.shot_list.addItem(QListWidgetItem(text))

        self.shot_list.blockSignals(False)

    def show_shot(self, row, shot):
        self.note_editor.blockSignals(True)
        self.note_editor.setPlainText(shot.note)
        self.note_editor.blockSignals(False)

        for button in self.shot_size_buttons:
            button.setChecked(button.text() == shot.shot_size)

        self.shot_label.setText(
            f"SHOT {row + 1:03d}   {format_time(shot.time_ms)}"
        )

    def clear_details(self):
        self.note_editor.blockSignals(True)
        self.note_editor.clear()
        self.note_editor.blockSignals(False)
        self.shot_label.setText("尚未選擇 SHOT")
        for button in self.shot_size_buttons:
            button.setChecked(False)
