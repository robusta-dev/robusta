from robusta.api import *


def do_cpu_throttling_analysis(pod: Pod) -> List[BaseBlock]:
    logging.info(f"running cpu throttling analysis on {pod.metadata.name}")
    return [
        MarkdownBlock(
            "*Alert Explanation:* This pod is throttled. It wanted to use the CPU and was blocked due to "
            "it's CPU limit (<https://github.com/robusta-dev/alert-explanations/wiki/CPUThrottlingHigh-"
            "(Prometheus-Alert)|learn more)>"
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
    ]


@on_manual_trigger
def cpu_throttling_analysis(event: ManualTriggerEvent):
    pod = RobustaPod.read("metrics-server-v0.3.6-7b5cdbcbb8-wddbk", "kube-system")
    event.processing_context.create_finding(
        title="Throttling report",
    )
    event.processing_context.finding.add_enrichment(
        blocks=do_cpu_throttling_analysis(pod), annotations={"unfurl": "False"}
    )
