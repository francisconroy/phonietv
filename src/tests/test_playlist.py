import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from phonietv.event import PhonieTVEvent
from phonietv.player import MediaFinishedPayload
from phonietv.playlist import PlaylistTask
from phonietv.playlist import PlayMediaPayload


class TestPlaylistTask(TestCase):
    def test_directory_selection_advances_using_filename(self):
        with TemporaryDirectory() as temp_dir:
            media_dir = Path(temp_dir) / "kids"
            media_dir.mkdir()
            (media_dir / "a.mp4").write_text("a", encoding="utf-8")
            (media_dir / "b.mp4").write_text("b", encoding="utf-8")
            (media_dir / "c.mp4").write_text("c", encoding="utf-8")
            persistence_file = Path(temp_dir) / "current_media_dir_item.json"
            task = PlaylistTask("playlist_task", threading.Event(), current_media_item_per_dir_path=persistence_file)

            first_media = task._select_directory_media(str(media_dir), reference_item=None, advance=False)
            second_media = task._select_directory_media(str(media_dir), reference_item="a.mp4", advance=True)
            third_media = task._select_directory_media(str(media_dir), reference_item="b.mp4", advance=True)
            wrapped_media = task._select_directory_media(str(media_dir), reference_item="c.mp4", advance=True)

            self.assertEqual(str(media_dir / "a.mp4"), first_media)
            self.assertEqual(str(media_dir / "b.mp4"), second_media)
            self.assertEqual(str(media_dir / "c.mp4"), third_media)
            self.assertEqual(str(media_dir / "a.mp4"), wrapped_media)
            self.assertEqual({str(media_dir): "a.mp4"}, task.current_media_item_per_dir)

    def test_directory_selection_falls_back_to_first_when_saved_filename_is_missing(self):
        with TemporaryDirectory() as temp_dir:
            media_dir = Path(temp_dir) / "kids"
            media_dir.mkdir()
            (media_dir / "a.mp4").write_text("a", encoding="utf-8")
            (media_dir / "c.mp4").write_text("c", encoding="utf-8")
            persistence_file = Path(temp_dir) / "current_media_dir_item.json"
            task = PlaylistTask("playlist_task", threading.Event(), current_media_item_per_dir_path=persistence_file)
            selected_media = task._select_directory_media(str(media_dir), reference_item="b.mp4", advance=True)

            self.assertEqual(str(media_dir / "a.mp4"), selected_media)
            self.assertEqual({str(media_dir): "a.mp4"}, task.current_media_item_per_dir)

    def test_on_token_detected_publishes_structured_play_media_payload(self):
        with TemporaryDirectory() as temp_dir:
            media_dir = Path(temp_dir) / "kids"
            media_dir.mkdir()
            (media_dir / "a.mp4").write_text("a", encoding="utf-8")
            (media_dir / "b.mp4").write_text("b", encoding="utf-8")
            persistence_file = Path(temp_dir) / "current_media_dir_item.json"
            task = PlaylistTask("playlist_task", threading.Event(), current_media_item_per_dir_path=persistence_file)
            task.MEDIA_URL_MAPPING = {"kids": str(media_dir)}
            published_events: list[PhonieTVEvent] = []
            task.publish_event = published_events.append

            task._on_token_detected(PhonieTVEvent("token_detected", "kids"))

            self.assertEqual(1, len(published_events))
            play_event = published_events[0]
            self.assertEqual("play_media", play_event.event_type)
            self.assertEqual(
                PlayMediaPayload(token_name="kids", media_path=str(media_dir / "a.mp4")),
                play_event.event_payload,
            )
            self.assertEqual({str(media_dir): "a.mp4"}, task.current_media_item_per_dir)

    def test_on_media_finished_uses_token_context_and_wraps(self):
        with TemporaryDirectory() as temp_dir:
            media_dir = Path(temp_dir) / "kids"
            media_dir.mkdir()
            (media_dir / "a.mp4").write_text("a", encoding="utf-8")
            (media_dir / "b.mp4").write_text("b", encoding="utf-8")
            persistence_file = Path(temp_dir) / "current_media_dir_item.json"
            task = PlaylistTask("playlist_task", threading.Event(), current_media_item_per_dir_path=persistence_file)
            task.MEDIA_URL_MAPPING = {"kids": str(media_dir)}
            published_events: list[PhonieTVEvent] = []
            task.publish_event = published_events.append

            task._on_media_finished(
                PhonieTVEvent(
                    "media_finished",
                    MediaFinishedPayload(token_name="kids", media_path=str(media_dir / "a.mp4")),
                )
            )
            task._on_media_finished(
                PhonieTVEvent(
                    "media_finished",
                    MediaFinishedPayload(token_name="kids", media_path=str(media_dir / "b.mp4")),
                )
            )

            self.assertEqual(2, len(published_events))
            self.assertEqual(
                PlayMediaPayload(token_name="kids", media_path=str(media_dir / "b.mp4")),
                published_events[0].event_payload,
            )
            self.assertEqual(
                PlayMediaPayload(token_name="kids", media_path=str(media_dir / "a.mp4")),
                published_events[1].event_payload,
            )





