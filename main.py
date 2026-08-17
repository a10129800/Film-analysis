import sys
import cv2
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap, QShortcut, QKeySequence, QImage
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSpinBox,
    QSplitter,
    QMessageBox,
    QFileDialog,
    QProgressDialog,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink, QVideoFrame

from services.video_service import VideoService
from services.thumbnail_service import ThumbnailService
from services.shot_service import ShotService
from core.time import format_time
from core.project_state import ProjectState
from controllers.playback_controller import PlaybackController
from controllers.project_controller import ProjectController
from widgets.thumbnail_timeline import ThumbnailTimeline
from widgets.shot_panel import ShotPanel
from widgets.video_panel import VideoPanel


APP_NAME = "🎬 拉片助手 v1.2"


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

        self.project_state = ProjectState()

        self.video_service = VideoService()

        self.thumbnail_service = ThumbnailService(
            self.video_service
        )

        self.shot_service = ShotService()
        self.project_controller = ProjectController()

        self.build_ui()

        self.setup_player()

        self.setup_shortcuts()

    @property
    def video_path(self):
        return self.project_state.video_path

    @video_path.setter
    def video_path(self, value):
        self.project_state.video_path = value

    @property
    def duration_ms(self):
        return self.project_state.duration_ms

    @duration_ms.setter
    def duration_ms(self, value):
        self.project_state.duration_ms = value

    @property
    def shots(self):
        return self.project_state.shots

    @shots.setter
    def shots(self, value):
        self.project_state.shots = value

    @property
    def current_shot_index(self):
        return self.project_state.current_shot_index

    @current_shot_index.setter
    def current_shot_index(self, value):
        self.project_state.current_shot_index = value

    @property
    def thumbnail_dir(self):
        return self.project_state.thumbnail_dir

    @thumbnail_dir.setter
    def thumbnail_dir(self, value):
        self.project_state.thumbnail_dir = value

    # =========================================================
    # 鍵盤快捷鍵
    # =========================================================

    def setup_shortcuts(self):

        self.shortcut_play = QShortcut(
            QKeySequence("Space"),
            self
        )

        self.shortcut_play.activated.connect(
            self.toggle_play
        )

        self.shortcut_back = QShortcut(
            QKeySequence("Left"),
            self
        )

        self.shortcut_back.activated.connect(
            lambda: self.seek_relative(-1000)
        )

        self.shortcut_forward = QShortcut(
            QKeySequence("Right"),
            self
        )

        self.shortcut_forward.activated.connect(
            lambda: self.seek_relative(1000)
        )
        self.shortcut_back_5 = QShortcut(
            QKeySequence("Shift+Left"),
            self
        )

        self.shortcut_back_5.activated.connect(
            lambda: self.seek_relative(-5000)
        )

        self.shortcut_forward_5 = QShortcut(
            QKeySequence("Shift+Right"),
            self
        )

        self.shortcut_forward_5.activated.connect(
            lambda: self.seek_relative(5000)
        )



        self.shortcut_j = QShortcut(
            QKeySequence("J"),
            self
        )

        self.shortcut_j.activated.connect(
            self.play_backward
        )

        self.shortcut_k = QShortcut(
            QKeySequence("K"),
            self
        )

        self.shortcut_k.activated.connect(
            self.toggle_play
        )

        self.shortcut_l = QShortcut(
            QKeySequence("L"),
            self
        )

        self.shortcut_l.activated.connect(
            self.play_forward
        )
    # =========================================================
    # 影片相對移動
    # =========================================================

    def play_backward(self):
        self.playback_controller.play_backward()

        self.statusBar().showMessage(
            "J：倒播 " + str(self.playback_controller.forward_speed)
        )

    def play_forward(self):
        self.playback_controller.play_forward()

        self.video_panel.set_playing(True)

        self.statusBar().showMessage(
            f"播放速度：{self.playback_controller.forward_speed:g}"
        )

    def increase_playback_speed(self):
        self.playback_controller.increase_playback_speed()

        self.statusBar().showMessage(
            f"播放速度：{self.playback_controller.forward_speed:g}"
        )

    def seek_relative(self, offset_ms):
        self.playback_controller.seek_relative(offset_ms)

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

        self.video_panel = VideoPanel()
        self.video_panel.play_requested.connect(self.toggle_play)
        self.video_panel.seek_requested.connect(self.seek_video)

        upper_splitter.addWidget(
            self.video_panel
        )

        # -----------------------------------------------------
        # SHOT 清單
        # -----------------------------------------------------

        self.shot_panel = ShotPanel()
        self.shot_panel.shot_selected.connect(self.select_shot)
        self.shot_panel.add_requested.connect(self.add_current_shot)
        self.shot_panel.delete_requested.connect(self.delete_current_shot)
        self.shot_panel.shot_size_changed.connect(self.set_shot_size)
        self.shot_panel.note_changed.connect(self.note_changed)

        # Temporary aliases keep the controller code focused on application state.
        self.shot_list = self.shot_panel.shot_list
        self.note_editor = self.shot_panel.note_editor
        self.shot_label = self.shot_panel.shot_label
        self.shot_size_buttons = self.shot_panel.shot_size_buttons

        upper_splitter.addWidget(
            self.shot_panel
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

        self.thumbnail_timeline = ThumbnailTimeline()
        self.thumbnail_timeline.shot_selected.connect(self.thumbnail_clicked)
        self.thumbnail_count_label = self.thumbnail_timeline.count_label

        splitter.addWidget(self.thumbnail_timeline)

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
            self.video_panel.video_widget
        )

        self.video_sink = (
            self.video_panel.video_widget.videoSink()
        )

        self.video_sink.videoFrameChanged.connect(
            self.video_frame_changed
        )

        self.player.positionChanged.connect(
            self.position_changed
        )

        self.player.durationChanged.connect(
            self.duration_changed
        )

        self.playback_controller = PlaybackController(
            self.player,
            lambda: self.duration_ms,
        )

        self.video_panel.speed_changed.connect(
            self.playback_controller.set_playback_speed
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

            self.project_state = self.project_controller.open_video(path)

            self.shot_panel.clear_details()

            self.player.setSource(

                QUrl.fromLocalFile(
                    self.video_path
                )

            )

            self.video_panel.set_video_name(Path(self.video_path).name)

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

                self.shot_service.add_shot(
                    self.shots,
                    time_ms,
                    thumbnail=str(output_file)
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
        self.thumbnail_timeline.clear()

    def refresh_thumbnail_timeline(self):
        self.thumbnail_timeline.set_shots(self.shots)

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
        self.shot_panel.set_shots(self.shots)

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

        self.shot_panel.show_shot(row, shot)

    # =========================================================
    # 景別
    # =========================================================

    def set_shot_size(self, value):

        index = self.current_shot_index

        if index < 0:
            return

        if index >= len(self.shots):
            return

        self.shot_service.update_shot_size(
            self.shots,
            index,
            value
        )

        self.shot_panel.show_shot(index, self.shots[index])

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

        self.shot_service.update_note(
            self.shots,
            index,
            self.note_editor.toPlainText()
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

        self.shot_service.add_shot(
            self.shots,
            current_time
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

        self.shot_service.delete_shot(
            self.shots,
            row
        )

        self.current_shot_index = -1




        self.shot_panel.clear_details()

        self.refresh_shot_list()

        self.refresh_thumbnail_timeline()

    # =========================================================
    # 播放
    # =========================================================

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_J:

            if not event.isAutoRepeat():

                if self.playback_controller.reverse_timer.isActive():

                    self.playback_controller.reverse_timer.stop()

                    self.video_panel.hide_preview()

                else:

                    self.play_backward()

            event.accept()
            return

        if event.key() == Qt.Key_L:

            if not event.isAutoRepeat():

                if self.playback_controller.forward_timer.isActive():

                    self.playback_controller.forward_timer.stop()

                else:

                    self.play_forward()

            event.accept()
            return

        if event.key() == Qt.Key_K:

            if not event.isAutoRepeat():

                self.playback_controller.reverse_timer.stop()
                self.playback_controller.forward_timer.stop()

                self.player.pause()

                self.video_panel.set_playing(False)

                self.statusBar().showMessage(
                    "已停止播放"
                )

            event.accept()
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):

        if event.key() == Qt.Key_J:

            event.accept()
            return

        if event.key() == Qt.Key_L:

            event.accept()
            return

        super().keyReleaseEvent(event)
    def show_preview_frame(self, frame):

        if frame is None:
            return

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        height, width, channels = frame.shape

        image = QImage(
            frame.data,
            width,
            height,
            channels * width,
            QImage.Format_RGB888
        ).copy()

        pixmap = QPixmap.fromImage(
            image
        )

        self.video_panel.show_preview(pixmap)
    def video_frame_changed(self, frame):


        if frame.isValid():

            self.video_panel.refresh_video_frame()

    def toggle_play(self):

        if self.playback_controller.reverse_timer.isActive():

            self.playback_controller.reverse_timer.stop()

            self.player.pause()

            self.video_panel.set_playing(False)

            return

        if self.playback_controller.forward_timer.isActive():

            self.playback_controller.forward_timer.stop()

            self.player.pause()

            self.video_panel.set_playing(False)

            return

        if (
            self.player.playbackState()
            == QMediaPlayer.PlayingState
        ):

            self.player.pause()

            self.video_panel.set_playing(False)

        else:

            self.player.play()

            self.video_panel.set_playing(True)

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

        self.video_panel.set_position(position, self.duration_ms)

    def duration_changed(
        self,
        duration
    ):

        self.duration_ms = duration

        self.video_panel.set_duration(duration)

        self.position_changed(
            self.player.position()
        )

    # =========================================================
    # 新專案
    # =========================================================

    def new_project(self):

        self.playback_controller.stop()

        self.project_state = self.project_controller.new_project()

        self.player.stop()

        self.player.setSource(
            QUrl()
        )

        self.shot_panel.set_shots([])
        self.shot_panel.clear_details()

        self.clear_thumbnail_widgets()

        self.video_panel.reset()

        self.thumbnail_count_label.setText(
            "尚未產生縮圖"
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

            self.project_controller.save_project(
                self.project_state,
                self.interval_spin.value(),
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

            state, interval_seconds = self.project_controller.load_project(path)
            video_path = state.video_path

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

            self.project_state = state

            self.interval_spin.setValue(interval_seconds)

            self.player.setSource(

                QUrl.fromLocalFile(
                    self.video_path
                )

            )

            self.video_panel.set_video_name(Path(self.video_path).name)

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

        try:

            self.project_controller.export_obsidian(self.project_state, path)

        except Exception as error:

            QMessageBox.critical(
                self,
                APP_NAME,
                "Obsidian Markdown 匯出失敗：\n\n"
                + repr(error)
            )

            return

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








































































































