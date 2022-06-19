from typing import Optional, List
from hikaru.model import EventList, Event

from ..reporting import TableBlock
from ..reporting.custom_rendering import RendererType
from ...integrations.kubernetes.api_client_utils import parse_kubernetes_datetime_to_ms


def filter_event(
    ev: Event, name_substring_filter: str, included_types: Optional[List[str]]
) -> bool:
    if name_substring_filter is not None and name_substring_filter not in ev.involvedObject.name:
        return False
    if included_types is not None and ev.type.lower() not in [
        t.lower() for t in included_types
    ]:
        return False
    return True


def get_resource_events_table(
    table_name: str,
    kind: str,
    name: str = None,
    namespace: str = None,
    name_substring: str = "",
    included_types: Optional[List[str]] = None,
    max_events: Optional[int] = None,
) -> Optional[TableBlock]:
    field_selector = f"involvedObject.kind={kind}"
    if name:
        field_selector += f",involvedObject.name={name}"
    if namespace:
        field_selector += f",involvedObject.namespace={namespace}"

    event_list: EventList = Event.listEventForAllNamespaces(
        field_selector=field_selector
    ).obj
    if not event_list.items:
        return

    headers = ["reason", "type", "time", "message"]
    filtered_events = [
        ev
        for ev in event_list.items
        if filter_event(ev, name_substring, included_types)
    ]
    if not filtered_events:
        return

    sorted_events = sorted(filtered_events, key=get_event_timestamp, reverse=True)
    if max_events is not None:
        sorted_events = sorted_events[:max_events]

    rows = [
        [
            event.reason,
            event.type,
            parse_kubernetes_datetime_to_ms(get_event_timestamp(event))
            if get_event_timestamp(event)
            else 0,
            event.message,
        ]
        for event in sorted_events
    ]
    return TableBlock(
        rows=rows,
        headers=headers,
        column_renderers={"time": RendererType.DATETIME},
        table_name=table_name,
    )


def get_event_timestamp(event: Event):
    if event.lastTimestamp:
        return event.lastTimestamp
    elif event.eventTime:
        return event.eventTime
    elif event.firstTimestamp:
        return event.firstTimestamp
    if event.metadata.creationTimestamp:
        return event.metadata.creationTimestamp
    return


def get_events_list(event_type: str = None) -> EventList:
    """
    event_types are ["Normal","Warning"]
    """
    if event_type:
        field_selector = f"type={event_type}"
        return Event.listEventForAllNamespaces(field_selector=field_selector).obj
    return Event.listEventForAllNamespaces().obj
