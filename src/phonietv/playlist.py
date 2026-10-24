import logging
import os
import queue
import threading
import time
import json
from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Callable

from .current_media_item_per_dir import (
    DEFAULT_CURRENT_MEDIA_ITEM_PER_DIR_PATH,
    get_media_items_from_directory,
    load_current_media_item_per_dir,
    save_current_media_item_per_dir,
)
from .event import PhonieTVEvent
from .threading import PhonieTVTask

LOGGER = logging.getLogger(__name__)
DEFAULT_MEDIA_LAYOUT_PATH = Path("media_layout.toml")
DEFAULT_MEDIA_URL_MAPPING = {
    "Grinch": "/mnt/video/movies/kids_movies/Dr Seuss The Grinch.mp4",
    "Paw Patrol": "/mnt/video/movies/kids_movies/Paw Patrol",
    "Raa Raa": "/mnt/video/tv/Raa Raa",
    "Thomas": "/mnt/video/tv/Thomas",
}


def save_media_url_mapping(
    media_url_mapping: dict[str, str],
    path: Path | str = DEFAULT_MEDIA_LAYOUT_PATH,
) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    serialized_lines = ["[tokens]"]
    for token_name, media_path in sorted(media_url_mapping.items()):
        serialized_lines.append(f"{json.dumps(token_name)} = {json.dumps(media_path)}")
    file_path.write_text("\n".join(serialized_lines) + "\n", encoding="utf-8")


def load_media_url_mapping(
    path: Path | str = DEFAULT_MEDIA_LAYOUT_PATH,
) -> dict[str, str]:
    file_path = Path(path)
    if not file_path.exists():
        save_media_url_mapping(DEFAULT_MEDIA_URL_MAPPING, file_path)

    with file_path.open("rb") as handle:
        data = tomllib.load(handle)

    tokens = data.get("tokens", data)
    if not isinstance(tokens, dict):
        raise ValueError("media layout file must contain a [tokens] table or a top-level mapping")

    media_url_mapping: dict[str, str] = {}
    for token_name, media_path in tokens.items():
        if not isinstance(token_name, str) or not isinstance(media_path, str):
            raise ValueError("media layout file token mappings must be strings")
        media_url_mapping[token_name] = media_path

    return media_url_mapping


@dataclass(frozen=True)
class PlayMediaPayload:
    token_name: str
    media_path: str


class PlaylistTask(PhonieTVTask):
    def __init__(
        self,
        task_name: str,
        stop_event,
        current_media_item_per_dir_path: Path | str = DEFAULT_CURRENT_MEDIA_ITEM_PER_DIR_PATH,
        media_layout_path: Path | str = DEFAULT_MEDIA_LAYOUT_PATH,
    ):
        super().__init__(task_name, stop_event)
        self.current_media_item_per_dir_path = Path(current_media_item_per_dir_path)
        self.media_layout_path = Path(media_layout_path)
        self.current_media_item_per_dir = load_current_media_item_per_dir(self.current_media_item_per_dir_path)
        self.media_url_mapping = load_media_url_mapping(self.media_layout_path)

    def _reload_media_url_mapping(self) -> dict[str, str]:
        try:
            self.media_url_mapping = load_media_url_mapping(self.media_layout_path)
        except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
            LOGGER.error("Unable to load media layout from %s: %s", self.media_layout_path, exc)
        return self.media_url_mapping

    def _persist_current_media_item_per_dir(self) -> None:
        save_current_media_item_per_dir(self.current_media_item_per_dir, self.current_media_item_per_dir_path)

    def _select_directory_media(self, directory: str, reference_item: str | None, advance: bool) -> str | None:
        media_files = get_media_items_from_directory(directory)
        if not media_files:
            LOGGER.info("No media files found in directory: %s", directory)
            return None

        media_items = [os.path.relpath(path, directory) for path in media_files]
        if reference_item is not None and reference_item in media_items:
            reference_index = media_items.index(reference_item)
            if advance:
                next_index = (reference_index + 1) % len(media_files)
            else:
                next_index = reference_index
        else:
            next_index = 0

        selected_media = media_files[next_index]
        self.current_media_item_per_dir[directory] = media_items[next_index]
        self._persist_current_media_item_per_dir()
        return selected_media

    def _publish_play_media(self, token_name: str, media_path: str) -> None:
        self.publish_event(
            PhonieTVEvent(
                "play_media",
                PlayMediaPayload(token_name=token_name, media_path=media_path),
            )
        )

    def _on_token_detected(self, event: PhonieTVEvent) -> None:
        LOGGER.info("Token detected: %s", event.event_payload)
        if not isinstance(event.event_payload, str):
            LOGGER.error("Invalid token_detected payload: %r", event.event_payload)
            return

        token_name = event.event_payload
        media_url = self._reload_media_url_mapping().get(token_name)
        if media_url is None:
            LOGGER.error("No media URL found for token: %s", token_name)
            return

        if os.path.isdir(media_url):
            selected_media = self._select_directory_media(
                media_url,
                reference_item=self.current_media_item_per_dir.get(media_url),
                advance=False,
            )
            if selected_media is not None:
                self._publish_play_media(token_name=token_name, media_path=selected_media)
            return

        self._publish_play_media(token_name=token_name, media_path=media_url)

    def _on_media_finished(self, event: PhonieTVEvent) -> None:
        LOGGER.info("Media finished playing.")
        token_name = getattr(event.event_payload, "token_name", None)
        media_path = getattr(event.event_payload, "media_path", None)
        if not isinstance(token_name, str) or not isinstance(media_path, str):
            LOGGER.error("Invalid media_finished payload: %r", event.event_payload)
            return

        media_url = self._reload_media_url_mapping().get(token_name)
        if media_url is None or not os.path.isdir(media_url):
            return

        reference_item = os.path.relpath(os.path.abspath(media_path), os.path.abspath(media_url))
        selected_media = self._select_directory_media(
            directory=media_url,
            reference_item=reference_item,
            advance=True,
        )
        if selected_media is not None:
            self._publish_play_media(token_name=token_name, media_path=selected_media)

    def task_function(self, stop_event: threading.Event):
        event_handlers: dict[str, Callable[[PhonieTVEvent], None]] = {
            "token_detected": self._on_token_detected,
            "media_finished": self._on_media_finished,
        }
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                handler = event_handlers.get(event_to_process.event_type)
                if handler is not None:
                    handler(event_to_process)

            except queue.Empty:
                pass

            time.sleep(0.1)
