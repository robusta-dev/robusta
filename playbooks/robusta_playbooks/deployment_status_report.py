import logging
from typing import List

import requests
from pydantic import SecretStr

from robusta.api import (
    GRAFANA_RENDERER_URL,
    ActionParams,
    DeploymentChangeEvent,
    DynamicDelayRepeat,
    ExecutionBaseEvent,
    FileBlock,
    Finding,
    FindingType,
    K8sOperationType,
    MarkdownBlock,
    action,
    is_matching_diff,
)


class ReportParams(ActionParams):
    """
    :var grafana_api_key: Grafana API key.
    :var report_name: The name of the report.
    :var fields_to_monitor: List of yaml attributes to monitor. Any field that contains one of these strings will match.
    :var delays: List of seconds intervals in which to generate this report.
            Specifying [60, 60] will generate this report twice, after 60 seconds and 120 seconds after the change.
    :var reports_panel_urls: List of panel urls included in this report.
         it's highly recommended to put relative time arguments, rather then absolute. i.e. from=now-1h&to=now

    :example reports_panel_urls: ["http://MY_GRAFANA/d-solo/SOME_OTHER_DASHBOARD/.../?orgId=1&from=now-1h&to=now&panelId=3"]
    """

    grafana_api_key: SecretStr
    report_name: str = "Deployment change report"
    fields_to_monitor: List[str] = ["image"]
    delays: List[int]
    reports_panel_urls: List[str]


@action
def report_rendering_task(event: ExecutionBaseEvent, action_params: ReportParams):
    """
    Rendering from a grafana dashboard.
    Make sure to set 'grafanaRenderer.enableContainer' to 'true' in the values yaml to use this action.
    """
    finding = Finding(
        title=action_params.report_name,
        aggregation_key="ReportRenderingTask",
        finding_type=FindingType.REPORT,
        failure=False,
    )
    try:
        for panel_url in action_params.reports_panel_urls:
            image: requests.models.Response = requests.post(
                GRAFANA_RENDERER_URL,
                data={
                    "apiKey": action_params.grafana_api_key.get_secret_value(),
                    "panelUrl": panel_url,
                },
            )
            finding.add_enrichment([FileBlock("panel.png", image.content)])
    except requests.exceptions.ConnectionError:
        finding.add_enrichment(
            [
                MarkdownBlock(
                    "Connection to grafana-renderer container was refused. "
                    "Make sure to set 'grafanaRenderer:enableContainer' to 'true' in the values yaml"
                )
            ]
        )

    event.add_finding(finding)


def has_matching_diff(event: DeploymentChangeEvent, fields_to_monitor: List[str]) -> bool:
    all_diffs = event.obj.diff(event.old_obj)
    for diff in all_diffs:
        if is_matching_diff(diff, fields_to_monitor):
            return True
    return False


@action
def deployment_status_report(event: DeploymentChangeEvent, action_params: ReportParams):
    """
    Collect predefined grafana panels screenshots, after a deployment change.
    The report will be generated in intervals, as configured in the 'delays' parameter.
    When the report is ready, it will be sent to the configured sinks.

    Make sure to set 'grafanaRenderer.enableContainer' to 'true' in the values yaml to use this action.
    """
    if event.operation == K8sOperationType.DELETE:
        return

    if event.operation == K8sOperationType.UPDATE:
        if not has_matching_diff(event, action_params.fields_to_monitor):
            return

    logging.info(f"Scheduling rendering report. deployment: {event.obj.metadata.name} delays: {action_params.delays}")
    event.get_scheduler().schedule_action(
        action_func=report_rendering_task,
        task_id=f"deployment_status_report_{event.obj.metadata.name}_{event.obj.metadata.namespace}",
        scheduling_params=DynamicDelayRepeat(delay_periods=action_params.delays),
        named_sinks=event.named_sinks,
        action_params=action_params,
        replace_existing=True,
        standalone_task=True,
    )
