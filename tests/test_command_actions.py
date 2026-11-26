import importlib
import inspect
import pkgutil
import re
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

import playbooks.robusta_playbooks as builtin_playbooks
import robusta.core.playbooks.internal as internal_playbooks
from playbooks.robusta_playbooks.job_actions import JobParams
from playbooks.robusta_playbooks.kubectl_enrichments import KubectlParams, get_unsafe_template_values, kubectl_command
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.actions_registry import Action, ActionsRegistry, action
from robusta.core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl
from robusta.core.reporting import FindingSubject
from robusta.core.reporting.base import FindingSubjectType
from robusta.integrations.prometheus.models import PrometheusAlert, PrometheusKubernetesAlert
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

COMMAND_ACTIONS = {
    "pod_bash_enricher",
    "node_bash_enricher",
    "kubectl_command",
    "alert_handling_job",
    "krr_scan",
    "popeye_scan",
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
    assert len(BUILTIN_ACTIONS) > 120
    assert COMMAND_ACTIONS | FIXED_TOOL_ACTIONS <= set(BUILTIN_ACTIONS)


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
    # WeeklyKRRScan is the one default playbook with a command action; it runs once krr_scan is in commandActions
    assert not used & (COMMAND_ACTIONS - {"krr_scan"})


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


@pytest.mark.parametrize("enabled", [[], ["node_bash_enricher"]])
def test_request_for_command_action(enabled):
    handler, action_def = _request_handler(command_action=True)
    handler.registry.get_command_actions.return_value = enabled
    response = handler.run_external_action("node_bash_enricher", {"name": "node", "bash_command": "id"}, sinks=None)
    assert response["success"] is False
    assert response["error_code"] == ErrorCodes.COMMAND_ACTION_NOT_ALLOWED.value
    assert "bash_command" not in response["msg"] and '"id"' not in response["msg"]
    action_def.from_params_func.assert_not_called()
    handler.run_actions.assert_not_called()


def test_stream_request_for_command_action():
    handler, action_def = _request_handler(command_action=True)
    response = handler.run_external_stream_action("node_bash_enricher", {"name": "node"}, ws=MagicMock())
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


def _subject(namespace="prod", **kwargs) -> FindingSubject:
    return FindingSubject(name="web-1", subject_type=FindingSubjectType.TYPE_POD, namespace=namespace, **kwargs)


@pytest.mark.parametrize(
    "command, subject, unsafe",
    [
        ("kubectl get pod $name -n $namespace", _subject(), []),
        ("kubectl get pods -l team=${labels.team}", _subject(labels={"team": "payments"}), []),
        ("kubectl get pod $name -n $namespace", _subject(namespace="a; b"), ["namespace"]),
        ("kubectl get pods -l team=${labels.team}", _subject(labels={"team": "$(x)"}), ["labels.team"]),
        ("kubectl get pods -l team=${labels.team}", _subject(), ["labels.team"]),
        ("kubectl get nodes", _subject(labels={"team": "a b"}), []),
        ("kubectl delete pod $name -n $namespace", _subject(namespace="--all-namespaces"), ["namespace"]),
        ("kubectl get pods -l team=${labels.team}", _subject(labels={"team": "-A"}), ["labels.team"]),
        ("kubectl get pods -l team=${labels.team}", _subject(labels={"team": ""}), ["labels.team"]),
        ("kubectl get pods -l team=${labels.team}", _subject(labels={"team": "9lives"}), []),
        ("kubectl get pod $name -n $namespace", _subject(namespace=None), ["namespace"]),
    ],
)
def test_kubectl_command_template_values(command, subject, unsafe):
    assert get_unsafe_template_values(subject, command) == unsafe


def test_kubectl_command_does_not_run_with_unsafe_value():
    event = MagicMock()
    event.get_subject.return_value = _subject(labels={"team": "a; b"})
    with patch("playbooks.robusta_playbooks.kubectl_enrichments.RobustaJob.run_simple_job_spec") as run_job:
        kubectl_command(event, KubectlParams(command="kubectl get pods -l team=${labels.team}"))
        run_job.assert_not_called()
        event.get_subject.return_value = _subject(labels={"team": "payments"})
        kubectl_command(event, KubectlParams(command="kubectl get pods -l team=${labels.team}"))
        assert run_job.call_args.args[0].containers[0].args == ["kubectl get pods -l team=payments"]


def test_alert_job_label_variables():
    from playbooks.robusta_playbooks import job_actions

    alert = PrometheusAlert(
        status="firing",
        startsAt=datetime.now(),
        endsAt=datetime.fromtimestamp(0),
        generatorURL="http://localhost",
        fingerprint="f",
        labels={"alertname": "A", "team": "payments", "bad name": "x", "a=b": "y"},
        annotations={},
    )
    event = PrometheusKubernetesAlert(alert=alert, alert_name="A", alert_severity="error")
    env = getattr(job_actions, "__get_alert_env_vars")(event, JobParams(image="busybox", command=["true"]))
    label_vars = {var.name: var.value for var in env if var.name.startswith("ALERT_LABEL_")}
    assert label_vars == {"ALERT_LABEL_ALERTNAME": "A", "ALERT_LABEL_TEAM": "payments"}
