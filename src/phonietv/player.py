# This file contains the media player functions
import json
import logging
import queue
import threading
import time
from pathlib import Path
from typing import Dict

from dataclasses import dataclass
import vlc

from .event import PhonieTVEvent
from .playlist import PlayMediaPayload
from .threading import PhonieTVTask

LOGGER = logging.getLogger(__name__)
PLAYER_TASK_SLEEP_TIME_S = 0.1
LOCATION_SAVE_FILE = Path("file_locations.json")


def load_location_data(location_save_file: Path | None = None) -> Dict[str, int]:
    location_save_file = location_save_file or LOCATION_SAVE_FILE

    if not location_save_file.exists():
        location_save_file.write_text("{}", encoding="utf-8")

    with location_save_file.open("r", encoding="utf-8") as location_file:
        location_data = json.load(location_file)

    if not isinstance(location_data, dict):
        raise ValueError("file_locations.json must contain a JSON object")

    return {
        str(path): int(position)
        for path, position in location_data.items()
    }


def save_location_data(location_data: Dict[str, int], location_save_file: Path | None = None) -> None:
    location_save_file = location_save_file or LOCATION_SAVE_FILE

    with location_save_file.open("w", encoding="utf-8") as location_file:
        json.dump(location_data, location_file, indent=2, sort_keys=True)


@dataclass(frozen=True)
class MediaFinishedPayload:
    token_name: str
    media_path: str

class PlayerTask(PhonieTVTask):
    def __init__(self, task_name: str, stop_event):
        super().__init__(task_name, stop_event)
        self.instance = vlc.Instance('--fullscreen')
        self.player = self.instance.media_player_new()
        self.events = self.player.event_manager()
        self.events.event_attach(vlc.EventType.MediaPlayerEndReached, self._media_finished_callback)
        self.current_media: PlayMediaPayload | None = None
        self.location_data: Dict[str, int]= load_location_data()

    def stop_player(self):
        if self.player.is_playing():
            location = self.player.get_time()
            LOGGER.info(f"Stopping media player at time: {location} ms")
            self.location_data[self.current_media.media_path] = location
            save_location_data(self.location_data)
        self.player.stop()
        self.current_media = None
        LOGGER.info("Media player stopped.")

    def _media_finished_callback(self, event):
        LOGGER.info("Media finished playing.")
        if self.current_media is None:
            return
        self.publish_event(
            PhonieTVEvent(
                "media_finished",
                MediaFinishedPayload(
                    token_name=self.current_media.token_name,
                    media_path=self.current_media.media_path,
                ),
            )
        )
        del self.location_data[self.current_media_url]
        save_location_data(self.location_data)
        self.publish_event(PhonieTVEvent("media_finished", None))

    def _save_location(self):
        if self.player.is_playing():
            current_time = self.player.get_time()
            LOGGER.info(f"Saving current media time: {current_time} ms")
            self.location_data[self.current_media.media_path] = current_time
            save_location_data(self.location_data)

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                if event_to_process.event_type == "play_media":
                    if not isinstance(event_to_process.event_payload, PlayMediaPayload):
                        LOGGER.error("Invalid play_media payload: %r", event_to_process.event_payload)
                        continue
                    self.current_media = event_to_process.event_payload
                    media = self.instance.media_new(self.current_media.media_path)
                    start_time = self.location_data.get(self.current_media.media_path, 0)
                    self.player.set_mrl(media.get_mrl())
                    self.player.play()
                    self.player.pause()  # Pause immediately to set the time before playing
                    self.player.set_time(start_time)
                    self.player.play()
                elif event_to_process.event_type == "stop_media":
                    self.stop_player()
            except queue.Empty:
                pass

            time.sleep(PLAYER_TASK_SLEEP_TIME_S)

if __name__ == "__main__":
    stop_event_in = threading.Event()
    player_task = PlayerTask("test_player", stop_event_in)
    player_task.start()
    player_task.inbound_queue.put(
        PhonieTVEvent(
            "play_media",
            PlayMediaPayload(token_name="debug", media_path=r'C:\Users\Francis\Downloads\sample-mp4-15s-11638kb.mp4'),
        )
    )
    time.sleep(2)
    player_task.inbound_queue.put(PhonieTVEvent("stop_media", None))
    time.sleep(2)
    player_task.inbound_queue.put(
        PhonieTVEvent(
            "play_media",
            PlayMediaPayload(token_name="debug", media_path=r'C:\Users\Francis\Downloads\sample-mp4-15s-11638kb.mp4'),
        )
    )
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