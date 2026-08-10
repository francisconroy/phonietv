import logging
import queue
from enum import Enum, auto
from queue import Queue

from phonietv.event import PhonieTVEvent
from phonietv.statemachine import PhonieTVState, StateMachine


class PhonieTVStateId(Enum):
    IDLE = auto()
    ACTIVE = auto()
    PLAYING = auto()
    PLAYLIST = auto()
    LOCKOUT = auto()


LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.DEBUG)
    LOGGER.info("Hello from phonietv!")

    ## This app uses Queues to communicate events
    main_queue = Queue()

    # Set up the modules and connect them together as needed

    # All synchronisation between tasks happens in this main thread, so that the tasks can run independently and not block each other

    def enter_idle_state(_):
        LOGGER.info("Entering idle state")
        main_queue.put(PhonieTVEvent("token_detected", "abcd"))

    def enter_lockout_state(_):
        LOGGER.info("Entering lockout state")

    def enter_playlist_state(_):
        main_queue.put(PhonieTVEvent("play_media", None))

    lockout_state = PhonieTVState("lockout", enter_lockout_state, None, {}, None)
    idle_state = PhonieTVState("idle", enter_idle_state, None, {}, None)
    active_state = PhonieTVState("active", None, None, {}, None)
    playing_state = PhonieTVState("playing", None, None, {}, active_state)
    playlist_state = PhonieTVState("playlist", enter_playlist_state, None, {}, active_state)

    ## Register the transitions
    lockout_state.transitions.update({"lockout_timer_reset": idle_state})
    idle_state.transitions.update({"token_detected": playlist_state})
    active_state.transitions.update({"token_removed": idle_state, "lockout_timer_expired": lockout_state})
    playing_state.transitions.update({"token_detected": playlist_state, "media_finished": playlist_state})
    playlist_state.transitions.update({"play_media": playing_state, "token_detected": playlist_state})

    # State machine
    state_machine = StateMachine(idle_state)

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
