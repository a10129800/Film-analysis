from pathlib import Path

from core.project import save_project, load_project


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
        return load_project(
            load_path
        )
