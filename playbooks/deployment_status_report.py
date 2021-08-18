from robusta.api import *
import requests


class ReportParams(BaseModel):
    grafana_api_key: str
    report_name: str = "Deployment change report"
    on_image_change_only: bool = True
    delays: List[int]
    reports_panel_urls: List[str]

    def __str__(self):
        return (
            f"grafana_api_key: {mask_secret(self.grafana_api_key)}, "
            f"report_name: {self.report_name}, "
            f"on_image_change_only: {self.on_image_change_only}, "
            f"delays: {self.delays}, "
            f"reports_panel_urls: {self.reports_panel_urls} "
        )


def report_rendering_task(event: RecurringTriggerEvent, action_params: ReportParams):
    event.finding = Finding(
        title=action_params.report_name,
    )
    for panel_url in action_params.reports_panel_urls:
        image: requests.models.Response = requests.post(
            GRAFANA_RENDERER_URL,
            data={"apiKey": action_params.grafana_api_key, "panelUrl": panel_url},
        )
        event.finding.add_enrichment([FileBlock("panel.png", image.content)])


# register this function as a scheduled callable
scheduled_callable(report_rendering_task, ReportParams)


@on_deployment_all_changes
def deployment_status_report(event: DeploymentEvent, action_params: ReportParams):
    """Export configured reports, every pre-defined period"""
    if event.operation == K8sOperationType.DELETE:
        return

    new_images = event.obj.get_images()
    old_images = event.old_obj.get_images()
    if action_params.on_image_change_only and new_images == old_images:
        return

    logging.info(
        f"Scheduling rendering report. deployment: {event.obj.metadata.name} delays: {action_params.delays}"
    )
    trigger_params = TriggerParams(
        trigger_name=f"deployment_status_report_{event.obj.metadata.name}_{event.obj.metadata.namespace}",
        scheduling_type=SchedulingType.DELAY_PERIODS,
        delays=action_params.delays,
    )
    scheduling_config = SchedulingConfig(
        replace_existing=True,
        sched_type=SchedulingType.DELAY_PERIODS,
        standalone_task=True,
    )
    deploy_on_scheduler_event(
        report_rendering_task,
        trigger_params,
        event.named_sinks,
        action_params,
        scheduling_config,
    )
