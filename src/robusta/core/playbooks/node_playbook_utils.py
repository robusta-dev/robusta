import logging
from datetime import datetime
from typing import Dict, List, Optional

from hikaru.model.rel_1_26 import Node

from robusta.core.model.base_params import ResourceChartItemType, ResourceChartResourceType, ResourceGraphEnricherParams
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.prometheus_enrichment_utils import create_resource_enrichment, get_node_internal_ip
from robusta.core.reporting.base import EnrichmentType
from robusta.core.reporting.blocks import FileBlock, GraphBlock
from robusta.integrations.kubernetes.custom_models import RobustaPod


def create_node_graph_enrichment(
    params: ResourceGraphEnricherParams,
    node: Node,
    metrics_legends_labels: Optional[List[str]] = None,
) -> GraphBlock:
    start_at = datetime.now()
    labels = {"node": node.metadata.name}
    internal_ip = get_node_internal_ip(node)
    if internal_ip:
        labels["node_internal_ip"] = internal_ip

    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Node,
        prometheus_params=params,
        graph_duration_minutes=params.graph_duration_minutes,
        metrics_legends_labels=metrics_legends_labels,
    )
    return graph_enrichment


def dmesg_enricher(event: ExecutionBaseEvent, node: Node, custom_annotations: Optional[Dict[str, str]] = None):
    if not node:
        logging.error("_dmesg_enricher was called on event without node")
        return
    exec_result = RobustaPod.exec_on_node(
        pod_name="dmesg_pod", node_name=node.metadata.name, cmd="dmesg", custom_annotations=custom_annotations
    )
    if exec_result:
        event.add_enrichment(
            [FileBlock("dmesg.log", exec_result.encode())],
            enrichment_type=EnrichmentType.text_file,
            title="DMESG Info",
        )
