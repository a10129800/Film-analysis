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
