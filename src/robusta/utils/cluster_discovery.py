import logging
import re
from enum import Enum, auto
from typing import Dict, Optional

from hikaru.model import NodeList


class ClusterProviderType(Enum):
    GKE = auto()
    AKS = auto()
    EKS = auto()
    Kind = auto()
    Minikube = auto()
    RancherDesktop = auto()
    Kapsule = auto()
    Kops = auto()
    Unknown = auto()


HOSTNAME_MATCH: Dict[ClusterProviderType, str] = {
    ClusterProviderType.Kind: ".*kind.*",
    ClusterProviderType.Minikube: ".*minikube.*",
    ClusterProviderType.RancherDesktop: ".*rancher-desktop.*"
}


def _get_node_label(node, label) -> Optional[str]:
    try:
        return node.metadata.labels[label]
    except KeyError:
        pass
    return None


def _detect_provider_from_hostname(nodes) -> Optional[ClusterProviderType]:
    nodes_host_names = [_get_node_label(node, "kubernetes.io/hostname") for node in nodes]
        return ClusterProviderType.Unknown
    nodes_host_names = _get_node_label(nodes[0], "kubernetes.io/hostname")
    for host_name in nodes_host_names:
        if not host_name:
            continue
        for cluster_type in HOSTNAME_MATCH:
            cluster_hostname_regex = HOSTNAME_MATCH[cluster_type]
            if len(re.findall(cluster_hostname_regex, host_name)) >= 1:
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

        KAPSULE_NODE_LABEL = "k8s.scaleway.com/kapsule"
        if _get_node_label(nodes[0], KAPSULE_NODE_LABEL):
            return ClusterProviderType.Kapsule

        KOPS_NODE_LABEL = "kops.k8s.io/instancegroup"
        if _get_node_label(nodes[0], KOPS_NODE_LABEL):
            return ClusterProviderType.Kops
    except Exception:
        logging.error("Error detecting cluster type", exc_info=True)
    return ClusterProviderType.Unknown
