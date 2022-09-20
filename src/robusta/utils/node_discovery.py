import logging
from typing import Dict, List
from kubernetes.client.api import core_v1_api
from pydantic import BaseModel


class NodeMetadataMetrics(BaseModel):
    name: str


class NodeMetrics(BaseModel):
    timestamp: str
    metadata: Dict[str, str]  # cpu and memory
    usage: Dict[str, str]  # cpu and memory


class NodeDiscovery(BaseModel):
    @staticmethod
    def get_nodess_metrics(node_names: List[str]) -> List[NodeMetrics]:
        metrics = []
        for node_name in node_names:
            try:
                response, status_code, _ = NodeDiscovery.get_node_metrics(node_name)
                if status_code != 200:
                    logging.warning(f"unable to get metrics {status_code}, {response}, headers")
                else:
                    metrics.append(NodeMetrics(**response))
                    logging.info(f"metrics recieved for node {node_name}")
            except Exception as e:
                # known possible exception kubernetes.client.exceptions.ApiException permissions issue
                logging.error(f"Error getting metrics for node {node_name}",
                              exc_info=True)
        return metrics

    @staticmethod
    def get_node_metrics(node_name: str):
        if not node_name:
            return
        metrics_path = f"/apis/metrics.k8s.io/v1beta1/nodes/{node_name}"
        v1 = core_v1_api.CoreV1Api()

        local_var_params = locals()

        all_params = [
            'allow_watch_bookmarks',
            '_continue',
            'field_selector',
            'label_selector',
            'limit',
            'pretty',
            'resource_version',
            'timeout_seconds',
            'watch'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout'
            ]
        )

        collection_formats = {}

        path_params = {}

        query_params = []
        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = v1.api_client.select_header_accept(
            ['application/json', 'application/yaml', 'application/vnd.kubernetes.protobuf'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerToken']  # noqa: E501

        return v1.api_client.call_api(
            metrics_path, 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='object', #'PodMetrics',  # noqa: E501
            auth_settings=auth_settings,
            _preload_content=True,
            collection_formats=collection_formats)