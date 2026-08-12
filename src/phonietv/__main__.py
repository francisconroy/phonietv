import logging
import queue
import threading
from enum import Enum, auto
from queue import Queue

from .event import PhonieTVEvent
from .player import PlayerTask
from .playlist import PlaylistTask
from .pn532 import Pn532Task
from .statemachine import PhonieTVState, StateMachine
from .timer import TimerTask


class PhonieTVStateId(Enum):
    IDLE = auto()
    ACTIVE = auto()
    PLAYING = auto()
    PLAYLIST = auto()
    LOCKOUT = auto()


LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("Hello from phonietv!")

    ## This app uses Queues to communicate events
    main_queue = Queue()
    stop_event = threading.Event()

    # Set up the modules and connect them together as needed
    pn532_task = Pn532Task("pn532_task", stop_event)
    player_task = PlayerTask("player_task", stop_event)
    playlist_task = PlaylistTask("playlist_task", stop_event)
    timer_task = TimerTask("timer_task", stop_event, num_indicators=8, timer_duration_s=60 * 60)  # 1-hour timer
    tasks = [pn532_task, player_task, playlist_task, timer_task]

    # Hook up event queues
    pn532_task.attach_event_queues({main_queue})
    player_task.attach_event_queues({main_queue})
    playlist_task.attach_event_queues({main_queue})

    def enter_playlist_state(inevent: PhonieTVEvent | None):
        if inevent is not None:
            playlist_task.inbound_queue.put(inevent)

    def enter_playing_state(inevent: PhonieTVEvent | None):
        if inevent is not None:
            player_task.inbound_queue.put(inevent)

    def exit_playing_state():
        player_task.inbound_queue.put(PhonieTVEvent("stop_media", None))

    lockout_state = PhonieTVState("lockout", None, None, {}, None)
    idle_state = PhonieTVState("idle", None, None, {}, None)
    active_state = PhonieTVState("active", None, None, {}, None)
    playing_state = PhonieTVState("playing", enter_playing_state, exit_playing_state, {}, active_state)
    playlist_state = PhonieTVState("playlist", enter_playlist_state, None, {}, active_state)

    ## Register the transitions
    lockout_state.transitions.update({"lockout_timer_reset": idle_state})
    idle_state.transitions.update({"token_detected": playlist_state})
    active_state.transitions.update({"token_removed": idle_state, "lockout_timer_expired": lockout_state})
    playing_state.transitions.update({"token_detected": playlist_state, "media_finished": playlist_state})
    playlist_state.transitions.update({"play_media": playing_state, "token_detected": playlist_state})

    # State machine
    state_machine = StateMachine(idle_state)

    # Start the tasks
    for task in tasks:
        task.start()

    while True:
        # Process events on the queue
        try:
            event = main_queue.get(timeout=0.1)
            LOGGER.info("Processing event: %s", event.event_type)
            state_machine.handle_event(event)
        except queue.Empty:
            continue


if __name__ == "__main__":
    main()
