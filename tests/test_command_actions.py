import importlib
import inspect
import pkgutil
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

import playbooks.robusta_playbooks as builtin_playbooks
import robusta.core.playbooks.internal as internal_playbooks
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.actions_registry import Action, ActionsRegistry, action
from robusta.core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl
from robusta.model.config import PlaybooksRegistryImpl
from robusta.model.playbook_action import PlaybookAction
from robusta.model.playbook_definition import PlaybookDefinition
from robusta.utils.error_codes import ErrorCodes

REPO_ROOT = Path(__file__).parent.parent

# Code that runs a command in a pod or on a node, or starts a pod, job or deployment to run one.
EXECUTION_CODE = re.compile(
    r"\.exec\(|exec_in_\w+\(|run_simple_job\w*\(|create_debugger_pod\(|subprocess|\bJob\(|RobustaPod\(\s*apiVersion"
)

# Actions that execute code and are not command actions: each reads with one fixed tool, starts nothing in the
# cluster, and takes no command line from the request.
FIXED_TOOL_ACTIONS = {
    "kubectl_describe",
    "fetch_resource_yaml",
    "fetch_crds",
    "fetch_cr_instances",
}

# Actions that send a request to an address from their parameters.
REQUEST_ACTIONS = {"http_get", "http_post", "http_put"}

# Retired actions that are still registered and return a "no longer supported" error.
RETIRED_ACTIONS_WITH_ERROR = {"kubectl_command", "rollout_restart", "alert_handling_job", "node_bash_enricher"}

# Every action of release 0.55.0 that no longer works.
RETIRED_ACTIONS = {
    *RETIRED_ACTIONS_WITH_ERROR,
    "ack_opsgenie_alert_from_slack", "argo_app_sync", "config_ab_testing", "count_pod_creations",
    "create_pvc_snapshot", "daemonset_fix_config", "daemonset_silence_false_alarm", "debugger_stack_trace",
    "disk_benchmark", "event_report", "generate_high_cpu", "git_change_audit", "helm_status_enricher",
    "hpa_events_enricher", "http_stress_test", "incluster_ping", "java_process_inspector",
    "job_restart_on_oomkilled_community", "json_change_tracker", "krr_scan", "node_disk_analyzer",
    "node_dmesg_enricher", "pod_dmesg_enricher", "pod_jmap_pid", "pod_jstack_pid", "pod_ps", "popeye_scan",
    "prometheus_sla_enricher", "python_debugger", "python_memory", "python_process_inspector", "python_profiler",
    "report_image_changes", "restart_named_rollout", "scale_hpa_callback", "stack_overflow_enricher",
    "target_down_dns_enricher", "test_pod_orm", "volume_analysis",
}

COMMAND_ACTIONS = {
    "pod_bash_enricher",
    *REQUEST_ACTIONS,
}

def _builtin_actions():
    actions = {}
    for package in (builtin_playbooks, internal_playbooks):
        for module_info in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{package.__name__}.{module_info.name}")
            for name, func in vars(module).items():
                if Action.is_action(func) and func.__module__ == module.__name__:
                    actions[name] = func
    return actions


BUILTIN_ACTIONS = _builtin_actions()


def _executes_code(func, seen=None) -> bool:
    """True if the function, or a robusta function it calls by name, has execution code."""
    seen = seen if seen is not None else set()
    if func in seen:
        return False
    seen.add(func)
    if EXECUTION_CODE.search(inspect.getsource(func)):
        return True
    for name in func.__code__.co_names:
        called = func.__globals__.get(name)
        if inspect.isfunction(called) and called.__module__.split(".")[0] in ("robusta", "playbooks"):
            if _executes_code(called, seen):
                return True
    return False


def _helm_values() -> dict:
    return yaml.safe_load((REPO_ROOT / "helm/robusta/values.yaml").read_text())


def test_builtin_actions_are_found():
    assert len(BUILTIN_ACTIONS) > 100
    assert COMMAND_ACTIONS | FIXED_TOOL_ACTIONS <= set(BUILTIN_ACTIONS)
    assert RETIRED_ACTIONS & set(BUILTIN_ACTIONS) == RETIRED_ACTIONS_WITH_ERROR


@pytest.mark.parametrize("name", sorted(BUILTIN_ACTIONS))
def test_action_classification(name):
    func = BUILTIN_ACTIONS[name]
    expected = (_executes_code(func) and name not in FIXED_TOOL_ACTIONS) or name in REQUEST_ACTIONS
    assert Action(func).command_action == expected


def test_command_actions_list():
    assert {name for name, func in BUILTIN_ACTIONS.items() if Action(func).command_action} == COMMAND_ACTIONS


def test_helm_defaults():
    values = _helm_values()
    assert values["commandActions"] == []
    assert not COMMAND_ACTIONS & set(values["lightActions"])


def test_default_playbooks_actions():
    values = _helm_values()
    used = {
        name
        for key in ("builtinPlaybooks", "priorityBuiltinPlaybooks", "platformPlaybooks")
        for playbook in values[key]
        for playbook_action in playbook["actions"]
        for name in playbook_action
    }
    assert not used & COMMAND_ACTIONS


def test_action_decorator_forms():
    @action
    def plain(event: ExecutionBaseEvent):
        pass

    @action()
    def called(event: ExecutionBaseEvent):
        pass

    @action(command_action=True)
    def command(event: ExecutionBaseEvent):
        pass

    assert not Action(plain).command_action
    assert not Action(called).command_action
    assert Action(command).command_action


def _request_handler(command_action: bool):
    registry = MagicMock()
    action_def = registry.get_actions.return_value.get_action.return_value
    action_def.command_action = command_action
    handler = PlaybooksEventHandlerImpl.__new__(PlaybooksEventHandlerImpl)
    handler.registry = registry
    handler.run_actions = MagicMock(return_value={"success": True})
    return handler, action_def


@pytest.mark.parametrize("enabled", [[], ["pod_bash_enricher"]])
def test_request_for_command_action(enabled):
    handler, action_def = _request_handler(command_action=True)
    handler.registry.get_command_actions.return_value = enabled
    response = handler.run_external_action("pod_bash_enricher", {"name": "pod", "bash_command": "id"}, sinks=None)
    assert response["success"] is False
    assert response["error_code"] == ErrorCodes.COMMAND_ACTION_NOT_ALLOWED.value
    assert "bash_command" not in response["msg"] and '"id"' not in response["msg"]
    action_def.from_params_func.assert_not_called()
    handler.run_actions.assert_not_called()


def test_stream_request_for_command_action():
    handler, action_def = _request_handler(command_action=True)
    response = handler.run_external_stream_action("pod_bash_enricher", {"name": "pod"}, ws=MagicMock())
    assert response["error_code"] == ErrorCodes.COMMAND_ACTION_NOT_ALLOWED.value
    action_def.from_params_func.assert_not_called()


def test_request_for_other_action():
    handler, action_def = _request_handler(command_action=False)
    assert handler.run_external_action("delete_pod", {"name": "pod", "namespace": "default"}, sinks=None) == {
        "success": True
    }
    action_def.from_params_func.assert_called_once()


def test_request_for_unknown_action():
    handler, _ = _request_handler(command_action=True)
    handler.registry.get_actions.return_value.get_action.return_value = None
    assert handler.run_external_action("no_such_action", {}, sinks=None)["error_code"] == ErrorCodes.ACTION_NOT_FOUND.value


def _run_from_playbook(enabled_command_actions, command_action=True):
    calls = []

    @action(command_action=command_action)
    def some_action(event: ExecutionBaseEvent):
        calls.append(event)

    registry = MagicMock()
    registry.get_actions.return_value.get_action.return_value = Action(some_action)
    registry.get_command_actions.return_value = enabled_command_actions
    registry.get_global_config.return_value = {}
    registry.get_sinks.return_value.get_all.return_value = {}
    handler = PlaybooksEventHandlerImpl.__new__(PlaybooksEventHandlerImpl)
    handler.registry = registry
    response = handler.run_actions(ExecutionBaseEvent(), [PlaybookAction(action_name="some_action")], no_sinks=True)
    return calls, response


def test_playbook_runs_enabled_command_action():
    calls, response = _run_from_playbook(["some_action"])
    assert len(calls) == 1
    assert response == {"success": True}


def test_playbook_skips_command_action_that_is_not_enabled():
    calls, response = _run_from_playbook([])
    assert calls == []
    assert response["error_code"] == ErrorCodes.COMMAND_ACTION_NOT_ALLOWED.value
    assert "commandActions" in response["msg"]


def test_playbook_runs_other_action_without_enabling():
    calls, response = _run_from_playbook([], command_action=False)
    assert len(calls) == 1
    assert response == {"success": True}


def _playbook(action_name: str) -> PlaybookDefinition:
    return PlaybookDefinition(triggers=[{"on_pod_create": {}}], actions=[{action_name: {}}])


def test_playbook_with_missing_action_is_skipped(caplog):
    @action
    def existing_action(event: ExecutionBaseEvent):
        pass

    actions_registry = ActionsRegistry()
    actions_registry._actions = {"existing_action": Action(existing_action)}
    kept, skipped = _playbook("existing_action"), _playbook("pod_ps")

    registry = PlaybooksRegistryImpl([skipped, kept], actions_registry, global_config={}, default_sinks=[])

    loaded = [playbook for playbooks in registry.triggers_to_playbooks.values() for playbook in playbooks]
    assert loaded == [kept]
    assert "Action pod_ps not found" in caplog.text
