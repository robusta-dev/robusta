from pydantic import SecretStr

from robusta.api import *


class ConfigurationSet(BaseModel):
    config_set_name: str
    config_items: Dict[str, str] = {}


class ABTestingParams(BaseModel):
    grafana_url: str = "http://kube-prometheus-stack-1616314181-grafana.default.svc"
    grafana_api_key: SecretStr
    grafana_dashboard_uid: str
    api_version: str = "v1"
    kind: str
    name: str
    namespace: str = "default"
    configuration_sets: List[ConfigurationSet]

    def pre_deploy_func(self, trigger_params: TriggerParams):
        trigger_params.repeat = len(self.configuration_sets)


@on_recurring_trigger(seconds_delay=None)
def config_ab_testing(event: RecurringTriggerEvent, action_params: ABTestingParams):
    """Change configuration according to pre-defined configuration sets."""
    if len(action_params.configuration_sets) < event.recurrence:
        logging.error(
            f"No matching configuration set for recurrence {event.recurrence}"
        )
        return

    next_config_set = action_params.configuration_sets[event.recurrence]
    object_class = get_api_version(action_params.api_version).get(action_params.kind)
    if object_class is None:
        logging.error(f"No matching tested kind {action_params.kind}")
        return

    # TODO: get rid of this ugly hack once we have a generic read() function on hikaru classes
    reader_function = getattr(object_class, f"readNamespaced{object_class.kind}")
    tested_object = reader_function(action_params.name, action_params.namespace).obj
    for attribute_name, attribute_value in next_config_set.config_items.items():
        update_item_attr(tested_object, attribute_name, attribute_value)

    update_function = getattr(tested_object, f"patchNamespaced{object_class.kind}")
    update_function(action_params.name, action_params.namespace)

    grafana_message = f"configuration:<pre>{next_config_set.config_set_name}</pre><hr class='solid'><pre>"
    for attribute_name, attribute_value in next_config_set.config_items.items():
        grafana_message += f"{attribute_name} : {attribute_value}<br>"
    grafana_message += "</pre>"
    grafana = Grafana(
        action_params.grafana_api_key.get_secret_value(), action_params.grafana_url
    )
    grafana.add_line_to_dashboard(
        action_params.grafana_dashboard_uid, grafana_message, tags=["AB Testing"]
    )
