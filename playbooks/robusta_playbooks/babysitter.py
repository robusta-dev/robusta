# TODO: we should attach a full yaml diff when the deployment spec (not status) changes
# options for generating a human-readable diff:
# * python_diff = "\n".join([x for x in unified_diff(before.splitlines(), after.splitlines(), fromfile="old", tofile="new")])
# * https://github.com/google/diff-match-patch/wiki/Language:-Python (see output format here: https://neil.fraser.name/software/diff_match_patch/demos/diff.html)
# * https://github.com/wagoodman/diff2HtmlCompare
# * https://github.com/GerHobbelt/google-diff-match-patch
import logging
from typing import List

from robusta.api import (
    ActionParams,
    Finding,
    FindingAggregationKey,
    FindingSource,
    FindingType,
    K8sOperationType,
    KubeObjFindingSubject,
    KubernetesAnyChangeEvent,
    KubernetesDiffBlock,
    NodeChangeEvent,
    action,
)
from robusta.core.reporting.base import EnrichmentType


class BabysitterConfig(ActionParams):
    """
    :var ignored_namespaces: List of namespaces to ignore
    """

    ignored_namespaces: List[str] = []


@action
def resource_babysitter(event: KubernetesAnyChangeEvent, config: BabysitterConfig):
    """
    Track changes to a k8s resource.
    Send the diff as a finding
    """
    if not event.obj.metadata:  # shouldn't happen, just to be on the safe side
        logging.warning(f"resource_babysitter skipping resource with no meta - {event.obj}")
        return

    if not isinstance(getattr(event, "filtered_diffs"), list):
        logging.warning(f"resource_babysitter running for an unsupported event type {event.__class__.__name__}")
        return

    if event.obj.metadata.namespace in config.ignored_namespaces:
        return

    if (
        event.operation == K8sOperationType.DELETE
    ):  # On delete, the current obj should be None, and not the actual object, as received
        old_obj = event.obj_filtered
        obj = None
    else:
        old_obj = event.old_obj_filtered
        obj = event.obj_filtered

    logging.warning(f"1 {event.operation}")
    logging.warning(f"1 {event.old_obj_filtered}")
    logging.warning(f"1 {event.old_obj}")
    logging.warning(f"2 {event.obj_filtered}")
    logging.warning(f"3 {event.filtered_diffs}")

    should_get_subject_node_name = isinstance(event, NodeChangeEvent)
    # we take it from the original event, in case metadata is omitted
    meta = event.obj.metadata
    diff_block = KubernetesDiffBlock(
        event.filtered_diffs, old_obj, obj, meta.name, kind=event.obj.kind, namespace=meta.namespace
    )
    finding = Finding(
        title=f"{diff_block.resource_name} {event.operation.value}d",
        description=diff_block.get_description(),
        source=FindingSource.KUBERNETES_API_SERVER,
        finding_type=FindingType.CONF_CHANGE,
        failure=False,
        aggregation_key=FindingAggregationKey.CONFIGURATION_CHANGE_KUBERNETES_RESOURCE_CHANGE.value,
        subject=KubeObjFindingSubject(event.obj, should_add_node_name=should_get_subject_node_name),
    )
    finding.add_enrichment(
        [diff_block],
        annotations={"operation": event.operation},
        enrichment_type=EnrichmentType.diff,
        title="Kubernetes Manifest Change",
    )
    event.add_finding(finding)
