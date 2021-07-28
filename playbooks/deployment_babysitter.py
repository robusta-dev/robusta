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
    fields_to_monitor: List[str] = ["status.readyReplicas", "message", "reason", "spec"]


# TODO: filter out all the managed fields crap
def babysitter_should_include_diff(diff_detail: DiffDetail, config: BabysitterConfig):
    return any(
        substring in diff_detail.formatted_path
        for substring in config.fields_to_monitor
    )


def do_babysitter(
    event: K8sBaseEvent, config: BabysitterConfig, resource_type: FindingSubjectType
):
    filtered_diffs = None
    if event.operation == K8sOperationType.UPDATE:
        all_diffs = event.obj.diff(event.old_obj)
        filtered_diffs = list(
            filter(lambda x: babysitter_should_include_diff(x, config), all_diffs)
        )
        if len(filtered_diffs) == 0:
            return

    event.finding = Finding(
        title=f"{resource_type.value} {event.obj.metadata.name} {event.operation.value}d in namespace {event.obj.metadata.namespace}",
        source=FindingSource.SOURCE_KUBERNETES_API_SERVER,
        finding_type=FindingType.TYPE_DEPLOYMENT_UPDATE,
        subject=FindingSubject(
            event.obj.metadata.name, resource_type, event.obj.metadata.namespace
        ),
    )
    event.finding.add_enrichment([DiffsBlock(filtered_diffs)])


@on_deployment_all_changes
def deployment_babysitter(event: DeploymentEvent, config: BabysitterConfig):
    """Track changes to a deployment and send the changes in slack."""
    do_babysitter(event, config, FindingSubjectType.SUBJECT_TYPE_DEPLOYMENT)


@on_pod_all_changes
def pod_babysitter(event: DeploymentEvent, config: BabysitterConfig):
    """Track changes to a pod and send the changes in slack."""
    do_babysitter(event, config, FindingSubjectType.SUBJECT_TYPE_POD)
