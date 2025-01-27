import json
import logging
import random
import string
from datetime import datetime
from typing import Dict, List, Optional

import requests

from robusta.api import PORT, ActionParams, AlertManagerEvent, ExecutionBaseEvent, action
from robusta.utils.error_codes import ActionException, ErrorCodes
from robusta.utils.silence_utils import AlertManagerParams, gen_alertmanager_headers, get_alertmanager_url

FALLBACK_PROMETHUES_GENERATOR_URL = "http://localhost:9090/graph?g0.expr=up%7Bjob%3D%22apiserver%22%7D&g0.tab=0&g0.stacked=0&g0.show_exemplars=0&g0.range_input=1h"


def parse_by_operator(pairs: str, operators: List[str]) -> Dict[str, str]:
    """
    Parses a comma-separated string of key-value segments where each segment
    can be split by one of multiple possible operators.
    For example:
        pairs_str = "foo:bar,baz=qux"
        operators = [":", "="]
    would return:
        {"foo": "bar", "baz": "qux"}

    :param pairs_str: Comma-separated string of key-value segments
    :param operators: List of possible operators (e.g., [":", "="])
    :return: Dictionary of parsed key-value pairs
    """

    if not pairs:
        return {}

    results: Dict[str, str] = {}
    segments = pairs.split(",")

    for segment in segments:
        segment = segment.strip()
        # If segment is empty, skip
        if not segment:
            continue

        # Find which operator appears first (lowest index) in this segment
        lowest_index = None
        chosen_operator = None

        for op in operators:
            idx = segment.find(op)
            if idx != -1 and (lowest_index is None or idx < lowest_index):
                lowest_index = idx
                chosen_operator = op

        # If none of the operators is found, skip or handle differently
        if chosen_operator is None:
            continue

        # Split once, using the chosen operator
        key, val = segment.split(chosen_operator, 1)
        results[key.strip()] = val.strip()

    return results


class PrometheusAlertParams(ActionParams):
    """
    :var alert_name: Simulated alert name.
    :var pod_name: Pod name, for a simulated pod alert.
    :var node_name: Node name, for a simulated node alert.
    :var deployment_name: Deployment name, for a simulated deployment alert.
    :var container_name: Container name, for adding a label on container.
    :var job_name: Job name, for a simulated Job alert.
    :var hpa: HPA name, for a simulated HorizontalPodAutoscaler alert.
    :var namespace: Pod namespace, for a simulated pod alert.
    :var service: service name, for additional prometheus labels.
    :var status: Simulated alert status. firing/resolved.
    :var severity: Simulated alert severity.
    :var description: Simulated alert description.
    :var generator_url: Prometheus generator_url. Some enrichers, use this attribute to query Prometheus.
    :var labels: Additional alert labels. For example: "key1: val1, key2: val2"
    :var annotations: Additional alert labels. For example: "key1=val1, key2=val2". Note that annotation separator is `=`
    :var runbook_url: Simulated alert runbook_url. For example: "https://my-runbook-url.dev"
    :var fingerprint: Simulated alert fingerprint. For example: "my-unique-fingerprint"
    """

    alert_name: str
    pod_name: Optional[str] = None
    node_name: Optional[str] = None
    deployment_name: Optional[str] = None
    container_name: Optional[str] = None
    service: Optional[str] = None
    job_name: Optional[str] = None
    name: Optional[str] = None
    hpa: Optional[str] = None
    statefulset_name: Optional[str] = None
    daemonset_name: Optional[str] = None
    namespace: str = "default"
    status: str = "firing"
    severity: str = "error"
    description: str = "simulated prometheus alert"
    summary: Optional[str]
    generator_url = FALLBACK_PROMETHUES_GENERATOR_URL
    runbook_url: Optional[str] = ""
    fingerprint: Optional[str] = ""
    labels: Optional[str] = None
    annotations: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


@action
def prometheus_alert(event: ExecutionBaseEvent, prometheus_event_data: PrometheusAlertParams):
    """
    Simulate Prometheus alert sent to the Robusta runner.
    Can be used for testing, when implementing actions triggered by Prometheus alerts.

    See the full parameters if you need to simulate an alert on a Pod or Node.
    """
    labels = {
        "severity": prometheus_event_data.severity,
        "namespace": prometheus_event_data.namespace,
        "alertname": prometheus_event_data.alert_name,
    }
    if prometheus_event_data.pod_name is not None:
        labels["pod"] = prometheus_event_data.pod_name
    if prometheus_event_data.node_name is not None:
        labels["node"] = prometheus_event_data.node_name
    if prometheus_event_data.deployment_name is not None:
        labels["deployment"] = prometheus_event_data.deployment_name
    if prometheus_event_data.container_name is not None:
        labels["container"] = prometheus_event_data.container_name
    if prometheus_event_data.service is not None:
        labels["service"] = prometheus_event_data.service
    if prometheus_event_data.job_name is not None:
        labels["job_name"] = prometheus_event_data.job_name
    if prometheus_event_data.name is not None:
        labels["name"] = prometheus_event_data.name
    if prometheus_event_data.hpa is not None:
        labels["horizontalpodautoscaler"] = prometheus_event_data.hpa
    if prometheus_event_data.statefulset_name is not None:
        labels["statefulset"] = prometheus_event_data.statefulset_name
    if prometheus_event_data.daemonset_name is not None:
        labels["daemonset"] = prometheus_event_data.daemonset_name
    if prometheus_event_data.labels is not None:
        labels.update(parse_by_operator(prometheus_event_data.labels, [":", "="]))

    starts_at = prometheus_event_data.starts_at if prometheus_event_data.starts_at else datetime.now().astimezone()

    if prometheus_event_data.ends_at is not None:
        ends_at = prometheus_event_data.ends_at
    elif prometheus_event_data.status == "resolved":
        ends_at = datetime.now()
    else:
        # alert not resolved and ends_at not specified
        ends_at = datetime.fromtimestamp(0)

    annotations = {
        "description": prometheus_event_data.description,
        "summary": prometheus_event_data.summary if prometheus_event_data.summary else prometheus_event_data.alert_name,
        "runbook_url": prometheus_event_data.runbook_url,
    }

    if prometheus_event_data.annotations is not None:
        annotations.update(parse_by_operator(prometheus_event_data.annotations, [":", "="]))

    fingerprint = prometheus_event_data.fingerprint
    if not fingerprint:  # if user didn't provide fingerprint, generate random one, to avoid runner deduplication
        fingerprint = "".join(random.choices(string.ascii_lowercase, k=8))

    prometheus_event = AlertManagerEvent(
        **{
            "status": prometheus_event_data.status,
            "description": prometheus_event_data.description,
            "externalURL": "",
            "groupKey": "{}/{}:{}",
            "version": "1",
            "receiver": "robusta receiver",
            "alerts": [
                {
                    "status": prometheus_event_data.status,
                    "endsAt": ends_at,
                    "startsAt": starts_at,
                    "generatorURL": prometheus_event_data.generator_url,
                    "fingerprint": fingerprint,
                    "labels": labels,
                    "annotations": annotations,
                }
            ],
        }
    )
    headers = {"Content-type": "application/json"}
    return requests.post(
        f"http://localhost:{PORT}/api/alerts",
        data=prometheus_event.json(),
        headers=headers,
    )


class AlertmanagerAlertParams(AlertManagerParams):
    """
    :var alert_name: Simulated alert name.
    :var pod_name: Pod name, for a simulated pod alert.
    :var status: Simulated alert status. firing/resolved.
    :var severity: Simulated alert severity.
    :var description: Simulated alert description.
    :var labels: Additional alert labels. For example: "key1=val1, key2=val2"
    :var annotations: Additional alert labels. For example: "key1=val1, key2=val2"
    :var namespace: Pod namespace, for a simulated pod alert.
    :var summary: Simulated alert summary.
    """

    alert_name: str = "KubePodNotReady"
    pod_name: Optional[str] = None
    namespace: str = "default"
    status: str = "firing"
    severity: str = "error"
    description: Optional[str] = "simulated alert manager alert"
    summary: Optional[str] = "alert manager alert created by Robusta"
    labels: Optional[str] = None
    annotations: Optional[str] = None


@action
def alertmanager_alert(event: ExecutionBaseEvent, action_params: AlertmanagerAlertParams):
    alert_labels = {
        "alertname": action_params.alert_name,
        "severity": action_params.severity,
        "namespace": action_params.namespace,
    }

    if action_params.pod_name is not None:
        alert_labels["pod"] = action_params.pod_name

    labels = action_params.labels
    if labels:
        alert_labels.update(parse_by_operator(labels, "="))

    annotations = {
        "summary": action_params.summary,
        "description": action_params.description,
    }

    if action_params.annotations:
        annotations.update(parse_by_operator(action_params.annotations, "="))

    alerts = [
        {
            "status": action_params.status,
            "labels": alert_labels,
            "annotations": annotations,
        }
    ]

    headers = gen_alertmanager_headers(action_params)

    alertmanager_url = get_alertmanager_url(action_params)
    if not alertmanager_url:
        raise ActionException(ErrorCodes.ALERT_MANAGER_DISCOVERY_FAILED)

    try:
        requests.post(
            f"{alertmanager_url}/api/v2/alerts",
            data=json.dumps(alerts),
            headers=headers,
        ).raise_for_status()
    except Exception:
        logging.exception(f"Failed to create alertmanager alerts {alerts}")
        raise ActionException(ErrorCodes.ALERT_MANAGER_REQUEST_FAILED)


class AlertManagerEventParams(ActionParams):
    event: Dict


@action
def handle_alertmanager_event(event: ExecutionBaseEvent, alert_manager_event: AlertManagerEventParams):
    """
    Handle alert manager event, as a Robusta action.
    """
    prometheus_event = AlertManagerEvent(**alert_manager_event.event)
    headers = {"Content-type": "application/json"}
    return requests.post(
        f"http://localhost:{PORT}/api/alerts",
        data=prometheus_event.json(),
        headers=headers,
    )
