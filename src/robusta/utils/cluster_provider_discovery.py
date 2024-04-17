import logging
import re
from enum import Enum
from typing import Dict, List, Optional

from hikaru.model.rel_1_26 import Node, NodeList


class ClusterProviderType(str, Enum):
    GKE = "GKE"
    AKS = "AKS"
    EKS = "EKS"
    Kind = "Kind"
    Minikube = "Minikube"
    RancherDesktop = "RancherDesktop"
    Kapsule = "Kapsule"
    Kops = "Kops"
    DigitalOcean = "DigitalOcean"
    Unknown = "Unknown"


# the value is a regex match of the hostname
HOSTNAME_MATCH: Dict[ClusterProviderType, str] = {
    ClusterProviderType.Kind: ".*kind.*",
    ClusterProviderType.RancherDesktop: ".*rancher-desktop.*",
}

# the value is a node label unique to the provider
NODE_LABELS: Dict[ClusterProviderType, str] = {
    ClusterProviderType.Minikube: "minikube.k8s.io/name",
    ClusterProviderType.DigitalOcean: "doks.digitalocean.com/version",
    ClusterProviderType.Kops: "kops.k8s.io/instancegroup",
    ClusterProviderType.Kapsule: "k8s.scaleway.com/kapsule",
}


class ClusterProviderDiscovery:
    provider: ClusterProviderType = ClusterProviderType.Unknown

    def init_provider_discovery(self):
        try:
            self.provider = self._find_cluster_provider()
            logging.info(f"{self.provider} cluster discovered.")
        except Exception:
            logging.error("Error detecting cluster type", exc_info=True)

    def get_cluster_provider(self):
        return self.provider

    @staticmethod
    def _get_node_label(node: Node, label: str) -> Optional[str]:
        if node.metadata.labels:
            return node.metadata.labels.get(label)
        return None

    @staticmethod
    def _is_str_in_cluster_provider(nodes: List[Node], identifier: str) -> bool:
        node = nodes[0]
        try:
            provider_id = node.spec.providerID
            return identifier in provider_id
        except (AttributeError, TypeError):
            # is not aks, field is optional so could be missing
            return False

    @staticmethod
    def _is_detect_cluster_from_kubelet_version(nodes: List[Node], kubelet_substring: str) -> bool:
        node = nodes[0]
        try:
            kubelet_version = node.status.nodeInfo.kubeletVersion
            return kubelet_substring in kubelet_version
        except (AttributeError, TypeError):
            # missing kubeletVersion
            return False

    def _detect_provider_from_hostname(self, nodes: List[Node]) -> Optional[ClusterProviderType]:
        nodes_host_names = [self._get_node_label(node, "kubernetes.io/hostname") for node in nodes]
        for host_name in nodes_host_names:
            if not host_name:
                continue
            for cluster_type in HOSTNAME_MATCH:
                cluster_hostname_regex = HOSTNAME_MATCH[cluster_type]
                if re.match(cluster_hostname_regex, host_name):
                    return cluster_type
        return ClusterProviderType.Unknown

    def _detect_provider_from_node_labels(self, nodes: List[Node]) -> Optional[ClusterProviderType]:
        for cluster_type, node_label in NODE_LABELS.items():
            if self._get_node_label(nodes[0], node_label):
                return cluster_type
        return ClusterProviderType.Unknown

    def _find_cluster_provider(self) -> ClusterProviderType:
        nodes = NodeList.listNode().obj.items
        cluster_hostname_provider = self._detect_provider_from_hostname(nodes)
        if cluster_hostname_provider != ClusterProviderType.Unknown:
            return cluster_hostname_provider
        elif self._is_str_in_cluster_provider(nodes, "aks"):
            return ClusterProviderType.AKS
        elif self._is_detect_cluster_from_kubelet_version(nodes, "gke"):
            return ClusterProviderType.GKE
        elif self._is_detect_cluster_from_kubelet_version(nodes, "eks"):
            return ClusterProviderType.EKS
        elif self._is_str_in_cluster_provider(nodes, "kind"):
            return ClusterProviderType.Kind

        return self._detect_provider_from_node_labels(nodes)


cluster_provider = ClusterProviderDiscovery()
__all__ = ["cluster_provider"]
