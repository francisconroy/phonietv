import enum
import logging
import queue
import threading
import time
from dataclasses import dataclass

from .event import PhonieTVEvent
from .threading import PhonieTVTask
from blinkt import set_pixel, show, clear, set_brightness, NUM_PIXELS

def update_blinkt(colours: list[tuple[int, int, int]]):
    colours = colours[:NUM_PIXELS]
    clear()
    for i, status in enumerate(colours):
        set_pixel(i, *status)
    show()

LOGGER = logging.getLogger(__name__)

LEDS_TASK_SLEEP_TIME_S = 0.1

class StatusColours(enum.Enum):
    COLOUR_BLUE = (0, 0, 255)
    COLOUR_GREEN = (0, 255, 0)
    COLOUR_RED = (255, 0, 0)
    COLOUR_GREY = (128, 128, 128)
    COLOUR_OFF = (0, 0, 0)


@dataclass
class LEDIndicatorCountPayload:
    indicator_count: int
    colour: StatusColours

class SetLedIndicatorCount(PhonieTVEvent):
    def __init__(self, indicator_count: int, indicator_colour: StatusColours):
        super().__init__("set_led_indicator_count", LEDIndicatorCountPayload(indicator_count, indicator_colour))

@dataclass
class LEDIndicatorColourPayload:
    colour: StatusColours

class SetLedsToSameColour(PhonieTVEvent):
    def __init__(self, indicator_colour: StatusColours):
        super().__init__("set_leds_same_colour", LEDIndicatorColourPayload(indicator_colour))


class LedsTask(PhonieTVTask):
    def __init__(self, task_name: str, stop_event):
        super().__init__(task_name, stop_event)
        set_brightness(0.1)  # Set brightness to 10%


    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                if event_to_process.event_type == "set_led_indicator_count":
                    indicator_count = event_to_process.event_payload.indicator_count
                    colour = event_to_process.event_payload.colour.value
                    colours = [colour] * indicator_count # + [StatusColours.COLOUR_OFF.value] * (NUM_PIXELS - indicator_count)
                    update_blinkt(colours)
                if event_to_process.event_type == "set_all_leds":
                    colour = event_to_process.event_payload
                    colours = [colour] * NUM_PIXELS
                    update_blinkt(colours)

                    pass
            except queue.Empty:
                pass

            time.sleep(LEDS_TASK_SLEEP_TIME_S)