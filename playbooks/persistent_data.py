# TODO: turn this into a bot that prints statistics/a graph of changes at the end of the day/week
# on what changed the most
from robusta.api import *


class DeploymentChangeCounter(BaseModel):
    changes_per_deployment: Dict[str, int] = {}


PERSISTENT_DATA_NAME = "test_persistency"


@on_deployment_update
def count_pod_creations(event: DeploymentEvent):
    logging.info("we got an event... sending it to slack")
    with get_persistent_data(PERSISTENT_DATA_NAME, DeploymentChangeCounter) as data:
        name = event.obj.metadata.name
        value = data.changes_per_deployment.get(name, 0)
        data.changes_per_deployment[name] = value + 1

    event.finding = Finding(
        title=f"DeploymentChangeCounter: {data.changes_per_deployment}"
    )
