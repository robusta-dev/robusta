from robusta.api import *
from robusta.integrations.kubernetes.api_client_utils import parse_kubernetes_datetime
from datetime import datetime, timezone
from collections import namedtuple
import humanize


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

    oom_kills: List[OOMKill] = []
    for pod in results.items:
        oom_statuses = filter(is_oom_status, pod.status.containerStatuses)
        for status in oom_statuses:
            dt = parse_kubernetes_datetime(status.lastState.terminated.finishedAt)
            time_ago = humanize.naturaltime(datetime.now(timezone.utc) - dt)
            msg = f"*{time_ago}*: pod={pod.metadata.name}; container={status.name}; image={status.image}"
            oom_kills.append(OOMKill(dt, msg))

    oom_kills.sort(key=lambda o: o.datetime)

    if oom_kills:
        logging.info(f"found at least one oom killer on {node.metadata.name}")
        return [ListBlock([oom.message for oom in oom_kills])]
    else:
        logging.info(f"found no oom killers on {node.metadata.name}")
        return []


@on_manual_trigger
def show_recent_oom_kills(event: ManualTriggerEvent):
    params = NodeNameParams(**event.data)
    node = Node().read(name=params.node_name)
    blocks = do_show_recent_oom_kills(node)
    if blocks:
        event.finding = Finding(
            title=f"Latest OOM Kills on {params.node_name}",
            subject=FindingSubject(name=params.node_name),
            source=FindingSource.MANUAL,
            finding_type="show_recent_oom_kills",
        )
        event.finding.add_enrichment(blocks)
