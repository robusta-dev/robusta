import logging
import threading
import time
from typing import List

from kubernetes import client, config
from robusta.core.model.env_vars import RRM_PERIOD_SEC, MAX_ALLOWED_RULES_PER_CRD
from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal
from robusta.core.sinks.robusta.rrm.prometheus_alert_resource_management import \
    PrometheusAlertResourceState, PrometheusAlertRule


# robusta resource management
class RRM:
    def __init__(self, dal: SupabaseDal, global_config: dict):
        self.dal = dal
        self.__sleep = RRM_PERIOD_SEC
        self.__max_allowed_rules_per_crd = MAX_ALLOWED_RULES_PER_CRD
        self.__global_config = global_config
        config.load_kube_config()
        self.__api = client.CustomObjectsApi()
        self.__label_selector_value = "robusta-resource-management"
        self.__label_selector_key = "release.app"
        self.__label_selector = f"{self.__label_selector_key}={self.__label_selector_value}"
        self.__plural = "prometheusrules"
        self.__group = "monitoring.coreos.com"
        self.__group_name = "kubernetes-apps"
        self.__version = "v1"
        self.__apiVersion = f"{self.__group}/{self.__version}"
        self.__kind = "PrometheusRule"
        self.__crd_name = "robusta-prometheus.rules"
        self.__thread = threading.Thread(target=self.__run_checks)
        self.__thread.start()

    def __run_checks(self):
        while True:
            try:
                self.account_resource_checks()

                time.sleep(self.__sleep)
            except Exception as e:
                logging.error(e)

    def __list_crd(self):
        try:
            return self.__api.list_cluster_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                label_selector=self.__label_selector
            )
        except Exception as e:
            raise f"An error occured while listing PrometheusRules CRD: {e}"

    def __delete_crd(self, name: str, namespace: str):
        try:
            self.__api.delete_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                name=name,
                namespace=namespace,
            )
        except Exception as e:
            raise f"An error occured while deleting PrometheusRules CRD: {e}"

    def __create_crd(self, name: str, rules: List[dict]) -> dict:
        try:
            snapshot_body = {
                "apiVersion": self.__apiVersion,
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

            return self.__api.create_cluster_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                body=snapshot_body
            )
        except Exception as e:
            raise f"An error occured while creating PrometheusRules CRD: {e}"

    def __create_prometheus_alerts(self, active_alert_rules: List[PrometheusAlertRule]):
        try:
            local_k8_crd = self.__list_crd()
            local_k8_rules = local_k8_crd.get("items")
            sorted_local_k8_rules: List[PrometheusAlertRule] = []
            if local_k8_rules:
                rules = []
                for obj in local_k8_rules:
                    groups = obj.get("spec", {}).get("groups")
                    if groups and groups[0].get("rules"):
                        rules.extend(groups[0].get("rules"))

                sorted_local_k8_rules = [PrometheusAlertRule.from_dict(item) for item in
                                         sorted(rules, key=lambda x: x["alert"])]

            sorted_active_rules: List[PrometheusAlertRule] = []
            if active_alert_rules:
                sorted_active_rules = sorted(active_alert_rules, key=lambda x: x.alert)

                # both local k8 rules and active rules from supabase are NOT same. Recreate the crd(s)
                if sorted_active_rules != sorted_local_k8_rules:
                    for obj in local_k8_rules:
                        self.__delete_crd(name=obj["metadata"]["name"], namespace=obj["metadata"]["namespace"])
                # both local k8 rules and active rules from supabase are the same. So dont recreate the crd(s)
                else:
                    return

            next_iteration = int((len(sorted_active_rules) / self.__max_allowed_rules_per_crd)) + 1
            name = f"{self.__crd_name}--{next_iteration}"
            new_crd_rules = [item.to_dict() for item in sorted_active_rules]
            self.__create_crd(name=name, rules=new_crd_rules)
        except Exception as e:
            logging.error(f"Error occured while creating prometheus alerts: {e}", exc_info=True)

    def account_resource_checks(self):
        try:
            account_resources = self.dal.get_account_resources()
            prometheus_rules = []
            for resource in account_resources:
                if isinstance(resource.resource_state, PrometheusAlertResourceState):
                    prometheus_rules.append(resource.resource_state.rule)

            self.__create_prometheus_alerts(active_alert_rules=prometheus_rules)
        except Exception as e:
            logging.error(f"Failed to get Account Resource. {e}", exc_info=True)
