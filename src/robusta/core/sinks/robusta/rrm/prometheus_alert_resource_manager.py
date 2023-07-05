import logging
from typing import Optional, Union
from kubernetes import client, config
from kubernetes.client import exceptions
from robusta.core.model.env_vars import INSTALLATION_NAMESPACE, MAX_ALLOWED_RULES_PER_CRD_ALERT
from robusta.core.sinks.robusta.rrm.types import AccountResource, BaseResourceManager, ResourceEntry, ResourceKind
from robusta.utils.common import index_of


class PrometheusAlertResourceEntry(ResourceEntry):
    slot: int


CRD_PARAMS = {
    "group": "monitoring.coreos.com",
    "version": "v1",
    "plural": "prometheusrules",
    "namespace": INSTALLATION_NAMESPACE,
}


class PrometheusAlertResourceManager(BaseResourceManager):
    def __init__(self) -> None:
        super().__init__(ResourceKind.PrometheusAlert)

        self.__cdr_slots_len: list[int] = []
        config.load_kube_config()
        self.__k8_api = client.CustomObjectsApi()

    @staticmethod
    def __crd_name(slot: int):
        return f"robusta-prometheus.rules--{slot}"

    @staticmethod
    def __create_prometheus_rule_template(slot: int, rules=[]):
        return {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "PrometheusRule",
            "metadata": {
                "name": PrometheusAlertResourceManager.__crd_name(slot),
                "labels": {
                    "release": "robusta",
                    "role": "alert-rules",
                    "release.app": "robusta-resource-management"
                },
            },

            "spec": {
                "groups": [
                    {
                        "name": f"rule-{slot}",
                        "rules": rules
                    }
                ]
            }
        }

    def create_resource(self, resource: AccountResource) -> Optional[ResourceEntry]:
        slot = self.__find_available_crd_slot()
        self.__append_rule(slot, resource)
        self._timestamp = resource.updated_at
        return PrometheusAlertResourceEntry(resource=resource, slot=slot)

    def update_resource(self, resource: AccountResource, old_entry: PrometheusAlertResourceEntry) -> Optional[
        ResourceEntry]:
        slot = old_entry.slot
        self.__modify_rule(slot, resource)
        self._timestamp = resource.updated_at
        return old_entry

    def delete_resource(self, resource: AccountResource, old_entry: PrometheusAlertResourceEntry) -> bool:
        slot = old_entry.slot
        self.__delete_rule(slot, resource)
        self._timestamp = resource.updated_at

        return True

    # initialize the resources
    def init_resources(self):
        try:
            # fetch the available crd files and then delete them in the first run
            crd_obj = self.__k8_api.list_namespaced_custom_object(
                **CRD_PARAMS,
                label_selector="release.app=robusta-resource-management",
            )

            items = crd_obj["items"]
            for obj in items:
                name = obj["metadata"]["name"]
                self.__k8_api.delete_namespaced_custom_object(
                    **CRD_PARAMS,
                    name=name,
                    grace_period_seconds=60
                )
        except Exception as e:
            logging.error(f"An error occured while initializing PrometheusRules CRD resources: {e}", exc_info=True)

    # fetch the first available slot in the crd files
    def __find_available_crd_slot(self) -> int:
        slot = index_of(self.__cdr_slots_len, lambda l: l < MAX_ALLOWED_RULES_PER_CRD_ALERT)
        if slot is not None:
            return slot

        self.__cdr_slots_len.append(0)
        return len(self.__cdr_slots_len) - 1

    # append rules to the crd files
    def __append_rule(self, slot: int, resource: AccountResource):
        name = PrometheusAlertResourceManager.__crd_name(slot)

        if "rule" not in resource.resource_state:
            resource.resource_state["rule"] = {}

        rule = resource.resource_state.get('rule')
        if "labels" not in rule:
            rule["labels"] = {}
        rule["labels"]["entity_id"] = resource.entity_id

        crd_obj = None
        try:
            crd_obj = self.__k8_api.get_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
            )
        except Exception as e:
            # If the crd file does not exist, a new crd file will be created.
            # Only raise an error if it's not a 404 exception.
            if not (isinstance(e, exceptions.ApiException) and e.status == 404):
                raise f"An error occurred while fetching PrometheusRules CRD alert: {e}"

        try:
            # create new if not found
            if crd_obj is None:
                self.__write_first_rule(slot, rule)
            else:
                crd_obj["spec"]["groups"][0]["rules"].append(rule)
                self.__k8_api.replace_namespaced_custom_object(
                    **CRD_PARAMS,
                    name=name,
                    body=crd_obj,
                )
            self.__cdr_slots_len[slot] += 1
        except Exception as e:
            raise f"An error occured while replacing PrometheusRules CRD alert => entity: {resource}. Error: {e}"

    # modify and apply rules to crd file
    def __modify_rule(self, slot: int, resource: AccountResource):
        try:
            name = PrometheusAlertResourceManager.__crd_name(slot)

            crd_obj = self.__k8_api.get_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
            )

            index = index_of(crd_obj["spec"]["groups"][0]["rules"],
                             lambda r: r["labels"]["entity_id"] == resource.entity_id)
            if index >= len(crd_obj["spec"]["groups"][0]["rules"]):
                return

            rule = resource.resource_state['rule']
            if "labels" not in rule:
                rule["labels"] = {}
            rule["labels"]["entity_id"] = resource.entity_id
            crd_obj["spec"]["groups"][0]["rules"][index] = rule

            self.__k8_api.replace_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
                body=crd_obj,
            )
        except Exception as e:
            raise f"An error occured while modify PrometheusRules CRD alert => entity: {resource}. Error: {e}"

    def __write_first_rule(self, slot: int, rule):
        try:
            self.__k8_api.create_namespaced_custom_object(
                **CRD_PARAMS,
                body=PrometheusAlertResourceManager.__create_prometheus_rule_template(slot, [rule]),
            )
        except Exception as e:
            raise f"An error occured while writing first rule to PrometheusRules CRD alert => rule: {rule}. Error: {e}"

    # delete an existing rule from the crd file
    def __delete_rule(self, slot, resource: AccountResource):
        try:
            name = PrometheusAlertResourceManager.__crd_name(slot)

            crd_obj = self.__k8_api.get_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
            )

            index = index_of(crd_obj["spec"]["groups"][0]["rules"],
                             lambda r: r["labels"]["entity_id"] == resource.entity_id)
            if index >= len(crd_obj["spec"]["groups"][0]["rules"]):
                return

            del crd_obj["spec"]["groups"][0]["rules"][index]

            self.__k8_api.replace_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
                body=crd_obj,
            )

            self.__cdr_slots_len[slot] = max(0, self.__cdr_slots_len[slot] - 1)
        except Exception as e:
            raise f"An error occured while deleting rule to PrometheusRules CRD alert => entity: {resource}. Error: {e}"
