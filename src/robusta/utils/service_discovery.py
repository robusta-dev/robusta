import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

from kubernetes import client
from kubernetes.client import V1ServiceList
from kubernetes.client.models.v1_service import V1Service

from robusta.core.model.env_vars import CLUSTER_DOMAIN


@dataclass
class DiscoveredServiceUrl:
    url: str
    headers: Optional[Dict[str, str]] = None

    def __str__(self) -> str:
        return self.url


def _should_use_proxy() -> bool:
    return not os.getenv("KUBERNETES_SERVICE_HOST")


def _derive_service_scheme(port) -> str:
    port_name = (port.name or "").lower()
    app_protocol = getattr(port, "app_protocol", None) or ""
    app_protocol = app_protocol.lower()

    if "https" in port_name or "https" in app_protocol or port.port == 443:
        return "https"
    return "http"


def _get_kube_proxy_headers() -> Optional[Dict[str, str]]:
    try:
        api_client = client.ApiClient()
        auth_header = api_client.configuration.get_api_key_with_prefix("authorization")
        headers: Dict[str, str] = {}
        if auth_header:
            headers["Authorization"] = auth_header
        if api_client.configuration.default_headers:
            headers.update(api_client.configuration.default_headers)
        return headers or None
    except Exception as e:
        logging.debug(f"Unable to build Kubernetes proxy headers: {e}")
        return None


def _build_proxy_url(name: str, namespace: str, port: int, scheme: str) -> Optional[str]:
    try:
        configuration = client.Configuration.get_default_copy()
    except Exception as e:
        logging.debug(f"Unable to load Kubernetes configuration for proxy url: {e}")
        return None

    host = (configuration.host or "").rstrip("/")
    if not host:
        return None

    path = f"/api/v1/namespaces/{namespace}/services/{scheme}:{name}:{port}/proxy"
    return f"{host}{path}"


def find_service_url(label_selector):
    """
    Get the url of a service with a specific label. When running outside the cluster,
    prefer the Kubernetes API proxy using the current user's credentials.
    """
    # we do it this way because there is a weird issue with hikaru's ServiceList.listServiceForAllNamespaces()
    v1 = client.CoreV1Api()
    svc_list: V1ServiceList = v1.list_service_for_all_namespaces(label_selector=label_selector)
    if not svc_list.items:
        return None
    svc: V1Service = svc_list.items[0]
    name = svc.metadata.name
    namespace = svc.metadata.namespace
    port_obj = svc.spec.ports[0]
    port = port_obj.port
    scheme = _derive_service_scheme(port_obj)

    cluster_local_url = f"{scheme}://{name}.{namespace}.svc.{CLUSTER_DOMAIN}:{port}"
    proxy_url = _build_proxy_url(name, namespace, port, scheme) if _should_use_proxy() else None
    headers = _get_kube_proxy_headers() if proxy_url else None
    final_url = proxy_url or cluster_local_url

    logging.info(
        f"discovered service with label-selector: `{label_selector}` at url: `{final_url}` "
        f"(proxy_used={proxy_url is not None})"
    )
    return DiscoveredServiceUrl(url=final_url, headers=headers)
