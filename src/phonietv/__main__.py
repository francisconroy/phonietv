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
    entry_function: Callable[[PhonieTVEvent|None],None] | None
    exit_function: Callable[[PhonieTVEvent|None],None] | None
    transitions: Dict[str, PhonieTVStateId]
    parent_state: PhonieTVStateId | None

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
        main_queue.put_nowait(PhonieTVEvent("change_to_lockout", None))

    def enter_lockout_state(_):
        LOGGER.info("Entering lockout state")
        main_queue.put_nowait(PhonieTVEvent("ya_mum", None))


    phonie_tv_states = {PhonieTVStateId.IDLE: PhonieTVState("idle", enter_idle_state, None, {"change_to_lockout": PhonieTVStateId.LOCKOUT}, None),
                        PhonieTVStateId.PLAYING: PhonieTVState("playing", None, None, {}, None),
                                      PhonieTVStateId.PLAYLIST: PhonieTVState("playlist", None, None, {}, None),
    PhonieTVStateId.LOCKOUT: PhonieTVState("lockout", enter_lockout_state, None, {"change_to_idle": PhonieTVStateId.IDLE}, None)
                        }

    current_state = phonie_tv_states[PhonieTVStateId.IDLE]
    # Run the entry function for the initial state
    if current_state.entry_function is not None:
        current_state.entry_function(None)
    while True:
        # Process events on the queue
        try:
            event = main_queue.get_nowait()
            LOGGER.info("Processing event: %s", event.event_type)
            next_state_id = current_state.transitions.get(event.event_type)
            current_state_has_parent = current_state.parent_state is not None
            if next_state_id is None and not current_state_has_parent:
                continue
            elif next_state_id is None and current_state_has_parent:
                current_parent_state = phonie_tv_states.get(current_state.parent_state)
                next_state_id = current_parent_state.transitions.get(event.event_type)
                if next_state_id is None:
                    continue

            next_state = phonie_tv_states[next_state_id]
        except queue.Empty:
            continue

        # Handle state transitions
        ## Exiting
        LOGGER.info("Exiting state: %s", current_state.name)
        if current_state.exit_function is not None:
            current_state.exit_function()

        # Handle parent state transitions if needed
        current_has_parent = current_state.parent_state is not None
        next_has_parent = next_state.parent_state is not None
        # We only need to exit out to the same level as the next state.
        # we only support a single level of nesting for now, so we don't need to worry about multiple levels of nesting
        current_parent_state = phonie_tv_states.get(current_state.parent_state)
        next_parent = phonie_tv_states.get(next_state.parent_state)
        if current_has_parent and next_has_parent:
            if current_state.parent_state == next_state.parent_state:
                pass # Don't need to exit from parent
            else:
                current_parent_state.exit_function()
                next_parent.entry_function(event)
        elif current_has_parent:
            current_parent_state.exit_function()
        elif next_has_parent:
            next_parent.entry_function(event)

        ## Entering
        LOGGER.info("Entering state: %s", next_state.name)
        if next_state.entry_function is not None:
            next_state.entry_function(event)

        current_state = next_state

if __name__ == "__main__":
    main()
