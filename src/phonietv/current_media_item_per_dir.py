from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CURRENT_MEDIA_ITEM_PER_DIR_PATH = Path("current_media_dir_item.json")
DEFAULT_MEDIA_FILE_EXTENSIONS = (".mp4", ".avi", ".mkv")


def get_media_items_from_directory(
    directory: Path | str,
    media_file_extensions: tuple[str, ...] = DEFAULT_MEDIA_FILE_EXTENSIONS,
) -> list[str]:
    file_list: list[str] = []
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for file_name in sorted(files):
            if file_name.lower().endswith(media_file_extensions):
                file_list.append(os.path.join(root, file_name))
    return file_list


def load_current_media_item_per_dir(path: Path | str = DEFAULT_CURRENT_MEDIA_ITEM_PER_DIR_PATH) -> dict[str, str]:
    file_path = Path(path)
    if not file_path.exists():
        return {}

    with file_path.open("r", encoding="utf-8") as handle:
        data: Any = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("current media directory item file must contain a JSON object")

    return {str(directory): str(item) for directory, item in data.items()}


def save_current_media_item_per_dir(
    current_media_item_per_dir: dict[str, str],
    path: Path | str = DEFAULT_CURRENT_MEDIA_ITEM_PER_DIR_PATH,
) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(current_media_item_per_dir, handle, indent=2, sort_keys=True)
        handle.write("\n")




