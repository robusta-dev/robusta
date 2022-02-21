from robusta.api import *


class PrometehusAlertParams(ActionParams):
    """
    :var alert_name: Simulated alert name.
    :var pod_name: Pod name, for a simulated pod alert.
    :var namespace: Pod namespace, for a simulated pod alert.
    :var status: Simulated alert status. firing/resolved.
    :var severity: Simulated alert severity.
    :var description: Simulated alert description.
    :var generator_url: Prometheus generator_url. Some enrichers, use this attribute to query Prometheus.
    """
    alert_name: str
    pod_name: Optional[str] = None
    node_name: Optional[str] = None
    namespace: str = "default"
    status: str = "firing"
    severity: str = "error"
    description: str = "simulated prometheus alert"
    generator_url = ""


@action
def prometheus_alert(
    event: ExecutionBaseEvent, prometheus_event_data: PrometehusAlertParams
):
    """
    Simulate Prometheus alert sent to the Robusta runner.
    Can be used for testing, when implementing actions triggered by Prometheus alerts.

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
                    "annotations": {},
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
