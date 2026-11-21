from unittest.mock import MagicMock, patch

import pytest

from robusta.core.playbooks.internal import crds
from robusta.core.playbooks.internal.crds import CRInstancesParams, ResourceParams

FLAG_VALUES = ["--server=https://example.com", "-f", "--filename=https://example.com/x.yaml", "pods --all", "a;b", ""]


@pytest.mark.parametrize("value", FLAG_VALUES)
def test_resource_params_reject_values_that_are_not_names(value):
    with pytest.raises(ValueError):
        ResourceParams(kind=value, name="my-pod")
    with pytest.raises(ValueError):
        ResourceParams(kind="pod", name=value)
    if value:
        with pytest.raises(ValueError):
            ResourceParams(kind="pod", name="my-pod", namespace=value)
    with pytest.raises(ValueError):
        CRInstancesParams(kind=value)


@pytest.mark.parametrize(
    "kind,name,namespace",
    [
        ("pod", "my-pod-5d8f7", "default"),
        ("deployments.apps", "web", None),
        ("certificates.cert-manager.io", "my.cert", "cert-manager"),
        ("clusterrole", "system:node", None),
    ],
)
def test_resource_params_accept_kubernetes_names(kind, name, namespace):
    params = ResourceParams(kind=kind, name=name, namespace=namespace)
    assert (params.kind, params.name, params.namespace) == (kind, name, namespace)


def test_positional_arguments_come_after_the_separator():
    with patch.object(crds, "run_kubectl_command", return_value="") as run:
        crds.fetch_resource_yaml(MagicMock(), ResourceParams(kind="pod", name="p", namespace="ns"))
    assert run.call_args.args[0] == ["kubectl", "get", "-o", "yaml", "-n", "ns", "--", "pod", "p"]


def test_empty_namespace_means_cluster_scoped():
    assert ResourceParams(kind="node", name="n1", namespace="").namespace is None
