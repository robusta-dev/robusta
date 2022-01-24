import asyncio
import logging
import threading
import time
from watchgod import watch

WAIT_SEC = 2


class FileSystemWatcher:
    def __init__(self, path_to_watch, reload_configuration):
        self.active = True
        self.change_detected = False
        self.path_to_watch = path_to_watch
        self.reload_configuration = reload_configuration
        self.stop_event = asyncio.Event()

        self.watch_thread = threading.Thread(target=self.watch, name="config-watcher")
        self.watch_thread.start()
        self.fs_watch_thread = threading.Thread(target=self.fs_watch, name="fs-watcher")
        self.fs_watch_thread.start()

        logging.info(f"watching dir {path_to_watch} for custom playbooks changes")

    def fs_watch(self):
        for _ in watch(self.path_to_watch, stop_event=self.stop_event):
            self.mark_change()

    def watch(self):
        while self.active:
            time.sleep(WAIT_SEC)

            if self.change_detected:
                time.sleep(
                    WAIT_SEC
                )  # once we detected a change, we wait a safety period to make sure all the changes under this 'bulk' are finished
                self.change_detected = False
                try:
                    self.reload_configuration(self.path_to_watch)
                except Exception as e:  # in case we have an error while trying to reload, we want the watch thread to stay alive
                    logging.exception("failed to reload configuration")

    def stop_watcher(self):
        self.active = False
        self.stop_event.set()

    def mark_change(self):
        self.change_detected = True
