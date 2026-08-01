from unittest import TestCase

from .timer import Timer

class TestTimer(TestCase):
    def test_get_indicator_count(self):
        self.assertEqual(0, Timer.get_indicator_count(num_indicators=5, timer_duration=12, elapsed_time=0.0))
        self.assertEqual(5, Timer.get_indicator_count(num_indicators=5, timer_duration=12, elapsed_time=11.99))
        self.assertEqual(2, Timer.get_indicator_count(num_indicators=5, timer_duration=12, elapsed_time=5))
