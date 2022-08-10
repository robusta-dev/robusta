from datetime import timedelta

import pydantic

from robusta.api import *
from robusta.integrations.resource_analysis.memory_analyzer import (
    MemoryAnalyzer,
    K8sMemoryTransformer,
)


class OomKillerEnricherParams(ActionParams):
    """
    :var new_oom_kills_duration_in_sec: In order to avoid duplicated, This playbook will only report OOMKills that occurred in the last new_oom_kills_duration_in_sec seconds. For example, if new_oom_kills_duration_in_sec is 1200, only OOMKills from the last 20 minutes will be considered.
    :var prometheus_url: Prometheus url. If omitted, we will try to find a prometheus instance in the same cluster.
    :example prometheus_url: "http://prometheus-k8s.monitoring.svc.cluster.local:9090".
    :var metrics_duration_in_secs: Memory usage metrics of nodes and pod containers where OOMKills have occurred will be queried from prometheus in order to determine the estimated reason of each OOMKill. This parameter determines the amount of time, in seconds, these metrics will be applied on. For example, if duration_in_secs is 1200, memory usage metrics from the last 20 minutes will be considered.
    """

    new_oom_kills_duration_in_sec: int = 1200
    prometheus_url: Optional[str] = None
    metrics_duration_in_secs: int = 1200


# If this amount of memory was exceeded (in the last metrics_duration_in_secs seconds), the playbook will
# report the corresponding node as the reason for the OOMKill.
CONTAINER_MEMORY_THRESHOLD = 0.92

# If this amount of memory was exceeded (in the last metrics_duration_in_secs seconds), the playbook will
# report the corresponding node as the reason for the OOMKill.
NODE_MEMORY_THRESHOLD = 0.95

@action
def oomkilled_container_graph_enricher(event: PodEvent, params: ResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for this pod. Note: "Disk" Resource is not supported.
    """
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run pod_oom_killer_enricher on event with no pod: {event}")
        return
    oomkilled_container = pod_most_recent_oom_killed_container(pod)
    if not oomkilled_container:
        logging.error(f"Unable to find oomkilled container")
        return

    container_graph = create_container_graph(params, pod, oomkilled_container.container, show_limit=True )
    event.add_enrichment([container_graph])


@action
def pod_oom_killer_enricher(
    event: PodEvent,
):
    """
    Retrieves pod and node information for an OOMKilled pod
    """
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run pod_oom_killer_enricher on event with no pod: {event}")
        return
    resource_requests = pod_requests(pod)
    resource_limits = pod_limits(pod)

    finding = Finding(
        title=f"Pod {pod.metadata.name} in namespace {pod.metadata.namespace} OOMKilled results",
        aggregation_key="pod_oom_killer_enricher",
        severity=FindingSeverity.HIGH
    )

    labels = [("Pod", pod.metadata.name),
              ("Namespace", pod.metadata.namespace),
              ("Node Name", pod.spec.nodeName),
              ]
    node: Node = Node.readNode(pod.spec.nodeName).obj
    if node:
        allocatable_memory = PodResources.parse_mem(node.status.allocatable.get("memory", "0Mi"))
        capacity_memory = PodResources.parse_mem(node.status.capacity.get("memory", "0Mi"))
        allocated_precent = (capacity_memory - allocatable_memory) * 100 / capacity_memory
        node_label = ("Node allocated memory", f"{allocated_precent:.2f}% out of {allocatable_memory}MB allocatable")
        labels.append(node_label)
    else:
        logging.warning(
            f"Node {pod.spec.nodeName} not found for OOMKilled pod {pod.metadata.name}"
        )

    oomkilled_container = pod_most_recent_oom_killed_container(pod)
    if not oomkilled_container or not oomkilled_container.state:
        logging.error(
            f"could not find OOMKilled status in pod {pod.metadata.name}"
        )
    else:
        requests, limits = PodContainer.get_memory_limits_and_requests_for_container(oomkilled_container.container)
        labels.append(("Container name", oomkilled_container.container.name))
        memory_limit = "No limit" if not limits else f"{limits}MB limit"
        memory_requests = "No request" if not requests else f"{requests}MB request"
        labels.append(("Container memory", f"{memory_requests}, {memory_limit}"))
        oom_killed_status = oomkilled_container.state
        if oom_killed_status.terminated.startedAt:
            labels.append(("Container started at", oom_killed_status.terminated.startedAt))
        if oom_killed_status.terminated.finishedAt:
            labels.append(("Container finished at", oom_killed_status.terminated.finishedAt))
    table_block = TableBlock(
        [[k, v] for (k, v) in labels],
        ["label", "value"],
        table_name="*Pod and Node OOMKilled data*",
    )
    finding.add_enrichment([table_block])
    event.add_finding(finding)

@action
def oom_killer_enricher(
    event: PrometheusKubernetesAlert, config: OomKillerEnricherParams
):
    """
    Enrich the finding information regarding node OOM killer.

    Add the list of pods on this node that we're killed by the OOM killer.
    """
    node = event.get_node()
    if not node:
        logging.error(
            f"cannot run OOMKillerEnricher on event with no node object: {event}"
        )
        return

    oom_kill_reason_investigator = KubernetesOomKillReasonInvestigator(
        node, event.alert, config
    )
    oom_kills_extractor = OomKillsExtractor(config, node, oom_kill_reason_investigator)
    oom_kills = oom_kills_extractor.extract_oom_kills()

    if len(oom_kills) > 0:
        logging.info(f"found at least one oom killer on {node.metadata.name}")

        oom_kills_headers = [
            "time",
            "pod",
            "container",
            "image",
            "memory_specs",
            "estimated_reason",
        ]
        oom_kills_rows = [
            [
                oom_kill.time,
                oom_kill.pod_name,
                oom_kill.container_name,
                oom_kill.image,
                repr(oom_kill.memory_specs),
                oom_kill.reason,
            ]
            for oom_kill in oom_kills
        ]
        event.add_enrichment(
            [
                TableBlock(
                    rows=oom_kills_rows,
                    headers=oom_kills_headers,
                    column_renderers={"time": RendererType.DATETIME},
                )
            ]
        )
    else:
        logging.info(f"found no oom killers on {node.metadata.name}")
        event.add_enrichment([])


class MemorySpecs(pydantic.BaseModel):
    requests: Optional[str] = None
    limits: Optional[str] = None


class OomKill(pydantic.BaseModel):
    time: float
    pod_name: str
    container_name: str
    image: str
    memory_specs: MemorySpecs
    reason: Optional[str]


# This class is used only because the OomKillsExtractor should appear before KubernetesOomKillReasonInvestigator, but still know its interface.
class OomKillReasonInvestigator(metaclass=abc.ABCMeta):
    @abstractmethod
    def get_reason(self, oom_kill: OomKill) -> str:
        return ""


class OomKillsExtractor:
    def __init__(
        self,
        config: OomKillerEnricherParams,
        node: Node,
        oom_kill_reason_investigator: OomKillReasonInvestigator,
    ):
        self.config = config
        self.node = node
        self.oom_kill_reason_investigator = oom_kill_reason_investigator

        self.memory_transformer = K8sMemoryTransformer()

    def extract_oom_kills(self) -> List[OomKill]:
        results: PodList = Pod.listPodForAllNamespaces(
            field_selector=f"spec.nodeName={self.node.metadata.name}"
        ).obj

        oom_kills: List[OomKill] = []
        for pod in results.items:
            pod_oom_kills = self.get_oom_kills_from_pod(pod)
            oom_kills.extend(pod_oom_kills)

        return oom_kills

    def get_oom_kills_from_pod(self, pod: Pod) -> List[OomKill]:
        new_oom_kills_duration = timedelta(
            seconds=self.config.new_oom_kills_duration_in_sec
        )

        containers_spec_by_name = {}
        for c in pod.spec.containers:
            containers_spec_by_name[c.name] = c

        oom_kills: List[OomKill] = []
        for c_status in pod.status.containerStatuses:
            # Ignore pods that were not oom killed
            container = get_oom_killed_container(c_status)
            state = container.state
            if state is None:
                continue

            # Ignore old oom kills
            dt = parse_kubernetes_datetime_to_ms(state.terminated.finishedAt)
            oom_kill_from = datetime.fromtimestamp(dt / 1000)
            now = datetime.now()
            if now - oom_kill_from > new_oom_kills_duration:
                continue

            # Report the current container as oom killed
            resources = (
                containers_spec_by_name[c_status.name].resources
                if c_status.name in containers_spec_by_name
                else None
            )
            memory_specs = self.get_memory_specs(resources)
            oom_kill = OomKill(
                time=dt,
                pod_name=pod.metadata.name,
                container_name=c_status.name,
                image=c_status.image,
                memory_specs=memory_specs,
                reason=None,
            )
            oom_kill.reason = self.oom_kill_reason_investigator.get_reason(oom_kill)
            oom_kills.append(oom_kill)

        return oom_kills



    @staticmethod
    def get_memory_specs(resources: Optional[ResourceRequirements]) -> MemorySpecs:
        if resources is None:
            return MemorySpecs()

        mem_specs = MemorySpecs()

        if resources.requests is not None and "memory" in resources.requests:
            mem_specs.requests = resources.requests["memory"]

        if resources.limits is not None and "memory" in resources.limits:
            mem_specs.limits = resources.limits["memory"]

        return mem_specs


class KubernetesOomKillReasonInvestigator(OomKillReasonInvestigator):
    def __init__(
        self, node: Node, alert: PrometheusAlert, params: OomKillerEnricherParams
    ):
        self.config = params
        self.memory_analyzer = MemoryAnalyzer(
            params.prometheus_url, alert.startsAt.tzinfo
        )
        self.node = node
        self.node_reason_calculated = False
        self.node_reason = None

    def get_reason(self, oom_kill: OomKill) -> str:
        container_reason = self.get_busy_container_reason(oom_kill)
        if container_reason is not None:
            return container_reason

        # Calculate if the node is the reason for the OOMKill only once, rather than for every OomKill
        if not self.node_reason_calculated:
            self.node_reason = self.get_busy_node_reason()
            self.node_reason_calculated = True

        if self.node_reason is not None:
            return self.node_reason

        return f"reason not found"

    def get_busy_container_reason(self, oom_kill: OomKill):
        duration = timedelta(seconds=self.config.metrics_duration_in_secs)

        if oom_kill.memory_specs.limits is None:
            return None

        memory_limit = oom_kill.memory_specs.limits
        max_memory_in_bytes = (
            K8sMemoryTransformer.get_number_of_bytes_from_kubernetes_mem_spec(
                memory_limit
            )
        )

        container_max_used_memory_in_bytes = (
            self.memory_analyzer.get_container_max_memory_usage_in_bytes(
                self.node.metadata.name,
                oom_kill.pod_name,
                oom_kill.container_name,
                duration,
            )
        )
        if container_max_used_memory_in_bytes is None:
            return None

        used_memory_percentage = (
            container_max_used_memory_in_bytes / max_memory_in_bytes
        )
        if used_memory_percentage < CONTAINER_MEMORY_THRESHOLD:
            return None

        reason = f"container used too much memory: reached {used_memory_percentage} percentage of its specified limit"
        return reason

    def get_busy_node_reason(self) -> Optional[str]:
        duration = timedelta(seconds=self.config.metrics_duration_in_secs)
        node_name = self.node.metadata.name

        node_max_used_memory_in_percentage = (
            self.memory_analyzer.get_max_node_memory_usage_in_percentage(
                node_name, duration
            )
        )
        if node_max_used_memory_in_percentage is None:
            return None

        if node_max_used_memory_in_percentage < NODE_MEMORY_THRESHOLD:
            return None

        reason = f"node {node_name} used too much memory: reached {node_max_used_memory_in_percentage} percentage of its available memory"
        return reason

