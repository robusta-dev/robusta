import logging
from typing import Optional, List
from kubernetes import client, config
import time
from robusta.core.model.env_vars import INSTALLATION_NAMESPACE, MAX_ALLOWED_RULES_PER_CRD_ALERT
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
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
    def __init__(self, dal: AccountResourceFetcher) -> None:
        super().__init__(ResourceKind.PrometheusAlert)
        self.dal = dal
        self.init_resources_max_attempts = 3
        self.__cdr_slots_len: List[int] = []
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
        """Initialize the resources

        If the API call fails, the initialization method will make additional attempts to list and delete
        the custom objects. If these attempts also fail, we will remove the failed resources from
        the __resource_managers list, rendering them inert.
        """

        exception: Optional[Exception] = None

        for itr in range(0, self.init_resources_max_attempts):
            try:
                # fetch the available crd files and then delete them in the first run
                crd_obj = self.__k8_api.list_namespaced_custom_object(
                    **CRD_PARAMS,
                    label_selector="release.app=robusta-resource-management"
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
                exception = e
                logging.error(
                    f"An error occurred while initializing PrometheusRules CRD resources: {e}. Attempting again..",
                    exc_info=True)
                time.sleep(5)

        if exception:
            raise exception

    def __find_available_crd_slot(self) -> int:
        """Fetch the first available slot in the crd files"""

        slot = index_of(self.__cdr_slots_len, lambda l: l < MAX_ALLOWED_RULES_PER_CRD_ALERT)
        if slot is not None:
            return slot

        self.__cdr_slots_len.append(0)
        return len(self.__cdr_slots_len) - 1

    def __append_rule(self, slot: int, resource: AccountResource):
        """Append rules to the crd files"""

        name = PrometheusAlertResourceManager.__crd_name(slot)

        rule = resource.resource_state.get('rule', {})
        labels = rule.get("labels", {}) or {}
        rule = {**rule, "labels": {**labels, "entity_id": resource.entity_id}}

        crd_obj = None
        try:
            crd_obj = self.__k8_api.get_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
            )
        except:
            pass

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
            raise f"An error occurred while replacing PrometheusRules CRD alert => entity: {resource}. Error: {e}"

    def __modify_rule(self, slot: int, resource: AccountResource):
        """Modify and apply rules to crd file"""

        try:
            name = PrometheusAlertResourceManager.__crd_name(slot)

            crd_obj = self.__k8_api.get_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
            )

            if not crd_obj:
                return

            index = index_of(crd_obj["spec"]["groups"][0]["rules"],
                             lambda r: r.get('labels', {}).get("entity_id") == resource.entity_id)
            if index >= len(crd_obj["spec"]["groups"][0]["rules"]):
                return

            rule = resource.resource_state.get('rule', {})
            labels = rule.get("labels", {}) or {}
            rule = {**rule, "labels": {**labels, "entity_id": resource.entity_id}}
            crd_obj["spec"]["groups"][0]["rules"][index] = rule

            self.__k8_api.replace_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
                body=crd_obj,
            )
        except Exception as e:
            raise f"An error occurred while modify PrometheusRules CRD alert => entity: {resource}. Error: {e}"

    def __write_first_rule(self, slot: int, rule):
        try:
            self.__k8_api.create_namespaced_custom_object(
                **CRD_PARAMS,
                body=PrometheusAlertResourceManager.__create_prometheus_rule_template(slot, [rule]),
            )
        except Exception as e:
            raise f"An error occurred while writing first rule to PrometheusRules CRD alert => rule: {rule}. Error: {e}"

    def __delete_rule(self, slot, resource: AccountResource):
        """Delete an existing rule from the crd file"""

        try:
            name = PrometheusAlertResourceManager.__crd_name(slot)

            crd_obj = self.__k8_api.get_namespaced_custom_object(
                **CRD_PARAMS,
                name=name,
            )

            if not crd_obj:
                return

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
            raise f"An error occurred while deleting rule to PrometheusRules CRD alert => entity: {resource}. Error: {e}"
