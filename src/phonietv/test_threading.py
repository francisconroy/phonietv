import queue
import threading
import time
from unittest import TestCase

from .event import PhonieTVEvent
from .threading import PhonieTVTask

class PhonieTVTaskTester(PhonieTVTask):

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            try:
                event_to_process = self.inbound_queue.get_nowait()
                print(f"got event {event_to_process.eventType}")
                self.publish_event(PhonieTVEvent("response_event", {"response": "ok"}))

            except queue.Empty:
                pass
            time.sleep(1)
            print(f"Thread {self.task_name} is ticking")


class TestPhonieTVTask(TestCase):
    def test_task_function(self):
        stop_event = threading.Event()
        task = PhonieTVTaskTester("test task", stop_event)
        other_queue = queue.Queue()
        task.attach_event_queues([other_queue])
        task.start()
        time.sleep(2)
        task.inbound_queue.put(PhonieTVEvent("party_event", {}))
        time.sleep(1)
        print(other_queue.get())
        stop_event.set()
        task.join()

