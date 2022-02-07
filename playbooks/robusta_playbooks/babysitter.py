# TODO: we should attach a full yaml diff when the deployment spec (not status) changes
# options for generating a human-readable diff:
# * python_diff = "\n".join([x for x in unified_diff(before.splitlines(), after.splitlines(), fromfile="old", tofile="new")])
# * https://github.com/google/diff-match-patch/wiki/Language:-Python (see output format here: https://neil.fraser.name/software/diff_match_patch/demos/diff.html)
# * https://github.com/wagoodman/diff2HtmlCompare
# * https://github.com/GerHobbelt/google-diff-match-patch
from typing import Tuple
from hikaru.meta import DiffDetail, DiffType

from robusta.api import *


class BabysitterConfig(ActionParams):
    """
    :var fields_to_monitor: List of yaml attributes to monitor. Any field that contains one of these strings will match.
    :var omitted_fields: List of yaml attributes changes to ignore.
    """

    fields_to_monitor: List[str] = ["spec"]
    omitted_fields: List[str] = [
        "status",
        "metadata.generation",
        "metadata.resourceVersion",
        "metadata.managedFields",
        "spec.replicas",
    ]


@action
def resource_babysitter(event: KubernetesAnyChangeEvent, config: BabysitterConfig):
    """
    Track changes to a k8s resource.
    Send the diff as a finding
    """
    filtered_diffs = []
    obj = duplicate_without_fields(event.obj, config.omitted_fields)
    old_obj = duplicate_without_fields(event.old_obj, config.omitted_fields)
    if event.operation == K8sOperationType.UPDATE:
        all_diffs = obj.diff(old_obj)
        filtered_diffs = list(
            filter(lambda x: is_matching_diff(x, config.fields_to_monitor), all_diffs)
        )
        if len(filtered_diffs) == 0:
            return

    if (
        event.operation == K8sOperationType.DELETE
    ):  # On delete, the current obj should be None, and not the actual object, as received
        obj = None
        old_obj = obj

    diff_block = KubernetesDiffBlock(filtered_diffs, old_obj, obj)
    finding = Finding(
        title=f"{diff_block.resource_name} {event.operation.value}d",
        description=f"Updates to significant fields: {diff_block.num_additions} additions, {diff_block.num_deletions} deletions, {diff_block.num_modifications} changes.",
        source=FindingSource.KUBERNETES_API_SERVER,
        finding_type=FindingType.CONF_CHANGE,
        failure=False,
        aggregation_key=f"ConfigurationChange/KubernetesResource/{event.operation.value}",
        subject=FindingSubject(
            event.obj.metadata.name,
            FindingSubjectType.from_kind(event.obj.kind),
            event.obj.metadata.namespace,
        ),
    )
    finding.add_enrichment([KubernetesDiffBlock(filtered_diffs, old_obj, obj)])
    event.add_finding(finding)
