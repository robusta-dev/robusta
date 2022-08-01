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
