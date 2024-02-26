import logging
import re
from functools import total_ordering
from typing import Dict, List, Tuple

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


@total_ordering
class Semver:
    """
    This is a class for comparing semantic version strings
    We ignore non numbered versions for the comparison (like alpha, beta) and zero versions
    i.e. v1, 1.0, 1.0.0 and v1.0-alpha are all equal in the comparison
    """

    semver_string: str
    numerical_semver: List[int]

    def __init__(self, semver_str: str):
        self.semver_string = semver_str
        numerical_semver_str = re.sub("[^\d\.]", "", semver_str)
        self.numerical_semver = [int(version_int_str) for version_int_str in numerical_semver_str.split(".")]
        if not self.numerical_semver:
            raise Exception(f"Invalid semver string {semver_str}.")

    @staticmethod
    def fixing_zero_versions(version1: List[int], version2: List[int]) -> Tuple[List[int], List[int]]:
        # semver 1.0.0 is the same version as 1.0 and 1
        len_diff = len(version1) - len(version2)

        if len_diff > 0:
            version2.extend([0] * len_diff)
        elif len_diff < 0:
            version1.extend([0] * (-len_diff))
        return version1, version2

    def __eq__(self, other) -> bool:
        self_semver, other_semver = self.fixing_zero_versions(self.numerical_semver, other.numerical_semver)
        max_len = len(self_semver)
        for index in range(max_len):
            if self_semver[index] != other_semver[index]:
                return False
        return True

    def __lt__(self, other) -> bool:
        self_semver, other_semver = self.fixing_zero_versions(self.numerical_semver, other.numerical_semver)
        max_len = len(self_semver)
        for index in range(max_len):
            if self_semver[index] < other_semver[index]:
                return True
            elif self_semver[index] > other_semver[index]:
                return False
            # on equal continue
        return False


class BuildInfoResults:
    api_versions: List[Semver]
    node_versions: List[Semver]
    raw_metrics: List[Dict[str, str]]

    def __init__(self, query_result: PrometheusQueryResult):
        self.raw_metrics = [result.metric for result in query_result.vector_result]
        self.api_versions = [
            Semver(metric.get("git_version")) for metric in self.raw_metrics if metric.get("node") is None
        ]
        self.node_versions = [
            Semver(metric.get("git_version")) for metric in self.raw_metrics if metric.get("node") is not None
        ]

    def is_results_valid(self) -> bool:
        # there must be atleast two different versions for this alert
        if len(self.raw_metrics) < 2:
            logging.error(f"Invalid prometheus results for version_mismatch_enricher.")
            return False

        # you can have multiple versions of the api server in the metrics at once
        # i.e. at the time of kubernetes upgrade both will show up in the metrics for several minutes
        if len(self.api_versions) == 0:
            logging.error(f"Missing api server results for version_mismatch_enricher.")
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

    max_api_version = max(build_infos.api_versions)
    max_node_version = max(build_infos.node_versions)

    # in the case where a node is of a higher version than the api server
    update_cluster_msg = "and cluster " if max_api_version != max_node_version else " "
    max_version_string = max([max_api_version, max_node_version]).semver_string
    alert.add_enrichment(
        [
            MarkdownBlock(f"Automatic {alert.alert_name} investigation:"),
            MarkdownBlock(f"The kubernetes api server is version {max_api_version}."),
            TableBlock(
                build_infos.results_to_node_table(),
                ["name", "version"],
                table_name="*Node Versions*",
            ),
            MarkdownBlock(
                f"To solve this alert, make sure to update all of your nodes {update_cluster_msg}to version"
                f" {max_version_string}. "
            ),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
    )
