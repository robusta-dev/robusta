from robusta.api import *
from robusta.integrations.kubernetes.api_client_utils import parse_kubernetes_datetime
from datetime import datetime, timezone
from collections import namedtuple


def is_oom_status(status: ContainerStatus):
    if not status.lastState:
        return False
    if not status.lastState.terminated:
        return False
    return status.lastState.terminated.reason == "OOMKilled"


OOMKill = namedtuple("OOMKill", ["datetime", "message"])


def do_show_recent_oom_kills(node: Node) -> List[BaseBlock]:
    results: PodList = Pod.listPodForAllNamespaces(
        field_selector=f"spec.nodeName={node.metadata.name}"
    ).obj

    oom_kills: List[List] = []
    headers = ["time", "pod", "container", "image"]
    for pod in results.items:
        oom_statuses = filter(is_oom_status, pod.status.containerStatuses)
        for status in oom_statuses:
            dt = parse_kubernetes_datetime_to_ms(status.lastState.terminated.finishedAt)
            oom_kills.append([dt, pod.metadata.name, status.name, status.image])

    oom_kills.sort(key=lambda o: o[0])

    if oom_kills:
        logging.info(f"found at least one oom killer on {node.metadata.name}")
        return [
            TableBlock(
                rows=oom_kills,
                headers=headers,
                column_renderers={"time": RendererType.DATETIME},
            )
        ]
    else:
        logging.info(f"found no oom killers on {node.metadata.name}")
        return []


@action
def show_recent_oom_kills(event: ExecutionBaseEvent, params: NodeNameParams):
    node = Node().read(name=params.node_name)
    blocks = do_show_recent_oom_kills(node)
    if blocks:
        finding = Finding(
            title=f"Latest OOM Kills on {params.node_name}",
            subject=FindingSubject(name=params.node_name),
            source=FindingSource.MANUAL,
            aggregation_key="show_recent_oom_kills",
        )
        finding.add_enrichment(blocks)
        event.add_finding(finding)
