from pydantic import SecretStr

from robusta.api import *


class ConfigurationSet(ActionParams):
    """
    :var config_set_name: The name of this configuration set. .
    :var config_items: The yaml attributes values for this configuration set.

    :example config_items:
        "spec.template.spec.containers[0].resources.requests.cpu": 250m,
        "spec.template.spec.containers[0].resources.requests.memory": 128Mi
    """
    config_set_name: str
    config_items: Dict[str, str] = {}


class ABTestingParams(GrafanaParams):
    """
    :var api_version: The api version of the tested resource.
    :var kind: The kind of the tested resource. Kind can be 'Deployment'/'StatefulSet' etc
    :var name: The name of the tested resource.
    :var namespace: The namespace of the tested resource.
    :var configuration_sets: List of test configurations.
    """
    api_version: str = "v1"
    kind: str
    name: str
    namespace: str = "default"
    configuration_sets: List[ConfigurationSet]

    def pre_deploy_func(self, trigger: BaseTrigger):
        if not isinstance(trigger, FixedDelayRepeatTrigger):
            return
        trigger.fixed_delay_repeat.repeat = len(self.configuration_sets)


@action
def config_ab_testing(event: ScheduledExecutionEvent, action_params: ABTestingParams):
    """
    Apply YAML configurations to Kubernetes resources for limited periods of time.

    Adds adds grafana annotations showing when each configuration was applied.

    The execution schedule is defined by the playbook trigger. (every X seconds)

    Commonly used for:
        **Troubleshooting** - Finding the first version a production bug appeared by iterating over image tags
        **Cost/performance optimization** - Comparing the cost or performance of different deployment configurations

    Note:
         Only changing attributes that already exists in the active configuration is supported.

         For example, you can change resources.requests.cpu, if that attribute already exists in the deployment.
    """
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
