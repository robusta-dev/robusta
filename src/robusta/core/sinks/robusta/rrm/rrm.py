import logging
import threading
import time
from typing import List

from robusta.core.model.env_vars import RRM_PERIOD_SEC
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.base_resource_manager import BaseResourceManager
from robusta.core.sinks.robusta.rrm.prometheus_alert_resource_manager import \
    PrometheusAlertResourceManager
from robusta.core.sinks.robusta.rrm.types import ResourceKind


# robusta resource management
class RRM:
    def __init__(self, dal: AccountResourceFetcher, cluster: str, account_id: str):
        self.dal = dal
        self.cluster = cluster
        self.__sleep = RRM_PERIOD_SEC

        self.__resource_managers: List[BaseResourceManager] = [
            PrometheusAlertResourceManager(resource_kind=ResourceKind.PrometheusAlert, cluster=self.cluster, dal=dal)]

        self.__thread = threading.Thread(target=self.__thread_loop)
        self.__thread.start()

    def __thread_loop(self):
        for res_man in self.__resource_managers:
            try:
                res_man.init_resources(updated_at=None)
            except Exception:
                self.__resource_managers.remove(res_man)
                logging.warning(
                    f"Unable to initialize the `{res_man.get_resource_kind()}` PrometheusRules CRD resources. Skipping it",
                    exc_info=True)

        while True:
            try:
                self.__periodic_loop()

                time.sleep(self.__sleep)
            except Exception as e:
                logging.error(e)

    def __periodic_loop(self):
        for res_man in self.__resource_managers:
            resource_kind = res_man.get_resource_kind()
            try:
                account_resources = self.dal \
                    .get_account_resources(resource_kind=resource_kind,
                                           updated_at=res_man.get_last_updated_at())

                res_man.prepare(account_resources)

            except Exception as e:
                logging.error(f"Failed to get Account Resource. {e}", exc_info=True)
