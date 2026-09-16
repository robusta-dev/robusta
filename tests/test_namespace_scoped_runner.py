from unittest.mock import MagicMock, patch

from robusta.core.discovery.discovery import Discovery
from robusta.integrations.kubernetes.api_client_utils import get_all_namespace_data
from robusta.integrations.prometheus.utils import AlertManagerDiscovery, HolmesDiscovery, PrometheusDiscovery
from robusta.utils.cluster_provider_discovery import ClusterProviderDiscovery, ClusterProviderType
from robusta.utils.service_discovery import find_service_url


def _list_result(count: int) -> MagicMock:
    res = MagicMock()
    res.items = [MagicMock()]
    res.metadata.remaining_item_count = count - 1
    return res


def test_discover_stats_scoped_namespace():
    with patch("robusta.core.discovery.discovery.CLUSTER_STATS_NAMESPACE", "robusta"), patch(
        "robusta.core.discovery.discovery.client"
    ) as mock_client:
        mock_client.VersionApi.return_value.get_code.return_value.git_version = "v1.30.0"
        apps = mock_client.AppsV1Api.return_value
        core = mock_client.CoreV1Api.return_value
        batch = mock_client.BatchV1Api.return_value
        apps.list_namespaced_deployment.return_value = _list_result(3)
        apps.list_namespaced_stateful_set.return_value = _list_result(2)
        apps.list_namespaced_daemon_set.return_value = _list_result(1)
        apps.list_namespaced_replica_set.return_value = _list_result(4)
        core.list_namespaced_pod.return_value = _list_result(7)
        batch.list_namespaced_job.return_value = _list_result(5)

        stats = Discovery.discover_stats()

        assert stats.deployments == 3
        assert stats.statefulsets == 2
        assert stats.daemonsets == 1
        assert stats.replicasets == 4
        assert stats.pods == 7
        assert stats.jobs == 5
        assert stats.nodes == 1  # nodes cannot be listed in scoped mode - reported as 1
        assert stats.k8s_version == "v1.30.0"
        core.list_node.assert_not_called()
        apps.list_namespaced_deployment.assert_called_once_with("robusta", limit=1, _continue=None)
        apps.list_deployment_for_all_namespaces.assert_not_called()


def test_discover_stats_cluster_wide_default():
    with patch("robusta.core.discovery.discovery.CLUSTER_STATS_NAMESPACE", ""), patch(
        "robusta.core.discovery.discovery.client"
    ) as mock_client:
        mock_client.VersionApi.return_value.get_code.return_value.git_version = "v1.30.0"
        apps = mock_client.AppsV1Api.return_value
        core = mock_client.CoreV1Api.return_value
        batch = mock_client.BatchV1Api.return_value
        apps.list_deployment_for_all_namespaces.return_value = _list_result(10)
        apps.list_stateful_set_for_all_namespaces.return_value = _list_result(2)
        apps.list_daemon_set_for_all_namespaces.return_value = _list_result(3)
        apps.list_replica_set_for_all_namespaces.return_value = _list_result(12)
        core.list_pod_for_all_namespaces.return_value = _list_result(50)
        core.list_node.return_value = _list_result(6)
        batch.list_job_for_all_namespaces.return_value = _list_result(4)

        stats = Discovery.discover_stats()

        assert stats.deployments == 10
        assert stats.nodes == 6
        apps.list_namespaced_deployment.assert_not_called()
        core.list_node.assert_called_once()


def test_cluster_provider_override_known_value():
    assert ClusterProviderDiscovery._provider_from_override("eks") == ClusterProviderType.EKS
    assert ClusterProviderDiscovery._provider_from_override("OpenShift") == ClusterProviderType.OpenShift


def test_cluster_provider_override_unknown_value_used_as_is():
    assert ClusterProviderDiscovery._provider_from_override("MyCloud") == "MyCloud"


def test_cluster_provider_override_skips_node_detection():
    provider_discovery = ClusterProviderDiscovery()
    with patch("robusta.utils.cluster_provider_discovery.CLUSTER_PROVIDER_OVERRIDE", "GKE"), patch.object(
        provider_discovery, "_find_cluster_provider"
    ) as mock_detect:
        provider_discovery.init_provider_discovery()
        mock_detect.assert_not_called()
        assert provider_discovery.get_cluster_provider() == ClusterProviderType.GKE


def test_find_service_url_namespaced():
    with patch("robusta.utils.service_discovery.client") as mock_client:
        core = mock_client.CoreV1Api.return_value
        svc = MagicMock()
        svc.metadata.name = "holmes"
        svc.metadata.namespace = "robusta"
        svc.spec.ports = [MagicMock(port=80)]
        core.list_namespaced_service.return_value.items = [svc]

        url = find_service_url("app=holmes", namespace="robusta")

        assert url.startswith("http://holmes.robusta.svc.")
        core.list_namespaced_service.assert_called_once_with("robusta", label_selector="app=holmes")
        core.list_service_for_all_namespaces.assert_not_called()


def test_find_service_url_all_namespaces_default():
    with patch("robusta.utils.service_discovery.client") as mock_client:
        core = mock_client.CoreV1Api.return_value
        core.list_service_for_all_namespaces.return_value.items = []

        assert find_service_url("app=holmes") is None
        core.list_service_for_all_namespaces.assert_called_once_with(label_selector="app=holmes")
        core.list_namespaced_service.assert_not_called()


def test_holmes_discovery_namespace_passed_through():
    HolmesDiscovery.cache.clear()
    with patch("robusta.integrations.prometheus.utils.HOLMES_DISCOVERY_NAMESPACE", "robusta"), patch(
        "robusta.integrations.prometheus.utils.find_service_url"
    ) as mock_find:
        mock_find.return_value = "http://holmes.robusta.svc.cluster.local:80"
        assert HolmesDiscovery.find_holmes_url() == "http://holmes.robusta.svc.cluster.local:80"
        mock_find.assert_called_once_with("app=holmes", namespace="robusta")
    HolmesDiscovery.cache.clear()


def test_prometheus_discovery_disabled():
    PrometheusDiscovery.cache.clear()
    with patch("robusta.integrations.prometheus.utils.DISABLE_PROMETHEUS_DISCOVERY", True), patch(
        "robusta.integrations.prometheus.utils.find_service_url"
    ) as mock_find:
        assert PrometheusDiscovery.find_prometheus_url() is None
        assert PrometheusDiscovery.find_vm_url() is None
        mock_find.assert_not_called()


def test_alertmanager_discovery_disabled():
    AlertManagerDiscovery.cache.clear()
    with patch("robusta.integrations.prometheus.utils.DISABLE_ALERTMANAGER_DISCOVERY", True), patch(
        "robusta.integrations.prometheus.utils.find_service_url"
    ) as mock_find:
        assert AlertManagerDiscovery.find_alert_manager_url() is None
        mock_find.assert_not_called()


def test_namespace_data_disabled():
    get_all_namespace_data.cache_clear()
    with patch("robusta.integrations.kubernetes.api_client_utils.NAMESPACE_DATA_MODE", "disabled"), patch(
        "robusta.integrations.kubernetes.api_client_utils.core_v1_api"
    ) as mock_core_v1_api:
        assert get_all_namespace_data() == {}
        mock_core_v1_api.CoreV1Api.assert_not_called()
    get_all_namespace_data.cache_clear()


def test_namespace_data_namespaced():
    get_all_namespace_data.cache_clear()
    with patch("robusta.integrations.kubernetes.api_client_utils.NAMESPACE_DATA_MODE", "namespaced"), patch(
        "robusta.integrations.kubernetes.api_client_utils.INSTALLATION_NAMESPACE", "robusta"
    ), patch("robusta.integrations.kubernetes.api_client_utils.core_v1_api") as mock_core_v1_api:
        core = mock_core_v1_api.CoreV1Api.return_value
        ns = MagicMock()
        ns.metadata.name = "robusta"
        core.read_namespace.return_value = ns

        data = get_all_namespace_data()

        assert list(data.keys()) == ["robusta"]
        core.read_namespace.assert_called_once_with("robusta")
        core.list_namespace.assert_not_called()
    get_all_namespace_data.cache_clear()


def test_prometheus_value_query_quiet_when_no_prometheus_url():
    from robusta.core.exceptions import NoPrometheusUrlFound
    from robusta.core.sinks.robusta.prometheus_discovery_utils import PrometheusDiscoveryUtils

    stub = MagicMock()
    stub.get_global_config.return_value = {}
    with patch(
        "robusta.core.sinks.robusta.prometheus_discovery_utils.run_prometheus_query",
        side_effect=NoPrometheusUrlFound("no url"),
    ), patch("robusta.core.sinks.robusta.prometheus_discovery_utils.logging") as mock_logging:
        result = PrometheusDiscoveryUtils._get_query_prometheus_value(stub, query="up")

    assert result is None
    mock_logging.exception.assert_not_called()
    mock_logging.debug.assert_called_once()


def _deployment(name: str, labels: dict, replicas: int = 1, ready: int = 1):
    from kubernetes.client import (
        V1Container,
        V1Deployment,
        V1DeploymentSpec,
        V1DeploymentStatus,
        V1LabelSelector,
        V1ObjectMeta,
        V1PodSpec,
        V1PodTemplateSpec,
        V1ResourceRequirements,
    )

    return V1Deployment(
        metadata=V1ObjectMeta(name=name, namespace="ns1", labels=labels, resource_version="7"),
        spec=V1DeploymentSpec(
            replicas=replicas,
            selector=V1LabelSelector(match_labels=labels),
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(labels=labels),
                spec=V1PodSpec(
                    containers=[V1Container(name="main", image="img:1", resources=V1ResourceRequirements())]
                ),
            ),
        ),
        status=V1DeploymentStatus(ready_replicas=ready),
    )


def test_discover_namespaced_robusta_services_self_registration():
    deployments = MagicMock()
    deployments.items = [
        _deployment("robusta-runner", {"app": "robusta-runner"}),
        _deployment("robusta-holmes", {"app": "holmes"}, replicas=2, ready=1),
        _deployment("unrelated-app", {"app": "checkout"}),
    ]
    with patch("robusta.core.discovery.discovery.client") as mock_client:
        apps = mock_client.AppsV1Api.return_value
        apps.list_namespaced_deployment.return_value = deployments

        services = Discovery.discover_namespaced_robusta_services("ns1")

    apps.list_namespaced_deployment.assert_called_once_with("ns1")
    assert [s.name for s in services] == ["robusta-runner", "robusta-holmes"]
    for service in services:
        assert service.namespace == "ns1"
        assert service.service_type == "Deployment"
    runner, holmes = services
    assert runner.service_config.labels == {"app": "robusta-runner"}
    assert holmes.service_config.labels == {"app": "holmes"}
    assert holmes.total_pods == 2
    assert holmes.ready_pods == 1


def test_get_resource_events_namespaced():
    from robusta.core.playbooks.common import get_resource_events

    with patch("robusta.core.playbooks.common.EventList") as mock_event_list:
        mock_event_list.listNamespacedEvent.return_value.obj.items = []

        events = get_resource_events(kind="Deployment", name="holmes", namespace="ns2")

    assert events == []
    mock_event_list.listNamespacedEvent.assert_called_once_with(
        "ns2", field_selector="regarding.kind=Deployment,regarding.name=holmes,regarding.namespace=ns2"
    )
    mock_event_list.listEventForAllNamespaces.assert_not_called()


def test_get_resource_events_cluster_scope_without_namespace():
    from robusta.core.playbooks.common import get_resource_events

    with patch("robusta.core.playbooks.common.EventList") as mock_event_list:
        mock_event_list.listEventForAllNamespaces.return_value.obj.items = []

        get_resource_events(kind="Node", name="node-1")

    mock_event_list.listEventForAllNamespaces.assert_called_once_with(
        field_selector="regarding.kind=Node,regarding.name=node-1"
    )
    mock_event_list.listNamespacedEvent.assert_not_called()


def test_robusta_event_get_events_namespaced():
    from robusta.integrations.kubernetes.custom_models import RobustaEvent

    with patch("robusta.integrations.kubernetes.custom_models.EventList") as mock_event_list:
        RobustaEvent.get_events(kind="Deployment", name="holmes", namespace="ns2")

    mock_event_list.listNamespacedEvent.assert_called_once_with(
        "ns2", field_selector="regarding.kind=Deployment,regarding.name=holmes,regarding.namespace=ns2"
    )
    mock_event_list.listEventForAllNamespaces.assert_not_called()
