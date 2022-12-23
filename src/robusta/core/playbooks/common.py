from typing import List, Optional, cast

from hikaru.model import Event, EventList

from robusta.core.reporting import TableBlock
from robusta.core.reporting.custom_rendering import RendererType
from robusta.integrations.kubernetes.api_client_utils import parse_kubernetes_datetime_to_ms


def filter_event(ev: Event, name_substring_filter: str, included_types: Optional[List[str]]) -> bool:
    assert ev.involvedObject.name is not None
    if name_substring_filter is not None and name_substring_filter not in ev.involvedObject.name:
        return False

    assert ev.type is not None
    if included_types is not None and ev.type.lower() not in [t.lower() for t in included_types]:
        return False

    return True


def get_resource_events_table(
    table_name: str,
    kind: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    name_substring: str = "",
    included_types: Optional[List[str]] = None,
    max_events: Optional[int] = None,
) -> Optional[TableBlock]:
    field_selector = f"involvedObject.kind={kind}"
    if name is not None:
        field_selector += f",involvedObject.name={name}"
    if namespace is not None:
        field_selector += f",involvedObject.namespace={namespace}"

    event_list = cast(EventList, Event.listEventForAllNamespaces(field_selector=field_selector).obj)
    if not event_list.items:
        return

    headers = ["reason", "type", "time", "message"]
    filtered_events = [ev for ev in event_list.items if filter_event(ev, name_substring, included_types)]
    if not filtered_events:
        return

    sorted_events = sorted(filtered_events, key=get_event_timestamp, reverse=True)
    if max_events is not None:
        sorted_events = sorted_events[:max_events]

    rows = [
        [
            event.reason,
            event.type,
            parse_kubernetes_datetime_to_ms(get_event_timestamp(event)) if get_event_timestamp(event) else 0,
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


def get_event_timestamp(event: Event) -> str:
    if event.lastTimestamp:
        return event.lastTimestamp
    if event.eventTime:
        return event.eventTime
    if event.firstTimestamp:
        return event.firstTimestamp
    if event.metadata.creationTimestamp:
        return event.metadata.creationTimestamp
    # TODO: Should we raise an exception here?
    return  # type: ignore


def get_events_list(event_type: Optional[str] = None) -> EventList:
    """
    event_types are ["Normal","Warning"]
    """
    if event_type is not None:
        field_selector = f"type={event_type}"
        return Event.listEventForAllNamespaces(field_selector=field_selector).obj  # type: ignore
    return Event.listEventForAllNamespaces().obj  # type: ignore
