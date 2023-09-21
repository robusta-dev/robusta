import copy
import logging
import math
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from kubernetes import client
from kubernetes.client import ApiException

from robusta.core.model.env_vars import INSTALLATION_NAMESPACE, MAX_ALLOWED_RULES_PER_CRD_ALERT, RRM_PERIOD_SEC
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.base_resource_manager import BaseResourceManager
from robusta.core.sinks.robusta.rrm.types import PrometheusAlertRule, ResourceKind, \
    AccountResource, PrometheusAlertResourceState, AccountResourceStatusType, AccountResourceStatusInfo


class PrometheusAlertResourceManager(BaseResourceManager):
    def __init__(self, resource_kind: ResourceKind, cluster: str, dal: AccountResourceFetcher, ):
        super().__init__(resource_kind, cluster, dal=dal)
        self.__sleep = RRM_PERIOD_SEC
        self.__max_allowed_rules_per_crd = MAX_ALLOWED_RULES_PER_CRD_ALERT
        self.__label_selector_value = "robusta-resource-management"
        self.__label_selector_key = "release.app"
        self.init_resources_max_attempts = 3
        self.__label_selector = f"{self.__label_selector_key}={self.__label_selector_value}"
        self.__plural = "prometheusrules"
        self.__group = "monitoring.coreos.com"
        self.__group_name = "kubernetes-apps"
        self.__version = "v1"
        self.__k8_apiVersion = f"{self.__group}/{self.__version}"
        self.__kind = "PrometheusRule"
        self.__crd_name = "robusta-prometheus.rules"
        self.__installation_namespace = INSTALLATION_NAMESPACE
        self.__k8_api = client.CustomObjectsApi()
        self.__crd_files_cache: Dict[str, List[PrometheusAlertRule]] = {}

    # initialize the resources
    def init_resources(self, updated_at: Optional[datetime]):
        """Initialize the resources

        If the API call fails, the initialization method will make additional attempts to list and delete
        the custom objects. If these attempts also fail, we will remove the failed resources from
        the __resource_managers list, rendering them inert.
        """
        self.__last_updated_at = None
        exception: Optional[Exception] = None
        self.__crd_files_cache = {}

        for itr in range(0, self.init_resources_max_attempts):
            try:
                # fetch the available crd files and then delete them in the first run
                crd_obj = self.__k8_api.list_namespaced_custom_object(
                    group=self.__group,
                    version=self.__version,
                    plural=self.__plural,
                    label_selector=self.__label_selector,
                    namespace=self.__installation_namespace
                )

                items = crd_obj["items"]
                for obj in items:
                    name = obj["metadata"]["name"]
                    self.__delete_crd_file(name=name)

            except Exception as e:
                exception = e
                logging.error(
                    f"An error occurred while initializing PrometheusRules CRD resources: {e}. Attempting again..",
                    exc_info=True)
                time.sleep(5)

        if exception:
            raise exception

    def __in_cluster(self, clusters_target_set: List[str] = []) -> bool:
        return "*" in clusters_target_set or self.cluster in clusters_target_set

    def prepare(self, account_resources: List[AccountResource]):
        prometheus_rules_map = self.__get_flattened_crd_files_cache_map()

        try:
            for resource in account_resources:
                self.set_last_updated_at(resource.updated_at)

                in_cluster = self.__in_cluster(resource.clusters_target_set)

                # Case 1: Remove the resource from the cache if it's marked as deleted.
                # Case 2: Remove the resource from the cache if it's NOT marked as enabled.
                # Case 3: Remove the resource from the cache if it's not assigned to the cluster anymore.
                if resource.deleted or not resource.enabled or not in_cluster:
                    if resource.entity_id in prometheus_rules_map:
                        del prometheus_rules_map[resource.entity_id]
                    continue

                if in_cluster:
                    resource_state = PrometheusAlertResourceState \
                        .from_dict(resource.resource_state, entity_id=resource.entity_id)
                    prometheus_rules_map[resource.entity_id] = resource_state.rule

            synced_item_count = self.start(active_alert_rules=list(prometheus_rules_map.values()))

            if synced_item_count > 0:
                self.set_account_resource_status(status_type=AccountResourceStatusType.success, info=None)

        except Exception as e:
            # if there was an error in applying these alerts then let the alert resource manager to fetch all the account related alerts again
            self.set_last_updated_at(updated_at=None)

            if isinstance(e, ApiException):
                info = AccountResourceStatusInfo(error=e.body)
                self.set_account_resource_status(status_type=AccountResourceStatusType.error, info=info)
            else:
                self.set_account_resource_status(status_type=AccountResourceStatusType.error, info=None)

            logging.error(f"Error occured while making prometheus alerts: {e}", exc_info=True)

            raise e

    def start(self, active_alert_rules: List[PrometheusAlertRule]) -> int:
        synced_item_count = 0
        try:
            sorted_active_rules: List[PrometheusAlertRule] = sorted(active_alert_rules, key=lambda x: x.alert)

            # Each CRD file has a limit of 700 rules. This limit is defined by the
            # [MAX_ALLOWED_RULES_PER_CRD_ALERT] variable. To adhere to this limit,
            # we calculate the number of iterations required. This calculation is
            # based on dividing the total number of active rules by the maximum
            # rules permitted per CRD.

            if self.__max_allowed_rules_per_crd == 0:
                max_iterations = 0
            else:
                max_iterations = math.ceil(len(sorted_active_rules) / self.__max_allowed_rules_per_crd)

            for next_iteration in range(0, max_iterations):
                start_index = next_iteration * self.__max_allowed_rules_per_crd
                end_index = (next_iteration + 1) * self.__max_allowed_rules_per_crd
                name = f"{self.__crd_name}--{(next_iteration + 1)}"

                sliced_alerts = sorted_active_rules[start_index:end_index]
                _, item_length = self.__create_crd_file(name=name, alerts=sliced_alerts)
                synced_item_count += item_length

            # When a user disables or deletes alerts from the sass platform, they may be
            # removed from [active_alert_rules] and consequently from the cluster
            # In certain edge cases, there's a possibility that these rules aren't entirely
            # cleared from the cluster or cache.
            # This typically happens when the [max_iterations] value is smaller than the size of the cached dictionary.
            # As a result, the above loop might not cover all crd file buckets, leaving
            # behind residual rules in both the cluster and cache.
            # The loop below ensures these residues are effectively cleaned up.
            cached_length = len(self.__crd_files_cache.keys())
            for next_iteration in range(max_iterations + 1, cached_length + 1):
                name = f"{self.__crd_name}--{next_iteration}"
                self.__delete_crd_file(name=name)

            return synced_item_count
        except Exception as e:
            logging.error(f"Error occured while creating prometheus alerts: {e}", exc_info=True)

            raise e

    def __get_snapshot_body(self, name: str, rules: List[dict]):
        return {
            "apiVersion": self.__k8_apiVersion,
            "kind": self.__kind,
            "metadata": {
                "name": name,
                "labels": {
                    "release": "robusta",
                    "role": "alert-rules",
                    self.__label_selector_key: self.__label_selector_value
                },
            },

            "spec": {
                "groups": [
                    {
                        "name": self.__group_name,
                        "rules": rules
                    }
                ]
            }
        }

    def __get_flattened_crd_files_cache_map(self) -> Dict[str, PrometheusAlertRule]:
        flattened_map = {}

        for sublist in self.__crd_files_cache.values():
            for item in sublist:
                # we need the deep copy to make sure than we do not modify the original cached object references
                flattened_map[item.labels.entity_id] = copy.deepcopy(item)

        return flattened_map

    def __list_alerts(self):
        try:
            return self.__k8_api.list_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                label_selector=self.__label_selector,
                namespace=self.__installation_namespace
            )
        except Exception as e:
            raise f"An error occured while listing PrometheusRules CRD: {e}"

    def __custom_object_exists(self, name: str):
        try:
            return self.__k8_api.get_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                namespace=self.__installation_namespace,
                name=name
            )
        except client.ApiException as e:
            if e.status == 404:
                return None
            else:
                raise e

    def __create_crd_file(self, name: str, alerts: List[PrometheusAlertRule]) -> Tuple[Optional[dict], int]:
        # Retrieve the cached alerts based on the given name, if it exists.
        cached_alerts: Optional[List[PrometheusAlertRule]] = self.__crd_files_cache.get(name)

        # If the provided alerts are the same as the cached items, do nothing and return None.
        if alerts == cached_alerts:
            return None, 0

        self.__crd_files_cache[name] = alerts
        rules = [rule.to_dict() for rule in alerts]

        try:
            # Check if a custom object with the given name already exists.
            existing_obj = self.__custom_object_exists(name=name)
            if existing_obj:
                if not existing_obj.get("spec"):
                    existing_obj["spec"] = {}

                if not existing_obj["spec"].get("groups"):
                    existing_obj["spec"]["groups"] = [{}]

                existing_obj["spec"]["groups"][0]["rules"] = rules

                # If a custom object with the given name already exists then replace the existing custom object with
                # the updated one.
                return self.__k8_api.replace_namespaced_custom_object(
                    group=self.__group,
                    version=self.__version,
                    plural=self.__plural,
                    body=existing_obj,
                    namespace=self.__installation_namespace,
                    name=name
                ), len(rules)
            else:
                # If the custom object doesn't exist, create a new one.
                return self.__k8_api.create_namespaced_custom_object(
                    group=self.__group,
                    version=self.__version,
                    plural=self.__plural,
                    body=self.__get_snapshot_body(name=name, rules=rules),
                    namespace=self.__installation_namespace
                ), len(rules)

        except Exception as e:
            # if there was an error in applying these alerts then reset the __crd_files_cache
            self.__crd_files_cache = {}
            logging.error(f"An error occured while creating PrometheusRules CRD: {e} ")

            raise e

    def __delete_crd_file(self, name: str):
        try:
            self.__k8_api.delete_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                namespace=self.__installation_namespace,
                name=name,
                grace_period_seconds=60
            )
            self.__crd_files_cache.pop(name, None)

        except Exception as e:
            logging.error(f"An error occured while deleting the PrometheusRules CRD: {e} ")

            raise e
