import logging
from typing import Optional, List, Dict
from kubernetes.client import CustomObjectsApi

from robusta.core.model.env_vars import RRM_PERIOD_SEC, MAX_ALLOWED_RULES_PER_CRD_ALERT, INSTALLATION_NAMESPACE
from pydantic import BaseModel

from robusta.core.sinks.robusta.rrm.resource_state import ResourceState


class PrometheusAlertAnnotations(BaseModel):
    description: Optional[str]
    runbook_url: Optional[str]
    summary: Optional[str]


class PrometheusAlertLabels(BaseModel):
    severity: Optional[str]


class PrometheusAlertRule(BaseModel):
    alert: str
    annotations: Optional[PrometheusAlertAnnotations]
    expr: str
    duration: Optional[str]
    labels: Optional[PrometheusAlertLabels]

    @staticmethod
    def from_dict(data: dict):
        return PrometheusAlertRule(
            alert=data.get("alert"),
            annotations=data.get("annotations"),
            expr=data.get("expr"),
            duration=data.get("for"),
            labels=data.get("labels"),
        )

    def to_dict(self):
        result = self.dict()
        result["for"] = self.duration
        del result["duration"]

        return result


class PrometheusAlertResourceState(ResourceState):
    rule: PrometheusAlertRule

    @staticmethod
    def from_dict(data: dict):
        rule = PrometheusAlertRule.from_dict(data.get("rule"))
        return PrometheusAlertResourceState(rule=rule)


class PrometheusAlertResourceManagement:

    def __init__(self, k8_api: CustomObjectsApi):
        self.__sleep = RRM_PERIOD_SEC
        self.__max_allowed_rules_per_crd_alert = MAX_ALLOWED_RULES_PER_CRD_ALERT
        self.__k8_api = k8_api
        self.__label_selector_value = "robusta-resource-management"
        self.__label_selector_key = "release.app"
        self.__label_selector = f"{self.__label_selector_key}={self.__label_selector_value}"
        self.__plural = "prometheusrules"
        self.__group = "monitoring.coreos.com"
        self.__group_name = "kubernetes-apps"
        self.__version = "v1"
        self.__k8_apiVersion = f"{self.__group}/{self.__version}"
        self.__kind = "PrometheusRule"
        self.__crd_alert_basename = "robusta-prometheus.rules"
        self.__installation_namespace = INSTALLATION_NAMESPACE

    def __list_crd_objects(self):
        try:
            return self.__k8_api.list_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                label_selector=self.__label_selector,
                namespace=self.__installation_namespace
            )
        except Exception as e:
            raise f"An error occured while listing PrometheusRules CRD alerts: {e}"

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

    def __replace_crd_alert(self, name: str, rules: List[dict], alert_object: Dict[str, dict]):
        try:
            alert_object["spec"]["groups"][0]["rules"] = rules

            self.__k8_api.replace_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                name=name,
                body=alert_object,
                namespace=self.__installation_namespace,
            )
        except Exception as e:
            raise f"An error occured while deleting PrometheusRules CRD alerts: {e}"

    def __create_crd_alert(self, name: str, rules: List[dict]) -> dict:
        try:
            return self.__k8_api.create_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                body=self.__get_snapshot_body(name=name, rules=rules),
                namespace=self.__installation_namespace
            )
        except Exception as e:
            raise f"An error occured while creating PrometheusRules CRD alerts: {e}"

    def __write_rules(self, active_alert_rules: List[PrometheusAlertRule], local_k8_alerts: List[dict]):
        try:
            max_alert_rules_iterations = int((len(active_alert_rules) / self.__max_allowed_rules_per_crd_alert)) + 1
            max_local_k8_alerts_iterations = len(local_k8_alerts)

            local_k8_alerts_names: Dict[str, dict] = {}
            for obj in local_k8_alerts:
                local_k8_alerts_names[obj["metadata"]["name"]] = obj

            # we need to partition the crd alert since only a maximum of approx ~726 rules can be applied to a single
            # crd item
            for next_iteration in range(1, (max(max_alert_rules_iterations, max_local_k8_alerts_iterations)) + 1):
                start_index = (next_iteration - 1) * self.__max_allowed_rules_per_crd_alert
                end_index = next_iteration * self.__max_allowed_rules_per_crd_alert
                name = f"{self.__crd_alert_basename}--{next_iteration}"

                crd_alert_rules = [item.to_dict() for item in active_alert_rules[start_index:end_index]]

                # if the crd alert name already exists in the cluster then replace the rules
                if name in local_k8_alerts_names:
                    self.__replace_crd_alert(name=name, rules=crd_alert_rules, alert_object=local_k8_alerts_names[name])
                # else create an alerts with the rules
                else:
                    self.__create_crd_alert(name=name, rules=crd_alert_rules)
        except Exception as e:
            raise f"An error occured while writing PrometheusRules CRD alerts: {e}"

    def create_prometheus_alerts(self, active_alert_rules: List[PrometheusAlertRule]):
        try:
            local_k8_crd_object = self.__list_crd_objects()
            local_k8_alerts = local_k8_crd_object.get("items", [])
            sorted_local_k8_rules: List[PrometheusAlertRule] = []
            if local_k8_alerts:
                rules = []
                for obj in local_k8_alerts:
                    groups = obj.get("spec", {}).get("groups")
                    if groups and groups[0].get("rules"):
                        rules.extend(groups[0].get("rules"))

                sorted_local_k8_rules = [PrometheusAlertRule.from_dict(item) for item in
                                         sorted(rules, key=lambda x: x["alert"])]

            sorted_active_rules = sorted(active_alert_rules, key=lambda x: x.alert)

            # both local k8 rules and active rules from supabase are same, stop
            if sorted_active_rules == sorted_local_k8_rules:
                return

            self.__write_rules(active_alert_rules=sorted_active_rules, local_k8_alerts=local_k8_alerts)
        except Exception as e:
            logging.error(f"Error occured while creating prometheus alerts: {e}", exc_info=True)
