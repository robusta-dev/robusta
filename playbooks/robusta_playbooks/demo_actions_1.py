from robusta.api import *
from kubernetes import client


class KindYamlParams(ActionParams):
    """
    :var kind: k8s requested kind. One of: deployments/replicasets/daemonsets/statefulsets
    """
    kind: str


@action
def get_kind_yamls(event: ExecutionBaseEvent, params: KindYamlParams):
    k8s_client = client.ApiClient()

    response = k8s_client.call_api(
        resource_path=f"/apis/apps/v1/{params.kind}",
        method="GET",  auth_settings=['BearerToken'], _preload_content=False, _return_http_data_only=True
    )
    event.add_finding(Finding(
        title=f"Cluster {params.kind} manifests report",
        aggregation_key="Manifest report",
    ))
    event.add_enrichment([FileBlock(f"{params.kind}.yaml", yaml.dump(json.loads(response.data)).encode())])


class PodStatusParams(ActionParams):
    """
    :var status: query pods by this status
    """
    status: str


@action
def list_pods_by_status(event: ExecutionBaseEvent, params: PodStatusParams):
    pods: PodList = Pod.listPodForAllNamespaces(field_selector=f"status.phase={params.status}").obj
    event.add_finding(Finding(
        title=f"Pod list for status {params.status}",
        aggregation_key="Pod status report",
    ))
    if pods.items:
        event.add_enrichment([
            TableBlock(
                table_name="pods list",
                headers=["name", "namespace"],
                rows=[[pod.metadata.name, pod.metadata.namespace] for pod in pods.items]
            )
        ])
    else:
        event.add_enrichment([MarkdownBlock(f"No pods with status {params.status}")])

