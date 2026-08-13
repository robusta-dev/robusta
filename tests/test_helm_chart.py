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
