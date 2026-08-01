import math
import threading
import time
from dataclasses import dataclass

from .event import PhonieTVEvent
from .threading import PhonieTVTask


# Events for the timer module
@dataclass
class IndicatorEventPayload:
    indicator_count: int

class TimerIndicatorEvent(PhonieTVEvent):
    def __init__(self, indicator_count: int):
        super().__init__("timer_indicator_event", IndicatorEventPayload(indicator_count))

class TimerExpiredEvent(PhonieTVEvent):
    def __init__(self):
        super().__init__("timer_expired_event", None)


class Timer(PhonieTVTask):
    def __init__(self, task_name: str, stop_event, num_indicators: int, timer_duration_s: float):
        super().__init__(task_name, stop_event)
        self.start_time = None
        self.num_indicators = num_indicators

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():

            time.monotonic()

    def start_timer(self):
        if self.start_time is None:
            self.start_time = time.monotonic()
        self.publish_event(TimerIndicatorEvent(0))

    @staticmethod
    def get_indicator_count(num_indicators: int, timer_duration: float, elapsed_time: float) -> int:
        return math.floor((elapsed_time/timer_duration)*(num_indicators+1))
