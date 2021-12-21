import logging
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WAIT_SEC = 2


class FsChangeHandler(FileSystemEventHandler):
    """reload playbooks on change."""

    def __init__(self, mark_change):
        super().__init__()
        self.mark_change = mark_change

    def on_moved(self, event):
        self.mark_change()

    def on_created(self, event):
        self.mark_change()

    def on_deleted(self, event):
        self.mark_change()

    def on_modified(self, event):
        self.mark_change()


class FileSystemWatcher:
    def __init__(self, path_to_watch, reload_configuration):
        self.active = True
        self.change_detected = False
        self.path_to_watch = path_to_watch
        self.reload_configuration = reload_configuration

        self.watch_thread = threading.Thread(target=self.watch, name="config-watcher")
        self.watch_thread.start()

        logging.info(f"watching dir {path_to_watch} for custom playbooks changes")

    def watch(self):
        observer = Observer()
        fs_change_handler = FsChangeHandler(self.mark_change)
        observer.schedule(fs_change_handler, self.path_to_watch, recursive=True)
        observer.start()
        try:
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
        finally:
            observer.stop()
            observer.join()

    def stop_watcher(self):
        self.active = False

    def mark_change(self):
        self.change_detected = True
