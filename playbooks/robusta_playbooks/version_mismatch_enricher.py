import logging
import re
from typing import List, Tuple

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


def _semver_max(versions: List[str]) -> str:
    max_semver = max([Semver(version) for version in versions])
    return max_semver.semver_string


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
    # there must be atleast two different versions for this alert
    metrics = [result.metric for result in query_result.vector_result]
    versions = list(set([metric.get("git_version") for metric in metrics]))
    if len(versions) < 2:
        logging.error(f"Invalid prometheus results for version_mismatch_enricher.")
        return

    kubernetes_api_versions = [metric.get("git_version") for metric in metrics if metric.get("node") is None]

    # you can have multiple versions of the api server in the metrics at once
    # i.e. at the time of kubernetes upgrade both will show up in the metrics for several minutes
    if len(kubernetes_api_versions) == 0:
        logging.error(f"Missing api server results for version_mismatch_enricher.")
        return

    kubernetes_api_version = _semver_max(kubernetes_api_versions)
    nodes_by_version = [
        [metric.get("node"), metric.get("git_version")] for metric in metrics if metric.get("node") is not None
    ]

    # in the case where a node is of a higher version than the api server
    api_server_msg = "and cluster " if _semver_max(kubernetes_api_versions) != _semver_max(versions) else " "

    alert.add_enrichment(
        [
            MarkdownBlock(f"Automatic {alert.alert_name} investigation:"),
            MarkdownBlock(f"The kubernetes api server is version {kubernetes_api_version}."),
            TableBlock(
                nodes_by_version,
                ["name", "version"],
                table_name="*Node Versions*",
            ),
            MarkdownBlock(
                f"To solve this alert, make sure to update all of your nodes {api_server_msg}to version {_semver_max(versions)}."
            ),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
    )
