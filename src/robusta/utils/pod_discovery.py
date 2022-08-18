import logging
import time
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
    def get_robusta_metrics() -> List[PodMetrics]:
        try:
            time.sleep(25)
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
            return PodDiscovery.get_pods_metrics(pods)
        except Exception as e:
            logging.error("Error retrieving pod metrics", exc_info=True)

    @staticmethod
    def get_pods_metrics(pods: List[Pod]) -> List[PodMetrics]:
        metrics = []
        for pod in pods:
            try:
                response, status_code, _ = PodDiscovery.get_pod_metrics(pod)
                if status_code != 200:
                    logging.warning(f"unable to get metrics {status_code}, {response}, headers")
                else:
                    metrics.append(PodMetrics(**response))
                    logging.info(f"metrics recieved for pod {pod.metadata.name} in namespace {pod.metadata.namespace}")
            except Exception as e:
                # known possible exception kubernetes.client.exceptions.ApiException permissions issue
                logging.error(f"Error getting metrics for pod {pod.metadata.name} in namespace {pod.metadata.namespace}",
                              exc_info=True)
        return metrics

    @staticmethod
    def get_pod_metrics(pod: Pod):
        if not pod:
            return
        metrics_path = f"/apis/metrics.k8s.io/v1beta1/namespaces/{pod.metadata.namespace}/pods/{pod.metadata.name}"
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
        return results