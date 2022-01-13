from robusta.api import *
from robusta.integrations.kubernetes.api_client_utils import parse_kubernetes_datetime
from datetime import datetime, timezone
from collections import namedtuple


def is_last_state_in_oom_status(status: ContainerStatus):
    if not status.lastState:
        return False
    if not status.lastState.terminated:
        return False
    return status.lastState.terminated.reason == "OOMKilled"


def is_state_in_oom_status(status: ContainerStatus):
    if not status.state:
        return False
    if not status.state.terminated:
        return False
    return status.state.terminated.reason == "OOMKilled"


OOMKill = namedtuple("OOMKill", ["datetime", "message"])


@action
def oom_killer_enricher(event: NodeEvent):
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

    results: PodList = Pod.listPodForAllNamespaces(
        field_selector=f"spec.nodeName={node.metadata.name}"
    ).obj

    oom_kills: List[List] = []
    headers = ["time", "pod", "container", "image"]
    for pod in results.items:
        container_id_to_oom_killed_state = {}

        oom_statuses_from_state = filter(is_state_in_oom_status, pod.status.containerStatuses)
        for status in oom_statuses_from_state:
            container_id_to_oom_killed_state[status.state.terminated.containerID] = (status, status.state)

        oom_statuses_from_last_state = filter(is_last_state_in_oom_status, pod.status.containerStatuses)
        for status in oom_statuses_from_last_state:
            container_id_to_oom_killed_state[status.lastState.terminated.containerID] = (status, status.lastState)

        for v in container_id_to_oom_killed_state.values():
            status = v[0]
            state = v[1]

            dt = parse_kubernetes_datetime_to_ms(state.terminated.finishedAt)
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
