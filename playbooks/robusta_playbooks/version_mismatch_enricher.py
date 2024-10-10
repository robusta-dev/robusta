import logging
from typing import Dict, List

from prometrix import PrometheusQueryResult
from robusta.api import (
    MarkdownBlock,
    PrometheusKubernetesAlert,
    PrometheusParams,
    SlackAnnotations,
    TableBlock,
    action,
    run_prometheus_query,
)


class VersionMismatchParams(PrometheusParams):
    """
    :var version_mismatch_query: The query to get all the build versions.
    """

    # made as parameter since job label doesn't always exist
    version_mismatch_query: str = 'count by (git_version, node) (label_replace(kubernetes_build_info{job!~"kube-dns|coredns"}, "git_version", "$1", "git_version", "(v[0-9]*.[0-9]*).*"))'


class BuildInfoResults:
    api_versions: List[str]
    raw_metrics: List[Dict[str, str]]

    def __init__(self, query_result: PrometheusQueryResult):
        self.raw_metrics = [result["metric"] for result in query_result.vector_result]
        self.api_versions = list(
            set([metric.get("git_version") for metric in self.raw_metrics if metric.get("node") is None])
        )

    def is_results_valid(self) -> bool:
        # there must be atleast two different versions for this alert
        if len(self.raw_metrics) < 2:
            logging.error(f"Invalid prometheus results for version_mismatch_enricher.")
            return False

        # some prometheus's remove specific labels due to space constraints
        if len([metric for metric in self.raw_metrics if metric.get("node") is not None]) == 0:
            logging.error(f"Prometheus is missing the 'node' label, unable to detect node versions.")
            return False

        return True

    def results_to_node_table(self) -> List[List[str]]:
        return [
            [metric.get("node"), metric.get("git_version")]
            for metric in self.raw_metrics
            if metric.get("node") is not None
        ]


@action
def version_mismatch_enricher(alert: PrometheusKubernetesAlert, params: VersionMismatchParams):
    """
    Enriches the finding with a prometheus query

    for example prometheus queries see here:
    https://prometheus.io/docs/prometheus/latest/querying/examples/
    """

    query_result = run_prometheus_query(prometheus_params=params, query=params.version_mismatch_query)
    if query_result.result_type == "error" or query_result.vector_result is None:
        logging.error(f"version_mismatch_enricher failed to get prometheus results.")
        return

    build_infos = BuildInfoResults(query_result)
    if not build_infos.is_results_valid():
        logging.error(f"Invalid prometheus results for version_mismatch_enricher.")
        return

    if len(build_infos.api_versions) == 0:
        api_version_string = f"version is unknown"
    elif len(build_infos.api_versions) > 1:
        api_version_string = f"has reported versions {', '.join(build_infos.api_versions)}"
    else:  # one build version
        api_version_string = f"is version {build_infos.api_versions[0]}"

    # in the case where a node is of a higher version than the api server
    alert.add_enrichment(
        [
            MarkdownBlock(f"The kubernetes api server {api_version_string}."),
            TableBlock(
                build_infos.results_to_node_table(),
                ["name", "version"],
                table_name="*Node Versions*",
            ),
            MarkdownBlock(
                f"To solve this alert, make sure to update all of your nodes and/or cluster to the latest version above."
            ),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
    )
