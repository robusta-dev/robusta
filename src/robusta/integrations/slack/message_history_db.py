import shelve
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class MessageHistoryDB(ABC):
    def __init__(self):
        self.lock = threading.Lock()

    @abstractmethod
    def get_message_id(self, aggregation_key: str):
        pass

    @abstractmethod
    def set_message_id(self, aggregation_key: str, thread_ts: str):
        pass


class ShelveMessageHistory(MessageHistoryDB):
    def __init__(self, shelve_path):
        super().__init__()
        self.db = shelve.open(shelve_path, writeback=True)
        self.cleanup_interval = 6 * 60 * 60  # 6 hours in seconds
        self.cleanup_thread = threading.Thread(target=self.start_cleanup, daemon=True)
        self.cleanup_thread.start()

    def get_message_id(self, aggregation_key: str):
        with self.lock:
            message_info = self.db.get(aggregation_key)
            if message_info is None:
                return None

            # Check if thread_ts is less than 6 hours old
            if datetime.now() - message_info['datetime'] < timedelta(hours=6):
                return message_info['message_id']
            else:
                del self.db[aggregation_key]
                return None

    def set_message_id(self, aggregation_key: str, thread_ts: str):
        with self.lock:
            self.db[aggregation_key] = {
                'message_id': thread_ts,
                'datetime': datetime.now(),
            }
            self.db.sync()  # ensure changes are written to the disk

    def __del__(self):
        self.db.close()

    def cleanup(self):
        with self.lock:
            keys_to_delete = []
            for key, value in self.db.items():
                if datetime.now() - value['datetime'] > timedelta(hours=6):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self.db[key]
            self.db.sync()

    def start_cleanup(self):
        while True:
            self.cleanup()
            time.sleep(self.cleanup_interval)
