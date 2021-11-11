from robusta.api import *


@action
def cpu_throttling_analysis_enricher(event: PodEvent):
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run CPUThrottlingAnalysis on event with no pod: {event}")
        return

    logging.info(f"running cpu throttling analysis on {pod.metadata.name}")
    event.add_enrichment(
        [
            MarkdownBlock(
                "*Alert Explanation:* This pod is throttled. It wanted to use the CPU and was blocked due to "
                "it's CPU limit (<https://github.com/robusta-dev/alert-explanations/wiki/CPUThrottlingHigh-"
                "(Prometheus-Alert)|learn more>)"
            ),
            MarkdownBlock(
                "_Tip: <https://github.com/robusta-dev/alert-explanations/wiki/CPUThrottlingHigh-(Prometheus-"
                "Alert)#low-cpu|This can occur even when CPU usage is far below the limit>._"
            ),
            MarkdownBlock(
                "*Robusta's Recommendation:* Remove this pod's CPU limit entirely. <https://github.com/"
                "robusta-dev/alert-explanations/wiki/CPUThrottlingHigh-(Prometheus-Alert)#no-limits|This is "
                "safe as long as other pods have somewhat-accurate CPU requests>"
            ),
        ],
        annotations={SlackAnnotations.UNFURL: False},
    )
