import base64
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import pytest
import yaml

CHART_PATH = Path(__file__).parent.parent / "helm" / "robusta"

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary not available")

# drain needs eviction; it cannot create workloads
ALLOWED_CLUSTER_WIDE_CREATE = {"pods/eviction"}


def render_chart(extra_args: Optional[List[str]] = None) -> List[dict]:
    cmd = [
        "helm",
        "template",
        str(CHART_PATH),
        "--set",
        "clusterName=test",
        "--set",
        "sinksConfig[0].file_sink.name=test",
        "-s",
        "templates/runner-service-account.yaml",
        "-s",
        "templates/runner.yaml",
    ] + (extra_args or [])
    output = subprocess.check_output(cmd, text=True)
    return [doc for doc in yaml.safe_load_all(output) if doc]


def playbook_names(extra_args: Optional[List[str]] = None) -> set:
    cmd = [
        "helm",
        "template",
        str(CHART_PATH),
        "--set",
        "clusterName=test",
        "--set",
        "sinksConfig[0].file_sink.name=test",
        "--set",
        "enablePlatformPlaybooks=true",
        "-s",
        "templates/playbooks-config.yaml",
    ] + (extra_args or [])
    docs = [doc for doc in yaml.safe_load_all(subprocess.check_output(cmd, text=True)) if doc]
    config = base64.b64decode(docs[0]["data"]["active_playbooks.yaml"]).decode()
    return {p.get("name") for p in yaml.safe_load(config)["active_playbooks"]}


def get_doc(docs: List[dict], kind: str, name_contains: str = "") -> Optional[dict]:
    for doc in docs:
        if doc["kind"] == kind and name_contains in doc["metadata"]["name"]:
            return doc
    return None


def test_runner_clusterrole_no_cluster_wide_create():
    docs = render_chart()
    cluster_role = get_doc(docs, "ClusterRole", "runner-cluster-role")
    assert cluster_role is not None

    violations = []
    for rule in cluster_role.get("rules", []):
        if "create" in rule.get("verbs", []):
            unexpected = set(rule.get("resources", [])) - ALLOWED_CLUSTER_WIDE_CREATE
            if unexpected:
                violations.append(rule)
    assert not violations, f"ClusterRole grants cluster-wide create: {violations}"


def test_runner_clusterrole_no_cluster_wide_pod_exec():
    docs = render_chart()
    cluster_role = get_doc(docs, "ClusterRole", "runner-cluster-role")
    for rule in cluster_role.get("rules", []):
        assert "pods/exec" not in rule.get("resources", []), f"pods/exec must not be cluster-wide: {rule}"


def test_runner_local_role_grants_namespaced_create():
    docs = render_chart()
    role = get_doc(docs, "Role", "runner-local-role")
    assert role is not None, "namespaced Role missing"

    granted = set()
    for rule in role.get("rules", []):
        if "create" in rule.get("verbs", []):
            granted.update(rule.get("resources", []))
    assert {
        "pods",
        "pods/exec",
        "configmaps",
        "persistentvolumeclaims",
        "secrets",
        "jobs",
        "deployments",
    } <= granted

    binding = get_doc(docs, "RoleBinding", "runner-local-role-binding")
    assert binding is not None
    subject = binding["subjects"][0]
    assert subject["kind"] == "ServiceAccount"
    assert "runner-service-account" in subject["name"]


def test_namespaced_create_flag_removes_role_and_disables_playbooks():
    docs = render_chart(["--set", "runner.rbac.disableCreateFromServiceAccount=true"])
    assert get_doc(docs, "Role", "runner-local-role") is None
    assert get_doc(docs, "RoleBinding", "runner-local-role-binding") is None

    names = playbook_names(["--set", "runner.rbac.disableCreateFromServiceAccount=true"])
    assert "NodeFSSpaceAlerts" not in names
    assert "WeeklyKRRScan" not in names


def test_playbooks_enabled_by_default():
    names = playbook_names()
    assert "NodeFSSpaceAlerts" in names
    assert "WeeklyKRRScan" in names


def test_namespace_scoped_rbac_renders_role_and_rolebinding():
    docs = render_chart(["--set", "runner.rbac.namespaceScoped=true"])

    assert get_doc(docs, "ClusterRole", "runner-cluster-role") is None
    assert get_doc(docs, "ClusterRoleBinding", "runner-cluster-role-binding") is None

    role = get_doc(docs, "Role", "runner-role")
    assert role is not None
    assert role["metadata"]["namespace"] == "default"
    # same rule set as the ClusterRole - spot-check a core rule survived the kind switch
    core_read = [
        r for r in role["rules"] if "pods" in r.get("resources", []) and "list" in r.get("verbs", [])
    ]
    assert core_read

    binding = get_doc(docs, "RoleBinding", "runner-role-binding")
    assert binding is not None
    assert binding["roleRef"]["kind"] == "Role"
    assert "runner-role" in binding["roleRef"]["name"]
    assert binding["subjects"][0]["kind"] == "ServiceAccount"

    # the namespaced create Role is unaffected
    assert get_doc(docs, "Role", "runner-local-role") is not None


def test_namespace_scoped_rbac_sets_env_defaults():
    docs = render_chart(["--set", "runner.rbac.namespaceScoped=true"])
    deployment = get_doc(docs, "Deployment", "runner")
    env = {e["name"]: e.get("value") for e in deployment["spec"]["template"]["spec"]["containers"][0]["env"]}
    assert env["DISABLE_DISCOVERY"] == "true"
    assert env["CLUSTER_STATS_NAMESPACE"] == "default"
    assert env["NAMESPACE_DATA_MODE"] == "namespaced"
    assert env["HOLMES_DISCOVERY_NAMESPACE"] == "default"
    assert env["DISABLE_PROMETHEUS_DISCOVERY"] == "true"
    assert env["DISABLE_ALERTMANAGER_DISCOVERY"] == "true"


def test_default_rbac_has_no_scoped_env_or_role():
    docs = render_chart()
    assert get_doc(docs, "Role", "runner-role") is None
    assert get_doc(docs, "RoleBinding", "runner-role-binding") is None
    deployment = get_doc(docs, "Deployment", "runner")
    env_names = {e["name"] for e in deployment["spec"]["template"]["spec"]["containers"][0]["env"]}
    assert "DISABLE_DISCOVERY" not in env_names
    assert "CLUSTER_STATS_NAMESPACE" not in env_names


def render_forwarder_chart(extra_args: Optional[List[str]] = None) -> List[dict]:
    cmd = [
        "helm",
        "template",
        str(CHART_PATH),
        "--set",
        "clusterName=test",
        "--set",
        "sinksConfig[0].file_sink.name=test",
        "-s",
        "templates/forwarder.yaml",
        "-s",
        "templates/forwarder-service-account.yaml",
        "-s",
        "templates/kubewatch-configmap.yaml",
    ] + (extra_args or [])
    output = subprocess.check_output(cmd, text=True)
    return [doc for doc in yaml.safe_load_all(output) if doc]


def test_kubewatch_enabled_by_default():
    docs = render_forwarder_chart()
    assert get_doc(docs, "Deployment", "forwarder") is not None
    assert get_doc(docs, "Service", "forwarder") is not None
    assert get_doc(docs, "ConfigMap", "kubewatch-config") is not None
    assert get_doc(docs, "ServiceAccount", "forwarder-service-account") is not None
    assert get_doc(docs, "ClusterRole", "forwarder-cluster-role") is not None
    assert get_doc(docs, "ClusterRoleBinding", "forwarder-cluster-role-binding") is not None


def test_kubewatch_disabled_removes_everything():
    docs = render_forwarder_chart(["--set", "kubewatch.enabled=false"])
    assert docs == [], f"kubewatch.enabled=false should render no forwarder resources, got: {docs}"


def test_override_cluster_roles_still_replaces_rules():
    docs = render_chart(
        [
            "--set",
            "runner.overrideClusterRoles[0].apiGroups[0]=",
            "--set",
            "runner.overrideClusterRoles[0].resources[0]=pods",
            "--set",
            "runner.overrideClusterRoles[0].verbs[0]=get",
        ]
    )
    cluster_role = get_doc(docs, "ClusterRole", "runner-cluster-role")
    assert cluster_role["rules"] == [{"apiGroups": [""], "resources": ["pods"], "verbs": ["get"]}]


def holmes_pod_annotations(extra_args: Optional[List[str]] = None) -> dict:
    cmd = [
        "helm",
        "template",
        str(CHART_PATH),
        "--set",
        "enableHolmesGPT=true",
        "--set",
        "clusterName=test",
        "--set",
        "sinksConfig[0].robusta_sink.name=robusta_ui_sink",
        "--set",
        "sinksConfig[0].robusta_sink.token=token",
        "-s",
        "charts/holmes/templates/holmes.yaml",
    ] + (extra_args or [])
    docs = [doc for doc in yaml.safe_load_all(subprocess.check_output(cmd, text=True)) if doc]
    return get_doc(docs, "Deployment", "holmes")["spec"]["template"]["metadata"]["annotations"]


def robusta_config_checksum(extra_args: Optional[List[str]] = None) -> str:
    return holmes_pod_annotations(extra_args)["checksum/robusta-config"]


def test_holmes_rolls_when_its_robusta_config_changes():
    baseline = robusta_config_checksum()
    assert robusta_config_checksum(["--set", "clusterName=renamed"]) != baseline
    assert robusta_config_checksum(["--set", "globalConfig.cluster_name=renamed"]) != baseline
    assert robusta_config_checksum(["--set", "sinksConfig[0].robusta_sink.token=rotated"]) != baseline


def test_holmes_rolls_when_the_legacy_robusta_api_key_changes():
    # A robustaApiKey replaces sinksConfig in the rendered config.
    legacy = ["--set", "robustaApiKey=token"]
    assert robusta_config_checksum(legacy) != robusta_config_checksum(legacy + ["--set", "robustaApiKey=rotated"])


def test_holmes_ignores_robusta_config_it_does_not_read():
    baseline = robusta_config_checksum()
    assert robusta_config_checksum(["--set", "clusterZone=zone"]) == baseline
    assert robusta_config_checksum(["--set", "disabledPlaybooks[0]=WeeklyKRRScan"]) == baseline


def test_holmes_robusta_config_checksum_keeps_user_pod_annotations():
    annotations = holmes_pod_annotations(["--set", "holmes.podAnnotations.team=sre"])
    assert annotations["team"] == "sre"
    assert "checksum/robusta-config" in annotations
