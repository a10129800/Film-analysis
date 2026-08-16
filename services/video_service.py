import subprocess
from pathlib import Path


class VideoService:

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent

        self.base_dir = Path(base_dir)

    def get_ffmpeg_path(self):
        candidates = [
            self.base_dir / "ffmpeg" / "ffmpeg.exe",
            Path.cwd() / "ffmpeg" / "ffmpeg.exe",
        ]

        for path in candidates:
            if path.exists():
                return path

        return None

    def get_ffprobe_path(self):
        candidates = [
            self.base_dir / "ffmpeg" / "ffprobe.exe",
            Path.cwd() / "ffmpeg" / "ffprobe.exe",
        ]

        for path in candidates:
            if path.exists():
                return path

        return None

    def generate_thumbnail(
        self,
        video_path,
        time_ms,
        output_file
    ):
        ffmpeg = self.get_ffmpeg_path()

        if ffmpeg is None:
            raise FileNotFoundError(
                "找不到 FFmpeg：ffmpeg\\ffmpeg.exe"
            )

        video_path = Path(video_path)
        output_file = Path(output_file)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        seconds = time_ms / 1000

        command = [
            str(ffmpeg),
            "-y",
            "-ss",
            str(seconds),
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-vf",
            "scale=320:-2",
            "-q:v",
            "3",
            str(output_file),
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            error_text = result.stderr.decode(
                "utf-8",
                errors="replace"
            )

            raise RuntimeError(
                "FFmpeg 產生縮圖失敗：\n"
                + error_text
            )

        if not output_file.exists():
            raise RuntimeError(
                "FFmpeg 執行完成，但沒有產生縮圖。"
            )

        return output_file
