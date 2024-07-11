from typing import List

from hikaru.model.rel_1_26 import Pod


def pod_row(pod: Pod) -> List[str]:
    ready_condition = [condition.status for condition in pod.status.conditions if condition.type == "Ready"]
    return [
        pod.metadata.namespace,
        pod.metadata.name,
        ready_condition[0] if ready_condition else "Unknown",
    ]
