import logging
import math
from typing import List, Dict, Optional
from kubernetes import client
from kubernetes.client import ApiException

from robusta.core.model.env_vars import INSTALLATION_NAMESPACE, MAX_ALLOWED_RULES_PER_CRD_ALERT, RRM_PERIOD_SEC, \
    RELEASE_NAME
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.base_resource_manager import BaseResourceManager
from robusta.core.sinks.robusta.rrm.types import PrometheusAlertRule, \
    AccountResource, ResourceKind, AccountResourceStatusType, AccountResourceStatusInfo


class PrometheusAlertResourceManager(BaseResourceManager):
    def __init__(self, cluster: str, resource_kind: ResourceKind, dal: AccountResourceFetcher):
        super().__init__(resource_kind, cluster, dal)
        self.__sleep = RRM_PERIOD_SEC
        self.cluster = cluster
        self.__max_allowed_rules_per_crd = MAX_ALLOWED_RULES_PER_CRD_ALERT
        self.__label_selector_key = "release.app"
        self.__label_selector_value = "robusta-resource-management"
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
        self.__alerts_config_supabase_cache: Dict[str, PrometheusAlertRule] = {}

    def __in_cluster(self, clusters_target_set: List[str] = []) -> bool:
        return "*" in clusters_target_set or self.cluster in clusters_target_set

    def __list_rules_objects(self) -> Optional[Dict[str, dict]]:
        try:
            return self.__k8_api.list_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                namespace=self.__installation_namespace,
                label_selector=f"{self.__label_selector}"
            )
        except client.ApiException as e:
            if e.status == 404:
                return None
            else:
                raise e

    def __exisiting_rules_objects_map(self) -> Optional[Dict[str, dict]]:
        objs = self.__list_rules_objects()

        if not objs:
            return None

        obj_items = objs.get("items", [])

        result: Dict[str, dict] = {}
        for item in obj_items:
            name = item.get("metadata").get("name")
            result[name] = item

        return result

    def __get_snapshot_body(self, name: str, rules: List[dict]):
        return {
            "apiVersion": self.__k8_apiVersion,
            "kind": self.__kind,
            "metadata": {
                "name": name,
                "labels": {
                    "release": RELEASE_NAME,
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

    def __create_cr_rules(self, name: str, active_rules: List[PrometheusAlertRule], existing_cr_obj: Optional[dict]) -> \
            Optional[dict]:
        try:
            rules = [rule.to_dict() for rule in active_rules]
            if existing_cr_obj:
                if not existing_cr_obj.get("spec"):
                    existing_cr_obj["spec"] = {}

                if not existing_cr_obj["spec"].get("groups"):
                    existing_cr_obj["spec"]["groups"] = [{}]

                existing_cr_obj["spec"]["groups"][0]["rules"] = rules

                # If a custom object with the given name already exists then replace the existing custom object with
                # the updated one.
                return self.__k8_api.replace_namespaced_custom_object(
                    group=self.__group,
                    version=self.__version,
                    plural=self.__plural,
                    body=existing_cr_obj,
                    namespace=self.__installation_namespace,
                    name=name
                )
            else:
                # If the custom object doesn't exist, create a new one.
                return self.__k8_api.create_namespaced_custom_object(
                    group=self.__group,
                    version=self.__version,
                    plural=self.__plural,
                    body=self.__get_snapshot_body(name=name, rules=rules),
                    namespace=self.__installation_namespace
                )

        except Exception as e:
            logging.error(f"An error occured while creating PrometheusRules CRD", exc_info=True)

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

        except Exception as e:
            logging.error(f"An error occured while deleting the PrometheusRules CRD", exc_info=True)

            raise e

    def start_syncing_alerts(self, account_resources: List[AccountResource]):
        for res in account_resources:
            if res.resource_state:
                rule_dict = res.resource_state.get("rule")
                rule: PrometheusAlertRule = PrometheusAlertRule.from_supabase_dict(rule_dict)

                in_cluster = self.__in_cluster(res.clusters_target_set)

                # Case 1: Remove the rule from the cache if it's marked as deleted.
                # Case 2: Remove the rule from the cache if it's NOT marked as enabled.
                # Case 3: Remove the rule from the cache if it's not assigned to the cluster anymore.
                if res.deleted or not res.enabled or not in_cluster:
                    if res.entity_id in self.__alerts_config_supabase_cache:
                        del self.__alerts_config_supabase_cache[res.entity_id]
                    continue

                if in_cluster:
                    self.__alerts_config_supabase_cache[res.entity_id] = rule

        self.prepare_syncing_rules()

    def prepare_syncing_rules(self):
        try:
            sorted_active_rules: List[PrometheusAlertRule] = sorted(
                list(self.__alerts_config_supabase_cache.values()),
                key=lambda x: x.alert)

            existing_cr_map = self.__exisiting_rules_objects_map()

            # Each CRD file has a limit of 700 rules. This limit is defined by the
            # [MAX_ALLOWED_RULES_PER_CRD_ALERT] variable. To adhere to this limit,
            # we calculate the number of iterations required. This calculation is
            # based on dividing the total number of active rules by the maximum
            # rules permitted per CRD.
            max_iterations = math.ceil(len(sorted_active_rules) / self.__max_allowed_rules_per_crd)

            for next_iteration in range(0, max_iterations):
                start_index = next_iteration * self.__max_allowed_rules_per_crd
                end_index = (next_iteration + 1) * self.__max_allowed_rules_per_crd
                name = f"{self.__crd_name}--{(next_iteration + 1)}"

                sliced_rules = sorted_active_rules[start_index:end_index]

                existing_cr_obj = existing_cr_map.get(name)
                self.__create_cr_rules(name=name, active_rules=sliced_rules, existing_cr_obj=existing_cr_obj)

                if existing_cr_obj:
                    # pop the already processed CR Object, if they exists
                    existing_cr_map.pop(name, None)

            # Clean up non-relevant CRDs, if they exists
            for existing_cr_name in existing_cr_map.keys():
                self.__delete_crd_file(name=existing_cr_name)

        except Exception as e:
            if isinstance(e, ApiException):
                info = AccountResourceStatusInfo(error=e.body)
                self.set_account_resource_status(status_type=AccountResourceStatusType.error, info=info)
            else:
                self.set_account_resource_status(status_type=AccountResourceStatusType.error, info=None)

            logging.error(f"Error occured while creating prometheus alerts", exc_info=True)

            raise e
