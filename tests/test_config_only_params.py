from unittest.mock import MagicMock

import pytest

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
        "holmes_url": "https://attacker.example",
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


@pytest.mark.parametrize("action_name", ["holmes_chat", "holmes_oauth", "ask_holmes", "holmes_issue_chat"])
def test_external_holmes_request_cannot_redirect_the_holmes_api_key(action_name):
    """The runner sends its Holmes API key to holmes_url. A request that could
    set it would receive the key, so the URL comes from the runner's config
    (or discovery) only."""
    handler, action_def = _handler_and_action()
    handler.run_external_action(
        action_name, {"holmes_url": "https://attacker.example", "ask": "hi"}, sinks=None
    )
    action_def.from_params_parameter_class.assert_called_once_with(ask="hi")
    playbook_action = handler.run_actions.call_args.args[1][0]
    assert "holmes_url" not in playbook_action.action_params


def test_external_stream_request_cannot_redirect_the_holmes_api_key():
    handler, action_def = _handler_and_action()
    run = handler._PlaybooksEventHandlerImpl__run_playbook_actions = MagicMock()
    handler.run_external_stream_action(
        "holmes_chat", {"holmes_url": "https://attacker.example", "ask": "hi"}, ws=MagicMock()
    )
    action_def.from_params_parameter_class.assert_called_once_with(ask="hi")
    playbook_action = run.call_args.args[1][0]
    assert "holmes_url" not in playbook_action.action_params
