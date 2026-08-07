import logging
import queue
import time
from csv import excel
from dataclasses import dataclass
from enum import Enum, auto
from queue import Queue
from typing import Callable, Dict

from phonietv.event import PhonieTVEvent


class PhonieTVStateId(Enum):
    IDLE = auto()
    PLAYING = auto()
    PLAYLIST = auto()
    LOCKOUT = auto()

@dataclass
class PhonieTVState:
    name: str
    entry_function: Callable | None
    exit_function: Callable | None
    transitions: Dict[str, PhonieTVStateId]

LOGGER = logging.getLogger(__name__)

def main():

    logging.basicConfig(level=logging.DEBUG)
    LOGGER.info("Hello from phonietv!")

    ## This app uses Queues to communicate events
    main_queue = Queue()

    # Set up the modules and connect them together as needed

    # All synchronisation between tasks happens in this main thread, so that the tasks can run independently and not block each other

    def enter_idle_state():
        LOGGER.info("Entering idle state")
        main_queue.put_nowait(PhonieTVEvent("change_to_lockout", None))

    def enter_lockout_state():
        LOGGER.info("Entering lockout state")
        main_queue.put_nowait(PhonieTVEvent("change_to_idle", None))


    phonie_tv_states = {PhonieTVStateId.IDLE: PhonieTVState("idle", enter_idle_state, None, {"change_to_lockout": PhonieTVStateId.LOCKOUT}),
                        PhonieTVStateId.PLAYING: PhonieTVState("playing", None, None, {}),
                                      PhonieTVStateId.PLAYLIST: PhonieTVState("playlist", None, None, {}),
    PhonieTVStateId.LOCKOUT: PhonieTVState("lockout", enter_lockout_state, None, {"change_to_idle": PhonieTVStateId.IDLE})
                        }

    current_state = phonie_tv_states[PhonieTVStateId.IDLE]
    # Run the entry function for the initial state
    if current_state.entry_function is not None:
        current_state.entry_function()
    while True:
        # Process events on the queue
        try:
            event = main_queue.get_nowait()
            LOGGER.info("Processing event: %s", event.event_type)
            next_state_id = current_state.transitions[event.event_type]
            next_state = phonie_tv_states[next_state_id]
        except queue.Empty:
            continue

        # Handle state transitions
        LOGGER.info("Exiting state: %s", current_state.name)
        if current_state.exit_function is not None:
            current_state.exit_function()
        LOGGER.info("Entering state: %s", next_state.name)
        if next_state.entry_function is not None:
            next_state.entry_function()

        current_state = next_state

if __name__ == "__main__":
    main()
