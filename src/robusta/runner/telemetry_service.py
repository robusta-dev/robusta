import logging
import os
import threading
from collections import defaultdict
from enum import Enum
from time import sleep

import requests
import sentry_sdk
from sentry_sdk.integrations.threading import ThreadingIntegration
from hikaru.model.rel_1_26 import NodeList

from robusta.core.model.env_vars import (
    ENABLE_TELEMETRY,
    PROMETHEUS_ENABLED,
    ROBUSTA_TELEMETRY_ENDPOINT,
    RUNNER_VERSION,
    SEND_ADDITIONAL_TELEMETRY,
    SENTRY_DSN,
    SENTRY_ENABLED,
    TELEMETRY_PERIODIC_SEC,
)
from robusta.model.config import Registry, Telemetry
from robusta.runner.telemetry import SinkInfo

class TelemetryService:
    def __init__(self, endpoint: str, periodic_time_sec: float, registry: Registry):
        self.endpoint = endpoint
        self.registry = registry
        self.periodic_time_sec = periodic_time_sec

        if SENTRY_ENABLED:
            logging.info("Telemetry set to include error info, Thank you for helping us improve Robusta.")
            try:
                sentry_sdk.init(
                    SENTRY_DSN,
                    enable_tracing=True,
                    traces_sample_rate=0.01,
                    profiles_sample_rate=0.01, 
                    release=RUNNER_VERSION,
                    integrations=[
                        ThreadingIntegration(propagate_scope=True),
                    ],
                )
                global_config = self.registry.get_global_config()
                sentry_sdk.set_user({"id": global_config.get("account_id", "")})
                sentry_sdk.set_tag("cluster_id", global_config.get("cluster_name", ""))
                sentry_sdk.set_tag("prometheus_enabled", PROMETHEUS_ENABLED)
            except Exception as e:
                logging.error(f"Sentry error: {e}", exc_info=True)

        self.__thread = threading.Thread(target=self.__log_periodic)
        self.__thread.start()

    def __log_periodic(self):
        while True:
            try:
                tele = self.registry.get_telemetry()

                current_nodes: NodeList = NodeList.listNode().obj
                tele.nodes_count = len(current_nodes.items)

                self.__log(tele)

                tele.sinks_info = defaultdict(lambda: SinkInfo())
            except Exception as e:
                logging.error(f"Failed to run periodic telemetry update {e}", exc_info=True)

            sleep(self.periodic_time_sec)

    def __log(self, data: Telemetry):
        r = requests.post(self.endpoint, data=data.json(), headers={"Content-Type": "application/json"})
        if r.status_code != 201:
            logging.error("Failed to log telemetry data")

        return r
