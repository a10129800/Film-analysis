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

        self.build_ui()

        self.setup_player()