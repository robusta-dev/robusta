import logging
from unittest.mock import MagicMock

import pytest

from robusta.core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl
from robusta.model.config import PlaybooksRegistryImpl
from robusta.model.playbook_definition import PlaybookDefinition


def scheduled_playbook(action_name: str) -> PlaybookDefinition:
    trigger = {"on_schedule": {"fixed_delay_repeat": {"repeat": 1, "seconds_delay": 60}}}
    return PlaybookDefinition(triggers=[trigger], actions=[{action_name: {}}])


def registry_without_actions() -> MagicMock:
    actions_registry = MagicMock()
    actions_registry.get_action.return_value = None
    return actions_registry


@pytest.mark.parametrize("action_name", ["krr_scan", "popeye_scan"])
def test_playbook_with_deprecated_action_is_loaded(action_name, caplog):
    with caplog.at_level(logging.ERROR):
        registry = PlaybooksRegistryImpl([scheduled_playbook(action_name)], registry_without_actions(), {}, [])

    assert f"Action {action_name} is deprecated and no longer supported" in caplog.text
    assert sum(len(playbooks) for playbooks in registry.triggers_to_playbooks.values()) == 1


def test_playbook_with_unknown_action_is_not_loaded():
    with pytest.raises(Exception, match="no_such_action not found"):
        PlaybooksRegistryImpl([scheduled_playbook("no_such_action")], registry_without_actions(), {}, [])


def test_external_request_for_deprecated_action_returns_error():
    handler = PlaybooksEventHandlerImpl.__new__(PlaybooksEventHandlerImpl)
    handler.registry = MagicMock()
    handler.registry.get_actions.return_value = registry_without_actions()

    response = handler.run_external_action("krr_scan", {}, sinks=None)

    assert response["success"] is False
    assert "krr_scan is deprecated and no longer supported" in response["msg"]
