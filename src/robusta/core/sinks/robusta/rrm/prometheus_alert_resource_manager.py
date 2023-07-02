
from typing import Optional, Union
from kubernetes import client, config
from robusta.core.model.env_vars import INSTALLATION_NAMESPACE, MAX_ALLOWED_RULES_PER_CRD_ALERT
from robusta.core.sinks.robusta.rrm.types import AccountResource, BaseResourceManager, ResourceEntry, ResourceKind


class PrometheusAlertResourceEntry(ResourceEntry):
    slot: int


CRD_PARAMS = {
    "group": "monitoring.coreos.com",
    "version": "v1",
    "plural": "prometheusrules",
    "namespace": INSTALLATION_NAMESPACE,
}

# def find_first(array:list, f):
#     return next((e for e in array if f(e)), None)


def index_of(array: list, predicate):
    for i in range(len(array)):
        if predicate(array[i]):
            return i
    return None


class PrometheusAlertResourceManager(BaseResourceManager):
    def __init__(self) -> None:
        super().__init__(ResourceKind.PrometheusAlert)

        self.__cdr_slots_len: list[int] = []
        config.load_kube_config()
        self.__k8_api = client.CustomObjectsApi()

    def create_resource(self, resource: AccountResource) -> Union[ResourceEntry , None]:

        slot = self.__find_available_crd_slot()
        self.__append_rule(slot, resource)
        self._timestamp = resource.updated_at
        return PrometheusAlertResourceEntry(resource=resource, slot=slot)

    def update_resource(self, resource: AccountResource, old_entry: PrometheusAlertResourceEntry) -> Union[ResourceEntry , None]:

        slot = old_entry.slot
        self.__modify_rule(slot, resource)
        self._timestamp = resource.updated_at
        return old_entry

    def delete_resource(self, resource: AccountResource, old_entry: ResourceEntry) -> bool:
        slot = old_entry.slot
        self.__delete_rule(slot, resource)
        self._timestamp = resource.updated_at

        pass

    def init_resources(self) -> None:
        # TODO: delete old CRDs
        pass

    def __find_available_crd_slot(self):
        slot = index_of(self.__cdr_slots_len, lambda l: l < MAX_ALLOWED_RULES_PER_CRD_ALERT)
        if slot is not None:
            return slot
        else:
            self.__cdr_slots_len.append(0)
            return len(self.__cdr_slots_len) - 1

    def __append_rule(self, slot: int, resource: AccountResource):
        name = self.__crd_name(slot)
        crd_obj = self.__k8_api.get_namespaced_custom_object(
            **CRD_PARAMS,
            name=name,
        )

        rule = {**resource.resource_state['rule'], 'alert': resource.entity_id}
        # crate new if not found
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

    def __modify_rule(self, slot: int, resource: AccountResource):
        name = self.__crd_name(slot)
        crd_obj = self.__k8_api.get_namespaced_custom_object(
            **CRD_PARAMS,
            name=name,
        )

        index = index_of(crd_obj["spec"]["groups"][0]["rules"], lambda r: r['alert'] == resource.entity_id)
        # TODO: check index
        crd_obj["spec"]["groups"][0]["rules"][index] = {**resource.resource_state['rule'], 'alert': resource.entity_id}

        self.__k8_api.replace_namespaced_custom_object(
            **CRD_PARAMS,
            name=name,
            body=crd_obj,
        )

    def __write_first_rule(self, slot: int, rule):
        self.__k8_api.create_namespaced_custom_object(
            **CRD_PARAMS,
            body=self.__create_prometheus_rule_template(slot, [rule])
        )

    def __delete_rule(self, slot, resource: AccountResource):
        name = self.__crd_name(slot)
        crd_obj = self.__k8_api.get_namespaced_custom_object(
            **CRD_PARAMS,
            name=name,
        )

        index = index_of(crd_obj["spec"]["groups"][0]["rules"], lambda r: r['alert'] == resource.entity_id)
        # TODO: check index
        del crd_obj["spec"]["groups"][0]["rules"][index]

        self.__cdr_slots_len[slot] -= 1  # TODO: check <0

    def __create_prometheus_rule_template(self, slot: int, rules=[]):
        return {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "PrometheusRule",
            "metadata": {
                "name": self.__crd_name(slot),
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

    def __crd_name(self, slot: int):
        return f"robusta-prometheus.rules--{slot}"
