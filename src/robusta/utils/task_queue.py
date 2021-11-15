import logging
import time
from threading import Thread, Lock
from queue import Queue, Full
import prometheus_client

from robusta.core.model.env_vars import INCOMING_EVENTS_QUEUE_MAX_SIZE


class QueueMetrics:
    def __init__(self):
        self.queued = prometheus_client.Counter(
            "queued", "Number of queued events", labelnames=("queue_name",)
        )
        self.processed = prometheus_client.Counter(
            "processed", "Number of processed events", labelnames=("queue_name",)
        )
        self.rejected = prometheus_client.Counter(
            "rejected", "Number of rejected events", labelnames=("queue_name",)
        )
        self.total_process_time = prometheus_client.Summary(
            "total_process_time",
            "Total process time (seconds)",
            labelnames=("queue_name",),
        )

    def on_rejected(self, queue_name):
        self.rejected.labels([queue_name]).inc()

    def on_queued(self, queue_name):
        self.queued.labels([queue_name]).inc()

    def on_processed(self, queue_name, processing_time: float):
        self.processed.labels([queue_name]).inc()
        self.total_process_time.labels([queue_name]).observe(processing_time)


class TaskQueue(Queue):
    def __init__(self, name: str, num_workers, metrics: QueueMetrics):
        Queue.__init__(self, maxsize=INCOMING_EVENTS_QUEUE_MAX_SIZE)
        logging.info(
            f"Initialized task queue: {num_workers} workers. Max size {INCOMING_EVENTS_QUEUE_MAX_SIZE}"
        )
        self.name = name
        self.num_workers = num_workers
        self.metrics = metrics
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
            item(*args, **kwargs)
            self.metrics.on_processed(self.name, time.time() - start_time)
            self.task_done()
