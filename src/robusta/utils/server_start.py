from datetime import datetime
from typing import Type

import pytz


class ServerStart:
    pod_start_time: datetime = None

    @staticmethod
    def set_pod_start_time() -> datetime:
        ServerStart.pod_start_time = datetime.now().astimezone(pytz.utc)
        return ServerStart.pod_start_time

    @staticmethod
    def get_pod_start_time() -> datetime:
        return ServerStart.pod_start_time
