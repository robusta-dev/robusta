from robusta.api import *
from robusta.integrations.kubernetes.api_client_utils import parse_kubernetes_datetime
from datetime import datetime, timezone


class EventEnricherParams(ActionParams):
    since_seconds: int = 600


@action
def all_events_enricher(event: ExecutionBaseEvent, params: EventEnricherParams):
    # TODO: this will have to be changed to EventList when we update Hikaru to v0.7.0b or higher
    # see https://github.com/haxsaw/hikaru/blob/226f06606cc9b1db5dcb9e79f584f114edab9e21/release_notes.rst
    event_list: EventList = Event.listEventForAllNamespaces().obj
    if not event_list.items:
        return

    now = datetime.now(timezone.utc)
    rows = [
        [parse_kubernetes_datetime_to_ms(event.lastTimestamp), event.message]
        for event in event_list.items
        if (parse_kubernetes_datetime(event.lastTimestamp) - now).total_seconds()
        < params.since_seconds
    ]
    event.add_enrichment(
        [
            MarkdownBlock("*All cluster events:*"),
            TableBlock(
                rows=rows,
                headers=["time", "message"],
                column_renderers={"time": RendererType.DATETIME},
            ),
        ]
    )
