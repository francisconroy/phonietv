import json
import tempfile
from pathlib import Path
import queue
import threading
from unittest import TestCase, mock

from phonietv import player

from phonietv.player import MediaFinishedPayload, PlayerTask
from phonietv.playlist import PlayMediaPayload


class TestPlayerLocationPersistence(TestCase):
    def test_load_location_data_creates_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            save_file = Path(temp_dir) / "file_locations.json"

            location_data = player.load_location_data(save_file)

            self.assertEqual(location_data, {})
            self.assertTrue(save_file.exists())
            self.assertEqual(json.loads(save_file.read_text(encoding="utf-8")), {})

    def test_save_and_reload_location_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            save_file = Path(temp_dir) / "file_locations.json"
            expected = {"/media/video.mp4": 12345, "/media/other.mp4": 67890}

            player.save_location_data(expected, save_file)

            self.assertEqual(json.loads(save_file.read_text(encoding="utf-8")), expected)
            self.assertEqual(player.load_location_data(save_file), expected)

    def test_player_task_loads_location_data_on_init(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            save_file = Path(temp_dir) / "file_locations.json"
            save_file.write_text(json.dumps({"/media/video.mp4": 42}), encoding="utf-8")

            with mock.patch.object(player, "LOCATION_SAVE_FILE", save_file), \
                mock.patch.object(player.vlc, "Instance") as mock_instance:
                mock_media_player = mock.Mock()
                mock_event_manager = mock.Mock()
                mock_media_player.event_manager.return_value = mock_event_manager
                mock_instance.return_value.media_player_new.return_value = mock_media_player

                task = player.PlayerTask("player-test", mock.Mock())

            self.assertEqual(task.location_data, {"/media/video.mp4": 42})


class TestPlayerTask(TestCase):
    @mock.patch("phonietv.player.vlc")
    def test_media_finished_event_includes_token_and_media_path(self, vlc_mock):
        event_manager = mock.Mock()
        media_player = mock.Mock()
        media_player.event_manager.return_value = event_manager
        instance = mock.Mock()
        instance.media_player_new.return_value = media_player
        vlc_mock.Instance.return_value = instance
        vlc_mock.EventType.MediaPlayerEndReached = object()

        outbound_queue: queue.Queue = queue.Queue()
        task = PlayerTask("player_task", threading.Event())
        task.attach_event_queues({outbound_queue})
        task.current_media = PlayMediaPayload(token_name="kids", media_path="/tmp/media/episode-01.mp4")

        task._media_finished_callback(None)

        event = outbound_queue.get_nowait()
        self.assertEqual("media_finished", event.event_type)
        self.assertEqual(
            MediaFinishedPayload(token_name="kids", media_path="/tmp/media/episode-01.mp4"),
            event.event_payload,
        )


