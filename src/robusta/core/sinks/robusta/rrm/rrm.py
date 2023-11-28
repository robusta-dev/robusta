import logging
import threading
import time
from datetime import datetime
from typing import Optional

from robusta.core.model.env_vars import RRM_PERIOD_SEC, MANAGED_CONFIGURATION_ENABLED
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.prometheus_alert_resource_manager import PrometheusAlertResourceManager
from robusta.core.sinks.robusta.rrm.types import ResourceKind, AccountResourceStatusType


# robusta resource management
class RRM:
    def __init__(self, dal: AccountResourceFetcher, cluster: str, account_id: str):
        self.dal = dal
        self.cluster = cluster
        self.__sleep = RRM_PERIOD_SEC
        self.__last_updated_at: Optional[datetime] = None
        self.__alert_resource_manager = PrometheusAlertResourceManager(
            cluster=self.cluster, dal=dal,
            resource_kind=ResourceKind.PrometheusAlert
        )

        self.__thread = threading.Thread(target=self.__thread_start)
        self.__thread.start()

    def __periodic_loop(self):
        account_resources = self.dal \
            .get_account_resources(updated_at=self.__last_updated_at)

        for resource_kind, resources in account_resources.items():
            if resource_kind == ResourceKind.PrometheusAlert:
                try:
                    self.__alert_resource_manager.start_syncing_alerts(account_resources=resources)
                    self.__last_updated_at = resources[-1].updated_at
                    self.__alert_resource_manager.set_last_updated_at(updated_at=self.__last_updated_at)
                    self.__alert_resource_manager.set_account_resource_status(
                        status_type=AccountResourceStatusType.success, info=None)
                except Exception:
                    logging.error("RRM Alerts config threw an error while executing `start_syncing_alerts`",
                                  exc_info=True)

    def __thread_start(self):
        while True:
            try:
                self.__periodic_loop()

                time.sleep(self.__sleep)
            except Exception as e:
                logging.error("RRM Alerts config threw an error while executing `__thread_start`", exc_info=True)
