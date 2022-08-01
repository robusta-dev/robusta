from robusta.api import *
from kubernetes import client
from kubernetes.client.configuration import Configuration


class PodStatusParams(ActionParams):
    """
    :var status: query pods by this status
    """
    status: str


@action
def list_pods_by_status(event: ExecutionBaseEvent, params: PodStatusParams):
    enable_monkeypatch(event)
    pods: PodList = Pod.listPodForAllNamespaces(field_selector=f"status.phase={params.status}").obj
    event.add_finding(Finding(
        title=f"Pod list for status {params.status}",
        aggregation_key="Pod status report",
    ))
    if pods.items:
        event.add_enrichment([
            TableBlock(
                table_name="pods list",
                headers=["name", "namespace"],
                rows=[[pod.metadata.name, pod.metadata.namespace] for pod in pods.items]
            )
        ])
    else:
        event.add_enrichment([MarkdownBlock(f"No pods with status {params.status}")])


@action
def get_pod_events(event: PodEvent):
    revert_monkeypatch(event)
    pod = event.get_pod()
    block_list: List[BaseBlock] = []
    event_list: EventList = EventList.listNamespacedEvent(
        namespace=pod.metadata.namespace,
        field_selector=f"involvedObject.name={pod.metadata.name}",
    ).obj

    if event_list.items:  # add enrichment only if we got events
        block_list.append(MarkdownBlock("*Pod events:*"))
        headers = ["time", "message"]
        rows = [
            [parse_kubernetes_datetime_to_ms(event.lastTimestamp), event.message]
            for event in event_list.items
        ]
        block_list.append(
            TableBlock(
                rows=rows,
                headers=headers,
                column_renderers={"time": RendererType.DATETIME},
            )
        )
        event.add_enrichment(block_list)
    else:
        event.add_enrichment([MarkdownBlock(f"No events found for pod {pod.metadata.name} namespace {pod.metadata.namespace}")])

@action
def enable_monkeypatch(event: ExecutionBaseEvent):
    print("running action request")
    Configuration.real_debug = Configuration.dummy_debug_impl
    set_replicasets_discovery(True)


@action
def revert_monkeypatch(event: ExecutionBaseEvent):
    print("run action request")
    Configuration.real_debug = Configuration.real_debug_impl
    set_replicasets_discovery(False)


def set_replicasets_discovery(discover: bool):
    os.environ["REPLICA_SET_DISCOVERY"] = str(discover)

