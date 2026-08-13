"""
Tests for the RBAC the Helm chart generates for the runner ServiceAccount.

The runner's ClusterRole is bound cluster-wide, so every write verb in it applies to every
namespace. Verbs Robusta only ever uses inside its own release namespace must therefore live in
the namespaced Role instead, otherwise the runner's token is a privilege-escalation primitive
(create a Deployment/Job with an arbitrary pod spec in kube-system => cluster-admin).
"""

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest
import yaml

CHART_PATH = Path(__file__).parent.parent / "helm" / "robusta"
TEMPLATE = "templates/runner-service-account.yaml"

# minimal values needed for the chart to render at all
BASE_ARGS = ["--set", "clusterName=test-cluster", "--set", "robustaApiKey=fake-token"]

READ_ONLY_VERBS = {"get", "list", "watch"}

# (apiGroup, resource, verb) triples that must never be granted cluster-wide, and the actions
# that legitimately need them inside the release namespace
NAMESPACED_ONLY_GRANTS = [
    ("", "secrets", "create"),  # RobustaJob.create_job_owned_secret
    ("apps", "deployments", "create"),  # generate_high_cpu
    ("apps", "deployments", "delete"),  # generate_high_cpu
    ("", "configmaps", "create"),  # ScheduledJobsStatesDal
    ("", "configmaps", "update"),  # ScheduledJobsStatesDal
]


@pytest.fixture(scope="module", autouse=True)
def _requires_helm():
    if shutil.which("helm") is None:
        pytest.skip("helm binary not available", allow_module_level=True)


def render(*extra_args: str) -> List[dict]:
    """Render the runner ServiceAccount template and return its Kubernetes objects."""
    output = subprocess.check_output(
        ["helm", "template", "robusta", str(CHART_PATH), "-s", TEMPLATE, *BASE_ARGS, *extra_args],
        text=True,
        stderr=subprocess.PIPE,
    )
    return [doc for doc in yaml.safe_load_all(output) if doc]


def by_kind(objects: List[dict]) -> Dict[str, dict]:
    return {obj["kind"]: obj for obj in objects}


def grants(role: dict) -> Set[Tuple[str, str, str]]:
    """Flatten a Role/ClusterRole into (apiGroup, resource, verb) triples."""
    result = set()
    for rule in role["rules"]:
        for api_group in rule["apiGroups"]:
            for resource in rule["resources"]:
                for verb in rule["verbs"]:
                    result.add((api_group, resource, verb))
    return result


def test_runner_clusterrole_no_cluster_wide_secret_create():
    """secrets:create and deployments:create must be namespaced (Role), not in the ClusterRole."""
    objects = by_kind(render())
    cluster_wide = grants(objects["ClusterRole"])
    namespaced = grants(objects["Role"])

    for grant in NAMESPACED_ONLY_GRANTS:
        assert grant not in cluster_wide, f"{grant} is granted cluster-wide"
        assert grant in namespaced, f"{grant} is missing from the namespaced Role"


def test_runner_clusterrole_grants_no_cluster_wide_pod_spec_creation():
    """Creating an arbitrary pod spec in any namespace is a path to cluster-admin."""
    cluster_wide = grants(by_kind(render())["ClusterRole"])
    for resource in ["deployments", "daemonsets", "statefulsets", "replicasets", "cronjobs"]:
        for api_group in ["apps", "batch", "extensions"]:
            assert (api_group, resource, "create") not in cluster_wide


def test_runner_clusterrole_keeps_reads_cluster_wide():
    """Narrowing writes must not break cluster-wide discovery, which the runner depends on."""
    cluster_wide = grants(by_kind(render())["ClusterRole"])
    for resource in ["pods", "configmaps", "namespaces", "events"]:
        for verb in READ_ONLY_VERBS:
            assert ("", resource, verb) in cluster_wide
    assert ("", "nodes", "list") in cluster_wide
    assert ("apps", "deployments", "list") in cluster_wide
    assert ("batch", "jobs", "list") in cluster_wide


def test_runner_role_is_bound_to_the_release_namespace():
    objects = by_kind(render("--namespace", "robusta-system"))
    role = objects["Role"]
    binding = objects["RoleBinding"]

    assert role["metadata"]["namespace"] == "robusta-system"
    assert binding["metadata"]["namespace"] == "robusta-system"
    assert binding["roleRef"]["kind"] == "Role"
    assert binding["roleRef"]["name"] == role["metadata"]["name"]
    assert binding["subjects"] == [
        {
            "kind": "ServiceAccount",
            "name": objects["ServiceAccount"]["metadata"]["name"],
            "namespace": "robusta-system",
        }
    ]


def test_runner_role_can_run_robustas_own_jobs_and_debug_pods():
    """KRR/Popeye jobs and the debug pods must keep working without any cluster-wide write."""
    namespaced = grants(by_kind(render("--set", "runner.clusterWideWriteAccess=false"))["Role"])
    for grant in [
        ("batch", "jobs", "create"),  # KRR, Popeye, kubectl enrichments
        ("batch", "jobs", "delete"),
        ("", "pods", "create"),  # debugger pods
        ("", "pods", "delete"),
        ("", "pods", "patch"),  # clearing job pod finalizers
        ("", "pods/exec", "get"),  # exec into the debugger pod (python client uses GET)
        ("", "pods/exec", "create"),  # `kubectl exec` from kubectl enrichments
        ("", "secrets", "create"),  # job owned secrets
        ("", "persistentvolumeclaims", "create"),  # disk_benchmark
    ]:
        assert grant in namespaced, f"{grant} is missing from the namespaced Role"


@pytest.mark.parametrize(
    "extra_args",
    [
        pytest.param([], id="defaults"),
        pytest.param(
            ["--set", "argoRollouts=true", "--set", "runner.customCRD[0]=StrimziPodSet"],
            id="optional-crds",
        ),
    ],
)
def test_cluster_wide_write_access_disabled_leaves_a_read_only_clusterrole(extra_args):
    objects = by_kind(render("--set", "runner.clusterWideWriteAccess=false", *extra_args))
    cluster_wide = grants(objects["ClusterRole"])
    write_verbs = {grant for grant in cluster_wide if grant[2] not in READ_ONLY_VERBS}
    assert write_verbs == set(), f"unexpected cluster-wide write verbs: {sorted(write_verbs)}"

    # exec is opened with a GET by the python client, so read verbs are not harmless here
    assert not [grant for grant in cluster_wide if grant[1] == "pods/exec"]

    # the writes did not disappear, they moved into the release namespace
    namespaced = grants(objects["Role"])
    assert ("", "pods/exec", "get") in namespaced
    assert ("apps", "deployments", "patch") in namespaced


def test_cluster_wide_write_access_enabled_by_default():
    """The default must stay backwards compatible: remediation actions work in every namespace."""
    cluster_wide = grants(by_kind(render())["ClusterRole"])
    for grant in [
        ("", "pods", "delete"),  # delete_pod
        ("", "pods/exec", "get"),  # pod_bash_enricher
        ("", "pods/exec", "create"),
        ("", "pods/eviction", "create"),  # drain
        ("", "nodes", "patch"),  # cordon / uncordon
        ("apps", "deployments", "patch"),  # rollout_restart
        ("apps", "statefulsets", "patch"),
        ("apps", "daemonsets", "patch"),
        ("batch", "jobs", "create"),  # job_restart_on_oomkilled_community
        ("autoscaling", "horizontalpodautoscalers", "update"),  # scale_hpa_callback
    ]:
        assert grant in cluster_wide, f"{grant} is missing from the ClusterRole"


def test_managed_configuration_prometheusrules_are_namespaced():
    """The runner only reads and writes PrometheusRules in its own namespace."""
    objects = by_kind(render("--set", "enabledManagedConfiguration=true"))
    assert ("monitoring.coreos.com", "prometheusrules", "create") in grants(objects["Role"])
    assert ("monitoring.coreos.com", "prometheusrules", "create") not in grants(objects["ClusterRole"])


def test_override_cluster_roles_replaces_all_rbac():
    """A read-only runner must not get write permissions back through the namespaced Role."""
    override = "runner.overrideClusterRoles[0]"
    objects = by_kind(
        render(
            "--set",
            f"{override}.apiGroups[0]=",
            "--set",
            f"{override}.resources[0]=pods",
            "--set",
            f"{override}.verbs[0]=get",
        )
    )
    assert grants(objects["ClusterRole"]) == {("", "pods", "get")}
    assert "Role" not in objects
    assert "RoleBinding" not in objects
