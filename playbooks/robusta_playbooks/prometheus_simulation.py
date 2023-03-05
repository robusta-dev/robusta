from datetime import datetime
from typing import Dict, Optional

import requests
from robusta.api import ActionParams, AlertManagerEvent, ExecutionBaseEvent, action


class PrometheusAlertParams(ActionParams):
    """
    :var alert_name: Simulated alert name.
    :var pod_name: Pod name, for a simulated pod alert.
    :var node_name: Node name, for a simulated node alert.
    :var deployment_name: Deployment name, for a simulated deployment alert.
    :var container_name: Container name, for adding a label on container.
    :var job_name: Job name, for a simulated Job alert.
    :var namespace: Pod namespace, for a simulated pod alert.
    :var service: service name, for additional prometheus labels.
    :var status: Simulated alert status. firing/resolved.
    :var severity: Simulated alert severity.
    :var description: Simulated alert description.
    :var generator_url: Prometheus generator_url. Some enrichers, use this attribute to query Prometheus.
    """

    alert_name: str
    pod_name: Optional[str] = None
    node_name: Optional[str] = None
    deployment_name: Optional[str] = None
    container_name: Optional[str] = None
    service: Optional[str] = None
    job_name: Optional[str] = None
    namespace: str = "default"
    status: str = "firing"
    severity: str = "error"
    description: str = "simulated prometheus alert"
    summary: Optional[str]
    generator_url = ""


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
        labels["job"] = prometheus_event_data.job_name

    annotations = {
        "description": prometheus_event_data.description,
        "summary": prometheus_event_data.summary if prometheus_event_data.summary else prometheus_event_data.alert_name,
    }
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
                    "endsAt": datetime.now(),
                    "startsAt": datetime.now(),
                    "generatorURL": prometheus_event_data.generator_url,
                    "labels": labels,
                    "annotations": annotations,
                }
            ],
        }
    )
    headers = {"Content-type": "application/json"}
    return requests.post(
        "http://localhost:5000/api/alerts",
        data=prometheus_event.json(),
        headers=headers,
    )


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
        "http://localhost:5000/api/alerts",
        data=prometheus_event.json(),
        headers=headers,
    )
