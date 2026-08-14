import threading
from queue import Queue
from unittest import TestCase, mock

from phonietv import timer
from phonietv.timer import TimerExpiredEvent, TimerIndicatorEvent, TimerSetEnabledStateEvent, TimerTask


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
        stop_indicator_event = threading.Event()
        timer_task = TimerTask("test_timer", stop_event=stop_indicator_event, num_indicators=5, timer_duration_s=10)
        outbound_queue = Queue()
        timer_task.attach_event_queues({outbound_queue})
        timer_task.start_timer()
        timer_task.stop_timer()

        start_indicator_event = outbound_queue.get_nowait()
        stop_indicator_event = outbound_queue.get_nowait()

        self.assertIsInstance(start_indicator_event, TimerIndicatorEvent)
        start_indicator_payload = start_indicator_event.event_payload
        self.assertIsInstance(start_indicator_payload, timer.IndicatorEventPayload)
        self.assertEqual(0, start_indicator_payload.indicator_count)
        self.assertIsInstance(stop_indicator_event, TimerIndicatorEvent)
        stop_indicator_payload = stop_indicator_event.event_payload
        self.assertIsInstance(stop_indicator_payload, timer.IndicatorEventPayload)
        self.assertEqual(0, stop_indicator_payload.indicator_count)

    @mock.patch("phonietv.timer.TIMER_TASK_SLEEP_TIME_S", 0)  # Make thread agressive
    def test_task_function_timer_signal_emits_indicator_and_expired_events(self):
        def cleanup():
            stop_event.set()
            timer_task.join()
        self.addCleanup(cleanup)
        stop_event = threading.Event()

        timer_task = TimerTask("test_timer", stop_event=stop_event, num_indicators=5, timer_duration_s=120)
        outbound_queue = Queue()
        timer_task.attach_event_queues({outbound_queue})
        with mock.patch.object(timer.time, "monotonic", side_effect=[100.0, 215.0, 220.0, 225.0]):
            timer_task.start()
            timer_task.inbound_queue.put(TimerSetEnabledStateEvent(True))

            start_indicator_event = outbound_queue.get(timeout=1)
            self.assertIsInstance(start_indicator_event, TimerIndicatorEvent)
            start_indicator_payload = start_indicator_event.event_payload
            self.assertIsInstance(start_indicator_payload, timer.IndicatorEventPayload)
            self.assertEqual(0, start_indicator_payload.indicator_count)

            second_indicator_event = outbound_queue.get(timeout=1)
            self.assertIsInstance(second_indicator_event, TimerIndicatorEvent)
            second_indicator_payload = second_indicator_event.event_payload
            self.assertIsInstance(second_indicator_payload, timer.IndicatorEventPayload)
            self.assertEqual(5, second_indicator_payload.indicator_count)

            expiry_event = outbound_queue.get(timeout=1)
            self.assertIsInstance(expiry_event, TimerExpiredEvent)

            indicator_reset_event = outbound_queue.get(timeout=1)
            self.assertIsInstance(indicator_reset_event, TimerIndicatorEvent)
            indicator_reset_payload = indicator_reset_event.event_payload
            self.assertIsInstance(indicator_reset_payload, timer.IndicatorEventPayload)
            self.assertEqual(0, indicator_reset_payload.indicator_count)
