import uuid
from datetime import datetime

import flask
from ...core.model.cloud_event import CloudEvent
from ...core.model.events import EventType


def parse_incoming_manual_trigger(request: flask.Request) -> CloudEvent:
    trigger_name = request.form.get("trigger_name")
    if trigger_name is None:
        raise Exception(f"manual trigger is missing trigger_name. request={request}")

    event_data = request.form.to_dict()
    event_data["description"] = f"manual trigger for playbook {trigger_name}"

    return CloudEvent(
        specversion="1.0",
        type=EventType.MANUAL_TRIGGER.name,
        source=EventType.MANUAL_TRIGGER.name,
        subject=trigger_name,
        id=str(uuid.uuid4()),
        time=datetime.now(),
        datacontenttype="application/json",
        data=event_data,
    )
