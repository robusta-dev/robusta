from robusta.api import *


class Params(BaseModel):
    grafana_url: str = None
    grafana_api_key: str
    grafana_dashboard_uid: str


@on_deployment_update
def add_deployment_lines_to_grafana(event: DeploymentEvent, action_params: Params):
    """
    Add annotations to grafana whenever a new application version is deployed so that you can easily see changes in performance.
    """
    new_images = event.obj.get_images()
    old_images = event.old_obj.get_images()
    if new_images == old_images:
        return

    msg = ""
    if new_images.keys() != old_images.keys():
        msg = f"number or names of images changed<br /><br />new<pre>{new_images}</pre>old<pre>{old_images}</pre>"
    else:
        for name in new_images:
            if new_images[name] != old_images[name]:
                msg += f"image name:<pre>{name}</pre>new tag:<pre>{new_images[name]}</pre>old tag<pre>{old_images[name]}</pre><hr class='solid'>"

    grafana = Grafana(action_params.grafana_api_key, action_params.grafana_url)
    grafana.add_line_to_dashboard(
        action_params.grafana_dashboard_uid, msg, tags=[event.obj.metadata.name]
    )


class AnnotationConfig(BaseModel):
    alert_name: str
    dashboard_uid: str
    dashboard_panel: Optional[str]


class AlertLineParams(BaseModel):
    grafana_url: str = None
    grafana_api_key: str
    annotations: List[AnnotationConfig]


# TODO: should we use filter_params and configure multiple instances of add_alert_lines_to_grafana instead of one master instance?
@on_pod_prometheus_alert
def add_alert_lines_to_grafana(
    event: PrometheusKubernetesAlert, params: AlertLineParams
):
    grafana = Grafana(params.grafana_api_key, params.grafana_url)
    for annotation_config in params.annotations:
        if annotation_config.alert_name != event.alert_name:
            continue

        if event.get_description():
            description = f"<pre>{event.get_description()}</pre>"
        else:
            description = ""
        grafana.add_line_to_dashboard(
            annotation_config.dashboard_uid,
            f'<h2>{event.get_title()}</h2><a href="{event.alert.generatorURL}">Open in AlertManager</a>{description}',
            tags=[f"{k}={v}" for k, v in event.alert.labels.items()],
            panel_substring=annotation_config.dashboard_panel,
        )


@on_deployment_update
def report_image_changes(event: DeploymentEvent):
    """
    Report image changed whenever a new application version is deployed so that you can easily see changes.
    """
    new_images = event.obj.get_images()
    old_images = event.old_obj.get_images()
    if new_images == old_images:
        return

    msg = ""
    changed_properties = []
    if new_images.keys() != old_images.keys():
        msg = (
            f"number or names of images changed: new - {new_images} old - {old_images}"
        )
    else:
        for name in new_images:
            if new_images[name] != old_images[name]:
                msg += f"image name: {name} new tag: {new_images[name]} old tag {old_images[name]}"
                changed_properties.append(
                    {
                        "property": "image",
                        "old": f"{name}:{old_images[name]}",
                        "new": f"{name}:{new_images[name]}",
                    }
                )

    event.finding = Finding(
        title=f"{FindingSubjectType.TYPE_DEPLOYMENT.value} {event.obj.metadata.name} updated in namespace {event.obj.metadata.namespace}",
        source=FindingSource.KUBERNETES_API_SERVER,
        aggregation_key="report_image_changes",
        subject=FindingSubject(
            event.obj.metadata.name,
            FindingSubjectType.TYPE_DEPLOYMENT,
            event.obj.metadata.namespace,
        ),
    )
    json_str = json.dumps(
        {
            "deployment": event.obj.metadata.name,
            "deployment_namespace": event.obj.metadata.namespace,
            "message": msg,
            "changed_properties": changed_properties,
        }
    )
    event.finding.add_enrichment([JsonBlock(json_str)])
