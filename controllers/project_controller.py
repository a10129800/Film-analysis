from pathlib import Path

from core.project_state import ProjectState
from services.obsidian_service import ObsidianService
from services.project_service import ProjectService


class ProjectController:
    """Coordinates project persistence without depending on Qt widgets."""

    def __init__(self, project_service=None, obsidian_service=None):
        self.project_service = project_service or ProjectService()
        self.obsidian_service = obsidian_service or ObsidianService()

    def new_project(self):
        return ProjectState()

    def open_video(self, video_path):
        return ProjectState(video_path=str(video_path))

    def load_project(self, project_path):
        data = self.project_service.load(project_path)
        state = ProjectState(
            video_path=data["video_path"],
            shots=data["shots"],
        )

        if state.shots and state.shots[0].thumbnail:
            state.thumbnail_dir = Path(state.shots[0].thumbnail).parent

        return state, data["interval_seconds"]

    def save_project(self, state, interval_seconds, save_path):
        return self.project_service.save(
            state.video_path,
            interval_seconds,
            state.shots,
            save_path,
        )

    def export_obsidian(self, state, output_path):
        return self.obsidian_service.export_markdown(
            state.video_path,
            state.shots,
            output_path,
        )
