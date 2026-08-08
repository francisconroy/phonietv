# This file contains the media player functions
import logging
import queue
import threading
import time
import vlc

from .threading import PhonieTVTask

LOGGER = logging.getLogger(__name__)
PLAYER_TASK_SLEEP_TIME_S = 0.1

class PlayerTask(PhonieTVTask):
    def __init__(self, task_name: str, stop_event):
        super().__init__(task_name, stop_event)

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                if event_to_process.event_type == "timer_set_state_event":
                    pass
            except queue.Empty:
                pass

            time.sleep(PLAYER_TASK_SLEEP_TIME_S)

    @staticmethod
    def on_finished(event):
        pass
        print("Media finished playing.")



if __name__ == "__main__":
    player = vlc.MediaPlayer()
    # player = vlc.MediaPlayer(r'C:\Users\Francis\Downloads\sample-mp4-15s-11638kb.mp4')
    instance = vlc.Instance('--no-audio', '--fullscreen')
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
    # player.play()
    # player.get_time()
    # state = player.get_state()
    #
    # time.sleep(30)
    # player.set_fullscreen(False)
    input()
    player.set_mrl(media_2.get_mrl())
    player.play()
    input()
    player.stop()
    # returns the corresponding instance
    pass