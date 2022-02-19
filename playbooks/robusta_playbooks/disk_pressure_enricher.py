from robusta.api import *


@action
def disk_pressure_enricher(event: NodeEvent):
    """
    Provides relevant disk information for troubleshooting disk pressure issues when the disk on a node is filling up.
    """
    node = event.get_node()
    if not node:
        logging.error(
            f"cannot run disk pressure enricher on event with no node object: {event}"
        )
        return

    # Run disk-tools on node. calculate two tables from it.

    event.add_enrichment(
            [
                TableBlock(
                    headers=["a", "b", "c"],
                    rows=[
                        ["a1", "b1", "c1"],
                        ["a2", "b2", "c2"]
                    ]
                )
            ]
        )
