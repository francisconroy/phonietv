import logging
from dataclasses import dataclass
from typing import Dict, Callable

from .event import PhonieTVEvent

LOGGER = logging.getLogger(__name__)


@dataclass
class PhonieTVState:
    name: str
    entry_function: Callable[[PhonieTVEvent | None], None] | None
    exit_function: Callable[[PhonieTVEvent | None], None] | None
    transitions: Dict[str, PhonieTVState]
    parent_state: PhonieTVState | None


class StateMachine:
    def __init__(self, initial_state: PhonieTVState):
        if initial_state.parent_state is not None:
            initial_state.parent_state.entry_function(None)
        if initial_state.entry_function is not None:
            initial_state.entry_function(None)
        self.current_state = initial_state

    def handle_event(self, event: PhonieTVEvent):
        next_state = self.current_state.transitions.get(event.event_type)
        current_state_has_parent = self.current_state.parent_state is not None
        if next_state is None and not current_state_has_parent:
            return
        elif next_state is None and current_state_has_parent:
            current_parent_state = self.current_state.parent_state
            next_state = current_parent_state.transitions.get(event.event_type)
            if next_state is None:
                return

        LOGGER.info("Exiting state: %s", self.current_state.name)
        if self.current_state.exit_function is not None:
            self.current_state.exit_function()

        # Handle parent state transitions if needed
        current_has_parent = self.current_state.parent_state is not None
        next_has_parent = next_state.parent_state is not None
        # We only need to exit out to the same level as the next state.
        # we only support a single level of nesting for now, so we don't need to worry about multiple levels of nesting
        if current_has_parent and next_has_parent:
            if self.current_state.parent_state == next_state.parent_state:
                pass  # Don't need to exit from parent
            else:
                if self.current_state.parent_state.exit_function is not None:
                    self.current_state.parent_state.exit_function()
                next_state.parent_state.entry_function(event)
        elif current_has_parent:
            if self.current_state.parent_state.exit_function is not None:
                self.current_state.parent_state.exit_function()
        elif next_has_parent:
            LOGGER.info("Entering state: %s", next_state.parent_state.name)
            if next_state.parent_state.entry_function is not None:
                next_state.parent_state.entry_function(event)

        ## Entering
        LOGGER.info("Entering state: %s", next_state.name)
        if next_state.entry_function is not None:
            next_state.entry_function(event)

        self.current_state = next_state

    def get_state(self):
        return self.current_state
