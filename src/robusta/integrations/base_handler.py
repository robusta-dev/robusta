import copy
import logging
import traceback

from typing import List

from ..core.framework.sinks.sink_factory import SinkFactory
from ..core.model.events import BaseEvent


def handle_event(
    func, event: BaseEvent, action_params, event_source: str, named_sinks: List[str]
):
    event_desc = getattr(event, "description", None)
    description = f"event={event_desc}" if event_desc else ""
    logging.info(
        f"running {event_source} playbook {func.__name__}; action_params={action_params}; sinks={named_sinks}; {description}"
    )
    if action_params is None:
        result = func(event)
    else:
        result = func(event, action_params)

    if event.processing_context.finding:
        for sink_name in named_sinks:
            try:
                sink = SinkFactory.get_sink_by_name(sink_name)
                if not sink:
                    logging.error(
                        f"sink {sink_name} not found. Skipping event finding {event.processing_context.finding}"
                    )
                    continue
                # create deep copy, so that iterating on one sink won't affect the others
                finding_copy = copy.deepcopy(event.processing_context.finding)
                sink.write_finding(finding_copy)
            except Exception:  # Faliure to send to one sink shouldn't fail all
                logging.error(
                    f"Failed to publish finding to sink {sink_name}",
                    traceback.print_exc(),
                )

    if result is not None:
        return result
    return "OK"
