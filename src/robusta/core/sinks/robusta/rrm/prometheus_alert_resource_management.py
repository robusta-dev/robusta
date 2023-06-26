import logging
from datetime import datetime
from typing import Optional, List, Dict
from kubernetes.client import CustomObjectsApi

from robusta.core.model.env_vars import RRM_PERIOD_SEC, MAX_ALLOWED_RULES_PER_CRD_ALERT, INSTALLATION_NAMESPACE
from pydantic import BaseModel

from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal
from robusta.core.sinks.robusta.rrm.account_resource import ResourceKind


class PrometheusAlertAnnotations(BaseModel):
    description: Optional[str]
    runbook_url: Optional[str]
    summary: Optional[str]


class PrometheusAlertLabels(BaseModel):
    severity: Optional[str]
    entity_id: Optional[str]


class PrometheusAlertRule(BaseModel):
    alert: str
    annotations: Optional[PrometheusAlertAnnotations]
    expr: str
    duration: Optional[str]
    labels: Optional[PrometheusAlertLabels]

    @staticmethod
    def from_dict(data: dict, entity_id: str):
        labels_dict = data.get("labels", {})
        labels_dict["entity_id"] = entity_id
        labels = PrometheusAlertLabels(**labels_dict)

        annotations = None
        if data.get("annotations"):
            annotations = PrometheusAlertAnnotations(**data.get("annotations"))

        return PrometheusAlertRule(
            alert=data.get("alert"),
            annotations=annotations,
            expr=data.get("expr"),
            duration=data.get("for"),
            labels=labels,
        )

    def to_dict(self):
        result = self.dict()
        result["for"] = self.duration
        del result["duration"]

        return result


class PrometheusAlertResourceState(BaseModel):
    rule: PrometheusAlertRule

    @staticmethod
    def from_dict(data: dict, entity_id: str):
        rule = PrometheusAlertRule.from_dict(data.get("rule"), entity_id=entity_id)
        return PrometheusAlertResourceState(rule=rule)


class PrometheusAlertsEntity(BaseModel):
    bucket_name: str
    entity_id: str
    resource_state: PrometheusAlertResourceState
    updated_at: datetime
    deleted: bool


class PrometheusAlertResourceManagement:

    def __init__(self, k8_api: CustomObjectsApi, dal: SupabaseDal):
        self.dal = dal
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
        self.__prometheus_alert_entities_cache: Dict[str, PrometheusAlertsEntity] = {}
        self.__installation_namespace = INSTALLATION_NAMESPACE
        self.__latest_updated_at = None
        self.__first_run()

    def __first_run(self):
        local_k8_crd_object = self.__list_crd_objects()
        local_k8_alerts_list: List[dict] = local_k8_crd_object.get("items", [])

        for obj in local_k8_alerts_list:
            name = obj["metadata"]["name"]
            self.__replace_crd_alert(name=name, rules=[], alert_object=obj)
            self.__delete_crd_alert(name=name)

    def __get_crd_alert_bucket_iteration(self, next_iteration: int):
        return f"{self.__crd_alert_basename}--{next_iteration}"

    def start_checks(self):
        try:
            prometheus_alert_resources = self.dal. \
                get_account_resources(resource_kind=ResourceKind.PrometheusAlert,
                                      updated_at=self.__latest_updated_at)

            new_entities: List[PrometheusAlertsEntity] = []

            # if there are no existing crd alerts or if this is very first run then `next_alert_bucket_iteration` is 1
            next_alert_bucket_iteration = 1
            local_k8_alerts_map = self.__local_k8_alerts_map()
            if self.__latest_updated_at:
                local_k8_alerts_map_keys = list(local_k8_alerts_map.keys())
                next_alert_bucket_iteration = len(local_k8_alerts_map_keys)

            current_bucket_rules_count = 0
            for resource in prometheus_alert_resources:
                if self.__latest_updated_at is None or resource.updated_at > self.__latest_updated_at:
                    self.__latest_updated_at = resource.updated_at

                if not resource.resource_state or resource.resource_kind != ResourceKind.PrometheusAlert:
                    continue

                existing_cached_entity = self.__prometheus_alert_entities_cache.get(resource.entity_id)
                if existing_cached_entity:
                    next_entity = PrometheusAlertsEntity(
                        bucket_name=existing_cached_entity.bucket_name,
                        entity_id=resource.entity_id,
                        resource_state=PrometheusAlertResourceState.from_dict(resource.resource_state,
                                                                              entity_id=resource.entity_id, ),
                        updated_at=resource.updated_at,
                        deleted=resource.deleted
                    )
                    new_entities.append(next_entity)
                else:
                    next_crd_alert_bucket_name = self.__get_crd_alert_bucket_iteration(
                        next_iteration=next_alert_bucket_iteration)
                    if not current_bucket_rules_count:
                        # check if the total count of rules in the next iteration has crossed the allowed max rules per crd
                        # if yes, then increment the next_alert_bucket_iteration by 1
                        alert_rules = local_k8_alerts_map.get(next_crd_alert_bucket_name, [])
                        current_bucket_rules_count = len(alert_rules)

                    if current_bucket_rules_count >= self.__max_allowed_rules_per_crd_alert:
                        next_alert_bucket_iteration += 1
                        current_bucket_rules_count = 0
                        next_crd_alert_bucket_name = self.__get_crd_alert_bucket_iteration(
                            next_iteration=next_alert_bucket_iteration)
                    else:
                        current_bucket_rules_count += 1

                    next_entity = PrometheusAlertsEntity(
                        bucket_name=next_crd_alert_bucket_name,
                        entity_id=resource.entity_id,
                        resource_state=PrometheusAlertResourceState.from_dict(resource.resource_state,
                                                                              entity_id=resource.entity_id, ),
                        updated_at=resource.updated_at,
                        deleted=resource.deleted
                    )
                    new_entities.append(next_entity)

            self.__create_prometheus_alert_resources(new_entities=new_entities)
        except Exception as e:
            logging.error(f"Failed to get Account Resource. {e}", exc_info=True)

    @staticmethod
    def find_alert_object(local_k8_alerts_list: List[dict], name: str) -> Optional[dict]:
        if local_k8_alerts_list:
            for alert in local_k8_alerts_list:
                if name == alert["metadata"]["name"]:
                    return alert
        return None

    def __local_k8_alerts_map(self) -> Dict[str, List[dict]]:
        local_k8_alerts_object = self.__list_crd_objects()
        local_k8_alerts_list = local_k8_alerts_object.get("items", [])

        output: Dict[str, List[dict]] = {}
        for obj in local_k8_alerts_list:
            name = obj["metadata"]["name"]

            if not output.get(name):
                output[name] = []

            groups = obj.get("spec", {}).get("groups")
            if groups:
                output[name] = groups[0].get("rules", [])

        return output

    def __get_rules_map(self, new_entities: List[PrometheusAlertsEntity]) -> Dict[str, List[dict]]:
        local_k8_alerts_map = self.__local_k8_alerts_map()
        unaltered_buckets = list(local_k8_alerts_map.keys())

        for new_entity in new_entities:
            cached_alert_entity = self.__prometheus_alert_entities_cache.get(new_entity.entity_id)
            rules = local_k8_alerts_map.get(new_entity.bucket_name, [])

            # the new resource exists in the local cache
            # so update the existing rule or delete them if it has been updated
            if cached_alert_entity:
                if cached_alert_entity != new_entity:
                    for idx, rule in enumerate(rules):
                        if rule["labels"]["entity_id"] == new_entity.resource_state.rule.labels.entity_id:
                            if new_entity.deleted:
                                del self.__prometheus_alert_entities_cache[new_entity.entity_id]
                                del rules[idx]
                            else:
                                rules[idx] = new_entity.resource_state.rule.to_dict()
                                self.__prometheus_alert_entities_cache[new_entity.entity_id] = new_entity

                    if new_entity.bucket_name in unaltered_buckets:
                        unaltered_buckets.remove(new_entity.bucket_name)

                local_k8_alerts_map[new_entity.bucket_name] = rules

            # the new resource DOES NOT exist in the local cache
            # so create a new
            else:
                if new_entity.deleted:
                    continue

                rules.append(new_entity.resource_state.rule.to_dict())
                local_k8_alerts_map[new_entity.bucket_name] = rules
                self.__prometheus_alert_entities_cache[new_entity.entity_id] = new_entity

                if new_entity.bucket_name in unaltered_buckets:
                    unaltered_buckets.remove(new_entity.bucket_name)

        # remove the unaltered buckets from the final output to prevent updating an unaltered crd alert files
        for bucket in unaltered_buckets:
            del local_k8_alerts_map[bucket]

        return local_k8_alerts_map

    def __create_prometheus_alert_resources(self, new_entities: List[PrometheusAlertsEntity]):
        try:
            rule_map = self.__get_rules_map(new_entities=new_entities)

            local_k8_alerts_object = self.__list_crd_objects()
            local_k8_alerts_items = local_k8_alerts_object.get("items", [])

            local_k8_alerts_map: Dict[str, dict] = {}
            for obj in local_k8_alerts_items:
                name = obj["metadata"]["name"]
                local_k8_alerts_map[name] = obj

            for bucket_name, rules in rule_map.items():
                alert_obj = local_k8_alerts_map.get(bucket_name)
                if alert_obj:
                    self.__replace_crd_alert(name=bucket_name, alert_object=alert_obj, rules=rules)
                else:
                    self.__create_crd_alert(name=bucket_name, rules=rules)

        except Exception as e:
            raise f"An error occured while creating alert resources: {e}"

    def __list_crd_objects(self) -> dict:
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

    def __replace_crd_alert(self, name: str, rules: List[dict], alert_object: dict):
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
            raise f"An error occured while replacing PrometheusRules CRD alerts: {e}"

    def __delete_crd_alert(self, name: str):
        try:
            self.__k8_api.delete_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                name=name,
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
