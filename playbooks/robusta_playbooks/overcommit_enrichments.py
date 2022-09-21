import logging

from robusta.api import *


@action
def cpu_overcommited_enricher(alert: PrometheusKubernetesAlert, params: PrometheusParams):
    """
    Enrich the finding with a detailed explanation for the cause of the CPU overcommitment.
    Includes recommendations for the identified cause.
    """
    cpu_analyzer = CpuAnalyzer(params.prometheus_url)
    cpu_requests = cpu_analyzer.get_total_cpu_requests(timedelta(minutes=10))
    cpu_total = cpu_analyzer.get_total_cpu_allocatable(timedelta(minutes=10))
    if not (cpu_total and cpu_requests):
        return

    alert.add_enrichment(
        [
            MarkdownBlock(
                f"*Stats:* Currently the total of your pods requests"
                f" is: {round(cpu_requests, 2)}, "
                f"and total of allocatable CPU is: "
                f"{round(cpu_total, 2)}."
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
    Enrich the finding with a detailed explanation for the cause of the Memory overcommitment.
    Includes recommendations for the identified cause.
    """
    mem_analyzer = MemoryAnalyzer(params.prometheus_url)
    mem_requests = mem_analyzer.get_total_mem_requests(timedelta(minutes=10))
    mem_total = mem_analyzer.get_total_mem_allocatable(timedelta(minutes=10))
    if not (mem_requests and mem_total):
        return

    alert.add_enrichment(
        [
            MarkdownBlock(
                f"*Stats:* Currently the total of your pods requests is: "
                f"{pretty_size(mem_requests)}, "
                f"and total of allocatable memory is: "
                f"{pretty_size(mem_total)}."
            ),
        ],
        annotations={SlackAnnotations.UNFURL: False}
    )
    alert.override_finding_attributes(description="Your cluster is currently OK, but if a single node "
                                                  "fails then some pods might not be scheduled. Add more Memory"
                                                  " to your cluster to increase resilience.")
