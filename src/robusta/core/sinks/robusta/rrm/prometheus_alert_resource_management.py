import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional, List, Dict
from kubernetes.client import CustomObjectsApi, exceptions

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
    clusters_target_set: Optional[List[str]] = None


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

    def first_run(self):
        try:
            local_k8_crd_object = self.__list_crd_objects()
            local_prometheus_crd_files_list: List[dict] = local_k8_crd_object.get("items", [])

            for obj in local_prometheus_crd_files_list:
                name = obj["metadata"]["name"]
                self.__delete_crd_alert(name=name)
        except Exception as e:
            logging.error(f"An error occured while first run PrometheusRules CRD alerts: {e}")

    def __get_prometheus_file_name(self, next_index: int):
        return f"{self.__crd_alert_basename}--{next_index}"

    def __is_of_this_cluster(self, clusters_target_set: List[str] = []):
        return "*" in clusters_target_set or self.dal.cluster in clusters_target_set

    def start_checks(self):
        try:
            prometheus_alert_resources = self.dal. \
                get_account_resources(resource_kind=ResourceKind.PrometheusAlert,
                                      updated_at=self.__latest_updated_at)

            new_entities: List[PrometheusAlertsEntity] = []

            local_prometheus_crd_bucket_map = self.__get_local_prometheus_crd_files_bucket_map()
            next_alert_bucket_index = 1
            items_added_to_next_bucket = 0
            for resource in prometheus_alert_resources:
                if self.__latest_updated_at is None or resource.updated_at > self.__latest_updated_at:
                    self.__latest_updated_at = resource.updated_at

                if not resource.resource_state or resource.resource_kind != ResourceKind.PrometheusAlert:
                    continue

                # if the entity exists in the cache
                existing_cached_entity = self.__prometheus_alert_entities_cache.get(resource.entity_id)
                if existing_cached_entity:
                    # mark the entity as deleted, if it has been deleted or
                    # mark it for deletion if the cluster_target_set of the entity no longer contains this cluster name
                    deleted = resource.deleted or not self.__is_of_this_cluster \
                        (clusters_target_set=resource.clusters_target_set)

                    next_entity = PrometheusAlertsEntity(
                        bucket_name=existing_cached_entity.bucket_name,
                        entity_id=resource.entity_id,
                        resource_state=PrometheusAlertResourceState.from_dict(resource.resource_state,
                                                                              entity_id=resource.entity_id, ),
                        updated_at=resource.updated_at,
                        deleted=deleted,
                        clusters_target_set=resource.clusters_target_set
                    )
                    new_entities.append(next_entity)
                else:
                    # if the new entities does not belong to this cluster then ignore
                    not_of_this_cluster = not self.__is_of_this_cluster(clusters_target_set=
                                                                        resource.clusters_target_set)
                    if not_of_this_cluster:
                        continue

                    # iterate through every bucket whenever there is are new entities to make sure we fill the
                    # empty or partially filled buckets first then proceed to create a new bucket if required
                    sliced_local_prometheus_rules = list(local_prometheus_crd_bucket_map.items())[
                                                    next_alert_bucket_index - 1:]
                    append_to_an_exisiting_bucket = False

                    # if there are partially filled buckets left or empty buckets left then scan through then
                    # determine the remaining slots for the rules and fill them up
                    if sliced_local_prometheus_rules:
                        for key, cached_rules in sliced_local_prometheus_rules:
                            total_items_in_next_bucket = items_added_to_next_bucket + len(cached_rules)

                            # if the total items in the "bucket of interest" has been filled
                            # then move over to the next bucket
                            if total_items_in_next_bucket >= self.__max_allowed_rules_per_crd_alert:
                                next_alert_bucket_index += 1
                                items_added_to_next_bucket = 0
                            else:
                                # if the bucket isnt filled then increment the items count
                                items_added_to_next_bucket += 1
                                append_to_an_exisiting_bucket = True
                                break

                    # if the slots in the existing bucket were exhausted then work out the next possible crd file index
                    if not append_to_an_exisiting_bucket:
                        if items_added_to_next_bucket >= self.__max_allowed_rules_per_crd_alert:
                            next_alert_bucket_index += 1
                            items_added_to_next_bucket = 1
                        else:
                            items_added_to_next_bucket += 1

                    next_crd_alert_bucket_name = self.__get_prometheus_file_name(next_index=next_alert_bucket_index)

                    next_entity = PrometheusAlertsEntity(
                        bucket_name=next_crd_alert_bucket_name,
                        entity_id=resource.entity_id,
                        resource_state=PrometheusAlertResourceState.from_dict(resource.resource_state,
                                                                              entity_id=resource.entity_id, ),
                        updated_at=resource.updated_at,
                        deleted=resource.deleted,
                        clusters_target_set=resource.clusters_target_set
                    )
                    new_entities.append(next_entity)

            self.__create_prometheus_alert_resources(new_entities=new_entities)
        except Exception as e:
            logging.error(f"Failed to get Account Resource. {e}", exc_info=True)

    @staticmethod
    def find_alert_object(local_prometheus_crd_files_list: List[dict], name: str) -> Optional[dict]:
        if local_prometheus_crd_files_list:
            for alert in local_prometheus_crd_files_list:
                if name == alert["metadata"]["name"]:
                    return alert
        return None

    # Get a map of Prometheus CRD bucket files and their associated rules
    def __get_local_prometheus_crd_files_bucket_map(self) -> Dict[str, List[dict]]:
        output: Dict[str, List[dict]] = defaultdict(list)
        for value in self.__prometheus_alert_entities_cache.values():
            output[value.bucket_name].append(value.resource_state.rule.to_dict())

        return output

    # Get a map of rules of new Prometheus alert entities after scanning the existing CRD buckets
    def __get_rules_map(self, new_entities: List[PrometheusAlertsEntity]) -> Dict[str, List[dict]]:
        local_prometheus_crd_bucket_map = self.__get_local_prometheus_crd_files_bucket_map()
        unaltered_buckets = list(local_prometheus_crd_bucket_map.keys())

        for new_entity in new_entities:
            cached_alert_entity = self.__prometheus_alert_entities_cache.get(new_entity.entity_id)
            rules = local_prometheus_crd_bucket_map.get(new_entity.bucket_name, [])

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

                local_prometheus_crd_bucket_map[new_entity.bucket_name] = rules

            # the new resource DOES NOT exist in the local cache so create a new one
            else:
                if new_entity.deleted:
                    continue

                rules.append(new_entity.resource_state.rule.to_dict())
                local_prometheus_crd_bucket_map[new_entity.bucket_name] = rules
                self.__prometheus_alert_entities_cache[new_entity.entity_id] = new_entity

                if new_entity.bucket_name in unaltered_buckets:
                    unaltered_buckets.remove(new_entity.bucket_name)

        # remove the unaltered buckets from the final output to prevent updating an unaltered crd alert files
        for bucket in unaltered_buckets:
            del local_prometheus_crd_bucket_map[bucket]

        return local_prometheus_crd_bucket_map

    def __create_prometheus_alert_resources(self, new_entities: List[PrometheusAlertsEntity]):
        try:
            rule_map = self.__get_rules_map(new_entities=new_entities)

            for bucket_name, rules in rule_map.items():
                self.__create_or_replace_crd_alert(name=bucket_name, rules=rules)

        except Exception as e:
            raise f"An error occured while creating alert resources: {e}"

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

    def __get_crd_object(self, name: str) -> Optional[dict]:
        try:
            return self.__k8_api.get_namespaced_custom_object(
                group=self.__group,
                version=self.__version,
                plural=self.__plural,
                namespace=self.__installation_namespace,
                name=name,
            )
        except Exception as e:
            if isinstance(e, exceptions.ApiException) and e.status == 404:
                return None
            raise f"An error occured while fetching PrometheusRules CRD alert: {e}"

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

    def __replace_crd_alert(self, name: str, rules: List[dict], alert_object: Optional[dict] = None):
        try:
            if not alert_object:
                alert_object = self.__get_crd_object(name=name)

            if not alert_object:
                return

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
                grace_period_seconds=60
            )
        except Exception as e:
            raise f"An error occured while deleting PrometheusRules CRD alerts: {e}"

    def __create_crd_alert(self, name: str, rules: List[dict]):
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

    def __create_or_replace_crd_alert(self, name: str, rules: List[dict]):
        try:
            alert_object = self.__get_crd_object(name=name)

            if alert_object:
                self.__replace_crd_alert(name=name, rules=rules, alert_object=alert_object)
            else:
                self.__create_crd_alert(name=name, rules=rules)

        except Exception as e:
            raise f"An error occured while creating PrometheusRules CRD alerts: {e}"
