import logging
from threading import Thread
from queue import Queue


class TaskQueue(Queue):
    def __init__(self, num_workers=1):
        Queue.__init__(self)
        logging.info(f"Initialized task queue: {num_workers} workers")
        self.num_workers = num_workers
        self.start_workers()

    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        self.put((task, args, kwargs))

    def start_workers(self):
        for i in range(self.num_workers):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            item, args, kwargs = self.get()
            item(*args, **kwargs)
            self.task_done()
