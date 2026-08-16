from pathlib import Path


class ThumbnailService:

    def __init__(self, video_service):
        self.video_service = video_service

    def get_thumbnail_dir(self, video_path):
        video_file = Path(video_path)

        return (
            video_file.parent
            / f".shotbreakdown_{video_file.stem}"
            / "thumbnails"
        )

    def prepare_thumbnail_dir(self, video_path):
        thumbnail_dir = self.get_thumbnail_dir(
            video_path
        )

        thumbnail_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        return thumbnail_dir

    def clear_thumbnails(self, thumbnail_dir):
        thumbnail_dir = Path(thumbnail_dir)

        if not thumbnail_dir.exists():
            return

        for old_file in thumbnail_dir.glob("*.jpg"):
            try:
                old_file.unlink()
            except Exception:
                pass
