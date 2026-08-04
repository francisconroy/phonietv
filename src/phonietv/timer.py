import logging
import math
import threading
import time
import queue
from dataclasses import dataclass

from .event import PhonieTVEvent
from .threading import PhonieTVTask

TIMER_TASK_SLEEP_TIME_S: float =1

LOGGER = logging.getLogger(__name__)

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

class TimerSetStateEvent(PhonieTVEvent):
    def __init__(self, state: bool):
        super().__init__("timer_set_state_event", state)

class Timer(PhonieTVTask):
    def __init__(self, task_name: str, stop_event, num_indicators: int, timer_duration_s: float):
        super().__init__(task_name, stop_event)
        self.start_time = None
        self.num_indicators = num_indicators
        self.prev_indicator_count = 0
        self.timer_duration_s = timer_duration_s

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                if event_to_process.event_type == "final_event":
                    LOGGER.info(f"Stopping thread {self.task_name}")
                    break
                else:
                    self.publish_event(PhonieTVEvent("response_event", {"response": "ok"}))
            except queue.Empty:
                pass
            # Handle indicator update
            if self.start_time is not None:
                elapsed_time = time.monotonic() - self.start_time
                indicator_count = self.get_indicator_count(self.num_indicators, self.timer_duration_s, elapsed_time)
                if indicator_count != self.prev_indicator_count:
                    self.prev_indicator_count = indicator_count
                    self.publish_event(TimerIndicatorEvent(indicator_count))
                if elapsed_time >= self.timer_duration_s:
                    self.publish_event(TimerExpiredEvent())
                    self.start_time = None
            time.sleep(TIMER_TASK_SLEEP_TIME_S)

    def start_timer(self):
        if self.start_time is None:
            self.start_time = time.monotonic()
            self.prev_indicator_count = 0
        self.publish_event(TimerIndicatorEvent(self.get_indicator_count(self.num_indicators, self.timer_duration_s, 0)))

    def stop_timer(self):
        self.start_time = None
        self.publish_event(TimerIndicatorEvent(0))

    @staticmethod
    def get_indicator_count(num_indicators: int, timer_duration: float, elapsed_time: float) -> int:
        return math.floor((elapsed_time/timer_duration)*(num_indicators+1))
