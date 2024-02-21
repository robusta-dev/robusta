import logging

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

    kubernetes_api_version = max(kubernetes_api_versions)
    nodes_by_version = [
        [metric.get("node"), metric.get("git_version")] for metric in metrics if metric.get("node") is not None
    ]

    # in the case where a node is of a higher version than the api server
    api_server_msg = "and cluster " if max(kubernetes_api_versions) != max(versions) else " "

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
                f"To solve this alert, make sure to update all of your nodes {api_server_msg}to version {max(versions)}."
            ),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
    )
