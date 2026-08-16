import json
from pathlib import Path


def save_project(
    video_path,
    interval_seconds,
    shots,
    save_path
):
    data = {
        "version": 12,
        "video_path": video_path,
        "interval_seconds": interval_seconds,
        "shots": [
            shot.to_dict()
            for shot in shots
        ],
    }

    save_path = Path(save_path)

    save_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    if not save_path.exists():
        raise RuntimeError(
            "write_text 執行完成，但找不到輸出的檔案。"
        )


def load_project(load_path):
    load_path = Path(load_path)

    data = json.loads(
        load_path.read_text(
            encoding="utf-8"
        )
    )

    return data
