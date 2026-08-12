# This file contains the media player functions
import logging
import queue
import threading
import time
import vlc

from .event import PhonieTVEvent
from .threading import PhonieTVTask

LOGGER = logging.getLogger(__name__)
PLAYER_TASK_SLEEP_TIME_S = 0.1

class PlayerTask(PhonieTVTask):
    def __init__(self, task_name: str, stop_event):
        super().__init__(task_name, stop_event)
        self.instance = vlc.Instance('--fullscreen')
        self.player = self.instance.media_player_new()
        self.events = self.player.event_manager()
        self.events.event_attach(vlc.EventType.MediaPlayerEndReached, self._media_finished_callback)
        self.current_media_url: str = ""

    def stop_player(self):
        self.player.stop()
        self.current_media_url = ""
        LOGGER.info("Media player stopped.")

    def _media_finished_callback(self, event):
        LOGGER.info("Media finished playing.")
        self.publish_event(PhonieTVEvent("media_finished", None))

    def _save_location(self):
        # Save the current location of the media player
        if self.player.is_playing():
            current_time = self.player.get_time()
            LOGGER.info(f"Saving current media time: {current_time} ms")
            # TODO : Implement saving to a file or database if needed

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                if event_to_process.event_type == "play_media":
                    self.current_media_url = event_to_process.event_payload
                    media = self.instance.media_new(self.current_media_url)
                    self.player.set_mrl(media.get_mrl())
                    self.player.play()
                elif event_to_process.event_type == "stop_media":
                    self._save_location()
                    self.stop_player()
            except queue.Empty:
                pass

            time.sleep(PLAYER_TASK_SLEEP_TIME_S)

if __name__ == "__main__":
    stop_event = threading.Event()
    player_task = PlayerTask("test_player", stop_event)
    player_task.start()
    player_task.inbound_queue.put(PhonieTVEvent("play_media", r'C:\Users\Francis\Downloads\sample-mp4-15s-11638kb.mp4'))
    time.sleep(2)
    player_task.inbound_queue.put(PhonieTVEvent("stop_media", None))
    time.sleep(2)
    player_task.inbound_queue.put(PhonieTVEvent("play_media", r'C:\Users\Francis\Downloads\sample-mp4-15s-11638kb.mp4'))
    input()

    # player = vlc.MediaPlayer()
    # player = vlc.MediaPlayer(r'C:\Users\Francis\Downloads\sample-mp4-15s-11638kb.mp4')
    instance = vlc.Instance('--fullscreen')
    player = instance.media_player_new() 
    media_1 = instance.media_new(r'C:\Users\Francis\Downloads\sample-mp4-15s-11638kb.mp4')
    media_2 = instance.media_new(r'C:\Users\Francis\Downloads\Finding Nemo.mp4')
    # player.set_fullscreen(True)
    player.set_mrl(media_1.get_mrl())

    player.play()
    time.sleep(2)
    print(player.get_time())
    player.set_time(500)


    events = player.event_manager()
    events.event_attach(vlc.EventType.MediaPlayerEndReached, print)

    input()
    player.set_mrl(media_2.get_mrl())
    player.play()
    input()
    player.stop()
    # returns the corresponding instance
    pass