from robusta.api import (
    Grafana,
    GrafanaAnnotationParams,
    KubernetesAnyChangeEvent,
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
