from robusta.api import *

supported_resources = [
    "Deployment",
    "DaemonSet",
    "ReplicaSet",
    "Pod",
    "StatefulSet"
]


def to_pod_row(pod: Pod, cluster_name: str) -> List:
    resource_requests = pod_requests(pod)
    resource_limits = pod_limits(pod)
    addresses = ",".join([address.ip for address in pod.status.podIPs])
    return [
        pod.metadata.name, pod.metadata.namespace, cluster_name, pod.spec.nodeName,
        resource_limits.cpu, resource_requests.cpu, resource_limits.memory, resource_requests.memory,
        pod.metadata.creationTimestamp, pod_restarts(pod), addresses, len(pod.spec.containers),
        pod.status.phase
    ]


@action
def related_pods(event: KubernetesResourceEvent):
    """
    Return the list of pods related to that k8s resource.
    For example, return all pods of a given k8s Deployment

    Supports Deployments, ReplicaSets, DaemonSets, StatefulSets and Pods
    """
    resource = event.get_resource()
    if resource.kind not in supported_resources:
        logging.error(f"Related pods is not supported for resource {resource.kind}")
        return

    if resource.kind == "Pod":
        pods = [resource]
    else:
        selector = build_selector_query(resource.spec.selector)
        pods = PodList.listNamespacedPod(namespace=resource.metadata.namespace, label_selector=selector).obj.items

    rows = [to_pod_row(pod, event.get_context().cluster_name) for pod in pods]

    event.add_enrichment([
        TableBlock(
            table_name="related pods",
            headers=["name", "namespace", "cluster", "node", "cpu limit", "cpu request", "memory limit",
                     "memory request", "creation_time", "restarts", "addresses", "containers", "status"],
            rows=rows
        )
    ])
