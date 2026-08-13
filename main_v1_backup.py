import sys
import json
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QSplitter,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


APP_NAME = "🎬 拉片助手 v1"


def format_time(ms):
    """毫秒 → HH:MM:SS.mmm"""
    ms = max(0, int(ms))

    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


class Shot:
    """代表一個拉片時間點"""

    def __init__(self, time_ms, note=""):
        self.time_ms = int(time_ms)
        self.note = note

    def to_dict(self):
        return {
            "time_ms": self.time_ms,
            "note": self.note,
        }

    @staticmethod
    def from_dict(data):
        return Shot(
            data.get("time_ms", 0),
            data.get("note", ""),
        )


class ShotBreakdownAssistant(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)

        self.video_path = ""
        self.duration_ms = 0

        self.shots = []
        self.current_shot_index = -1

        self.build_ui()
        self.setup_player()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # -----------------------------------------------------
        # 上方工具列
        # -----------------------------------------------------

        toolbar = QHBoxLayout()

        self.open_button = QPushButton("🎬 開啟影片")
        self.open_button.clicked.connect(self.open_video)

        self.new_button = QPushButton("🆕 新專案")
        self.new_button.clicked.connect(self.new_project)

        self.save_button = QPushButton("💾 儲存專案")
        self.save_button.clicked.connect(self.save_project)

        self.load_button = QPushButton("📂 載入專案")
        self.load_button.clicked.connect(self.load_project)

        self.export_button = QPushButton("📤 匯出 Obsidian")
        self.export_button.clicked.connect(self.export_obsidian)

        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.new_button)
        toolbar.addWidget(self.save_button)
        toolbar.addWidget(self.load_button)
        toolbar.addWidget(self.export_button)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("取樣間隔："))

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 300)
        self.interval_spin.setValue(3)
        self.interval_spin.setSuffix(" 秒")

        toolbar.addWidget(self.interval_spin)

        self.generate_button = QPushButton("⏱️ 建立時間點")
        self.generate_button.clicked.connect(
            self.generate_shots
        )

        toolbar.addWidget(self.generate_button)

        main_layout.addLayout(toolbar)

        # -----------------------------------------------------
        # 中央區域
        # -----------------------------------------------------

        splitter = QSplitter(Qt.Horizontal)

        # =====================================================
        # 左側：影片
        # =====================================================

        video_panel = QWidget()
        video_layout = QVBoxLayout(video_panel)

        self.video_widget = QVideoWidget()

        video_layout.addWidget(
            self.video_widget,
            1
        )

        # -----------------------------------------------------
        # 播放控制
        # -----------------------------------------------------

        controls = QHBoxLayout()

        self.play_button = QPushButton("▶ 播放")
        self.play_button.clicked.connect(
            self.toggle_play
        )

        self.position_slider = QSlider(
            Qt.Horizontal
        )

        self.position_slider.setRange(
            0,
            0
        )

        self.position_slider.sliderMoved.connect(
            self.seek_video
        )

        self.time_label = QLabel(
            "00:00:00.000 / 00:00:00.000"
        )

        controls.addWidget(
            self.play_button
        )

        controls.addWidget(
            self.position_slider,
            1
        )

        controls.addWidget(
            self.time_label
        )

        video_layout.addLayout(
            controls
        )

        self.video_name_label = QLabel(
            "尚未開啟影片"
        )

        video_layout.addWidget(
            self.video_name_label
        )

        splitter.addWidget(
            video_panel
        )

        # =====================================================
        # 右側：SHOT
        # =====================================================

        shot_panel = QWidget()
        shot_layout = QVBoxLayout(shot_panel)

        shot_layout.addWidget(
            QLabel("🎞️ 拉片時間點")
        )

        self.shot_list = QListWidget()

        self.shot_list.currentRowChanged.connect(
            self.select_shot
        )

        shot_layout.addWidget(
            self.shot_list,
            1
        )

        # -----------------------------------------------------
        # SHOT 操作
        # -----------------------------------------------------

        shot_buttons = QHBoxLayout()

        self.add_shot_button = QPushButton(
            "✂️ 目前時間新增"
        )

        self.add_shot_button.clicked.connect(
            self.add_current_shot
        )

        self.delete_shot_button = QPushButton(
            "🗑️ 刪除"
        )

        self.delete_shot_button.clicked.connect(
            self.delete_current_shot
        )

        shot_buttons.addWidget(
            self.add_shot_button
        )

        shot_buttons.addWidget(
            self.delete_shot_button
        )

        shot_layout.addLayout(
            shot_buttons
        )

        # -----------------------------------------------------
        # 筆記
        # -----------------------------------------------------

        self.shot_label = QLabel(
            "尚未選擇 SHOT"
        )

        shot_layout.addWidget(
            self.shot_label
        )

        self.note_editor = QTextEdit()

        self.note_editor.setPlaceholderText(
            "在這裡寫你的拉片觀察……"
        )

        self.note_editor.textChanged.connect(
            self.note_changed
        )

        shot_layout.addWidget(
            self.note_editor,
            1
        )

        splitter.addWidget(
            shot_panel
        )

        splitter.setSizes(
            [800, 400]
        )

        main_layout.addWidget(
            splitter,
            1
        )

        self.statusBar().showMessage(
            "請先開啟影片"
        )

    # =========================================================
    # 播放器
    # =========================================================

    def setup_player(self):

        self.player = QMediaPlayer(self)

        self.audio_output = QAudioOutput(
            self
        )

        self.player.setAudioOutput(
            self.audio_output
        )

        self.player.setVideoOutput(
            self.video_widget
        )

        self.player.positionChanged.connect(
            self.position_changed
        )

        self.player.durationChanged.connect(
            self.duration_changed
        )

    # =========================================================
    # 開啟影片
    # =========================================================

    def open_video(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇影片",
            "",
            (
                "影片 (*.mp4 *.mkv *.mov *.avi "
                "*.webm *.m4v);;"
                "所有檔案 (*.*)"
            ),
        )

        if not path:
            return

        self.video_path = path

        self.player.setSource(
            QUrl.fromLocalFile(path)
        )

        self.video_name_label.setText(
            Path(path).name
        )

        self.shots.clear()

        self.refresh_shot_list()

        self.statusBar().showMessage(
            "影片已開啟"
        )

    # =========================================================
    # 建立時間點
    # =========================================================

    def generate_shots(self):

        if not self.video_path:

            QMessageBox.warning(
                self,
                APP_NAME,
                "請先開啟影片。"
            )

            return

        if self.duration_ms <= 0:

            QMessageBox.warning(
                self,
                APP_NAME,
                "影片長度尚未讀取完成。\n"
                "請稍候再按一次。"
            )

            return

        interval = (
            self.interval_spin.value()
            * 1000
        )

        self.shots = []

        current = 0

        while current <= self.duration_ms:

            self.shots.append(
                Shot(current)
            )

            current += interval

        self.refresh_shot_list()

        self.statusBar().showMessage(
            f"已建立 {len(self.shots)} 個時間點"
        )

    # =========================================================
    # 更新 SHOT 清單
    # =========================================================

    def refresh_shot_list(self):

        self.shot_list.blockSignals(
            True
        )

        self.shot_list.clear()

        for index, shot in enumerate(
            self.shots,
            start=1
        ):

            text = (
                f"SHOT {index:03d}   "
                f"{format_time(shot.time_ms)}"
            )

            if shot.note.strip():

                text += "   📝"

            item = QListWidgetItem(
                text
            )

            self.shot_list.addItem(
                item
            )

        self.shot_list.blockSignals(
            False
        )

    # =========================================================
    # 選擇 SHOT
    # =========================================================

    def select_shot(self, row):

        if row < 0:
            return

        if row >= len(self.shots):
            return

        self.current_shot_index = row

        shot = self.shots[row]

        self.player.setPosition(
            shot.time_ms
        )

        self.note_editor.blockSignals(
            True
        )

        self.note_editor.setPlainText(
            shot.note
        )

        self.note_editor.blockSignals(
            False
        )

        self.shot_label.setText(
            f"SHOT {row + 1:03d}   "
            f"{format_time(shot.time_ms)}"
        )

    # =========================================================
    # 筆記變更
    # =========================================================

    def note_changed(self):

        index = self.current_shot_index

        if index < 0:
            return

        if index >= len(self.shots):
            return

        self.shots[index].note = (
            self.note_editor.toPlainText()
        )

        self.refresh_shot_list()

        self.shot_list.setCurrentRow(
            index
        )

    # =========================================================
    # 新增目前時間
    # =========================================================

    def add_current_shot(self):

        if not self.video_path:

            QMessageBox.warning(
                self,
                APP_NAME,
                "請先開啟影片。"
            )

            return

        current_time = (
            self.player.position()
        )

        self.shots.append(
            Shot(current_time)
        )

        self.shots.sort(
            key=lambda shot:
            shot.time_ms
        )

        self.refresh_shot_list()

        for i, shot in enumerate(
            self.shots
        ):

            if shot.time_ms == current_time:

                self.shot_list.setCurrentRow(
                    i
                )

                break

    # =========================================================
    # 刪除 SHOT
    # =========================================================

    def delete_current_shot(self):

        row = (
            self.shot_list.currentRow()
        )

        if row < 0:
            return

        self.shots.pop(row)

        self.current_shot_index = -1

        self.note_editor.clear()

        self.refresh_shot_list()

    # =========================================================
    # 播放 / 暫停
    # =========================================================

    def toggle_play(self):

        if (
            self.player.playbackState()
            == QMediaPlayer.PlayingState
        ):

            self.player.pause()

            self.play_button.setText(
                "▶ 播放"
            )

        else:

            self.player.play()

            self.play_button.setText(
                "⏸ 暫停"
            )

    # =========================================================
    # 時間軸
    # =========================================================

    def seek_video(self, position):

        self.player.setPosition(
            position
        )

    def position_changed(self, position):

        self.position_slider.blockSignals(
            True
        )

        self.position_slider.setValue(
            position
        )

        self.position_slider.blockSignals(
            False
        )

        self.time_label.setText(
            f"{format_time(position)} / "
            f"{format_time(self.duration_ms)}"
        )

    def duration_changed(self, duration):

        self.duration_ms = duration

        self.position_slider.setRange(
            0,
            duration
        )

        self.position_changed(
            self.player.position()
        )

    # =========================================================
    # 新專案
    # =========================================================

    def new_project(self):

        self.video_path = ""

        self.shots.clear()

        self.current_shot_index = -1

        self.duration_ms = 0

        self.player.stop()

        self.player.setSource(
            QUrl()
        )

        self.shot_list.clear()

        self.note_editor.clear()

        self.video_name_label.setText(
            "尚未開啟影片"
        )

        self.time_label.setText(
            "00:00:00.000 / 00:00:00.000"
        )

        self.statusBar().showMessage(
            "已建立新專案"
        )

    # =========================================================
    # 儲存專案
    # =========================================================

    def save_project(self):

        if not self.video_path:

            QMessageBox.warning(
                self,
                APP_NAME,
                "請先開啟影片。"
            )

            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "儲存拉片專案",
            (
                Path(self.video_path).stem
                + ".shotproj.json"
            ),
            "拉片專案 (*.shotproj.json)",
        )

        if not path:
            return

        data = {

            "version": 1,

            "video_path":
                self.video_path,

            "interval_seconds":
                self.interval_spin.value(),

            "shots":
                [
                    shot.to_dict()
                    for shot in self.shots
                ],
        }

        Path(path).write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        self.statusBar().showMessage(
            "專案已儲存"
        )

    # =========================================================
    # 載入專案
    # =========================================================

    def load_project(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "載入拉片專案",
            "",
            "拉片專案 (*.shotproj.json)"
        )

        if not path:
            return

        try:

            data = json.loads(
                Path(path).read_text(
                    encoding="utf-8"
                )
            )

            video_path = data.get(
                "video_path",
                ""
            )

            if not Path(
                video_path
            ).exists():

                QMessageBox.warning(
                    self,
                    APP_NAME,
                    "原本的影片找不到。\n"
                    "請重新開啟影片後再使用專案。"
                )

                return

            self.video_path = video_path

            self.interval_spin.setValue(
                int(
                    data.get(
                        "interval_seconds",
                        3
                    )
                )
            )

            self.shots = [

                Shot.from_dict(item)

                for item
                in data.get(
                    "shots",
                    []
                )
            ]

            self.player.setSource(
                QUrl.fromLocalFile(
                    self.video_path
                )
            )

            self.video_name_label.setText(
                Path(
                    self.video_path
                ).name
            )

            self.refresh_shot_list()

            self.statusBar().showMessage(
                "專案已載入"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                APP_NAME,
                "載入失敗：\n\n"
                + str(error)
            )

    # =========================================================
    # Obsidian
    # =========================================================

    def export_obsidian(self):

        if not self.video_path:

            QMessageBox.warning(
                self,
                APP_NAME,
                "請先開啟影片。"
            )

            return

        if not self.shots:

            QMessageBox.warning(
                self,
                APP_NAME,
                "目前沒有 SHOT。"
            )

            return

        default_name = (
            Path(
                self.video_path
            ).stem
            + "_拉片.md"
        )

        path, _ = QFileDialog.getSaveFileName(
            self,
            "匯出 Obsidian Markdown",
            default_name,
            "Markdown (*.md)"
        )

        if not path:
            return

        title = Path(
            self.video_path
        ).stem

        lines = []

        lines.append(
            f"# {title} — 拉片"
        )

        lines.append("")

        lines.append(
            f"> 來源影片：`{Path(self.video_path).name}`"
        )

        lines.append("")

        for index, shot in enumerate(
            self.shots,
            start=1
        ):

            lines.append(
                f"## SHOT {index:03d}"
            )

            lines.append("")

            lines.append(
                f"**時間：** "
                f"{format_time(shot.time_ms)}"
            )

            lines.append("")

            lines.append(
                "### 我的觀察"
            )

            lines.append("")

            if shot.note.strip():

                lines.append(
                    shot.note.strip()
                )

            else:

                lines.append(
                    "（尚未填寫）"
                )

            lines.append("")

            lines.append("---")

            lines.append("")

        Path(path).write_text(
            "\n".join(lines),
            encoding="utf-8"
        )

        QMessageBox.information(
            self,
            APP_NAME,
            "Obsidian Markdown 匯出完成！\n\n"
            + path
        )

        self.statusBar().showMessage(
            "Obsidian Markdown 已匯出"
        )


# =============================================================
# 程式入口
# =============================================================

def main():

    app = QApplication(sys.argv)

    app.setApplicationName(
        APP_NAME
    )

    window = ShotBreakdownAssistant()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()