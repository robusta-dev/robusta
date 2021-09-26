import logging
from robusta.api import *


class RestartLoopParams(BaseModel):
    restart_reason: str = None
    rate_limit: int = 3600


def get_crashing_containers(
    status: PodStatus, config: RestartLoopParams
) -> [ContainerStatus]:
    return [
        container_status
        for container_status in status.containerStatuses
        if container_status.state.waiting is not None
        and container_status.restartCount
        > 1  # report only after the 2nd restart and get previous logs
        and (
            config.restart_reason is None
            or container_status.state.waiting.reason == config.restart_reason
        )
    ]


@on_pod_update
def restart_loop_reporter(event: PodEvent, config: RestartLoopParams):
    crashed_container_statuses = get_crashing_containers(event.obj.status, config)

    if len(crashed_container_statuses) == 0:
        return  # no matched containers

    pod = event.obj
    pod_name = pod.metadata.name
    if not RateLimiter.mark_and_test(
        "restart_loop_reporter", pod_name + pod.metadata.namespace, config.rate_limit
    ):
        return

    event.finding = Finding(
        title=f"Crashing pod {pod.metadata.name} in namespace {pod.metadata.namespace}",
        source=FindingSource.KUBERNETES_API_SERVER,
        aggregation_key="restart_loop_reporter",
        subject=FindingSubject(
            name=pod_name,
            subject_type=FindingSubjectType.TYPE_POD,
            namespace=pod.metadata.namespace,
        ),
    )
    blocks: List[BaseBlock] = []
    for container_status in crashed_container_statuses:
        blocks.append(
            MarkdownBlock(
                f"*{container_status.name}* restart count: {container_status.restartCount}"
            )
        )
        if container_status.state and container_status.state.waiting:
            blocks.append(
                MarkdownBlock(
                    f"*{container_status.name}* waiting reason: {container_status.state.waiting.reason}"
                )
            )
        if container_status.state and container_status.state.terminated:
            blocks.append(
                MarkdownBlock(
                    f"*{container_status.name}* termination reason: {container_status.state.terminated.reason}"
                )
            )
        if container_status.lastState and container_status.lastState.terminated:
            blocks.append(
                MarkdownBlock(
                    f"*{container_status.name}* termination reason: {container_status.lastState.terminated.reason}"
                )
            )
        container_log = pod.get_logs(container_status.name, previous=True)
        if container_log:
            blocks.append(FileBlock(f"{pod_name}.txt", container_log))
        else:
            blocks.append(
                MarkdownBlock(
                    f"Container logs unavailable for container: {container_status.name}"
                )
            )
            logging.error(
                f"could not fetch logs from container: {container_status.name}. logs were {container_log}"
            )

    event.finding.add_enrichment(blocks)
