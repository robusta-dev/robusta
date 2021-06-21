# TODO: we should attach a full yaml diff when the deployment spec (not status) changes
# options for generating a human-readable diff:
# * python_diff = "\n".join([x for x in unified_diff(before.splitlines(), after.splitlines(), fromfile="old", tofile="new")])
# * https://github.com/google/diff-match-patch/wiki/Language:-Python (see output format here: https://neil.fraser.name/software/diff_match_patch/demos/diff.html)
# * https://github.com/wagoodman/diff2HtmlCompare
# * https://github.com/GerHobbelt/google-diff-match-patch
from typing import Tuple
from hikaru.meta import DiffDetail, DiffType
from robusta.api import *


class DeploymentBabysitterConfig(BaseModel):
    slack_channel: str = ""
    fields_to_monitor: Tuple[str] = (
        "status.readyReplicas",
        "message",
        "reason",
        "spec"
    )
    sinks: List[SinkConfigBase] = None


# TODO: filter out all the managed fields crap
def babysitter_should_include_diff(diff_detail: DiffDetail, config: DeploymentBabysitterConfig):
    return any(substring in diff_detail.formatted_path for substring in config.fields_to_monitor)


def babysitter_get_blocks(diffs: List[DiffDetail]):
    num_additions = len([d for d in diffs if d.diff_type == DiffType.ADDED])
    num_subtractions = len([d for d in diffs if d.diff_type == DiffType.REMOVED])
    num_modifications = len(diffs) - num_additions - num_subtractions
    blocks = [
        MarkdownBlock(f"{num_additions} fields added. {num_subtractions} fields removed. {num_modifications} fields changed")
    ]
    for d in diffs:
        blocks.extend([DividerBlock(),
                       MarkdownBlock(f"*{d.formatted_path}*: {d.other_value} :arrow_right: {d.value}")])
    return blocks


@on_deployment_all_changes
def deployment_babysitter(event: DeploymentEvent, config: DeploymentBabysitterConfig):
    """Track changes to a deployment and send the changes in slack."""
    filtered_diffs = None
    if event.operation == K8sOperationType.UPDATE:
        all_diffs = event.obj.diff(event.old_obj)
        filtered_diffs = list(filter(lambda x: babysitter_should_include_diff(x, config), all_diffs))
        if len(filtered_diffs) == 0:
            return
        event.report_attachment_blocks.extend(babysitter_get_blocks(filtered_diffs))

    event.report_title = f"Deployment {event.obj.metadata.name} {event.operation.value}d in namespace {event.obj.metadata.namespace}"
    if config.slack_channel:
        event.slack_channel = config.slack_channel
        send_to_slack(event)

    if config.sinks:
        data = {
            "deployment": event.obj.metadata.name,
            "deployment_namespace": event.obj.metadata.namespace,
            "message": "Deployment properties change",
            "changed_properties": [{
                "property": ".".join(diff.path),
                "old": diff.other_value,
                "new": diff.value
            } for diff in filtered_diffs]
        }
        for sink_config in config.sinks:
            SinkFactory.get_sink(sink_config).write(data)


