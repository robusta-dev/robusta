from robusta.api import *


@action
def test_log_event(event: PodLogEvent):
    logging.error(
        f"got pod log event from {event.vector_log_payload.file} on {event.vector_log_payload.stream}"
    )
