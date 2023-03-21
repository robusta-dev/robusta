import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union

from prometheus_api_client import PrometheusApiClientException
from robusta.api import (
    ActionParams,
    ExecutionBaseEvent,
    NamedRegexPattern,
    PrometheusDateRange,
    PrometheusDiscovery,
    PrometheusDuration,
    PrometheusQueryParams,
    PrometheusQueryResult,
    action,
    run_prometheus_query,
)
from robusta.core.reporting.blocks import FileBlock, PrometheusBlock


def parse_timestamp_string(date_string: str) -> Optional[datetime]:
    try:
        if date_string:
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S %Z")
        return None
    except Exception:
        logging.error(f"Failed parsing time string {date_string}", exc_info=True)
        return None


def parse_duration(
    duration: Union[PrometheusDateRange, PrometheusDuration]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    if isinstance(duration, PrometheusDateRange):
        return parse_timestamp_string(duration.starts_at), parse_timestamp_string(duration.ends_at)
    elif isinstance(duration, PrometheusDuration):
        starts_at = datetime.utcnow() - timedelta(minutes=duration.duration_minutes)
        ends_at = datetime.utcnow()
        return starts_at, ends_at
    logging.error("Non supported duration provided")
    return None, None


class PrometheusLogsParams(ActionParams):
    """
    :var regex_replacer_patterns: regex patterns to replace text, for example for security reasons (Note: Replacements are executed in the given order)
    :var regex_replacement_style: one of SAME_LENGTH_ASTERISKS or NAMED (See RegexReplacementStyle)
    :var lines_with_regex: only shows lines that match the regex
    """

    regex_replacer_patterns: Optional[List[NamedRegexPattern]] = None
    regex_replacement_style: str = "SAME_LENGTH_ASTERISKS"
    lines_with_regex: Optional[str] = None


def filter_logs(logs: str, lines_with_regex: str) -> str:
    regex = re.compile(lines_with_regex)
    return "\n".join(re.findall(regex, logs))


@action
def prometheus_logs_enricher(event: ExecutionBaseEvent, params: PrometheusLogsParams):
    """
    Enriches the finding with the logs from your prometheus pod

    For clusters with an out of cluster prometheus or no detectable prometheus this action will silently do nothing.
    """
    regex_replacement_style = (
        RegexReplacementStyle[params.regex_replacement_style] if params.regex_replacement_style else None
    )
    pods = PrometheusDiscovery.find_prometheus_pods()
    logging.warning(len(pods))
    if pods:
        log_data = pods[0].get_logs(
            regex_replacer_patterns=params.regex_replacer_patterns, regex_replacement_style=regex_replacement_style
        )
        if params.lines_with_regex:
            log_data = filter_logs(log_data, params.lines_with_regex)
        logging.warning(log_data)
        if log_data:
            event.add_enrichment(
                [FileBlock(f"{pods[0].metadata.name}.log", log_data.encode())],
            )


@action
def prometheus_enricher(event: ExecutionBaseEvent, params: PrometheusQueryParams):
    """
    Enriches the finding with a prometheus query

    for example prometheus queries see here:
    https://prometheus.io/docs/prometheus/latest/querying/examples/
    """
    # verifies params.promql_query is not an empty string ""
    if not params.promql_query:
        raise Exception("Invalid request, prometheus_enricher requires a promql query.")
    starts_at, ends_at = parse_duration(params.duration)
    if not starts_at or not ends_at:
        raise Exception("Invalid request, verify the duration times are of format '%Y-%m-%d %H:%M:%S %Z'")
        return
    try:
        prometheus_result = run_prometheus_query(
            prometheus_params=params,
            promql_query=params.promql_query,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        event.add_enrichment(
            [PrometheusBlock(data=prometheus_result, query=params.promql_query)],
        )
    except PrometheusApiClientException as e:
        data = PrometheusQueryResult({"resultType": "error", "result": str(e)})
        event.add_enrichment(
            [PrometheusBlock(data=data, query=params.promql_query)],
        )
