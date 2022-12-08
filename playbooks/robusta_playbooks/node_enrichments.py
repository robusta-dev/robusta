from datetime import datetime

from robusta.api import *


def pod_row(pod: Pod) -> List[str]:
    ready_condition = [condition.status for condition in pod.status.conditions if condition.type == "Ready"]
    return [
        pod.metadata.namespace,
        pod.metadata.name,
        ready_condition[0] if ready_condition else "Unknown",
    ]


@action
def node_running_pods_enricher(event: NodeEvent):
    """
    Enrich the finding with pods running on this node, along with the 'Ready' status of each pod.
    """
    node = event.get_node()
    if not node:
        logging.error(f"NodeRunningPodsEnricher was called on event without node: {event}")
        return

    block_list: List[BaseBlock] = []
    pod_list: PodList = Pod.listPodForAllNamespaces(field_selector=f"spec.nodeName={node.metadata.name}").obj
    effected_pods_rows = [pod_row(pod) for pod in pod_list.items]
    block_list.append(
        TableBlock(effected_pods_rows, ["namespace", "name", "ready"], table_name="Pods running on the node")
    )
    event.add_enrichment(block_list)


@action
def node_allocatable_resources_enricher(event: NodeEvent):
    """
    Enrich the finding with the node resources available for allocation.

    Can help troubleshooting node issues.
    """
    node = event.get_node()
    if not node:
        logging.error(f"node_allocatable_resources_enricher was called on event without node : {event}")
        return

    block_list: List[BaseBlock] = []
    if node:
        block_list.append(
            TableBlock(
                [[k, v] for (k, v) in node.status.allocatable.items()],
                ["resource", "value"],
                table_name="Node Allocatable Resources - The amount of compute resources that are available for pods",
            )
        )
    event.add_enrichment(block_list)


# TODO: can we make this a KubernetesAnyEvent and just check that the resource has .status.condition inside the code?
# TODO: merge with deployment_status_enricher?
@action
def node_status_enricher(event: NodeEvent):
    """
    Enrich the finding with the node's status conditions.

    Can help troubleshooting Node issues.
    """
    if not event.get_node():
        logging.error(f"node_status_enricher was called on event without node : {event}")
        return

    event.add_enrichment(
        [
            TableBlock(
                [[c.type, c.status] for c in event.get_node().status.conditions],
                headers=["Type", "Status"],
                table_name=f"*Node status details:*",
            ),
        ]
    )


@action
def node_health_watcher(event: NodeChangeEvent):
    """
    Notify when a node becomes unhealthy.

    Add useful information regarding the node's health status.
    """
    new_condition = [c for c in event.obj.status.conditions if c.type == "Ready"]
    old_condition = [c for c in event.old_obj.status.conditions if c.type == "Ready"]

    if len(new_condition) != 1 or len(old_condition) != 1:
        logging.warning(f"more than one Ready condition. new={new_condition} old={old_condition}")

    new_condition = new_condition[0]
    old_condition = old_condition[0]

    currently_ready = "true" in new_condition.status.lower()
    previously_ready = "true" in old_condition.status.lower()

    if currently_ready and not previously_ready:
        logging.info(f"node changed back to healthy: old={event.old_obj} new={event.obj}")

    if currently_ready or currently_ready == previously_ready:
        return

    finding = Finding(
        title=f"Unhealthy node {event.obj.metadata.name}",
        source=FindingSource.KUBERNETES_API_SERVER,
        aggregation_key="node_not_ready",
        severity=FindingSeverity.MEDIUM,
        subject=KubeObjFindingSubject(event.obj),
    )
    event.add_finding(finding)
    event.add_enrichment([KubernetesDiffBlock([], event.old_obj, event.obj, event.obj.metadata.name)])
    node_status_enricher(event)


@action
def node_graph_enricher(node_event: NodeEvent, params: ResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for this node.
    """
    node = node_event.get_node()
    graph_enrichment = create_node_graph_enrichment(params, node)
    node_event.add_enrichment([graph_enrichment])
