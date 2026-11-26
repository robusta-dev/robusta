import importlib
import logging
from unittest.mock import MagicMock

import pytest

from playbooks.robusta_playbooks import kubectl_enrichments, node_actions, pod_actions, workload_actions
from robusta.core.model import env_vars
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


def test_drain_needs_pod_evict_flag(monkeypatch):
    monkeypatch.setattr(node_actions, "ENABLE_POD_EVICT", False)
    with pytest.raises(ActionException, match="enablePodEvict"):
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


def test_scheduled_playbooks_with_no_create_setting(monkeypatch, caplog):
    monkeypatch.setattr(config_loader, "DISABLE_CREATE_FROM_SERVICE_ACCOUNT", True)
    loader = MagicMock()
    playbooks_registry = MagicMock()
    playbooks_registry.get_playbooks.return_value = [MagicMock()]

    with caplog.at_level(logging.ERROR):
        ConfigLoader._ConfigLoader__reload_scheduler(loader, playbooks_registry)

    loader.registry.get_scheduler.assert_not_called()
    assert len(caplog.records) == 1
    assert "disableCreateFromServiceAccount" in caplog.text


@pytest.mark.parametrize(
    "flag",
    [
        "ENABLE_POD_DELETE",
        "ENABLE_JOB_DELETE",
        "ENABLE_NODE_EDIT",
        "ENABLE_POD_EVICT",
        "ENABLE_ROBUSTA_CONFIG_MAP_CREATE",
        "ENABLE_ROBUSTA_CONFIG_MAP_EDIT",
    ],
)
def test_flag_without_env_var_is_off(monkeypatch, flag):
    monkeypatch.delenv(flag, raising=False)
    assert importlib.reload(env_vars).__dict__[flag] is False


def test_kubectl_command_is_no_longer_supported(caplog):
    with caplog.at_level(logging.ERROR), pytest.raises(ActionException, match="no longer supported"):
        kubectl_enrichments.kubectl_command(MagicMock(), kubectl_enrichments.KubectlParams(command="kubectl get pods"))
    assert "kubectl_command is deprecated" in caplog.text


def test_rollout_restart_is_no_longer_supported(caplog):
    with pytest.raises(ActionException):
        workload_actions.rollout_restart(MagicMock())
    assert "rollout_restart is deprecated" in caplog.text
