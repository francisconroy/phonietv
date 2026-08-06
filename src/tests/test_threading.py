import logging
import queue
import threading
import time
from unittest import TestCase

from phonietv.event import PhonieTVEvent
from phonietv.threading import PhonieTVTask

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
LOGGER = logging.getLogger(__name__)

class PhoneTVTaskTesterA(PhonieTVTask):

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
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
            time.sleep(1)
            LOGGER.info(f"Thread {self.task_name} is ticking")


class PhonieTVTaskTesterB(PhonieTVTask):

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            event_to_process = self.inbound_queue.get(block=True)
            LOGGER.info(f"got event {event_to_process.event_type}")
            if event_to_process.event_type == "response_event":
                self.publish_event(PhonieTVEvent("final_event", {"response": "ok"}))
                LOGGER.info(f"Stopping thread {self.task_name}")
                break


class TestPhonieTVTask(TestCase):
    def test_task_function(self):
        stop_event = threading.Event()
        taska = PhoneTVTaskTesterA("test task A", stop_event)
        taskb = PhonieTVTaskTesterB("test task B", stop_event)
        # other_queue = queue.Queue()
        taska.attach_event_queues({taskb.inbound_queue})
        taskb.attach_event_queues({taska.inbound_queue})
        taska.start()
        taskb.start()
        time.sleep(2)
        taska.inbound_queue.put(PhonieTVEvent("party_event", {}))
        # time.sleep(1)
        # stop_event.set()
        taska.join()
        taskb.join()
