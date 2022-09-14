from robusta.api import *


@action
def cpu_overcommited_enricher(alert: PrometheusKubernetesAlert, params: PrometheusParams):
    """
    Enrich the finding with a deep analysis for the cause of the CPU throttling.
    Includes recommendations for the identified cause.
    """
    cpu_analyzer = CpuAnalyzer(params.prometheus_url, None)

    alert.add_external_link(ExternalLink(
        url="https://www.youtube.com/watch?v=Ei8tXaTJi98",
        name="CPU Overcommited"
    ))

    alert.add_enrichment(
        [
            MarkdownBlock(
                f"*Details:* Currently the total of your pods requests"
                f" is: {round(cpu_analyzer.get_total_cpu_requests(), 2)}, "
                f"and total of allocatable CPU is: {round(cpu_analyzer.get_total_cpu_allocatable(), 2)}."
                f" If one of your nodes fails, there will be no enough resources to schedule some of the pods."
            ),
            MarkdownBlock(
                "*Alert Explanation:* This alert doesn’t meant that the Unscheduled Pod has already appeared."
                " It appeared to indicate that it is time to expand the cluster."
                " See the attached video if you need more information."
            ),
        ],
        annotations={SlackAnnotations.UNFURL: False}
    )
    alert.override_finding_attributes(description="The total CPU requests on your cluster is high. \n"
                                                  "In case of a single node failure, some of your pods"
                                                  " might not be scheduled because of "
                                                  "lack of CPU resources")


@action
def memory_overcommited_enricher(alert: PrometheusKubernetesAlert, params: PrometheusParams):
    """
    Enrich the finding with a deep analysis for the cause of the CPU throttling.
    Includes recommendations for the identified cause.
    """
    mem_analyzer = MemoryAnalyzer(params.prometheus_url, None)

    alert.add_external_link(ExternalLink(
        url="https://www.youtube.com/watch?v=Ei8tXaTJi98",
        name="CPU Overcommited"
    ))

    alert.add_enrichment(
        [
            MarkdownBlock(
                f"*Details:* Currently the total of your pods requests is: "
                f"{pretty_size(mem_analyzer.get_total_mem_requests())}, "
                f"and total of allocatable memory is: {pretty_size(mem_analyzer.get_total_mem_allocatable())}. "
                f"If one of your nodes fails, there will be no enough resources to schedule some of the pods."
            ),
            MarkdownBlock(
                "*Alert Explanation:* This alert doesn’t meant that the Unscheduled Pod has already appeared."
                " It appeared to indicate that it is time to expand the cluster."
                " See the attached video if you need more information."
            ),
        ],
        annotations={SlackAnnotations.UNFURL: False}
    )
    alert.override_finding_attributes(description="The total Memory requests on your cluster is high. \n"
                                                  "In case of a single node failure, some of your pods"
                                                  " might not be scheduled because of "
                                                  "lack of Memory resources")
