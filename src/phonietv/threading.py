import logging
import threading
from abc import ABC, abstractmethod
from queue import Queue
from typing import Set

from .event import PhonieTVEvent

LOGGER = logging.getLogger(__name__)

class PhonieTVTask(ABC):
    def __init__(self, task_name: str, stop_event):
        self.thread = threading.Thread(target=self.task_function, name=task_name, args=(stop_event,))
        self.event_queues = set()
        self.event_queue_lock = threading.Lock()
        self.inbound_queue = Queue()
        self.task_name = task_name

    def join(self):
        self.thread.join()

    @abstractmethod
    def task_function(self, stop_event: threading.Event):
        raise NotImplementedError

    def start(self):
        self.thread.start()

    def attach_event_queues(self, event_queues: Set[Queue]):
        """
        Attach outbound queues, we will post events to these queues
        :param event_queues:
        :return: None
        """
        with self.event_queue_lock:
            self.event_queues.update(event_queues)

    def publish_event(self, event: PhonieTVEvent):
        """
        :param event:
        :return:
        """
        LOGGER.info(f"{self.task_name}: publishing event {event.event_type}, payload: {event.event_payload}")
        with self.event_queue_lock:
            for queue in self.event_queues:
                queue.put(event)
