import logging
from functools import wraps
from typing import NamedTuple, Union, List
from hikaru.model.rel_1_16 import *

from .models import PrometheusEvent, PrometheusKubernetesAlert, PrometheusAlert
from ..base_handler import handle_event
from ..kubernetes.custom_models import (
    RobustaPod,
    traceback,
    RobustaDeployment,
    RobustaJob,
)

from ...core.model.playbook_hash import playbook_hash
from ...integrations.kubernetes.base_triggers import prefix_match
from ...core.active_playbooks import register_playbook, activate_playbook
from ...core.model.trigger_params import TriggerParams
from ...core.model.cloud_event import CloudEvent
from ...core.model.events import EventType
from ...utils.decorators import doublewrap


def find_node_by_ip(ip) -> Node:
    nodes: NodeList = NodeList.listNode().obj
    for node in nodes.items:
        addresses = [a.address for a in node.status.addresses]
        logging.info(f"node {node.metadata.name} has addresses {addresses}")
        if ip in addresses:
            return node
    raise Exception(f"No node exists with IP '{ip}'")


@doublewrap
def on_pod_prometheus_alert(
    func,
    alert_name="",
    pod_name_prefix="",
    namespace_prefix="",
    instance_name_prefix="",
    status="",
):
    register_playbook(
        func,
        deploy_on_pod_prometheus_alert,
        TriggerParams(
            alert_name=alert_name,
            pod_name_prefix=pod_name_prefix,
            namespace_prefix=namespace_prefix,
            instance_name_prefix=instance_name_prefix,
            status=status,
        ),
    )
    return func


def does_alert_match_trigger(
    alert: PrometheusAlert, trigger_params: TriggerParams
) -> bool:
    if (
        trigger_params.alert_name
        and trigger_params.alert_name != alert.labels["alertname"]
    ):
        return False
    if trigger_params.status != "" and trigger_params.status != alert.status:
        return False
    if not prefix_match(trigger_params.pod_name_prefix, alert.labels.get("pod")):
        return False
    if not prefix_match(trigger_params.namespace_prefix, alert.labels.get("namespace")):
        return False
    if not prefix_match(
        trigger_params.instance_name_prefix, alert.labels.get("instance")
    ):
        return False
    return True


class ResourceMapping(NamedTuple):
    hikaru_class: Union[RobustaPod, RobustaDeployment, Job]
    attribute_name: str
    prometheus_label: str


MAPPINGS = [
    ResourceMapping(RobustaPod, "pod", "pod"),
    ResourceMapping(RobustaDeployment, "deployment", "deployment"),
    ResourceMapping(RobustaJob, "job", "job_name"),
    ResourceMapping(DaemonSet, "daemonset", "daemonset"),
]


def load_node(alert: PrometheusAlert, node_name: str) -> Node:
    node = None
    try:
        # sometimes we get an IP:PORT instead of the node name. handle that case
        if ":" in node_name:
            node = find_node_by_ip(node_name.split(":")[0])
        else:
            node = Node().read(name=node_name)
    except Exception as e:
        logging.info(f"Error loading Node kubernetes object {alert}. error: {e}")

    return node


def build_prometheus_event(alert: PrometheusAlert) -> PrometheusKubernetesAlert:
    event = PrometheusKubernetesAlert(
        alert=alert,
        alert_name=alert.labels["alertname"],
        alert_severity=alert.labels.get("severity"),
    )

    namespace = alert.labels.get("namespace", "default")

    for mapping in MAPPINGS:
        try:
            resource_name = alert.labels.get(mapping.prometheus_label, None)
            if not resource_name:
                continue
            resource = mapping.hikaru_class().read(
                name=resource_name, namespace=namespace
            )
            setattr(event, mapping.attribute_name, resource)
            logging.info(
                f"Successfully loaded Kubernetes resource {resource_name} for alert {event.alert_name}"
            )
        except Exception as e:
            logging.info(
                f"Error loading {mapping.hikaru_class} kubernetes object {event.alert}. error: {e}"
            )

    node_name = alert.labels.get("node")
    if node_name:
        event.node = load_node(alert, node_name)

    # we handle nodes differently than other resources
    node_name = event.alert.labels.get("instance", None)
    job_name = event.alert.labels.get(
        "job", None
    )  # a prometheus "job" not a kubernetes "job" resource
    # when the job_name is kube-state-metrics "instance" refers to the IP of kube-state-metrics not the node
    if not event.node and node_name and job_name != "kube-state-metrics":
        event.node = load_node(alert, node_name)

    return event


def handle_single_alert(
    alert: PrometheusAlert,
    trigger_params: TriggerParams,
    named_sinks: List[str],
    func,
    action_params=None,
):
    if not does_alert_match_trigger(alert, trigger_params):
        return

    event = build_prometheus_event(alert)

    return handle_event(func, event, action_params, "prometheus", named_sinks)


def deploy_on_pod_prometheus_alert(
    func, trigger_params: TriggerParams, named_sinks: List[str], action_params=None
):
    @wraps(func)
    def wrapper(cloud_event: CloudEvent):
        logging.debug(
            f"checking if we should run {func} on prometheus event {trigger_params.alert_name}"
        )
        prometheus_event = PrometheusEvent(**cloud_event.data)
        results = []
        for alert in prometheus_event.alerts:
            try:
                result = handle_single_alert(
                    alert, trigger_params, named_sinks, func, action_params
                )
                if result:
                    results.append(result)
            except Exception:
                logging.error(
                    f"Failed to process alert {alert} {traceback.format_exc()}"
                )

        return ",".join(results)

    playbook_id = playbook_hash(func, trigger_params, action_params)
    activate_playbook(EventType.PROMETHEUS, wrapper, func, playbook_id)
    return wrapper
