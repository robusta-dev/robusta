
import logging
import threading
import time

from kubernetes import client, config

from robusta.core.model.env_vars import RRM_PERIOD_SEC
from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal
from robusta.core.sinks.robusta.rrm.prometheus_alert_resource_manager import PrometheusAlertResourceManager
from robusta.core.sinks.robusta.rrm.types import AccountResource, BaseResourceManager, ResourceEntry


# robusta resource management



class RRM:
    def __init__(self, dal: SupabaseDal, global_config: dict):
        self.dal = dal
        self.__sleep = RRM_PERIOD_SEC

        self.__resource_managers:list[BaseResourceManager] = [PrometheusAlertResourceManager()]
        # map entry_id => ResourceEntry
        self.__entries = dict[str, ResourceEntry]()

        self.__thread = threading.Thread(target=self.__thread_loop)
        self.__thread.start()

    def __thread_loop(self):
        for res_man in self.__resource_managers:
            res_man.init_resources()

        while True:  # TODO: termination ?
            try:
                self.__periodic_loop()

                time.sleep(self.__sleep)
            except Exception as e:
                logging.error(e)

    def __periodic_loop(self):

        for res_man in self.__resource_managers:
            resources: list[AccountResource] = self.dal.get_account_resources(
                resource_kind=res_man.get_resource_kind(),
                updated_at=res_man.get_updated_ts())

            for resource in resources:
                entity_id = resource.entity_id
                # if this resource is already tracked by __entries
                if entity_id in self.__entries:
                    # just deleted or it is not in cluster anymore => remove it
                    if (resource.deleted or not self.__in_cluster(resource.clusters_target_set)):
                        if res_man.delete_resource(resource, self.__entries[entity_id]):
                            del self.__entries[entity_id]
                    else:
                        entry = res_man.update_resource(resource, self.__entries[entity_id])
                        if entry is not None:
                            self.__entries[entity_id] = entry
                else:  # new resource
                    entry = res_man.create_resource(resource)
                    if entry is not None:
                        self.__entries[entity_id] = entry

    def __in_cluster(self, clusters_target_set: list[str] = []):
        return "*" in clusters_target_set or self.dal.cluster in clusters_target_set



    
    
