import threading
from datetime import timedelta
from queue import Queue
from unittest import TestCase
from unittest.mock import patch

import time
from freezegun import freeze_time

from . import timer
from .timer import TimerExpiredEvent, TimerIndicatorEvent, TimerSetStateEvent, TimerTask


class TestTimer(TestCase):
    def test_get_indicator_count(self):
        self.assertEqual(0, TimerTask.get_indicator_count(num_indicators=5, timer_duration=12, elapsed_time=0.0))
        self.assertEqual(5, TimerTask.get_indicator_count(num_indicators=5, timer_duration=12, elapsed_time=11.99))
        self.assertEqual(2, TimerTask.get_indicator_count(num_indicators=5, timer_duration=12, elapsed_time=5))

    def test_timer_task(self):
        stop_event = threading.Event()
        timer_task = TimerTask("test_timer", stop_event=stop_event, num_indicators=5, timer_duration_s=12)
        self.assertEqual("test_timer", timer_task.task_name)

    def test_start_and_stop_timer_publish_indicator_events(self):
        stop_event = threading.Event()
        timer_task = TimerTask("test_timer", stop_event=stop_event, num_indicators=5, timer_duration_s=10)
        outbound_queue = Queue()
        timer_task.attach_event_queues({outbound_queue})

        with freeze_time("2026-01-01 12:00:00"):
            timer_task.start_timer()
            timer_task.stop_timer()

        start_event = outbound_queue.get_nowait()
        stop_event = outbound_queue.get_nowait()

        self.assertIsInstance(start_event, TimerIndicatorEvent)
        self.assertEqual(0, start_event.event_payload.indicator_count)
        self.assertIsInstance(stop_event, TimerIndicatorEvent)
        self.assertEqual(0, stop_event.event_payload.indicator_count)

    def test_task_function_timer_signal_emits_indicator_and_expired_events(self):
        stop_event = threading.Event()
        timer_task = TimerTask("test_timer", stop_event=stop_event, num_indicators=2, timer_duration_s=2)
        outbound_queue = Queue()
        timer_task.attach_event_queues({outbound_queue})
        timer_task.inbound_queue.put(TimerSetStateEvent(True))

        sleep_calls = {"count": 0}

        with freeze_time("2026-01-01 12:00:00") as frozen_time:
            def fake_sleep(_sleep_seconds: float):
                sleep_calls["count"] += 1
                frozen_time.tick(delta=timedelta(seconds=1))
                if sleep_calls["count"] >= 3:
                    stop_event.set()

            with patch.object(timer.time, "monotonic", side_effect=lambda: time.time()), patch.object(timer.time,
                                                                                                      "sleep",
                                                                                                      side_effect=fake_sleep):
                timer_task.task_function(stop_event)

        events = []
        while not outbound_queue.empty():
            events.append(outbound_queue.get_nowait())

        indicator_counts = [
            event.event_payload.indicator_count
            for event in events
            if isinstance(event, TimerIndicatorEvent)
        ]

        self.assertGreaterEqual(len(indicator_counts), 2)
        self.assertEqual(0, indicator_counts[0])
        self.assertTrue(any(count > 0 for count in indicator_counts[1:]))
        self.assertTrue(any(isinstance(event, TimerExpiredEvent) for event in events))
