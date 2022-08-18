import logging
from typing import List, Dict
from kubernetes.client.api import core_v1_api
from hikaru.model import Pod, PodList
from pydantic import BaseModel

from ..core.model.env_vars import RELEASE_NAME


class ContainersMetrics(BaseModel):
    name: str
    usage: Dict[str, str]  # cpu and memory


class MetadataMetrics(BaseModel):
    name: str
    namespace: str


class PodMetrics(BaseModel):
    timestamp: str
    metadata: MetadataMetrics
    containers: List[ContainersMetrics]


class PodDiscovery(BaseModel):
    @staticmethod
    def get_metrics():
        try:
            return PodDiscovery.get_pods()
        except Exception as e:
            logging.error("PodDiscovery error",exc_info=True)

    @staticmethod
    def get_pods():
        metrics = []
        pods = []
        forwarder = PodDiscovery.find_forwarder_pod()
        if forwarder and forwarder.items:
            pods.extend(forwarder.items)
        runner_pod = PodDiscovery.find_runner_pod()
        if runner_pod and runner_pod.items:
            pods.extend(runner_pod.items)
        prometheus = PodDiscovery.find_prometheus_pods()
        if prometheus and prometheus.items:
            pods.extend(prometheus.items)
        for pod in pods:
            pod_metrics, status_code, headers = PodDiscovery.get_pod_metrics(pod)
            if status_code != 200:
                logging.warning(f"unable to get metrics {status_code}, headers")
            else:
                metrics.append(PodMetrics(**pod_metrics))
        return metrics

    @staticmethod
    def get_pod_metrics(pod: Pod):
        if not pod:
            return
        path = f"/apis/metrics.k8s.io/v1beta1/namespaces/{pod.metadata.namespace}/pods/{pod.metadata.name}"
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
        if 'allow_watch_bookmarks' in local_var_params and local_var_params[
            'allow_watch_bookmarks'] is not None:  # noqa: E501
            query_params.append(('allowWatchBookmarks', local_var_params['allow_watch_bookmarks']))  # noqa: E501
        if '_continue' in local_var_params and local_var_params['_continue'] is not None:  # noqa: E501
            query_params.append(('continue', local_var_params['_continue']))  # noqa: E501
        if 'field_selector' in local_var_params and local_var_params['field_selector'] is not None:  # noqa: E501
            query_params.append(('fieldSelector', local_var_params['field_selector']))  # noqa: E501
        if 'label_selector' in local_var_params and local_var_params['label_selector'] is not None:  # noqa: E501
            query_params.append(('labelSelector', local_var_params['label_selector']))  # noqa: E501
        if 'limit' in local_var_params and local_var_params['limit'] is not None:  # noqa: E501
            query_params.append(('limit', local_var_params['limit']))  # noqa: E501
        if 'pretty' in local_var_params and local_var_params['pretty'] is not None:  # noqa: E501
            query_params.append(('pretty', local_var_params['pretty']))  # noqa: E501
        if 'resource_version' in local_var_params and local_var_params['resource_version'] is not None:  # noqa: E501
            query_params.append(('resourceVersion', local_var_params['resource_version']))  # noqa: E501
        if 'timeout_seconds' in local_var_params and local_var_params['timeout_seconds'] is not None:  # noqa: E501
            query_params.append(('timeoutSeconds', local_var_params['timeout_seconds']))  # noqa: E501
        if 'watch' in local_var_params and local_var_params['watch'] is not None:  # noqa: E501
            query_params.append(('watch', local_var_params['watch']))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = v1.api_client.select_header_accept(
            ['application/json', 'application/yaml', 'application/vnd.kubernetes.protobuf',
             'application/json;stream=watch', 'application/vnd.kubernetes.protobuf;stream=watch'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerToken']  # noqa: E501

        return v1.api_client.call_api(
            path, 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='object', #'PodMetrics',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats)

    @staticmethod
    def find_relevant_pods():
        selectors = [f"app={RELEASE_NAME}-runner",f"app={RELEASE_NAME}-forwarder",
                     "app=kube-prometheus-stack-prometheus",
                     "app.kubernetes.io/name=prometheus",]
        return PodDiscovery.find_pod_with_selectors(selectors)

    @staticmethod
    def find_forwarder_pod():
        selectors = [f"app={RELEASE_NAME}-forwarder"]
        return PodDiscovery.find_pod_with_selectors(selectors)

    @staticmethod
    def find_runner_pod():
        selectors = [f"app={RELEASE_NAME}-runner"]
        return PodDiscovery.find_pod_with_selectors(selectors)

    @staticmethod
    def find_prometheus_pods():
        selectors=[
            "app=kube-prometheus-stack-prometheus",
            "app.kubernetes.io/name=prometheus",
        ]
        return PodDiscovery.find_pod_with_selectors(selectors)

    @staticmethod
    def find_pod_with_selectors(selectors: List[str]) -> PodList:
        labels_selector = ",".join(selectors)
        results: PodList = Pod.listPodForAllNamespaces(
            label_selector=labels_selector
        ).obj
        for pod in results.items:
            logging.warning(f"podname: {pod.metadata.name}")
        return results