import queue
import threading
from unittest import TestCase, mock

from phonietv.player import MediaFinishedPayload, PlayerTask
from phonietv.playlist import PlayMediaPayload


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



