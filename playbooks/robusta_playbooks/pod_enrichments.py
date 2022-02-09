from robusta.api import *


@action
def pod_events_enricher(event: PodEvent):
    """
    Enrich the finding with the pod events.
    """
    pod = event.get_pod()
    if not pod:
        logging.error(
            f"cannot run PodEventsEnricher on alert with no pod object: {event}"
        )
        return

    events_table_block = get_resource_events_table("*Pod events:*", pod.kind, pod.metadata.name, pod.metadata.namespace)
    if events_table_block:
        event.add_enrichment([events_table_block])
