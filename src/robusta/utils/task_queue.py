import logging
import time
from queue import Full, Queue
from threading import Thread

import prometheus_client

from robusta.core.model.env_vars import INCOMING_EVENTS_QUEUE_MAX_SIZE


class QueueMetrics:
    def __init__(self):
        self.queue_event = prometheus_client.Counter(
            "queue_event", "Number of queue events status", labelnames=("queue_name", "status")
        )
        self.total_process_time = prometheus_client.Summary(
            "queue_process_time",
            "queue process time (seconds)",
            labelnames=("queue_name",),
        )
        self.queue_size = prometheus_client.Gauge("queue_size", "Current size of the queue", labelnames=("queue_name",))

    def size_callback(self, queue_name, queue_size_callback_fn):
        self.queue_size.labels(queue_name).set_function(queue_size_callback_fn)

    def on_rejected(self, queue_name):
        self.queue_event.labels(queue_name, "rejected").inc()

    def on_queued(self, queue_name):
        self.queue_event.labels(queue_name, "queued").inc()

    def on_processed(self, queue_name, processing_time: float):
        self.queue_event.labels(queue_name, "processed").inc()
        self.total_process_time.labels(queue_name).observe(processing_time)


class TaskQueue(Queue):
    def __init__(self, name: str, num_workers, metrics: QueueMetrics):
        Queue.__init__(self, maxsize=INCOMING_EVENTS_QUEUE_MAX_SIZE)
        logging.info(f"Initialized task queue: {num_workers} workers. Max size {INCOMING_EVENTS_QUEUE_MAX_SIZE}")
        self.name = name
        self.num_workers = num_workers
        self.metrics = metrics
        self.metrics.size_callback(self.name, lambda: self._qsize())
        self.__start_workers()

    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        try:
            self.put((task, args, kwargs), block=False)
            self.metrics.on_queued(self.name)
        except Full:
            self.metrics.on_rejected(self.name)

    def __start_workers(self):
        for i in range(self.num_workers):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            item, args, kwargs = self.get()
            start_time = time.time()

            try:
                item(*args, **kwargs)
            except Exception:
                logging.error("Task worker error", exc_info=True)

            self.metrics.on_processed(self.name, time.time() - start_time)
            self.task_done()
