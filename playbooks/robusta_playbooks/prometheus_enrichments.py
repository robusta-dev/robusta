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
)


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
