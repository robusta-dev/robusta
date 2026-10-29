from datetime import datetime
from unittest.mock import patch

import pytest

from robusta.core.model.base_params import PrometheusParams
from robusta.core.playbooks import prometheus_enrichment_utils
from robusta.integrations.prometheus import utils
from robusta.integrations.prometheus.utils import generate_prometheus_config

NAMESPACES = {"shop": {"team": "corporate"}, "billing": {"team": "retail"}, "unlabeled": {"app": "web"}}


@pytest.fixture
def tenant_label():
    def labels(namespace):
        return NAMESPACES[namespace]

    with patch.object(utils, "PROMETHEUS_TENANT_LABEL", "team"), patch.object(
        utils, "get_namespace_labels", side_effect=labels
    ) as get_labels:
        yield get_labels


def _headers(**params):
    return generate_prometheus_config(PrometheusParams(prometheus_url="http://prometheus:9090", **params)).headers


def test_tenant_from_namespace_label(tenant_label):
    assert _headers(namespace="shop") == {"X-Scope-OrgID": "corporate"}


def test_tenant_replaces_configured_one_and_keeps_other_headers(tenant_label):
    headers = _headers(namespace="billing", prometheus_additional_headers={"X-Scope-OrgID": "default", "X-Other": "1"})
    assert headers == {"X-Scope-OrgID": "retail", "X-Other": "1"}


def test_no_namespace_keeps_default_tenant(tenant_label):
    assert _headers(prometheus_additional_headers={"X-Scope-OrgID": "default"}) == {"X-Scope-OrgID": "default"}
    tenant_label.assert_not_called()


@pytest.mark.parametrize("namespace", ["unlabeled", "missing"])
def test_unlabeled_or_unknown_namespace_keeps_default_tenant(tenant_label, namespace):
    headers = _headers(namespace=namespace, prometheus_additional_headers={"X-Scope-OrgID": "default"})
    assert headers == {"X-Scope-OrgID": "default"}


def test_feature_off_reads_nothing(tenant_label):
    with patch.object(utils, "PROMETHEUS_TENANT_LABEL", None):
        assert not _headers(namespace="shop")
    tenant_label.assert_not_called()


@pytest.mark.parametrize(
    "tenant_label_env, params_namespace, labels, expected",
    [
        ("team", None, {"namespace": "shop", "pod": "web"}, "shop"),  # alert graph: namespace from the labels
        ("team", "billing", {"namespace": "shop"}, "billing"),  # an explicit namespace wins
        ("team", None, {"node": "node-1"}, None),  # node graph: default tenant
        (None, None, {"namespace": "shop"}, None),  # feature off: params untouched
    ],
)
def test_graph_enrichment_namespace(tenant_label_env, params_namespace, labels, expected):
    params = PrometheusParams(namespace=params_namespace)
    with patch.object(prometheus_enrichment_utils, "PROMETHEUS_TENANT_LABEL", tenant_label_env), patch.object(
        prometheus_enrichment_utils, "create_chart_from_prometheus_query"
    ) as create_chart:
        create_chart.side_effect = Exception("stop")
        with pytest.raises(Exception, match="stop"):
            prometheus_enrichment_utils.create_graph_enrichment(
                datetime.now(), labels, "up", params, 60, None, None
            )
    assert create_chart.call_args.args[0].namespace == expected
    assert params.namespace == params_namespace


def test_configured_headers_are_not_changed(tenant_label):
    configured = {"X-Scope-OrgID": "default"}
    _headers(namespace="shop", prometheus_additional_headers=configured)
    assert configured == {"X-Scope-OrgID": "default"}
