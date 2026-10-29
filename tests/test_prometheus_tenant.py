from types import SimpleNamespace
from unittest.mock import patch

from robusta.core.model import base_params
from robusta.core.model.base_params import PrometheusParams, PrometheusQueryParams
from robusta.core.reporting.base import FindingSubject
from robusta.core.reporting.consts import FindingSubjectType
from robusta.integrations.prometheus.tenant import resolve_tenant

NAMESPACE_LABELS = "robusta.integrations.prometheus.tenant.get_namespace_labels"


def _namespaces(labels_by_namespace):
    return lambda namespace: labels_by_namespace[namespace]


def test_tenant_from_namespace_label():
    with patch(NAMESPACE_LABELS, side_effect=_namespaces({"shop": {"team": "corporate"}})):
        assert resolve_tenant("team", "shop") == "corporate"


def test_no_namespace_reads_nothing():
    with patch(NAMESPACE_LABELS) as labels:
        assert resolve_tenant("team", None) is None
    labels.assert_not_called()


def test_missing_label_returns_none():
    with patch(NAMESPACE_LABELS, side_effect=_namespaces({"shop": {"app": "web"}})):
        assert resolve_tenant("team", "shop") is None


def test_namespace_with_no_labels_returns_none():
    with patch(NAMESPACE_LABELS, side_effect=_namespaces({"shop": None})):
        assert resolve_tenant("team", "shop") is None


def test_unknown_namespace_returns_none():
    with patch(NAMESPACE_LABELS, side_effect=KeyError("shop")):
        assert resolve_tenant("team", "shop") is None


def _event(subject: FindingSubject):
    return SimpleNamespace(get_subject=lambda: subject)


# The pod and alert labels carry another value on purpose: only the namespace label counts
POD_SUBJECT = FindingSubject(
    name="web", subject_type=FindingSubjectType.TYPE_POD, namespace="shop", labels={"team": "from-pod"}
)
NAMESPACE_ONLY_SUBJECT = FindingSubject(name="Unresolved", subject_type=FindingSubjectType.TYPE_NONE, namespace="shop")
UNRESOLVED_SUBJECT = FindingSubject(name="Unresolved", subject_type=FindingSubjectType.TYPE_NONE)
NAMESPACES = {"shop": {"team": "corporate"}, "billing": {"team": "retail"}}


def test_no_tenant_label_configured_changes_nothing():
    params = PrometheusParams(prometheus_additional_headers={"X-Scope-OrgID": "sent"})
    with patch.object(base_params, "PROMETHEUS_TENANT_LABEL", None), patch(NAMESPACE_LABELS) as labels:
        params.post_event_initialization(_event(POD_SUBJECT))
    assert params.prometheus_additional_headers == {"X-Scope-OrgID": "sent"}
    labels.assert_not_called()


def test_tenant_from_subject_namespace_ignores_resource_labels():
    params = PrometheusParams()
    with patch.object(base_params, "PROMETHEUS_TENANT_LABEL", "team"), patch(
        NAMESPACE_LABELS, side_effect=_namespaces(NAMESPACES)
    ):
        params.post_event_initialization(_event(POD_SUBJECT))
    assert params.prometheus_additional_headers == {"X-Scope-OrgID": "corporate"}


def test_namespace_only_alert_gets_tenant():
    params = PrometheusParams()
    with patch.object(base_params, "PROMETHEUS_TENANT_LABEL", "team"), patch(
        NAMESPACE_LABELS, side_effect=_namespaces(NAMESPACES)
    ):
        params.post_event_initialization(_event(NAMESPACE_ONLY_SUBJECT))
    assert params.prometheus_additional_headers == {"X-Scope-OrgID": "corporate"}


def test_tenant_header_replaces_sent_one_and_keeps_others():
    params = PrometheusParams(prometheus_additional_headers={"X-Scope-OrgID": "forged", "X-Other": "1"})
    with patch.object(base_params, "PROMETHEUS_TENANT_LABEL", "team"), patch(
        NAMESPACE_LABELS, side_effect=_namespaces(NAMESPACES)
    ):
        params.post_event_initialization(_event(POD_SUBJECT))
    assert params.prometheus_additional_headers == {"X-Scope-OrgID": "corporate", "X-Other": "1"}


def test_no_namespace_keeps_default_tenant():
    params = PrometheusParams(prometheus_additional_headers={"X-Scope-OrgID": "default"})
    with patch.object(base_params, "PROMETHEUS_TENANT_LABEL", "team"), patch(NAMESPACE_LABELS) as labels:
        params.post_event_initialization(_event(UNRESOLVED_SUBJECT))
    assert params.prometheus_additional_headers == {"X-Scope-OrgID": "default"}
    labels.assert_not_called()


def test_query_params_namespace_wins_over_event_subject():
    params = PrometheusQueryParams(promql_query="up", duration={"duration_minutes": 5}, namespace="billing")
    with patch.object(base_params, "PROMETHEUS_TENANT_LABEL", "team"), patch(
        NAMESPACE_LABELS, side_effect=_namespaces(NAMESPACES)
    ):
        params.post_event_initialization(_event(POD_SUBJECT))
    assert params.prometheus_additional_headers == {"X-Scope-OrgID": "retail"}


def test_requests_do_not_share_headers():
    # Two requests built from the same global config, as merge_global_params does, for different tenants
    global_config = {"prometheus_additional_headers": {"X-Scope-OrgID": "default"}}
    with patch.object(base_params, "PROMETHEUS_TENANT_LABEL", "team"), patch(
        NAMESPACE_LABELS, side_effect=_namespaces(NAMESPACES)
    ):
        first, second = [
            PrometheusQueryParams(
                **global_config.copy(), promql_query="up", duration={"duration_minutes": 5}, namespace=namespace
            )
            for namespace in ("shop", "billing")
        ]
        first.post_event_initialization(_event(UNRESOLVED_SUBJECT))
        second.post_event_initialization(_event(UNRESOLVED_SUBJECT))

    assert first.prometheus_additional_headers == {"X-Scope-OrgID": "corporate"}
    assert second.prometheus_additional_headers == {"X-Scope-OrgID": "retail"}
    assert global_config == {"prometheus_additional_headers": {"X-Scope-OrgID": "default"}}
