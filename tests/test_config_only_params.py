from pathlib import Path
from unittest.mock import MagicMock

import yaml

from robusta.core.model.base_params import drop_config_only_params
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


def test_empty_params_are_left_alone():
    assert drop_config_only_params(None) is None
    assert drop_config_only_params({}) == {}


def _handler_and_action():
    registry = MagicMock()
    action_def = registry.get_actions.return_value.get_action.return_value
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


def test_simulated_alert_is_not_a_default_light_action():
    values = yaml.safe_load((Path(__file__).parent.parent / "helm/robusta/values.yaml").read_text())
    assert "prometheus_alert" not in values["lightActions"]
    assert "alertmanager_alert" in values["lightActions"]
