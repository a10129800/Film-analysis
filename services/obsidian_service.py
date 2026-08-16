from pathlib import Path

from core.time import format_time


class ObsidianService:

    def export_markdown(
        self,
        video_path,
        shots,
        output_path
    ):

        video_path = Path(video_path)
        output_path = Path(output_path)

        title = video_path.stem

        lines = []

        lines.append(
            f"# {title}  拉片"
        )

        lines.append("")

        lines.append(
            f"> 來源影片："
            f"`{video_path.name}`"
        )

        lines.append("")

        for index, shot in enumerate(
            shots,
            start=1
        ):

            lines.append(
                f"## SHOT {index:03d}"
            )

            lines.append("")

            lines.append(
                f"**時間：** "
                f"{format_time(shot.time_ms)}"
            )

            lines.append("")

            if shot.thumbnail:

                lines.append(
                    f"**縮圖：** "
                    f"`{Path(shot.thumbnail).name}`"
                )

                lines.append("")

            lines.append(
                "### 我的觀察"
            )

            lines.append("")

            if shot.note.strip():

                lines.append(
                    shot.note.strip()
                )

            else:

                lines.append(
                    "（尚未填寫）"
                )

            lines.append("")

            lines.append("---")

            lines.append("")

        output_path.write_text(
            "\n".join(lines),
            encoding="utf-8"
        )

        return output_path
