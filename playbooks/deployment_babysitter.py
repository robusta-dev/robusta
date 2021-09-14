# TODO: we should attach a full yaml diff when the deployment spec (not status) changes
# options for generating a human-readable diff:
# * python_diff = "\n".join([x for x in unified_diff(before.splitlines(), after.splitlines(), fromfile="old", tofile="new")])
# * https://github.com/google/diff-match-patch/wiki/Language:-Python (see output format here: https://neil.fraser.name/software/diff_match_patch/demos/diff.html)
# * https://github.com/wagoodman/diff2HtmlCompare
# * https://github.com/GerHobbelt/google-diff-match-patch
from typing import Tuple
from hikaru.meta import DiffDetail, DiffType

from robusta.api import *


class BabysitterConfig(BaseModel):
    fields_to_monitor: List[str] = ["spec"]


def do_babysitter(
    event: K8sBaseEvent, config: BabysitterConfig, resource_type: FindingSubjectType
):
    filtered_diffs = []
    if event.operation == K8sOperationType.UPDATE:
        all_diffs = event.obj.diff(event.old_obj)
        filtered_diffs = list(
            filter(lambda x: is_matching_diff(x, config.fields_to_monitor), all_diffs)
        )
        if len(filtered_diffs) == 0:
            return

    old_obj = event.old_obj
    obj = event.obj
    if (
        event.operation == K8sOperationType.DELETE
    ):  # On delete, the current obj should be None, and not the actual object, as recieved
        obj = None
        old_obj = event.obj

    diff_block = KubernetesDiffBlock(filtered_diffs, old_obj, obj)
    event.finding = Finding(
        title=f"{diff_block.resource_name} {event.operation.value}d",
        description=f"{diff_block.num_additions} fields added. {diff_block.num_deletions} fields removed. {diff_block.num_modifications} fields changed",
        source=FindingSource.KUBERNETES_API_SERVER,
        finding_type=FindingType.CONF_CHANGE,
        failure=False,
        aggregation_key=f"ConfigurationChange/KubernetesResource/{event.operation.value}",
        subject=FindingSubject(
            event.obj.metadata.name, resource_type, event.obj.metadata.namespace
        ),
    )
    event.finding.add_enrichment([KubernetesDiffBlock(filtered_diffs, old_obj, obj)])


@on_deployment_all_changes
def deployment_babysitter(event: DeploymentEvent, config: BabysitterConfig):
    """Track changes to a deployment and send the changes in slack."""
    do_babysitter(event, config, FindingSubjectType.TYPE_DEPLOYMENT)


@on_pod_all_changes
def pod_babysitter(event: DeploymentEvent, config: BabysitterConfig):
    """Track changes to a pod and send the changes in slack."""
    do_babysitter(event, config, FindingSubjectType.TYPE_POD)
