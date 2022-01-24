from robusta.api import *


@action
def cpu_throttling_analysis_enricher(event: PodEvent):
    """
    Enrich the finding with a deep analysis for the cause of the CPU throttling.

    Includes recommendations for the identified cause.
    """
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run CPUThrottlingAnalysis on event with no pod: {event}")
        return

    if pod.metadata.name.startswith("metrics-server-") and pod.has_toleration(
        "components.gke.io/gke-managed-components"
    ):
        logging.info(
            "ignoring cpu throttling for GKE because there is nothing you can do about it"
        )
        event.stop_processing = True

    elif pod.metadata.name.startswith("metrics-server-") and pod.has_cpu_limit():
        event.add_enrichment(
            [
                MarkdownBlock(
                    "*Alert Explanation:* This alert is likely due to a known issue with metrics-server. "
                    "<https://github.com/kubernetes/autoscaler/issues/4141|The default metrics-server deployment has cpu "
                    "limits which are too low.>"
                ),
                MarkdownBlock(
                    "*Robusta's Recommendation:* Increase the CPU limit for the metrics-server deployment. Note that "
                    "metrics-server does *not* respect normal cpu limits. For instructions on fixing this issue, see the "
                    "<https://github.com/robusta-dev/alert-explanations/wiki/CPUThrottlingHigh-on-metrics-server-(Prometheus-alert)|Robusta wiki>."
                ),
            ],
            annotations={SlackAnnotations.UNFURL: False},
        )

    elif pod.has_cpu_limit():
        # TODO: ideally we would check if there is a limit on the specific container which is triggering the alert
        event.add_enrichment(
            [
                MarkdownBlock(
                    "*Alert Explanation:* This pod is throttled. It wanted to use the CPU and was blocked due to "
                    "it's CPU limit. This can occur even when CPU usage is far below the limit."
                    "(<https://github.com/robusta-dev/alert-explanations/wiki/CPUThrottlingHigh-"
                    "(Prometheus-Alert)|Learn more.>)"
                ),
                MarkdownBlock(
                    "*Robusta's Recommendation:* Remove this pod's CPU limit entirely. <https://github.com/robusta-dev/"
                    "alert-explanations/wiki/CPUThrottlingHigh-(Prometheus-Alert)#:~:text=relatively%20accurate%20one-,"
                    "Explanation,-As%20long%20as|Despite common misconceptions, using CPU limits is *not* a best "
                    "practice.>"
                ),
            ],
            annotations={SlackAnnotations.UNFURL: False},
        )
    else:
        event.add_enrichment(
            [
                MarkdownBlock(
                    "*Alert Explanation:* This pod is cpu throttled even though it doesn't have CPU limits and is free "
                    "to take advantage of extra cpu on the node. This strongly implies that you have too few resources "
                    "on your cluster or have defined your other CPU requests incorrectly, leading Kubernetes to "
                    "schedule too many pods on this node."
                )
            ],
            annotations={SlackAnnotations.UNFURL: False},
        )
