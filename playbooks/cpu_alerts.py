from robusta.api import *


class HighCpuConfig(BaseModel):
    slack_channel: str


@on_report_callback
def high_cpu_delete_confirmation_handler(event: ReportCallbackEvent):
    logging.info(f'high_cpu_delete_confirmation_handler {event.source_context}')


@on_report_callback
def high_cpu_profile_confirmation_handler(event: ReportCallbackEvent):
    logging.info(f'high_cpu_profile_confirmation_handler {event.source_context}')


@on_pod_prometheus_alert(alert_name="HighCPUAlert", status="firing")
def slack_confirmation_on_cpu(event: PrometheusKubernetesAlert, config: HighCpuConfig):
    logging.info(f'running slack_confirmation_on_cpu alert - alert: {event.alert} pod: {event.pod}')

    choices = {
        'delete pod': high_cpu_delete_confirmation_handler,
        'profile pod': high_cpu_profile_confirmation_handler
    }
    context = {
        'pod_name': event.pod.metadata.name,
        'namespace': event.pod.metadata.namespace
    }

    event.report_title = f"Pod {event.pod.metadata.name} has high cpu"
    event.slack_channel = config.slack_channel
    event.report_blocks.extend([
        CallbackBlock(choices, context)
    ])

    send_to_slack(event)
