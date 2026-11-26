import logging
from unittest.mock import MagicMock

import pytest

from playbooks.robusta_playbooks import node_actions, pod_actions
from robusta.core.playbooks.rbac_flags import RBAC_FLAGS_DOCS_URL, require_rbac_flag
from robusta.integrations.kubernetes.custom_models import RobustaJob, RobustaPod
from robusta.runner import config_loader
from robusta.runner.config_loader import ConfigLoader
from robusta.utils.error_codes import ActionException


def test_disabled_flag_message_has_flag_and_docs_link():
    with pytest.raises(ActionException) as error:
        require_rbac_flag(False, "enablePodDelete")
    assert "runner.rbac.enablePodDelete" in error.value.msg
    assert RBAC_FLAGS_DOCS_URL in error.value.msg


def test_enabled_flag_passes():
    require_rbac_flag(True, "enablePodDelete")


def test_delete_pod_with_flag_disabled(monkeypatch):
    monkeypatch.setattr(pod_actions, "ENABLE_POD_DELETE", False)
    event = MagicMock()
    with pytest.raises(ActionException):
        pod_actions.delete_pod(event)
    event.get_pod.return_value.delete.assert_not_called()


def test_drain_needs_node_create_flag(monkeypatch):
    monkeypatch.setattr(node_actions, "ENABLE_NODE_CREATE", False)
    with pytest.raises(ActionException, match="enableNodeCreate"):
        node_actions.drain(MagicMock())


def test_pod_creation_not_supported():
    with pytest.raises(ActionException, match="create pods"):
        RobustaPod.create_debugger_pod("pod", "node")


def test_cordon_with_flag_disabled(monkeypatch):
    monkeypatch.setattr(node_actions, "ENABLE_NODE_EDIT", False)
    with pytest.raises(ActionException, match="enableNodeEdit"):
        node_actions.cordon(MagicMock())


def test_scheduled_playbooks_with_configmap_flags_disabled(monkeypatch, caplog):
    monkeypatch.setattr(config_loader, "ENABLE_ROBUSTA_CONFIG_MAP_EDIT", False)
    loader = MagicMock()
    playbooks_registry = MagicMock()
    playbooks_registry.get_playbooks.return_value = [MagicMock()]

    with caplog.at_level(logging.ERROR):
        ConfigLoader._ConfigLoader__reload_scheduler(loader, playbooks_registry)

    loader.registry.get_scheduler.assert_not_called()
    assert "enableRobustaConfigMapEdit" in caplog.text


def test_job_creation_not_supported():
    with pytest.raises(ActionException, match="create Jobs"):
        RobustaJob.run_simple_job_spec(MagicMock(), "job", 60)
