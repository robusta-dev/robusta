from robusta.api import *


def pod_events_enrichment(name: str, namespace: str) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    block_list.append(MarkdownBlock("*Pod events:*"))
    headers = ["time", "message"]
    event_list: EventList = EventList.listNamespacedEvent(
        namespace=namespace, field_selector=f"involvedObject.name={name}"
    ).obj
    rows = [[event.lastTimestamp, event.message] for event in event_list.items]
    block_list.append(TableBlock(rows=rows, headers=headers))
    return block_list


@on_manual_trigger
def pod_events(event: ManualTriggerEvent):
    action_params = PodParams(**event.data)
    logging.info(f"getting info for: {action_params}")

    blocks = pod_events_enrichment(action_params.pod_name, action_params.pod_namespace)
    for block in blocks:
        if isinstance(block, TableBlock):
            for row in block.rows:
                print(f"row {row}")
