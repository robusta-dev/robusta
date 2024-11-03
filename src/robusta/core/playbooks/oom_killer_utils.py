import logging
import time
from typing import Optional

from robusta.api import (
    EmptyFileBlock,
    ExecutionBaseEvent,
    FileBlock,
    LogEnricherParams,
    MarkdownBlock,
    PodEvent,
    RegexReplacementStyle,
    RobustaPod,
)
from robusta.core.playbooks.pod_utils.crashloop_utils import get_crash_report_enrichments
from robusta.core.reporting.base import EnrichmentType


def start_log_enrichment(
    event: ExecutionBaseEvent,
    params: LogEnricherParams,
    pod: RobustaPod,
    title_override: Optional[str] = None
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

    enrichments = get_crash_report_enrichments(pod)
    for enrichment in enrichments:
        event.add_enrichment(enrichment.blocks,
                             enrichment_type=enrichment.enrichment_type,
                             title=enrichment.title)

    if not container and pod.spec.containers:
        # TODO do we want to keep this part of code? It used to sometimes report logs for a wrong
        #  container when a container inside a pod was oomkilled. I can imagine it could cause
        #  similar problems in other cases.
        container = pod.spec.containers[0].name

    log_data = ""
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
        break

    if not log_data:
        log_block = EmptyFileBlock(filename=f"{pod.metadata.name}.log",
                                   remarks=f"Logs unavailable for container: {container}")
        logging.info(
            f"could not fetch logs from container: {container}"
        )
    else:
        log_block = FileBlock(filename=f"{pod.metadata.name}.log", contents=log_data.encode())
    title = "Logs" if not title_override else title_override
    event.add_enrichment([log_block],
                         enrichment_type=EnrichmentType.text_file, title=title)


def logs_enricher(event: PodEvent, params: LogEnricherParams):
    """
    Fetch and attach Pod logs.
    The pod to fetch logs for is determined by the alert’s pod label from Prometheus.

    By default, if the alert has no pod this enricher will silently do nothing.
    """
    pod = event.get_pod()

    logging.debug(f"received a logs_enricher action: {params}")
    start_log_enrichment(event=event, params=params, pod=pod)
