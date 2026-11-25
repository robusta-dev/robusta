import importlib
import inspect
import pkgutil
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

import playbooks.robusta_playbooks as builtin_playbooks
import robusta.core.playbooks.internal as internal_playbooks
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.actions_registry import Action, action
from robusta.core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl
from robusta.utils.error_codes import ErrorCodes

REPO_ROOT = Path(__file__).parent.parent

# Code that runs a command in a pod or on a node, or starts a pod, job or deployment to run one.
EXECUTION_CODE = re.compile(
    r"\.exec\(|exec_in_\w+\(|exec_on_node\(|run_debugger_pod\(|create_debugger_pod\(|run_simple_job\w*\("
    r"|get_processes\(|ProcessFinder\(|upload_file\(|subprocess|RobustaDeployment\.from_image\(|\bJob\("
    r"|RobustaPod\(\s*apiVersion"
)


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


# Actions that execute code and stay available to remote requests: each runs one fixed tool, and none of
# its command line comes from the request. pod_oom_killer_enricher executes only with dmesg_log, which a
# request cannot set.
REMOTE_EXECUTION_EXCEPTIONS = {
    "pod_oom_killer_enricher",
    "krr_scan",
    "popeye_scan",
    "kubectl_describe",
    "fetch_resource_yaml",
    "fetch_crds",
    "fetch_cr_instances",
}

LOCAL_ONLY_ACTIONS = {
    "pod_bash_enricher",
    "node_bash_enricher",
    "kubectl_command",
    "alert_handling_job",
    "incluster_ping",
    "http_stress_test",
    "disk_benchmark",
    "generate_high_cpu",
    "test_pod_orm",
    "python_profiler",
    "pod_ps",
    "python_memory",
    "debugger_stack_trace",
    "python_process_inspector",
    "python_debugger",
    "java_process_inspector",
    "pod_jmap_pid",
    "pod_jstack_pid",
    "node_dmesg_enricher",
    "pod_dmesg_enricher",
    "node_disk_analyzer",
    "volume_analysis",
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


def test_audit_finds_the_builtin_actions():
    assert len(BUILTIN_ACTIONS) > 140
    assert LOCAL_ONLY_ACTIONS | REMOTE_EXECUTION_EXCEPTIONS <= set(BUILTIN_ACTIONS)


@pytest.mark.parametrize("name", sorted(BUILTIN_ACTIONS))
def test_action_that_executes_code_is_local_only(name):
    func = BUILTIN_ACTIONS[name]
    executes = _executes_code(func)
    expected = executes and name not in REMOTE_EXECUTION_EXCEPTIONS
    assert Action(func).local_only == expected


def test_local_only_actions_are_exactly_the_audited_list():
    assert {name for name, func in BUILTIN_ACTIONS.items() if Action(func).local_only} == LOCAL_ONLY_ACTIONS


def test_default_light_actions_have_no_local_only_action():
    values = yaml.safe_load((REPO_ROOT / "helm/robusta/values.yaml").read_text())
    assert not LOCAL_ONLY_ACTIONS & set(values["lightActions"])


def test_default_light_actions_start_no_scan_job():
    values = yaml.safe_load((REPO_ROOT / "helm/robusta/values.yaml").read_text())
    assert not {"krr_scan", "popeye_scan"} & set(values["lightActions"])


def test_no_button_calls_a_local_only_action():
    """A button's callback is an action request, which the runner refuses for a local-only action."""
    sources = [*(REPO_ROOT / "playbooks/robusta_playbooks").glob("*.py"), *(REPO_ROOT / "src/robusta").rglob("*.py")]
    callback_actions = set()
    for source in sources:
        for choice in re.findall(r"CallbackChoice\((.*?)\)", source.read_text(), re.DOTALL):
            callback_actions.update(re.findall(r"action=(\w+)", choice))
    assert callback_actions & set(BUILTIN_ACTIONS), "the scan found no button, so it checks nothing"
    assert not callback_actions & LOCAL_ONLY_ACTIONS
    assert callback_actions <= set(BUILTIN_ACTIONS)


def test_action_decorator_forms():
    @action
    def plain(event: ExecutionBaseEvent):
        pass

    @action()
    def called(event: ExecutionBaseEvent):
        pass

    @action(local_only=True)
    def local(event: ExecutionBaseEvent):
        pass

    assert not Action(plain).local_only
    assert not Action(called).local_only
    assert Action(local).local_only


def _handler(local_only: bool):
    registry = MagicMock()
    action_def = registry.get_actions.return_value.get_action.return_value
    action_def.local_only = local_only
    handler = PlaybooksEventHandlerImpl.__new__(PlaybooksEventHandlerImpl)
    handler.registry = registry
    handler.run_actions = MagicMock(return_value={"success": True})
    return handler, action_def


def test_external_request_cannot_run_a_local_only_action():
    handler, action_def = _handler(local_only=True)
    response = handler.run_external_action("node_bash_enricher", {"name": "node", "bash_command": "id"}, sinks=None)
    assert response["success"] is False
    assert response["error_code"] == ErrorCodes.LOCAL_ONLY_ACTION.value
    action_def.from_params_parameter_class.assert_not_called()
    action_def.from_params_func.assert_not_called()
    handler.run_actions.assert_not_called()


def test_external_stream_request_cannot_run_a_local_only_action():
    handler, action_def = _handler(local_only=True)
    response = handler.run_external_stream_action("node_bash_enricher", {"name": "node"}, ws=MagicMock())
    assert response["success"] is False
    assert response["error_code"] == ErrorCodes.LOCAL_ONLY_ACTION.value
    action_def.from_params_func.assert_not_called()


def test_rejection_does_not_echo_the_request_params():
    handler, _ = _handler(local_only=True)
    response = handler.run_external_action("node_bash_enricher", {"bash_command": "secret-value"}, sinks=None)
    assert "secret-value" not in response["msg"]


def test_external_request_cannot_turn_on_the_oom_enricher_dmesg_pod():
    handler, action_def = _handler(local_only=False)
    handler.run_external_action(
        "pod_oom_killer_enricher", {"name": "pod", "namespace": "default", "dmesg_log": True}, sinks=None
    )
    action_def.from_params_parameter_class.assert_called_once_with(name="pod", namespace="default")
    assert handler.run_actions.call_args.args[1][0].action_params == {"name": "pod", "namespace": "default"}


def test_external_request_still_runs_other_actions():
    handler, action_def = _handler(local_only=False)
    assert handler.run_external_action("delete_pod", {"name": "pod", "namespace": "default"}, sinks=None) == {
        "success": True
    }
    action_def.from_params_func.assert_called_once()


def test_unknown_action_is_still_reported_as_not_found():
    handler, _ = _handler(local_only=True)
    handler.registry.get_actions.return_value.get_action.return_value = None
    assert handler.run_external_action("no_such_action", {}, sinks=None)["error_code"] == ErrorCodes.ACTION_NOT_FOUND.value


def test_playbook_from_configuration_still_runs_a_local_only_action():
    """Playbooks in the runner's own configuration go through run_actions, which has no local-only check."""
    source = inspect.getsource(PlaybooksEventHandlerImpl.run_actions) + inspect.getsource(
        PlaybooksEventHandlerImpl.handle_trigger
    )
    assert "local_only" not in source
