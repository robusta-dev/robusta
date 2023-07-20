import logging
import threading
import time
from typing import List

from robusta.core.model.env_vars import RRM_PERIOD_SEC
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.prometheus_alert_resource_manager import PrometheusAlertResourceManager
from robusta.core.sinks.robusta.rrm.types import AccountResource, BaseResourceManager, ResourceEntry


# robusta resource management
class RRM:
    def __init__(self, dal: AccountResourceFetcher, cluster: str, account_id: str):
        self.dal = dal
        self.cluster = cluster
        self.account_id = account_id
        self.__sleep = RRM_PERIOD_SEC

        self.__resource_managers: List[BaseResourceManager] = \
            [PrometheusAlertResourceManager(dal=self.dal, account_id=self.account_id)]
        self.__entries = dict[str, ResourceEntry]()

        self.__thread = threading.Thread(target=self.__thread_loop)
        self.__thread.start()

    def __thread_loop(self):
        for res_man in self.__resource_managers:
            try:
                res_man.init_resources()
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

    def __in_cluster(self, clusters_target_set: List[str] = []):
        return "*" in clusters_target_set or self.cluster in clusters_target_set

    def __periodic_loop(self):
        for res_man in self.__resource_managers:
            resource_kind = res_man.get_resource_kind()

            try:
                resources: List[AccountResource] = self.dal.get_account_resources(
                    resource_kind=resource_kind, updated_at=res_man.get_updated_ts()
                )

                for resource in resources:
                    entity_id = resource.entity_id
                    # if this resource is already tracked by __entries
                    if entity_id in self.__entries:
                        # just deleted or it is not in cluster anymore => remove it
                        if resource.deleted or not self.__in_cluster(resource.clusters_target_set):
                            if res_man.delete_resource(resource, self.__entries[entity_id]):
                                del self.__entries[entity_id]
                        else:
                            entry = res_man.update_resource(resource, self.__entries[entity_id])
                            if entry is not None:
                                self.__entries[entity_id] = entry
                    else:
                        # if the resource is not of the cluster then skip it
                        if resource.deleted or not self.__in_cluster(resource.clusters_target_set):
                            return

                        # new resource
                        entry = res_man.create_resource(resource)
                        if entry is not None:
                            self.__entries[entity_id] = entry
            except Exception as e:
                logging.error(
                    f"An error occurred while running rrm periodic checks. Resource_kind => {resource_kind}. Error: {e}",
                    exc_info=True,
                )
