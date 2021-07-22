from robusta.api import *


@on_report_callback
def high_cpu_delete_confirmation_handler(event: ReportCallbackEvent):
    logging.info(f"high_cpu_delete_confirmation_handler {event.source_context}")


@on_report_callback
def high_cpu_profile_confirmation_handler(event: ReportCallbackEvent):
    logging.info(f"high_cpu_profile_confirmation_handler {event.source_context}")


### Can we remove this??
@on_pod_prometheus_alert(alert_name="HighCPUAlert", status="firing")
def slack_confirmation_on_cpu(event: PrometheusKubernetesAlert, config: SlackParams):
    logging.info(
        f"running slack_confirmation_on_cpu alert - alert: {event.alert} pod: {event.pod}"
    )

    choices = {
        "delete pod": high_cpu_delete_confirmation_handler,
        "profile pod": high_cpu_profile_confirmation_handler,
    }
    context = {
        "pod_name": event.pod.metadata.name,
        "namespace": event.pod.metadata.namespace,
    }

    event.report_title = f"Pod {event.pod.metadata.name} has high cpu"
    event.report_blocks.extend([CallbackBlock(choices, context)])

    send_to_slack(event, config.slack_channel)


@on_pod_create
def test_pod_orm(event: PodEvent):
    logging.info("running test_pod_orm")
    pod = event.obj

    images = [container.image for container in event.obj.spec.containers]
    logging.info(f"pod images are {images}")

    exec_resp = pod.exec("ls -l /")
    logging.info(f"pod ls / command: {exec_resp}")

    logging.info(f"deleting pod {pod.metadata.name}")
    RobustaPod.deleteNamespacedPod(pod.metadata.name, pod.metadata.namespace)
    logging.info(f"pod deleted")
