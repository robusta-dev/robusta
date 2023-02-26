import logging
import re
from enum import Enum, auto
from typing import Dict, Optional

from hikaru.model import NodeList


class ClusterProviderType(Enum):
    GKE = "GKE"
    AKS = "AKS"
    EKS = "EKS"
    Kind = "Kind"
    Minikube = "Minikube"
    RancherDesktop = "RancherDesktop"
    Kapsule = "Kapsule"
    Kops = "Kops"
    DigitalOcean = "DigitalOcean"
    Unknown = auto()

# the value is a regex match of the hostname
HOSTNAME_MATCH: Dict[ClusterProviderType, str] = {
    ClusterProviderType.Kind: ".*kind.*",
    ClusterProviderType.RancherDesktop: ".*rancher-desktop.*"
}

# the value is a node label unique to the provider
NODE_LABELS: Dict[ClusterProviderType, str] = {
    ClusterProviderType.Minikube: "minikube.k8s.io/name",
    ClusterProviderType.DigitalOcean: "doks.digitalocean.com/version",
    ClusterProviderType.Kops: "kops.k8s.io/instancegroup",
    ClusterProviderType.Kapsule: "k8s.scaleway.com/kapsule"
}

__CLUSTER_PROVIDER__ = None


def _get_node_label(node, label) -> Optional[str]:
    try:
        return node.metadata.labels[label]
    except KeyError:
        pass
    return None


def _detect_provider_from_hostname(nodes) -> Optional[ClusterProviderType]:
    nodes_host_names = [_get_node_label(node, "kubernetes.io/hostname") for node in nodes]
    for host_name in nodes_host_names:
        if not host_name:
            continue
        for cluster_type in HOSTNAME_MATCH:
            cluster_hostname_regex = HOSTNAME_MATCH[cluster_type]
            if len(re.findall(cluster_hostname_regex, host_name)) >= 1:
                return cluster_type
    return ClusterProviderType.Unknown


def _detect_provider_from_node_labels(nodes) -> Optional[ClusterProviderType]:
    for cluster_type in NODE_LABELS:
        if _get_node_label(nodes[0], NODE_LABELS[cluster_type]):
            return cluster_type
    return ClusterProviderType.Unknown


def _is_aks(nodes) -> bool:
    try:
        node = nodes[0]
        provider_id = node.spec.providerID
        if "aks" in provider_id:
            return True
    except AttributeError:
        # is not aks, field is optional so could be missing
        pass
    return False


def _is_detect_cluster_from_kubelet_version(nodes, kubelet_substring) -> bool:
    try:
        node = nodes[0]
        kubelet_version = node.status.nodeInfo.kubeletVersion
        if kubelet_substring in kubelet_version:
            return True
    except AttributeError:
        # missing kubeletVersion
        pass
    return False


def get_cluster_provider():
    global __CLUSTER_PROVIDER__
    return __CLUSTER_PROVIDER__


def discover_cluster_provider():
    global __CLUSTER_PROVIDER__
    if not __CLUSTER_PROVIDER__:
        __CLUSTER_PROVIDER__ = find_cluster_provider().value
        logging.info(f"{__CLUSTER_PROVIDER__} cluster detected")

def find_cluster_provider() -> ClusterProviderType:
    try:
        nodes = NodeList.listNode().obj.items
        cluster_hostname_provider = _detect_provider_from_hostname(nodes)
        if cluster_hostname_provider != ClusterProviderType.Unknown:
            return cluster_hostname_provider
        elif _is_aks(nodes):
            return ClusterProviderType.AKS
        elif _is_detect_cluster_from_kubelet_version(nodes, 'gke'):
            return ClusterProviderType.GKE
        elif _is_detect_cluster_from_kubelet_version(nodes, 'eks'):
            return ClusterProviderType.EKS

        cluster_provider_from_labels = _detect_provider_from_node_labels(nodes)
        if cluster_provider_from_labels != ClusterProviderType.Unknown:
            return cluster_provider_from_labels

    except Exception:
        logging.error("Error detecting cluster type", exc_info=True)
    return ClusterProviderType.Unknown
