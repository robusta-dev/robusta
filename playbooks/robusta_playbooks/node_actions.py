from typing import List

from kubernetes import client
from kubernetes.client import V1OwnerReference, V1PodList

from robusta.api import ActionException, ErrorCodes, FileBlock, MarkdownBlock, NodeEvent, action


@action
def cordon(event: NodeEvent):
    """
    Cordon, Taints a node as unschedulable.
    """
    node = event.get_node()
    if not node:
        raise ActionException(ErrorCodes.RESOURCE_NOT_FOUND, "Failed to get node for cordon")

    if node.spec.unschedulable:
        event.add_enrichment([MarkdownBlock(f"Node {node.metadata.name} already cordoned")])
        return

    try:
        client.CoreV1Api().patch_node(node.metadata.name, {"spec": {"unschedulable": True}})
        event.add_enrichment([MarkdownBlock(f"Node {node.metadata.name} cordoned")])
    except Exception as e:
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, f"Failed to cordon node {node.metadata.name} {e}")


@action
def uncordon(event: NodeEvent):
    """
    Unordon, Taints a node as schedulable.
    """
    node = event.get_node()
    if not node:
        raise ActionException(ErrorCodes.RESOURCE_NOT_FOUND, "Failed to get node for uncordon")

    if node.spec.unschedulable is False:
        event.add_enrichment([MarkdownBlock(f"Node {node.metadata.name} already uncordoned")])
        return

    try:
        client.CoreV1Api().patch_node(node.metadata.name, {"spec": {"unschedulable": False}})
        event.add_enrichment([MarkdownBlock(f"Node {node.metadata.name} uncordoned")])
    except Exception as e:
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, f"Failed to uncordoned node {node.metadata.name} {e}")


@action
def drain(event: NodeEvent):
    """
    Drain, taints a node as unschedulable, and evicts all pods from the node.
    DaemonSets pod are skipped, as they tolerant unschedulable nodes by default.
    """
    cordon(event)

    node = event.get_node()
    api = client.CoreV1Api()
    try:
        pods: V1PodList = api.list_pod_for_all_namespaces(
            watch=False, field_selector=f"spec.nodeName={node.metadata.name}"
        )
    except Exception as e:
        uncordon(event)
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR, f"Failed to list pods for drain action Uncordoning.\n{e}"
        )

    msg = ""
    for pod in pods.items:
        name = pod.metadata.name
        namespace = pod.metadata.namespace

        owner_list: List[V1OwnerReference] = pod.metadata.owner_references if pod.metadata.owner_references else []
        if any(owner.kind == "DaemonSet" for owner in owner_list):
            msg += f"Skipping {namespace}/DaemonSet/{name}\n"
            continue

        try:
            body = client.V1Eviction(metadata=client.V1ObjectMeta(name=name, namespace=namespace))
            api.create_namespaced_pod_eviction(name, namespace, body, pretty="True")
            action = "Evicting" if owner_list else "Deleting"
            msg += f"{action} {namespace}/Pod/{name}\n"
        except Exception as e:
            msg += f"Error evicting {namespace}/Pod/{name} {e}\n"
            continue

    event.add_enrichment(
        [
            FileBlock(
                filename=f"Drain {node.metadata.name} report.log",
                contents=f"drain node {node.metadata.name} \n\n{msg}".encode(),
            )
        ]
    )
