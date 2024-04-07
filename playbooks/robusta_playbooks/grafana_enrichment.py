import json

from robusta.api import (
    Finding,
    FindingSource,
    FindingSubjectType,
    FindingType,
    Grafana,
    GrafanaAnnotationParams,
    JsonBlock,
    KubeObjFindingSubject,
    KubernetesAnyChangeEvent,
    NodeChangeEvent,
    PrometheusKubernetesAlert,
    action,
    extract_images,
)


@action
def add_deployment_lines_to_grafana(event: KubernetesAnyChangeEvent, action_params: GrafanaAnnotationParams):
    """
    Add annotations to Grafana when a Kubernetes resource is updated and the image tags change.

    Supports Deployments, ReplicaSets, DaemonSets, StatefulSets, Jobs, and Pods
    """
    new_images = extract_images(event.obj)
    old_images = extract_images(event.old_obj)
    if new_images == old_images:
        return

    if len(event.obj.metadata.ownerReferences) != 0:
        return  # not handling runtime objects

    msg = ""
    if new_images.keys() != old_images.keys():
        msg = f"number or names of images changed<br /><br />new<pre>{new_images}</pre>old<pre>{old_images}</pre>"
    else:
        for name in new_images:
            if new_images[name] != old_images[name]:
                msg += f"image name:<pre>{name}</pre>new tag:<pre>{new_images[name]}</pre>old tag<pre>{old_images[name]}</pre><hr class='solid'>"

    grafana = Grafana(action_params.grafana_api_key.get_secret_value(), action_params.grafana_url)
    tags = [
        event.obj.metadata.name,
        event.obj.metadata.namespace,
        action_params.cluster_name,
    ]
    if action_params.cluster_zone:
        tags.append(action_params.cluster_zone)
    if action_params.custom_tags:
        tags.extend(action_params.custom_tags)

    grafana.add_line_to_dashboard(
        action_params.grafana_dashboard_uid,
        msg,
        tags=tags,
        panel_substring=action_params.grafana_dashboard_panel,
    )


@action
def add_alert_lines_to_grafana(event: PrometheusKubernetesAlert, params: GrafanaAnnotationParams):
    grafana = Grafana(params.grafana_api_key.get_secret_value(), params.grafana_url)

    if event.get_description():
        description = f"<pre>{event.get_description()}</pre>"
    else:
        description = ""

    grafana.add_line_to_dashboard(
        params.grafana_dashboard_uid,
        f'<h2>{event.get_title()}</h2><a href="{event.alert.generatorURL}">Open in AlertManager</a>{description}',
        tags=[f"{k}={v}" for k, v in event.alert.labels.items()],
        panel_substring=params.grafana_dashboard_panel,
    )


@action
def report_image_changes(event: KubernetesAnyChangeEvent):
    """
    Report image changed whenever a new application version is deployed so that you can easily see changes.
    """
    new_images = extract_images(event.obj)
    old_images = extract_images(event.old_obj)
    if new_images == old_images:
        return

    if len(event.obj.metadata.ownerReferences) != 0:
        return  # not handling runtime objects

    msg = ""
    changed_properties = []
    if new_images.keys() != old_images.keys():
        msg = f"number or names of images changed: new - {new_images} old - {old_images}"
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
    should_get_subject_node_name = isinstance(event, NodeChangeEvent)
    finding = Finding(
        title=f"{FindingSubjectType.TYPE_DEPLOYMENT.value} {event.obj.metadata.name} updated in namespace {event.obj.metadata.namespace}",
        source=FindingSource.KUBERNETES_API_SERVER,
        aggregation_key="ReportImageChanges",
        subject=KubeObjFindingSubject(event.obj, should_add_node_name=should_get_subject_node_name),
        finding_type=FindingType.CONF_CHANGE,
        failure=False,
    )
    json_str = json.dumps(
        {
            "deployment": event.obj.metadata.name,
            "deployment_namespace": event.obj.metadata.namespace,
            "message": msg,
            "changed_properties": changed_properties,
        }
    )
    finding.add_enrichment([JsonBlock(json_str)])
    event.add_finding(finding)
