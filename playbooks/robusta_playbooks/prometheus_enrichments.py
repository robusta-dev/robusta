import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union

from kubernetes import client
from kubernetes.client.models.v1_service import V1Service
from prometheus_api_client import PrometheusApiClientException
from prometrix import PrometheusQueryResult
from robusta.api import (
    ExecutionBaseEvent,
    MarkdownBlock,
    PrometheusBlock,
    PrometheusDateRange,
    PrometheusDuration,
    PrometheusKubernetesAlert,
    PrometheusQueryParams,
    action,
    run_prometheus_query,
    run_prometheus_query_range,
)
from robusta.core.model.base_params import PrometheusParams
from robusta.core.reporting import JsonBlock
from robusta.integrations.prometheus.utils import get_prometheus_connect


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
        starts_at = datetime.utcnow().replace(microsecond=0) - timedelta(minutes=duration.duration_minutes)
        ends_at = datetime.utcnow().replace(microsecond=0)
        return starts_at, ends_at
    logging.error("Non supported duration provided")
    return None, None


@action
def prometheus_all_available_metrics(event: ExecutionBaseEvent, prometheus_params: PrometheusParams):
    result = get_prometheus_all_available_metrics(prometheus_params=prometheus_params)

    event.add_enrichment([JsonBlock(json.dumps({"metrics": result}))])


def get_prometheus_all_available_metrics(prometheus_params: PrometheusParams) -> List[str]:
    try:
        prom = get_prometheus_connect(prometheus_params=prometheus_params)
        return prom.all_metrics()

    except Exception as e:
        logging.error("An error occurred while fetching all available Prometheus metrics", exc_info=True)
        raise e


class PrometheusGetSeriesParams(PrometheusParams):
    """
    :var match: List of Prometheus series selectors.
    :var start_time: Optional start time for the query as datetime.
    :var end_time: Optional end time for the query as datetime.
    """

    match: List[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@action
def prometheus_get_series(event: ExecutionBaseEvent, prometheus_params: PrometheusGetSeriesParams):
    result = get_prometheus_series(prometheus_params=prometheus_params)

    event.add_enrichment([JsonBlock(json.dumps({"series": result}))])


def get_prometheus_series(prometheus_params: PrometheusGetSeriesParams) -> dict:
    try:
        prom = get_prometheus_connect(prometheus_params=prometheus_params)
        return prom.get_series(
            match=prometheus_params.match, end_time=prometheus_params.end_time, start_time=prometheus_params.start_time
        )

    except Exception as e:
        logging.error(
            f"Failed to fetch Prometheus series for match criteria {prometheus_params.match} within the time range {prometheus_params.start_time} - {prometheus_params.end_time}",
            exc_info=True,
        )
        raise e


class PrometheusGetLabelNames(PrometheusParams):
    """
    :var match: List of Prometheus series selectors. If this parameter is None or an empty list, the labels won't be filtered by specific series selectors.
    :var start: Optional start time for the query as datetime.If this parameter is None, Prometheus won't filter labels by start time.
    :var end: Optional end time for the query as datetime. If this parameter is None, Prometheus won't filter labels by end time.
    :var limit: Optional maximum number of returned series. If this parameter is None, the returned list length won't be limited by number.
    """

    match: Optional[List[str]] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: Optional[int] = None


@action
def prometheus_get_label_names(event: ExecutionBaseEvent, prometheus_params: PrometheusGetLabelNames):
    """
    Fetches a list of label names from prometheus instance.

    https://prometheus.io/docs/prometheus/latest/querying/api/#getting-label-names
    """
    try:
        prom = get_prometheus_connect(prometheus_params=prometheus_params)
        prom_label_names = prom.get_label_names(prometheus_params.dict())

    except Exception as e:
        logging.error("An error occurred while fetching all available Prometheus metrics", exc_info=True)
        raise e

    event.add_enrichment([JsonBlock(json.dumps({"labels": prom_label_names}))])


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
        prometheus_result = run_prometheus_query_range(
            prometheus_params=params,
            promql_query=params.promql_query,
            starts_at=starts_at,
            ends_at=ends_at,
            step=params.step,
        )
        event.add_enrichment(
            [PrometheusBlock(data=prometheus_result, query=params.promql_query)],
        )
    except PrometheusApiClientException as e:
        data = PrometheusQueryResult({"resultType": "error", "result": str(e)})
        event.add_enrichment(
            [PrometheusBlock(data=data, query=params.promql_query)],
        )


def get_duplicate_kubelet_msg(rule_group: Optional[str]) -> Optional[str]:
    """
    checks if there are multiple kubelets and
    """
    if not rule_group or "kubelet" not in rule_group:
        return None
    labels_selectors = "k8s-app=kubelet, app.kubernetes.io/managed-by=prometheus-operator"
    v1 = client.CoreV1Api()
    kubelet_services: List[V1Service] = v1.list_service_for_all_namespaces(label_selector=labels_selectors).items
    if not kubelet_services or len(kubelet_services) <= 1:
        return None
    # there is more than one kubelet
    kubelet_names_string = ", ".join(
        [f"{kubelet.metadata.namespace}/{kubelet.metadata.name}" for kubelet in kubelet_services]
    )
    return f"The rule failure might be caused by multiple kubelet services running in your cluster: {kubelet_names_string}."


@action
def prometheus_rules_enricher(alert: PrometheusKubernetesAlert):
    """
    Enriches the finding with a for information due to rule failure
    """
    kubelet_error_string = get_duplicate_kubelet_msg(alert.get_alert_label("rule_group"))
    if kubelet_error_string:
        alert.add_enrichment([MarkdownBlock(kubelet_error_string)])


class PrometheusSlaParams(PrometheusParams):
    """
    :var promql_query: a promql non range query that should return a scalar or vector.
    :var operator: one of < > == != used for SLA condition.
    :var threshold: float used with operator for SLA condition.
    """

    promql_query: str
    operator: str
    threshold: float


@action
def prometheus_sla_enricher(event: ExecutionBaseEvent, params: PrometheusSlaParams):
    """
    Enriches the finding title and description with an SLA VIOATLION warning incase a condition is met.
    """

    if not params.promql_query:
        raise Exception("Invalid request, prometheus_enricher requires a promql query.")

    if params.operator not in [">", "<", "==", "!="]:
        params.operator = ">"

    try:
        prometheus_result = run_prometheus_query(prometheus_params=params, query=params.promql_query)
    except PrometheusApiClientException as e:
        data = PrometheusQueryResult({"resultType": "error", "result": str(e)})
        event.add_enrichment(
            [PrometheusBlock(data=data, query=params.promql_query)],
        )
        return

    query_result = 0
    if prometheus_result.result_type == "scalar":
        query_result = prometheus_result.scalar_result["value"]
    elif prometheus_result.result_type == "vector":
        query_result = float(prometheus_result.vector_result[-1]["value"]["value"])

    rule_result: bool = False
    results: dict = {
        ">": query_result > params.threshold,
        "<": query_result < params.threshold,
        "==": query_result == params.threshold,
        "!=": query_result != params.threshold,
    }
    rule_result = results.get(params.operator, False)

    original_title = ""
    for sink in event.named_sinks:
        for finding in event.sink_findings[sink]:
            original_title = finding.title
        break

    event.add_enrichment(
        [MarkdownBlock("*SLA Query* : " + params.promql_query)],
    )

    operator_to_name = {"<": "lt", "==": "eq", ">": "gt", "!=": "ne"}
    sla_violation = "SLA VIOLATION" if rule_result else "SLA"
    new_title = f"{sla_violation} {query_result:.3f} {operator_to_name.get(params.operator)} {params.threshold} {original_title}"
    event.override_finding_attributes(title=new_title)
