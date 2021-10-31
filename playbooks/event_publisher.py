from robusta.api import *


class PrometehusAlertParams(BaseModel):
    alert_name: str
    pod_name: str
    status: str = "firing"
    description: str = "simulated prometheus alert"
    namespace: str = "default"
    generator_url = ""


# Usage: curl -X POST -F 'alert_name=HighCPUAlert' -F 'pod_name=robusta-runner-5d6f654bf9-jm2hx' -F 'namespace=robusta' -F 'trigger_name=prometheus_alert' http://localhost:5000/api/trigger
# or: robusta trigger prometheus_alert alert_name=HighCPUAlert pod_name=robusta-runner-5d6f654bf9-jm2hx namespace=robusta
@on_manual_trigger
def prometheus_alert(event: ManualTriggerEvent):
    prometheus_event_data = PrometehusAlertParams(**event.data)

    prometheus_event = PrometheusEvent(
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
                    "labels": {
                        "severity": "info",
                        "pod": prometheus_event_data.pod_name,
                        "namespace": prometheus_event_data.namespace,
                        "alertname": prometheus_event_data.alert_name,
                    },
                    "annotations": {},
                }
            ],
        }
    )

    run_playbooks(prometheus_cloud_event(prometheus_event))
