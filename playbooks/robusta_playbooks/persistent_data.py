# TODO: turn this into a bot that prints statistics/a graph of changes at the end of the day/week
# on what changed the most
import logging
from typing import Dict

from pydantic import BaseModel

from robusta.api import DeploymentEvent, Finding, FindingType, action, get_persistent_data


class DeploymentChangeCounter(BaseModel):
    changes_per_deployment: Dict[str, int] = {}


PERSISTENT_DATA_NAME = "test_persistency"


@action
def count_pod_creations(event: DeploymentEvent):
    logging.info("we got an event... sending it to slack")
    with get_persistent_data(PERSISTENT_DATA_NAME, DeploymentChangeCounter) as data:
        deployment = event.get_deployment()
        if not deployment:
            logging.info(f"count_pod_creations - no deployment for event: {DeploymentEvent}")
            return
        name = deployment.metadata.name
        value = data.changes_per_deployment.get(name, 0)
        data.changes_per_deployment[name] = value + 1

    finding = Finding(
        title=f"DeploymentChangeCounter: {data.changes_per_deployment}",
        aggregation_key="CountPodCreations",
        finding_type=FindingType.REPORT,
        failure=False,
    )
    event.add_finding(finding)
