import json
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from phonietv.current_media_item_per_dir import (
    get_media_items_from_directory,
    load_current_media_item_per_dir,
    save_current_media_item_per_dir,
)
from phonietv.playlist import PlaylistTask


class TestCurrentMediaItemPerDir(TestCase):
    def test_get_media_items_from_directory_returns_sorted_media_files(self):
        with TemporaryDirectory() as temp_dir:
            media_dir = Path(temp_dir) / "kids"
            media_dir.mkdir()
            (media_dir / "b.mp4").write_text("b", encoding="utf-8")
            (media_dir / "a.mkv").write_text("a", encoding="utf-8")
            (media_dir / "notes.txt").write_text("skip", encoding="utf-8")
            nested_dir = media_dir / "nested"
            nested_dir.mkdir()
            (nested_dir / "c.avi").write_text("c", encoding="utf-8")

            files = get_media_items_from_directory(str(media_dir))

            self.assertEqual(
                [
                    str(media_dir / "a.mkv"),
                    str(media_dir / "b.mp4"),
                    str(nested_dir / "c.avi"),
                ],
                files,
            )

    def test_get_media_items_from_directory_returns_empty_when_no_matches(self):
        with TemporaryDirectory() as temp_dir:
            media_dir = Path(temp_dir) / "kids"
            media_dir.mkdir()
            (media_dir / "readme.txt").write_text("skip", encoding="utf-8")

            files = get_media_items_from_directory(str(media_dir))

            self.assertEqual([], files)

    def test_load_returns_empty_mapping_when_file_is_missing(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "current_media_dir_item.json"

            self.assertEqual({}, load_current_media_item_per_dir(file_path))

    def test_save_creates_file_and_round_trips_mapping(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "current_media_dir_item.json"
            mapping = {"/media/tv": "episode-02.mp4"}

            save_current_media_item_per_dir(mapping, file_path)

            self.assertTrue(file_path.exists())
            self.assertEqual(mapping, load_current_media_item_per_dir(file_path))
            self.assertEqual(mapping, json.loads(file_path.read_text(encoding="utf-8")))

    def test_playlist_task_does_not_create_persistence_file_on_init(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "current_media_dir_item.json"
            stop_event = threading.Event()

            task = PlaylistTask("playlist_task", stop_event, current_media_item_per_dir_path=file_path)

            self.assertFalse(file_path.exists())
            self.assertEqual({}, task.current_media_item_per_dir)




