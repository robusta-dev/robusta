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
    grafana.add_line_to_dashboard(action_params.grafana_dashboard_uid, msg, tags=[event.obj.metadata.name])


class ImageChangesParams(BaseModel):
    sinks: List[SinkConfigBase]


@on_deployment_update
def report_image_changes(event: DeploymentEvent, action_params: ImageChangesParams):
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
        msg = f"number or names of images changed: new - {new_images} old - {old_images}"
    else:
        for name in new_images:
            if new_images[name] != old_images[name]:
                msg += f"image name: {name} new tag: {new_images[name]} old tag {old_images[name]}"
                changed_properties.append({
                    "property": "image",
                    "old": f"{name}:{old_images[name]}",
                    "new": f"{name}:{new_images[name]}"
                })

    data = {
        "deployment": event.obj.metadata.name,
        "deployment_namespace": event.obj.metadata.namespace,
        "message": msg,
        "changed_properties": changed_properties
    }
    for sink_config in action_params.sinks:
        SinkFactory.get_sink(sink_config).write(data)

