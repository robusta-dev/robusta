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


@action
def oom_killer_enricher(event: NodeEvent):
    node = event.get_node()
    if not node:
        logging.error(
            f"cannot run OOMKillerEnricher on event with no node object: {event}"
        )
        return

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
        event.add_enrichment(
            [
                TableBlock(
                    rows=oom_kills,
                    headers=headers,
                    column_renderers={"time": RendererType.DATETIME},
                )
            ]
        )
    else:
        logging.info(f"found no oom killers on {node.metadata.name}")
        event.add_enrichment([])
