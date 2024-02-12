from datetime import datetime
from typing import Optional, List

from hikaru.model.rel_1_26 import Container, Pod

from robusta.core.model.base_params import ResourceChartItemType, ResourceChartResourceType, ResourceGraphEnricherParams
from robusta.core.model.pods import PodContainer
from robusta.core.playbooks.prometheus_enrichment_utils import XAxisLine, YAxisLine, create_resource_enrichment
from robusta.integrations.kubernetes.api_client_utils import parse_kubernetes_datetime


def create_container_graph(params: ResourceGraphEnricherParams, pod: Pod, oomkilled_container: PodContainer, show_limit=False,
                           metrics_legends_labels: Optional[List[str]] = None,):
    container = oomkilled_container.container
    oom_killed_status = oomkilled_container.state
    labels = {
        "pod": pod.metadata.name,
        "container": container.name,
        "namespace": pod.metadata.namespace,
    }

    start_at = datetime.now()
    limit_lines = []
    if show_limit:
        if params.resource_type == "Memory":
            requests, limits = PodContainer.get_memory_resources(container)
            if limits > 0:
                memory_limit_in_bytes = limits * 1024 * 1024
                limit_line = XAxisLine(label="Limit", value=memory_limit_in_bytes)
                limit_lines.append(limit_line)

            if requests > 0:
                request_limit_in_bytes = requests * 1024 * 1024
                limit_line = XAxisLine(label="Request", value=request_limit_in_bytes)
                limit_lines.append(limit_line)

        if params.resource_type == "CPU":
            requests, limits = PodContainer.get_cpu_resources(container)

            if limits > 0:
                cpu_limit_in_bytes = limits * 1024 * 1024
                limit_line = XAxisLine(label="Limit", value=cpu_limit_in_bytes)
                limit_lines.append(limit_line)

            if requests > 0:
                request_limit_in_bytes = requests * 1024 * 1024
                limit_line = XAxisLine(label="Request", value=request_limit_in_bytes)
                limit_lines.append(limit_line)

        if oomkilled_container.state.terminated and \
                oomkilled_container.state.terminated.reason == "OOMKilled" and \
                oom_killed_status.terminated and \
                oom_killed_status.terminated.finishedAt:
            oom_killed_datetime = parse_kubernetes_datetime(oom_killed_status.terminated.finishedAt)
            limit_line = YAxisLine(label="OOM Kill Time", value=oom_killed_datetime.timestamp())
            limit_lines.append(limit_line)

    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Container,
        prometheus_params=params,
        graph_duration_minutes=params.graph_duration_minutes,
        lines=limit_lines,
        title_override=f"{params.resource_type} Usage for container {container.name}",
        metrics_legends_labels=metrics_legends_labels,
    )
    return graph_enrichment
