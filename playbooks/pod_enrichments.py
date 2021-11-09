from robusta.api import *


@action
def pod_events_enricher(event: PodEvent):
    pod = event.get_pod()
    if not pod:
        logging.error(
            f"cannot run PodEventsEnricher on alert with no pod object: {event}"
        )
        return

    block_list: List[BaseBlock] = []
    event_list: EventList = EventList.listNamespacedEvent(
        namespace=pod.metadata.namespace,
        field_selector=f"involvedObject.name={pod.metadata.name}",
    ).obj
    if event_list.items:  # add enrichment only if we got events
        block_list.append(MarkdownBlock("*Pod events:*"))
        headers = ["time", "message"]
        rows = [
            [parse_kubernetes_datetime_to_ms(event.lastTimestamp), event.message]
            for event in event_list.items
        ]
        block_list.append(
            TableBlock(
                rows=rows,
                headers=headers,
                column_renderers={"time": RendererType.DATETIME},
            )
        )
    event.add_enrichment(block_list)
