import logging
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict

from robusta.core.model.env_vars import RRM_PERIOD_SEC, MANAGED_CONFIGURATION_ENABLED
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.base_resource_manager import BaseResourceHandler
from robusta.core.sinks.robusta.rrm.prometheus_alert_resource_manager import PrometheusAlertResourceHandler
from robusta.core.sinks.robusta.rrm.types import ResourceKind, AccountResourceStatusType, AccountResourceStatusInfo


# robusta resource management
class RRM:
    def __init__(self, dal: AccountResourceFetcher, cluster: str, account_id: str):
        self.dal = dal
        self.cluster = cluster
        self.__sleep = RRM_PERIOD_SEC
        self.__latest_revision: Optional[datetime] = None
        self.__resource_handler_map: Dict[ResourceKind, BaseResourceHandler] = {
            ResourceKind.PrometheusAlert: PrometheusAlertResourceHandler(
                cluster=self.cluster,
                resource_kind=ResourceKind.PrometheusAlert
            )
        }

        self.__thread = threading.Thread(target=self.__run_rrm)
        self.__thread.start()

    def __periodic_loop(self):
        errors: List[str] = []
        latest_revision: Optional[datetime] = self.__latest_revision

        try:
            account_resources = self.dal \
                .get_account_resources(latest_revision=self.__latest_revision)
            for resource_kind, resources in account_resources.items():
                handler = self.__resource_handler_map.get(resource_kind)

                # Update latest_revision with the max timestamp
                if resources:
                    current_max_resource_timestamp = resources[-1].updated_at
                    if latest_revision is None or current_max_resource_timestamp > latest_revision:
                        latest_revision = current_max_resource_timestamp

                if handler:
                    error = handler.handle_resources(resources)
                    if error:
                        errors.append(error)
                else:
                    logging.warning(f"Could not handle resources from kind {resource_kind}")

        except Exception:
            error = "An error occured while handling resources. Please check the runner logs for details"
            errors.append(error)

            logging.error(f"An error occurred while creating CR rules", exc_info=True)

        # If the configuration was applied to the values file before enabling it in the UI
        if latest_revision is None:
            return

        self.__latest_revision = latest_revision
        if len(errors):
            self.dal.set_account_resource_status(status_type=AccountResourceStatusType.error,
                                                 info=AccountResourceStatusInfo(error=", ".join(errors)),
                                                 latest_revision=self.__latest_revision)
        else:
            self.dal.set_account_resource_status(status_type=AccountResourceStatusType.success, info=None,
                                                 latest_revision=self.__latest_revision)

    def __run_rrm(self):
        if not MANAGED_CONFIGURATION_ENABLED:
            return

        while True:
            try:
                self.__periodic_loop()

            except Exception as e:
                logging.error("RRM Alerts config threw an error while executing `__thread_start`", exc_info=True)

            # even if `__periodic_loop` throws an exception the program should wait before re attempting
            time.sleep(self.__sleep)
