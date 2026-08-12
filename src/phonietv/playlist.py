import logging
import queue
import threading
import time

from .event import PhonieTVEvent
from .threading import PhonieTVTask


LOGGER = logging.getLogger(__name__)

class PlaylistTask(PhonieTVTask):
    def __init__(self, task_name: str, stop_event):
        super().__init__(task_name, stop_event)


    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                if event_to_process.event_type == "token_detected":
                    LOGGER.info(f"Token detected: {event_to_process.data}")
                    # Handle play_media event
                    self.publish_event(PhonieTVEvent("play_media", event_to_process.data))
                    pass
                elif event_to_process.event_type == "media_finished":
                    LOGGER.info(f"Media finished playing.")
                    # Handle stop_media event
                    pass

            except queue.Empty:
                pass

            time.sleep(0.1)