import datetime
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

class TimerSetEnabledStateEvent(PhonieTVEvent):
    def __init__(self, state: bool):
        super().__init__("timer_set_state_event", state)


class TimerTask(PhonieTVTask):
    def __init__(self, task_name: str, stop_event, num_indicators: int, timer_duration_s: float):
        super().__init__(task_name, stop_event)
        self.start_time = None
        self.elapsed_time_for_today = 0
        self.num_indicators = num_indicators
        self.prev_indicator_count = 0
        self.timer_duration_s = timer_duration_s
        self.timer_start_day: int = datetime.datetime.now().toordinal()  # Day on which the timer expired

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            try:
                event_to_process = self.inbound_queue.get_nowait()
                LOGGER.info(f"got event {event_to_process.event_type}")
                if event_to_process.event_type == "timer_set_state_event":
                    if event_to_process.event_payload:
                        self.start_timer()
                    else:
                        self.stop_timer()
                    continue
            except queue.Empty:
                pass
            # Handle indicator update
            if self.start_time is not None:
                elapsed_time_current_block = time.monotonic() - self.start_time
                elapsed_time = self.elapsed_time_for_today + elapsed_time_current_block
                if self.is_expired(elapsed_time):
                    self.publish_event(TimerExpiredEvent())
                    self.stop_timer()
                else:
                    self.handle_indicator_count(elapsed_time)

            # Check if the day has changed since the timer expired
            day_now = datetime.datetime.now().toordinal()
            if day_now != self.timer_start_day:
                self.publish_event(PhonieTVEvent("timer_reset", None))
                self.timer_start_day = day_now
                self.elapsed_time_for_today = 0

            time.sleep(TIMER_TASK_SLEEP_TIME_S)

    def handle_indicator_count(self, elapsed_time: float):
        indicator_count = self.get_indicator_count(self.num_indicators, self.timer_duration_s, elapsed_time)
        assert indicator_count <= self.num_indicators, "Indicator count greater than registered number of indicators!"
        if indicator_count != self.prev_indicator_count:
            self.prev_indicator_count = indicator_count
            self.publish_event(TimerIndicatorEvent(indicator_count))

    def is_expired(self, elapsed_time: float) -> bool:
        return elapsed_time >= self.timer_duration_s


    def start_timer(self):
        if self.start_time is None:
            self.start_time = time.monotonic()
            self.timer_start_day = datetime.datetime.now().toordinal()
            self.prev_indicator_count = 0
        self.publish_event(TimerIndicatorEvent(self.get_indicator_count(self.num_indicators, self.timer_duration_s, 0)))

    def stop_timer(self):
        if self.start_time is not None:
            elapsed_time = time.monotonic() - self.start_time
            self.elapsed_time_for_today += elapsed_time
        self.start_time = None
        self.publish_event(TimerIndicatorEvent(0))

    @staticmethod
    def get_indicator_count(num_indicators: int, timer_duration: float, elapsed_time: float) -> int:
        return math.floor((elapsed_time/timer_duration)*(num_indicators+1))
