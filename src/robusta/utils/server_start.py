from datetime import datetime

import pytz


class ServerStart:
    start_time: datetime = None

    @staticmethod
    def set():
        ServerStart.start_time = datetime.now()

    @staticmethod
    def get() -> datetime:
        return ServerStart.start_time
