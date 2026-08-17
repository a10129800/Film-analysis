from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectState:
    """Mutable state belonging to the currently open shot-breakdown project."""

    video_path: str = ""
    duration_ms: int = 0
    shots: list = field(default_factory=list)
    current_shot_index: int = -1
    thumbnail_dir: Path | None = None
