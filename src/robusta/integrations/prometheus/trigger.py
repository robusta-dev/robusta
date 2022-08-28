import logging
from concurrent.futures.process import ProcessPoolExecutor
from typing import NamedTuple, Union, Type, List, Optional, Dict
from pydantic.main import BaseModel
from hikaru.model.rel_1_16 import *

from .models import PrometheusKubernetesAlert, PrometheusAlert
from ..helper import exact_match, prefix_match
from ..kubernetes.custom_models import RobustaPod, RobustaDeployment, RobustaJob
from ...core.model.env_vars import ALERT_BUILDER_WORKERS
from ...core.playbooks.base_trigger import BaseTrigger, TriggerEvent
from ...core.reporting.base import Finding
from ...core.model.events import ExecutionBaseEvent


class PrometheusTriggerEvent(TriggerEvent):
    alert: PrometheusAlert

    def get_event_name(self) -> str:
        return PrometheusTriggerEvent.__name__

    def get_event_description(self) -> str:
        alert_name = self.alert.labels.get("alertname", "NA")
        alert_severity = self.alert.labels.get("severity", "NA")
        return f"PrometheusAlert-{alert_name}-{alert_severity}"


class ResourceMapping(NamedTuple):
    hikaru_class: Union[
        Type[RobustaPod], Type[RobustaDeployment], Type[Job], Type[DaemonSet],
        Type[StatefulSet]
    ]
    attribute_name: str
    prometheus_label: str


MAPPINGS = [
    ResourceMapping(RobustaDeployment, "deployment", "deployment"),
    ResourceMapping(DaemonSet, "daemonset", "daemonset"),
    ResourceMapping(StatefulSet, "statefulset", "statefulset"),
    ResourceMapping(RobustaJob, "job", "job_name"),
    ResourceMapping(RobustaPod, "pod", "pod"),
]


class PrometheusAlertTrigger(BaseTrigger):
    """
    :var status: one of "firing", "resolved", or "all"
    """

    alert_name: str = None
    status: str = "firing"
    pod_name_prefix: str = None
    namespace_prefix: str = None
    instance_name_prefix: str = None

    def get_trigger_event(self):
        return PrometheusTriggerEvent.__name__

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        if not isinstance(event, PrometheusTriggerEvent):
            return False

        labels = event.alert.labels
        if not exact_match(self.alert_name, labels["alertname"]):
            return False

        if self.status != "all" and not exact_match(self.status, event.alert.status):
            return False

        if not prefix_match(self.pod_name_prefix, labels.get("pod")):
            return False

        if not prefix_match(self.namespace_prefix, labels.get("namespace")):
            return False

        if not prefix_match(self.instance_name_prefix, labels.get("instance")):
            return False

        return True

    def build_execution_event(
        self, event: PrometheusTriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        return AlertEventBuilder.build_event(event, sink_findings)

    @staticmethod
    def get_execution_event_type() -> type:
        return PrometheusKubernetesAlert


class PrometheusAlertTriggers(BaseModel):
    on_prometheus_alert: Optional[PrometheusAlertTrigger]


class AlertEventBuilder:
    executor = ProcessPoolExecutor(max_workers=ALERT_BUILDER_WORKERS)

    @classmethod
    def __find_node_by_ip(cls, ip) -> Optional[Node]:
        nodes: NodeList = NodeList.listNode().obj
        for node in nodes.items:
            addresses = [a.address for a in node.status.addresses]
            logging.info(f"node {node.metadata.name} has addresses {addresses}")
            if ip in addresses:
                return node
        return None

    @classmethod
    def __load_node(cls, alert: PrometheusAlert, node_name: str) -> Optional[Node]:
        node = None
        try:
            # sometimes we get an IP:PORT instead of the node name. handle that case
            if ":" in node_name:
                node = cls.__find_node_by_ip(node_name.split(":")[0])
            else:
                node = Node().read(name=node_name)
        except Exception as e:
            logging.info(f"Error loading Node kubernetes object {alert}. error: {e}")
        return node

    @staticmethod
    def _build_event_task(
            event: PrometheusTriggerEvent,
            sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        labels = event.alert.labels
        execution_event = PrometheusKubernetesAlert(
            sink_findings=sink_findings,
            alert=event.alert,
            alert_name=labels["alertname"],
            alert_severity=labels.get("severity"),
            label_namespace=labels.get("namespace", None)
        )

        namespace = labels.get("namespace", "default")

        for mapping in MAPPINGS:
            try:
                resource_name = labels.get(mapping.prometheus_label, None)
                if not resource_name or "kube-state-metrics" in resource_name:
                    continue
                resource = mapping.hikaru_class().read(
                    name=resource_name, namespace=namespace
                )
                setattr(execution_event, mapping.attribute_name, resource)
                logging.info(
                    f"Successfully loaded Kubernetes resource {resource_name} for alert {execution_event.alert_name}"
                )
            except Exception as e:
                reason = getattr(e, "reason", "NA")
                status = getattr(e, "status", 0)
                logging.info(
                    f"Error loading kubernetes {mapping.attribute_name} {namespace}/{resource_name}. "
                    f"reason: {reason} status: {status}"
                )

        node_name = labels.get("node")
        if node_name:
            execution_event.node = AlertEventBuilder.__load_node(execution_event.alert, node_name)

        # we handle nodes differently than other resources
        node_name = labels.get("instance", None)
        job_name = labels.get(
            "job", None
        )  # a prometheus "job" not a kubernetes "job" resource
        # when the job_name is kube-state-metrics "instance" refers to the IP of kube-state-metrics not the node
        # If the alert has pod, the 'instance' attribute contains the pod ip
        if not execution_event.node and node_name and job_name != "kube-state-metrics":
            execution_event.node = AlertEventBuilder.__load_node(execution_event.alert, node_name)

        return execution_event

    @staticmethod
    def build_event(
            event: PrometheusTriggerEvent,
            sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        future = AlertEventBuilder.executor.submit(AlertEventBuilder._build_event_task, event, sink_findings)
        return future.result()
