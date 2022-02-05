from typing import Optional
from hikaru.model import EventList, Event

from ..reporting import TableBlock
from ..reporting.custom_rendering import RendererType
from ...integrations.kubernetes.api_client_utils import parse_kubernetes_datetime_to_ms


def get_resource_events_table(table_name: str, kind: str, name: str, namespace: str = None) -> Optional[TableBlock]:
    field_selector = f"involvedObject.kind={kind},involvedObject.name={name}"
    if namespace:
        field_selector += f",involvedObject.namespace={namespace}"

    event_list: EventList = Event.listEventForAllNamespaces(field_selector=field_selector).obj

    if event_list.items:
        headers = ["reason", "type", "time", "message"]
        rows = [
            [event.reason, event.type, parse_kubernetes_datetime_to_ms(event.lastTimestamp), event.message]
            for event in event_list.items
        ]
        return TableBlock(
                rows=rows,
                headers=headers,
                column_renderers={"time": RendererType.DATETIME},
                table_name=table_name
            )
    return None

