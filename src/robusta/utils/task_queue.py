import logging
import threading
import time
from threading import Thread
from queue import Queue, Full

from robusta.core.model.env_vars import INCOMING_EVENTS_QUEUE_MAX_SIZE


class QueueMetrics:
    queued: int = 0
    processed: int = 0
    total_process_time: int = 0
    rejected: int = 0


class TaskQueue(Queue):
    def __init__(self, name: str, num_workers=1):
        Queue.__init__(self, maxsize=INCOMING_EVENTS_QUEUE_MAX_SIZE)
        logging.info(f"Initialized task queue: {num_workers} workers. Max size {INCOMING_EVENTS_QUEUE_MAX_SIZE}")
        self.name = name
        self.num_workers = num_workers
        self.__init_metrics()
        self.__start_workers()

    def __init_metrics(self):
        self.metrics = QueueMetrics()
        self.metrics_thread = Thread(target=self.__report_metrics)
        self.metrics_thread.daemon = True
        self.metrics_thread.start()
        self.metrics_lock = threading.Lock()

    def __report_metrics(self):
        while True:
            avg_process_time = self.metrics.total_process_time / self.metrics.processed \
                if self.metrics.processed > 0 else 0
            #  For now, just add it to the log. Can provide insightful data
            logging.info(f"queue {self.name} "
                         f"size {self.qsize()} "
                         f"queued {self.metrics.queued} "
                         f"processed {self.metrics.processed} "
                         f"rejected {self.metrics.rejected} "
                         f"avg process time {avg_process_time}")
            time.sleep(120)

    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        try:
            self.put((task, args, kwargs), block=False)
        except Full:
            with self.metrics_lock:
                self.metrics.rejected += 1
            return

        with self.metrics_lock:
            self.metrics.queued += 1

    def __start_workers(self):
        for i in range(self.num_workers):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            item, args, kwargs = self.get()
            with self.metrics_lock:
                self.metrics.processed += 1
            start_time = time.time()
            item(*args, **kwargs)
            with self.metrics_lock:
                self.metrics.total_process_time += (time.time() - start_time)
            self.task_done()
