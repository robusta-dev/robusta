from robusta.api import *
from datetime import datetime, timezone
from collections import namedtuple
import humanize


class OOMKillerParams (BaseModel):
    node_name: str = None
    slack_channel: str


def is_oom_status(status: ContainerStatus):
    if not status.lastState:
        return False
    if not status.lastState.terminated:
        return False
    return status.lastState.terminated.reason == "OOMKilled"


OOMKill = namedtuple('OOMKill', ['datetime', 'message'])


def do_show_recent_oom_kills(node: Node) -> List[BaseBlock]:
    results: PodList = Pod.listPodForAllNamespaces(field_selector=f"spec.nodeName={node.metadata.name}").obj

    oom_kills: List[OOMKill] = []
    for pod in results.items:
        oom_statuses = filter(is_oom_status, pod.status.containerStatuses)
        for status in oom_statuses:
            dt = datetime.fromisoformat(status.lastState.terminated.finishedAt.replace("Z", "+00:00"))
            time_ago = humanize.naturaltime(datetime.now(timezone.utc)-dt)
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
    params = OOMKillerParams(**event.data)
    node = Node().read(name=params.node_name)
    blocks = do_show_recent_oom_kills(node)
    if blocks:
        event.report_blocks.extend(blocks)
        event.slack_channel = params.slack_channel
        event.report_title = f"Latest OOM Kills on {params.node_name}"
        send_to_slack(event)


