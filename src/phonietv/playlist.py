import logging
import queue
import threading
import time

from .event import PhonieTVEvent
from .threading import PhonieTVTask

LOGGER = logging.getLogger(__name__)


class PlaylistTask(PhonieTVTask):
    MEDIA_URL_MAPPING = {"Grinch": "/mnt/video/movies/kids_movies/Dr Seuss The Grinch.mp4",
                         "Paw Patrol": "/mnt/video/movies/kids_movies/Paw Patrol The Movie.mp4"}

    def __init__(self, task_name: str, stop_event):
        super().__init__(task_name, stop_event)

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                if event_to_process.event_type == "token_detected":
                    LOGGER.info(f"Token detected: {event_to_process.event_payload}")
                    token_name = event_to_process.event_payload
                    media_url = self.MEDIA_URL_MAPPING.get(token_name)
                    if media_url is not None:
                        self.publish_event(PhonieTVEvent("play_media", media_url))
                    else:
                        LOGGER.error(f"No media URL found for token: {token_name}")
                    pass
                elif event_to_process.event_type == "media_finished":
                    LOGGER.info(f"Media finished playing.")
                    # Handle stop_media event
                    pass

            except queue.Empty:
                pass

            time.sleep(0.1)
