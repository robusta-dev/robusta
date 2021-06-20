import logging
from functools import wraps
from hikaru.model.rel_1_16 import *

from .models import PrometheusEvent, PrometheusKubernetesAlert
from ..kubernetes.custom_models import RobustaPod, Node, traceback, RobustaDeployment
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
def on_pod_prometheus_alert(func, alert_name="", pod_name_prefix="", namespace_prefix="", instance_name_prefix="",
                            status=""):
    register_playbook(func, deploy_on_pod_prometheus_alert, TriggerParams(
        alert_name=alert_name,
        pod_name_prefix=pod_name_prefix,
        namespace_prefix=namespace_prefix,
        instance_name_prefix=instance_name_prefix,
        status=status))
    return func


def deploy_on_pod_prometheus_alert(func, trigger_params: TriggerParams, action_params=None):
    @wraps(func)
    def wrapper(cloud_event: CloudEvent):
        logging.debug(f'checking if we should run {func} on prometheus event {trigger_params.alert_name}')
        prometheus_event = PrometheusEvent(**cloud_event.data)
        results = []
        for alert in prometheus_event.alerts:
            try:
                alert_name = alert.labels['alertname']
                if trigger_params.alert_name and alert_name != trigger_params.alert_name:
                    continue
                if trigger_params.status != "" and trigger_params.status != alert.status:
                    continue
                if not prefix_match(trigger_params.pod_name_prefix, alert.labels.get('pod')):
                    continue
                if not prefix_match(trigger_params.namespace_prefix, alert.labels.get('namespace')):
                    continue
                if not prefix_match(trigger_params.instance_name_prefix, alert.labels.get('instance')):
                    continue

                kubernetes_obj = None
                pod_name = alert.labels.get('pod', None)
                node_name = alert.labels.get('instance', None)
                deployment_name = alert.labels.get('deployment', None)
                try:
                    if pod_name is not None:  # pod alert
                        pod_namespace = alert.labels.get('namespace', 'default')
                        kubernetes_obj = RobustaPod.read(pod_name, pod_namespace)
                        if kubernetes_obj is None:
                            logging.info(f'pod {pod_name} namespace {pod_namespace} not found. Skipping alert {alert_name}')
                            continue
                    elif deployment_name:
                        namespace = alert.labels.get('namespace', 'default')
                        kubernetes_obj = RobustaDeployment.readNamespacedDeployment(deployment_name, namespace).obj
                        if kubernetes_obj is None:
                            logging.info(f'deployment {deployment_name} namespace {namespace} not found. Skipping alert {alert_name}')
                            continue
                    elif alert.labels.get('job_name', None):  # jobs alert not implemented yet
                        continue
                    elif node_name is not None: # node alert
                        # sometimes we get an IP:PORT instead of the node name. handle that case
                        if ":" in node_name:
                            kubernetes_obj = find_node_by_ip(node_name.split(":")[0])
                        else:
                            kubernetes_obj = Node.readNode(node_name).obj
                        if kubernetes_obj is None:
                            logging.info(f'node {node_name} not found. Skipping alert {alert_name}')
                            continue
                    else: # other alert, not implemented yet
                        logging.warn(f'alert {alert_name} does not contain pod/instance identifier. Not loading kubernetes object')
                except Exception as e:
                    logging.info(f"Error loading alert kubernetes object {alert}. error: {e}")

                kubernetes_alert = PrometheusKubernetesAlert(alert=alert, obj=kubernetes_obj)

                logging.info(f"running prometheus playbook {func.__name__}; action_params={action_params}")
                if action_params is None:
                    result = func(kubernetes_alert)
                else:
                    result = func(kubernetes_alert, action_params)

                if result is not None:
                    results = results.append(result)
            except Exception:
                logging.error(f"Failed to process alert {alert} {traceback.format_exc()}")
        return ",".join(results)

    playbook_id = playbook_hash(func, trigger_params, action_params)
    activate_playbook(EventType.PROMETHEUS, wrapper, func, playbook_id)
    return wrapper
