import logging
import os
from collections import defaultdict
from enum import Enum
from time import sleep
import sentry_sdk
import requests
import threading
from ..model.config import Registry, Telemetry
from .telemetry import SinkInfo

from hikaru.model import NodeList

class TelemetryLevel(Enum):
    NONE = 0,
    USAGE = 1,
    ERROR = 2 

class TelemetryService: 
    def __init__(
        self,
        telemetry_level: TelemetryLevel,
        endpoint: str,
        periodic_time_sec: float,
        registry : Registry
    ):
        self.telemetry_level = telemetry_level
        self.endpoint = endpoint
        self.registry = registry
        self.periodic_time_sec = periodic_time_sec

        sentry_dsn = os.environ.get("SENTRY_DSN", "")
        if self.telemetry_level == TelemetryLevel.ERROR and sentry_dsn:
            logging.info(f"Telemetry set to include error info, Thank you for helping us improve Robusta.")
            try:
                sentry_sdk.init(sentry_dsn, traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", 0.5)))
                global_config = account_id = self.registry.get_global_config()
                sentry_sdk.set_user({"id": global_config.get("account_id", "")})
                sentry_sdk.set_tag("cluster_id", global_config.get("cluster_name", ""))
            except Exception as e:
                logging.error(f"Sentry error: {e}", exc_info=True)

        self.__thread = threading.Thread(target=self.__log_periodic)
        self.__thread.start()


    def __log_periodic(self):
        while(True):
            try:
                tele = self.registry.get_telemetry()
            
                current_nodes: NodeList = NodeList.listNode().obj
                tele.nodes_count = len(current_nodes.items)

                self.__log(tele)

                tele.sinks_info = defaultdict(lambda: SinkInfo())

                sleep(self.periodic_time_sec)
            except Exception as e:
                logging.error(f"Failed to run periodic telemetry update {e}", exc_info=True)
                pass


    def __log(self, data: Telemetry):
        r = requests.post(self.endpoint, data=data.json(), headers={'Content-Type': 'application/json'})
        if(r.status_code != 201):
            logging.error(f"Failed to log telemetry data")

        return r
