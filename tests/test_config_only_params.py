from unittest.mock import MagicMock

import pytest

from robusta.core.model.base_params import drop_config_only_params
from robusta.core.playbooks.playbook_utils import merge_global_params
from robusta.core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl


def test_config_only_params_are_dropped():
    params = {
        "serviceAccountName": "other-sa",
        "service_account_name": "other-sa",
        "custom_annotations": {"key": "value"},
        "krr_args": "--cpu-min 15",
        "popeye_args": "-s po",
        "args": "-n default",
        "timeout": 60,
    }
    assert drop_config_only_params(params) == {"timeout": 60}


def test_dropped_params_are_logged_by_name_only(caplog):
    drop_config_only_params({"prometheus_auth": "Bearer from-request", "timeout": 60})
    assert "prometheus_auth" in caplog.text
    assert "from-request" not in caplog.text
    caplog.clear()
    drop_config_only_params({"timeout": 60})
    assert not caplog.records


def test_empty_params_are_left_alone():
    assert drop_config_only_params(None) is None
    assert drop_config_only_params({}) == {}


def _handler_and_action():
    registry = MagicMock()
    action_def = registry.get_actions.return_value.get_action.return_value
    action_def.command_action = False
    handler = PlaybooksEventHandlerImpl.__new__(PlaybooksEventHandlerImpl)
    handler.registry = registry
    handler.run_actions = MagicMock(return_value={"success": True})
    return handler, action_def


def test_external_action_request_cannot_set_config_only_params():
    handler, action_def = _handler_and_action()
    handler.run_external_action(
        "krr_scan", {"serviceAccountName": "other-sa", "custom_annotations": {"a": "b"}, "timeout": 60}, sinks=None
    )
    action_def.from_params_parameter_class.assert_called_once_with(timeout=60)
    playbook_action = handler.run_actions.call_args.args[1][0]
    assert playbook_action.action_params == {"timeout": 60}


def test_generator_url_comes_from_configuration():
    handler, action_def = _handler_and_action()
    handler.run_external_action(
        "prometheus_alert", {"alert_name": "A", "generator_url": "http://example.com/graph?g0.expr=up"}, sinks=None
    )
    action_def.from_params_parameter_class.assert_called_once_with(alert_name="A")


@pytest.mark.parametrize(
    "param",
    [
        "prometheus_url",
        "prometheus_url_query_string",
        "prometheus_auth",
        "prometheus_graphs_overrides",
        "alertmanager_url",
        "alertmanager_flavor",
        "alertmanager_auth",
        "alertmanager_additional_headers",
        "grafana_url",
        "grafana_api_key",
        "holmes_url",
    ],
)
@pytest.mark.parametrize("stream", [False, True])
def test_connection_params_come_from_configuration(param, stream):
    handler, action_def = _handler_and_action()
    params = {param: "from-request", "prometheus_additional_headers": {"X-Scope-OrgID": "a"}}
    if stream:
        action_def.from_params_func.return_value = None
        handler.run_external_stream_action("holmes_chat", params, ws=MagicMock())
    else:
        handler.run_external_action("get_silences", params, sinks=None)
    action_def.from_params_parameter_class.assert_called_once_with(
        prometheus_additional_headers={"X-Scope-OrgID": "a"}
    )


def test_configured_connection_params_reach_the_action():
    params = merge_global_params(
        {"alertmanager_url": "http://configured:9093", "alertmanager_auth": "Bearer configured"},
        drop_config_only_params({"alertmanager_url": "http://from-request", "silence_id": "1"}),
    )
    assert params == {
        "alertmanager_url": "http://configured:9093",
        "alertmanager_auth": "Bearer configured",
        "silence_id": "1",
    }
