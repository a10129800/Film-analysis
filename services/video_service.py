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
    def open_video(self, video_path):
        import cv2

        self.close_video()

        self._reverse_cap = cv2.VideoCapture(
            str(video_path)
        )

        if not self._reverse_cap.isOpened():
            self._reverse_cap = None
            raise RuntimeError(
                "OpenCV 無法開啟影片。"
            )

        self._reverse_video_path = str(video_path)

        return self._reverse_cap


    def close_video(self):

        cap = getattr(
            self,
            "_reverse_cap",
            None
        )

        if cap is not None:
            cap.release()

        self._reverse_cap = None
        self._reverse_video_path = None


    def get_frame_at(self, video_path, time_ms):
        import cv2

        cap = getattr(
            self,
            "_reverse_cap",
            None
        )

        if (
            cap is None
            or getattr(
                self,
                "_reverse_video_path",
                None
            ) != str(video_path)
        ):
            cap = self.open_video(
                video_path
            )

        cap.set(
            cv2.CAP_PROP_POS_MSEC,
            time_ms
        )

        success, frame = cap.read()

        if not success:
            return None

        return frame

    def get_frame(
        self,
        video_path,
        time_ms
    ):
        import cv2

        cap = cv2.VideoCapture(
            str(video_path)
        )

        if not cap.isOpened():
            raise RuntimeError(
                "OpenCV 無法開啟影片。"
            )

        cap.set(
            cv2.CAP_PROP_POS_MSEC,
            time_ms
        )

        success, frame = cap.read()

        cap.release()

        if not success:
            return None

        return frame


