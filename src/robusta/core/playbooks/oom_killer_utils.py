import logging
import time

from robusta.api import (
    ExecutionBaseEvent,
    FileBlock,
    LogEnricherParams,
    MarkdownBlock,
    PodEvent,
    RegexReplacementStyle,
    RobustaPod,
)
from robusta.core.reporting.base import EnrichmentType


def start_log_enrichment(
    event: ExecutionBaseEvent,
    params: LogEnricherParams,
    pod: RobustaPod,
):
    if pod is None:
        if params.warn_on_missing_label:
            event.add_enrichment(
                [MarkdownBlock("Cannot fetch logs because the pod is unknown. The alert has no `pod` label")],
            )
        return

    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    if params.container_name:
        container = params.container_name
    elif any(status.name == event.get_subject().container for status in all_statuses):
        # support alerts with a container label, make sure it's related to this pod.
        container = event.get_subject().container
    else:
        container = ""

    tries: int = 2
    backoff_seconds: int = 2
    regex_replacement_style = (
        RegexReplacementStyle[params.regex_replacement_style] if params.regex_replacement_style else None
    )

    if not container and pod.spec.containers:
        # TODO do we want to keep this part of code? It used to sometimes report logs for a wrong
        #  container when a container inside a pod was oomkilled. I can imagine it could cause
        #  similar problems in other cases.
        container = pod.spec.containers[0].name
    for _ in range(tries - 1):
        log_data = pod.get_logs(
            container=container,
            regex_replacer_patterns=params.regex_replacer_patterns,
            regex_replacement_style=regex_replacement_style,
            filter_regex=params.filter_regex,
            previous=params.previous,
        )
        if not log_data:
            logging.info("log data is empty, retrying...")
            time.sleep(backoff_seconds)
            continue

        log_name = pod.metadata.name
        log_name += f"/{container}"
        event.add_enrichment(
            [FileBlock(filename=f"{pod.metadata.name}.log", contents=log_data.encode())],
            enrichment_type=EnrichmentType.text_file,
            title="Pod Logs"
        )
        break


def logs_enricher(event: PodEvent, params: LogEnricherParams):
    """
    Fetch and attach Pod logs.
    The pod to fetch logs for is determined by the alert’s pod label from Prometheus.

    By default, if the alert has no pod this enricher will silently do nothing.
    """
    pod = event.get_pod()

    logging.debug(f"received a logs_enricher action: {params}")
    start_log_enrichment(event=event, params=params, pod=pod)
