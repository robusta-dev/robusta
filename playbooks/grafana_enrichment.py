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


@on_pod_create
def test_pod_orm(event : PodEvent):
    logging.info('running test_pod_orm')
    pod = event.obj

    images = [container.image for container in event.obj.spec.containers]
    logging.info(f'pod images are {images}')

    exec_resp = pod.exec("ls -l /")
    logging.info(f'pod ls / command: {exec_resp}')

    logging.info(f'deleting pod {pod.metadata.name}')
    RobustaPod.deleteNamespacedPod(pod.metadata.name, pod.metadata.namespace)
    logging.info(f'pod deleted')
