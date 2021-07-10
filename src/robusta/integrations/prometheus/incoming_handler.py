import datetime
import uuid

import flask

from ...core.model.cloud_event import CloudEvent
from ...core.model.events import EventType


def parse_incoming_prometheus_alerts(request: flask.Request) -> CloudEvent:
    event_data = request.get_json()
    event_data["description"] = "prometheus alerts group"
    return prometheus_cloud_event(event_data)


def prometheus_cloud_event(event_data):
    cloud_event = CloudEvent(
        **{
            "specversion": "1.0",
            "type": EventType.PROMETHEUS.name,
            "source": EventType.PROMETHEUS.name,
            "subject": "",
            "id": str(uuid.uuid4()),
            "datacontenttype": "application/json",
            "time": datetime.datetime.now(),
            "data": event_data,
        }
    )
    return cloud_event
