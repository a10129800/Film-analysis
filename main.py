import sys
import json
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QPixmap
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
    QScrollArea,
    QProgressDialog,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from services.video_service import VideoService
from services.thumbnail_service import ThumbnailService
from services.project_service import ProjectService


APP_NAME = "🎬 拉片助手 v1.2"


def format_time(ms):
    ms = max(0, int(ms))

    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}."
        f"{milliseconds:03d}"
    )


class Shot:

    def __init__(
        self,
        time_ms,
        note="",
        thumbnail="",
        shot_size=""
    ):
        self.time_ms = int(time_ms)
        self.note = note
        self.thumbnail = thumbnail
        self.shot_size = shot_size

    def to_dict(self):

        return {
            "time_ms": self.time_ms,
            "note": self.note,
            "thumbnail": self.thumbnail,
            "shot_size": self.shot_size,
        }

    

    @staticmethod
    def from_dict(data):

        return Shot(
            data.get("time_ms", 0),
            data.get("note", ""),
            data.get("thumbnail", ""),
            data.get("shot_size", ""),
        )


class ThumbnailButton(QPushButton):

    def __init__(
        self,
        shot_index,
        shot,
        parent=None
    ):

        super().__init__(parent)

        self.shot_index = shot_index
        self.shot = shot

        self.setFixedSize(
            190,
            145
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setToolTip(
            f"SHOT {shot_index + 1:03d}\n"
            f"{format_time(shot.time_ms)}"
        )


class ShotBreakdownAssistant(
    QMainWindow
):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            APP_NAME
        )

        self.resize(
            1400,
            850
        )

        self.video_path = ""

        self.duration_ms = 0

        self.shots = []

        self.current_shot_index = -1

        self.thumbnail_dir = None

        self.video_service = VideoService()

        self.thumbnail_service = ThumbnailService(
            self.video_service
        )

        self.project_service = ProjectService()

        self.build_ui()

        self.setup_player()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        # =====================================================
        # 工具列
        # =====================================================

        toolbar = QHBoxLayout()

        self.open_button = QPushButton(
            "🎬 開啟影片"
        )

        self.open_button.clicked.connect(
            self.open_video
        )

        self.new_button = QPushButton(
            "🆕 新專案"
        )

        self.new_button.clicked.connect(
            self.new_project
        )

        self.save_button = QPushButton(
            "💾 儲存專案"
        )

        self.save_button.clicked.connect(
            self.save_project
        )

        self.load_button = QPushButton(
            "📂 載入專案"
        )

        self.load_button.clicked.connect(
            self.load_project
        )

        self.export_button = QPushButton(
            "📤 匯出 Obsidian"
        )

        self.export_button.clicked.connect(
            self.export_obsidian
        )

        toolbar.addWidget(
            self.open_button
        )

        toolbar.addWidget(
            self.new_button
        )

        toolbar.addWidget(
            self.save_button
        )

        toolbar.addWidget(
            self.load_button
        )

        toolbar.addWidget(
            self.export_button
        )

        toolbar.addStretch()

        toolbar.addWidget(
            QLabel("縮圖間隔：")
        )

        self.interval_spin = QSpinBox()

        self.interval_spin.setRange(
            1,
            60
        )

        self.interval_spin.setValue(
            3
        )

        self.interval_spin.setSuffix(
            " 秒"
        )

        toolbar.addWidget(
            self.interval_spin
        )

        self.generate_button = QPushButton(
            "🖼️ 產生縮圖"
        )

        self.generate_button.clicked.connect(
            self.generate_thumbnails
        )

        toolbar.addWidget(
            self.generate_button
        )

        self.clear_thumbnail_button = QPushButton(
            "🗑 清除縮圖"
        )

        self.clear_thumbnail_button.clicked.connect(
            self.clear_thumbnails
        )

        toolbar.addWidget(
            self.clear_thumbnail_button
        )

        main_layout.addLayout(
            toolbar
        )

        # =====================================================
        # 中央區域
        # =====================================================

        splitter = QSplitter(
            Qt.Vertical
        )

        # =====================================================
        # 上方：影片 + SHOT
        # =====================================================

        upper_splitter = QSplitter(
            Qt.Horizontal
        )

        # -----------------------------------------------------
        # 影片
        # -----------------------------------------------------

        video_panel = QWidget()

        video_layout = QVBoxLayout(
            video_panel
        )

        self.video_widget = QVideoWidget()

        video_layout.addWidget(
            self.video_widget,
            1
        )

        controls = QHBoxLayout()

        self.play_button = QPushButton(
            "▶ 播放"
        )

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

        upper_splitter.addWidget(
            video_panel
        )

        # -----------------------------------------------------
        # SHOT 清單
        # -----------------------------------------------------

        shot_panel = QWidget()

        shot_layout = QVBoxLayout(
            shot_panel
        )

        shot_layout.addWidget(
            QLabel("🎞️ SHOT")
        )

        self.shot_list = QListWidget()

        self.shot_list.currentRowChanged.connect(
            self.select_shot
        )

        shot_layout.addWidget(
            self.shot_list,
            1
        )

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

        self.shot_label = QLabel(
            "尚未選擇 SHOT"
        )

        shot_layout.addWidget(
            self.shot_label
        )

        # =====================================================
        # v1.2：景別
        # =====================================================

        shot_layout.addWidget(
            QLabel(" 景別")
        )

        self.shot_size_buttons = []

        shot_size_layout = QHBoxLayout()

        for text in [
            "大特寫",
            "特寫",
            "中景",
            "全景",
            "大全景"
        ]:

            button = QPushButton(
                text
            )

            button.setCheckable(
                True
            )

            button.clicked.connect(
                lambda checked=False,
                value=text:
                self.set_shot_size(value)
            )

            self.shot_size_buttons.append(
                button
            )

            shot_size_layout.addWidget(
                button
            )

        shot_layout.addLayout(
            shot_size_layout
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

        upper_splitter.addWidget(
            shot_panel
        )

        upper_splitter.setSizes(
            [900, 400]
        )

        splitter.addWidget(
            upper_splitter
        )

        # =====================================================
        # 下方：縮圖時間軸
        # =====================================================

        thumbnail_panel = QWidget()

        thumbnail_layout = QVBoxLayout(
            thumbnail_panel
        )

        thumbnail_header = QHBoxLayout()

        thumbnail_header.addWidget(
            QLabel(
                "🖼️ 縮圖時間軸"
            )
        )

        self.thumbnail_count_label = QLabel(
            "尚未產生縮圖"
        )

        thumbnail_header.addWidget(
            self.thumbnail_count_label
        )

        thumbnail_header.addStretch()

        thumbnail_layout.addLayout(
            thumbnail_header
        )

        self.thumbnail_scroll = QScrollArea()

        self.thumbnail_scroll.setWidgetResizable(
            True
        )

        self.thumbnail_container = QWidget()

        self.thumbnail_layout = QHBoxLayout(
            self.thumbnail_container
        )

        self.thumbnail_layout.setAlignment(
            Qt.AlignLeft
        )

        self.thumbnail_layout.setSpacing(
            12
        )

        self.thumbnail_scroll.setWidget(
            self.thumbnail_container
        )

        thumbnail_layout.addWidget(
            self.thumbnail_scroll,
            1
        )

        splitter.addWidget(
            thumbnail_panel
        )

        splitter.setSizes(
            [560, 280]
        )

        main_layout.addWidget(
            splitter,
            1
        )

        self.statusBar().showMessage(
            "請先開啟影片"
        )

    # =========================================================
    # Player
    # =========================================================

    def setup_player(self):

        self.player = QMediaPlayer(
            self
        )

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
    # 產生縮圖
    # =========================================================

    # =========================================================
    # 開啟影片
    # =========================================================

    def open_video(self):

        path, _ = QFileDialog.getOpenFileName(

            self,

            "開啟影片",

            "",

            "影片檔案 (*.mp4 *.mov *.mkv *.avi *.wmv *.m4v)"

        )

        if not path:

            return

        try:

            self.video_path = path

            self.shots.clear()

            self.current_shot_index = -1

            self.thumbnail_dir = None

            self.note_editor.clear()

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

            self.thumbnail_count_label.setText(
                "尚未產生縮圖"
            )

            self.refresh_shot_list()

            self.refresh_thumbnail_timeline()

            self.statusBar().showMessage(
                "影片已開啟"
            )

        except Exception as error:

            QMessageBox.critical(

                self,

                APP_NAME,

                "開啟影片失敗：\n\n"
                + repr(error)

            )


    def generate_thumbnails(self):

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
                "請稍候再試。"
            )

            return

        interval = (
            self.interval_spin.value()
            * 1000
        )

        self.thumbnail_dir = (
            self.thumbnail_service.prepare_thumbnail_dir(
                self.video_path
            )
        )

        # -----------------------------------------------------
        # 清除舊資料
        # -----------------------------------------------------

        self.thumbnail_service.clear_thumbnails(
            self.thumbnail_dir
        )


        self.shots.clear()

        total = (
            self.duration_ms
            // interval
        ) + 1

        progress = QProgressDialog(
            "正在產生影片縮圖……",
            "取消",
            0,
            total,
            self
        )

        progress.setWindowTitle(
            "🎬 拉片助手"
        )

        progress.setWindowModality(
            Qt.WindowModal
        )

        progress.show()

        for index in range(total):

            if progress.wasCanceled():

                break

            time_ms = (
                index
                * interval
            )

            if time_ms > self.duration_ms:

                break

            seconds = (
                time_ms / 1000
            )

            output_file = (
                self.thumbnail_dir
                / f"{index:05d}.jpg"
            )

            try:

                self.video_service.generate_thumbnail(
                    self.video_path,
                    time_ms,
                    output_file
                )

                self.shots.append(
                    Shot(
                        time_ms,
                        thumbnail=str(
                            output_file
                        )
                    )
                )

            except Exception as error:

                progress.close()

                QMessageBox.critical(
                    self,
                    APP_NAME,
                    "FFmpeg 執行失敗：\n\n"
                    + str(error)
                )

                return


                self.shots.append(
                    Shot(
                        time_ms,
                        thumbnail=str(
                            output_file
                        )
                    )
                )

            progress.setValue(
                index + 1
            )

            QApplication.processEvents()

        progress.close()

        self.refresh_shot_list()

        self.refresh_thumbnail_timeline()

        self.thumbnail_count_label.setText(
            f"{len(self.shots)} 張縮圖"
        )

        self.statusBar().showMessage(
            f"完成：{len(self.shots)} 張縮圖"
        )

    # =========================================================
    # 縮圖時間軸
    # =========================================================

    def clear_thumbnail_widgets(self):

        while (
            self.thumbnail_layout.count()
            > 0
        ):

            item = (
                self.thumbnail_layout
                .takeAt(0)
            )

            widget = item.widget()

            if widget:

                widget.deleteLater()

    def refresh_thumbnail_timeline(self):

        self.clear_thumbnail_widgets()

        for index, shot in enumerate(
            self.shots
        ):

            container = QWidget()

            layout = QVBoxLayout(
                container
            )

            layout.setContentsMargins(
                2,
                2,
                2,
                2
            )

            button = ThumbnailButton(
                index,
                shot
            )

            button.clicked.connect(
                lambda checked=False,
                i=index:
                self.thumbnail_clicked(i)
            )

            if (
                shot.thumbnail
                and Path(
                    shot.thumbnail
                ).exists()
            ):

                pixmap = QPixmap(
                    shot.thumbnail
                )

                if not pixmap.isNull():

                    pixmap = pixmap.scaled(
                        180,
                        105,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )

                    button.setIcon(
                        pixmap
                    )

                    button.setIconSize(
                        QSize(
                            180,
                            105
                        )
                    )

            layout.addWidget(
                button
            )

            time_label = QLabel(
                f"SHOT {index + 1:03d}\n"
                f"{format_time(shot.time_ms)}"
            )

            time_label.setAlignment(
                Qt.AlignCenter
            )

            layout.addWidget(
                time_label
            )

            self.thumbnail_layout.addWidget(
                container
            )

    def thumbnail_clicked(
        self,
        index
    ):

        if index < 0:

            return

        if index >= len(
            self.shots
        ):

            return

        shot = self.shots[index]

        self.player.setPosition(
            shot.time_ms
        )

        self.shot_list.setCurrentRow(
            index
        )

        self.current_shot_index = index

    # =========================================================
    # 清除縮圖
    # =========================================================

    def clear_thumbnails(self):

        if not self.thumbnail_dir:

            self.clear_thumbnail_widgets()

            return

        if self.thumbnail_dir.exists():

            self.thumbnail_service.clear_thumbnails(
                self.thumbnail_dir
            )

        self.clear_thumbnail_widgets()

        self.thumbnail_count_label.setText(
            "尚未產生縮圖"
        )

        self.statusBar().showMessage(
            "縮圖已清除"
        )

    # =========================================================
    # SHOT 清單
    # =========================================================

    def refresh_shot_list(self):

        self.shot_list.blockSignals(
            True
        )

        self.shot_list.clear()

        for index, shot in enumerate(
            self.shots
        ):

            text = (
                f"SHOT {index + 1:03d}   "
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

        if row >= len(
            self.shots
        ):

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

        # -----------------------------------------------------
        # 更新景別按鈕
        # -----------------------------------------------------

        for button in self.shot_size_buttons:

            button.setChecked(
                button.text() == shot.shot_size
            )

        self.shot_label.setText(
            f"SHOT {row + 1:03d}   "
            f"{format_time(shot.time_ms)}"
        )

    # =========================================================
    # 景別
    # =========================================================

    def set_shot_size(self, value):

        index = self.current_shot_index

        if index < 0:
            return

        if index >= len(self.shots):
            return

        self.shots[index].shot_size = value

        for button in self.shot_size_buttons:

            button.setChecked(
                button.text() == value
            )

        self.refresh_shot_list()

        self.shot_list.setCurrentRow(
            index
        )

    # =========================================================
    # 筆記
    # =========================================================

    def note_changed(self):

        index = self.current_shot_index

        if index < 0:

            return

        if index >= len(
            self.shots
        ):

            return

        self.shots[index].note = (
            self.note_editor
            .toPlainText()
        )

        self.refresh_shot_list()

        self.shot_list.setCurrentRow(
            index
        )

    # =========================================================
    # 新增 SHOT
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
            Shot(
                current_time
            )
        )

        self.shots.sort(
            key=lambda shot:
            shot.time_ms
        )

        self.refresh_shot_list()

        self.shot_list.setCurrentRow(
            self.shots.index(
                next(
                    shot
                    for shot
                    in self.shots
                    if shot.time_ms
                    == current_time
                )
            )
        )

    # =========================================================
    # 刪除 SHOT
    # =========================================================

    def delete_current_shot(self):

        row = (
            self.shot_list.currentRow()
        )

        if row < 0:

            return

        self.shots.pop(
            row
        )

        self.current_shot_index = -1

        self.note_editor.clear()

        self.refresh_shot_list()

        self.refresh_thumbnail_timeline()

    # =========================================================
    # 播放
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

    def seek_video(
        self,
        position
    ):

        self.player.setPosition(
            position
        )

    def position_changed(
        self,
        position
    ):

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

    def duration_changed(
        self,
        duration
    ):

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

        self.thumbnail_dir = None

        self.player.stop()

        self.player.setSource(
            QUrl()
        )

        self.shot_list.clear()

        self.note_editor.clear()

        self.clear_thumbnail_widgets()

        self.video_name_label.setText(
            "尚未開啟影片"
        )

        self.thumbnail_count_label.setText(
            "尚未產生縮圖"
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
                Path(
                    self.video_path
                ).stem
                + ".shotproj.json"
            ),

            "拉片專案 (*.shotproj.json)",

        )

        if not path:

            return

        try:

            save_path = Path(path)

            self.project_service.save(
                self.video_path,
                self.interval_spin.value(),
                self.shots,
                save_path
            )

            QMessageBox.information(

                self,

                APP_NAME,

                "專案已成功儲存！\n\n"
                + str(save_path)

            )

            self.statusBar().showMessage(
                "專案已儲存"
            )

        except Exception as error:

            QMessageBox.critical(

                self,

                APP_NAME,

                "儲存專案失敗：\n\n"
                + repr(error)

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

            data = self.project_service.load(
                path
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

                    "原本的影片找不到。\n\n"
                    "請確認影片仍然存在：\n"
                    + video_path

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

                Shot.from_dict(
                    item
                )

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

            if self.shots:

                first_thumbnail = (
                    self.shots[0]
                    .thumbnail
                )

                if first_thumbnail:

                    self.thumbnail_dir = (
                        Path(
                            first_thumbnail
                        ).parent
                    )

            self.refresh_shot_list()

            self.refresh_thumbnail_timeline()

            self.thumbnail_count_label.setText(

                f"{len(self.shots)} 張縮圖"

                if self.shots

                else
                "尚未產生縮圖"

            )

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
            f"> 來源影片："
            f"`{Path(self.video_path).name}`"
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

            if shot.thumbnail:

                lines.append(
                    f"**縮圖：** "
                    f"`{Path(shot.thumbnail).name}`"
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


def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        APP_NAME
    )

    window = (
        ShotBreakdownAssistant()
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()

