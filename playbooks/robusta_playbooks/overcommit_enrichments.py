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
                f"*Stats:* Currently the total of your pods requests"
                f" is: {round(cpu_analyzer.get_total_cpu_requests(), 2)}, "
                f"and total of allocatable CPU is: {round(cpu_analyzer.get_total_cpu_allocatable(), 2)}."
            ),
        ],
        annotations={SlackAnnotations.UNFURL: False}
    )
    alert.override_finding_attributes(description="Your cluster is currently OK, but if a single node "
                                                  "fails then some pods might not be scheduled."
                                                  " Add more CPU to your cluster to increase resilience.")


@action
def memory_overcommited_enricher(alert: PrometheusKubernetesAlert, params: PrometheusParams):
    """
    Enrich the finding with a deep analysis for the cause of the CPU throttling.
    Includes recommendations for the identified cause.
    """
    mem_analyzer = MemoryAnalyzer(params.prometheus_url, None)

    alert.add_external_link(ExternalLink(
        url="https://www.youtube.com/watch?v=Ei8tXaTJi98",
        name="Memory Overcommited"
    ))

    alert.add_enrichment(
        [
            MarkdownBlock(
                f"*Stats:* Currently the total of your pods requests is: "
                f"{pretty_size(mem_analyzer.get_total_mem_requests())}, "
                f"and total of allocatable memory is: {pretty_size(mem_analyzer.get_total_mem_allocatable())}."
            ),
        ],
        annotations={SlackAnnotations.UNFURL: False}
    )
    alert.override_finding_attributes(description="Your cluster is currently OK, but if a single node "
                                                  "fails then some pods might not be scheduled. Add more Memory"
                                                  " to your cluster to increase resilience.")
