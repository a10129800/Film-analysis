from core.project import save_project, load_project
from core.shot import Shot


class ProjectService:

    def save(
        self,
        video_path,
        interval_seconds,
        shots,
        save_path
    ):
        return save_project(
            video_path,
            interval_seconds,
            shots,
            save_path
        )

    def load(self, load_path):

        data = load_project(
            load_path
        )

        shots = [
            Shot.from_dict(item)
            for item in data.get(
                "shots",
                []
            )
        ]

        return {
            "video_path": data.get(
                "video_path",
                ""
            ),
            "interval_seconds": int(
                data.get(
                    "interval_seconds",
                    3
                )
            ),
            "shots": shots
        }
