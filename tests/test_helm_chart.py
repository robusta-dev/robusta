import base64
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent / "helm" / "robusta"

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary not available")


READ_ONLY_VERBS = {"get", "list", "watch"}


RBAC_FLAGS = [
    "enablePodDelete",
    "enableJobDelete",
    "enableNodeEdit",
    "enablePodEvict",
    "enableRobustaConfigMapCreate",
    "enableRobustaConfigMapEdit",
]


KRR_CRONJOB_DISABLED = ["--set", "runner.krrCronJob.enabled=false"]


def render_chart(extra_args: Optional[List[str]] = None) -> List[dict]:
    cmd = [
        "helm",
        "template",
        str(CHART_PATH),
        "--set",
        "clusterName=test",
        "--set",
        "sinksConfig[0].robusta_sink.name=robusta_ui_sink",
        "-s",
        "templates/runner-service-account.yaml",
        "-s",
        "templates/runner.yaml",
    ] + (extra_args or [])
    output = subprocess.check_output(cmd, text=True)
    return [doc for doc in yaml.safe_load_all(output) if doc]


def enable(*flags: str) -> List[str]:
    return [arg for flag in flags for arg in ("--set", f"runner.rbac.{flag}=true")]


def runner_config(extra_args: Optional[List[str]] = None) -> dict:
    cmd = [
        "helm",
        "template",
        str(CHART_PATH),
        "--set",
        "clusterName=test",
        "--set",
        "sinksConfig[0].robusta_sink.name=robusta_ui_sink",
        "--set",
        "enablePlatformPlaybooks=true",
        "-s",
        "templates/playbooks-config.yaml",
    ] + (extra_args or [])
    docs = [doc for doc in yaml.safe_load_all(subprocess.check_output(cmd, text=True)) if doc]
    return yaml.safe_load(base64.b64decode(docs[0]["data"]["active_playbooks.yaml"]).decode())


def playbook_names(extra_args: Optional[List[str]] = None) -> set:
    return {p.get("name") for p in runner_config(extra_args)["active_playbooks"]}


def write_rules(docs: List[dict]) -> set:
    granted = set()
    for doc in docs:
        if doc["kind"] not in ("Role", "ClusterRole"):
            continue
        for rule in doc["rules"]:
            for verb in set(rule["verbs"]) - READ_ONLY_VERBS:
                granted.update((doc["kind"], resource, verb) for resource in rule["resources"])
    return granted


def get_doc(docs: List[dict], kind: str, name_contains: str = "") -> Optional[dict]:
    for doc in docs:
        if doc["kind"] == kind and name_contains in doc["metadata"]["name"]:
            return doc
    return None


def test_runner_clusterrole_verbs():
    docs = render_chart()
    cluster_role = get_doc(docs, "ClusterRole", "runner-cluster-role")
    assert cluster_role is not None

    violations = [rule for rule in cluster_role["rules"] if not set(rule["verbs"]) <= READ_ONLY_VERBS]
    assert not violations, f"ClusterRole grants write verbs: {violations}"


def test_runner_clusterrole_no_cluster_wide_pod_exec():
    docs = render_chart()
    cluster_role = get_doc(docs, "ClusterRole", "runner-cluster-role")
    for rule in cluster_role.get("rules", []):
        assert "pods/exec" not in rule.get("resources", []), f"pods/exec must not be cluster-wide: {rule}"


def test_default_render_has_no_write_rules():
    docs = render_chart()
    assert get_doc(docs, "Role", "runner-local-role") is None
    assert write_rules(docs) == set()

    config = runner_config()
    names = {p.get("name") for p in config["active_playbooks"]}
    assert not names & {"NodeFSSpaceAlerts", "WeeklyKRRScan", "RobustaMaintenance"}
    assert not set(config["light_actions"]) & {"delete_pod", "delete_job", "drain", "krr_scan", "pod_ps", "rollout_restart"}

    env = get_doc(docs, "Deployment", "runner")["spec"]["template"]["spec"]["containers"][0]["env"]
    assert {"name": "ENABLE_POD_DELETE", "value": "false"} in env


def test_all_flags_grant_only_listed_write_rules():
    optional_rules = [
        "--set", "enabledManagedConfiguration=true",
        "--set", "openshift.enabled=true",
        "--set", "argoRollouts=true",
        "--set", "runner.customCRD={StrimziPodSet,CNPGCluster,ExecutionContext}",
        "--api-versions", "snapshot.storage.k8s.io/v1/VolumeSnapshot",
    ]
    docs = render_chart(enable(*RBAC_FLAGS) + KRR_CRONJOB_DISABLED + optional_rules)
    assert write_rules(docs) == {
        ("ClusterRole", "nodes", "patch"),
        ("ClusterRole", "pods/eviction", "create"),
        ("ClusterRole", "pods", "delete"),
        ("ClusterRole", "jobs", "delete"),
        ("Role", "configmaps", "create"),
        ("Role", "configmaps", "update"),
        ("ClusterRole", "securitycontextconstraints", "use"),
        ("ClusterRole", "prometheusrules", "create"),
        ("ClusterRole", "prometheusrules", "delete"),
        ("ClusterRole", "prometheusrules", "patch"),
        ("ClusterRole", "prometheusrules", "update"),
    }
    configmap_update = [rule for rule in get_doc(docs, "Role", "runner-local-role")["rules"] if "update" in rule["verbs"]]
    assert configmap_update[0]["resourceNames"] == ["scheduled-jobs"]

    light_actions = runner_config(enable(*RBAC_FLAGS))["light_actions"]
    assert {"delete_pod", "delete_job", "drain", "cordon"} <= set(light_actions)
    assert not {"rollout_restart", "krr_scan", "popeye_scan", "pod_ps"} & set(light_actions)
    assert "drain" not in runner_config(enable("enableNodeEdit"))["light_actions"]


def test_no_create_setting_overrides_configmap_flags():
    no_create = enable(*RBAC_FLAGS) + ["--set", "runner.rbac.disableCreateFromServiceAccount=true"]
    docs = render_full_chart(no_create)
    assert get_doc(docs, "Role", "runner-local-role") is None
    assert get_doc(docs, "CronJob", "robusta-krr") is None
    assert not {"NodeFSSpaceAlerts", "WeeklyKRRScan", "RobustaMaintenance"} & playbook_names(no_create)
    env = get_doc(docs, "Deployment", "robusta-runner")["spec"]["template"]["spec"]["containers"][0]["env"]
    assert {"name": "DISABLE_CREATE_FROM_SERVICE_ACCOUNT", "value": "true"} in env


def test_default_read_rules():
    docs = render_chart()
    rules = get_doc(docs, "ClusterRole", "runner-cluster-role")["rules"]
    resources = [(group, resource) for rule in rules for group in rule["apiGroups"] for resource in rule["resources"]]
    assert len(resources) == len(set(resources))
    assert not {"configmaps", "serviceaccounts", "podsecuritypolicies"} & {resource for _, resource in resources}
    optional_groups = ("argoproj.io", "fluxcd.io", "strimzi.io", "keda.sh", "crossplane.io", "istio.io", "velero.io")
    assert not [group for group, _ in resources if group == "extensions" or group.endswith(optional_groups)]


def test_optional_crd_read_rules():
    docs = render_chart(["--set", "runner.crdPermissions.flux=true", "--set", "runner.crdPermissions.externalSecrets=true"])
    groups = {group for rule in get_doc(docs, "ClusterRole", "runner-cluster-role")["rules"] for group in rule["apiGroups"]}
    assert "helm.toolkit.fluxcd.io" in groups
    assert "external-secrets.io" not in groups


def test_scheduled_jobs_configmap_read_rule():
    rules = get_doc(render_chart(enable("enableRobustaConfigMapEdit")), "Role", "runner-local-role")["rules"]
    assert rules == [{"apiGroups": [""], "resources": ["configmaps"], "resourceNames": ["scheduled-jobs"], "verbs": ["get", "update"]}]


def test_job_creating_playbooks_always_disabled():
    names = playbook_names(enable(*RBAC_FLAGS) + KRR_CRONJOB_DISABLED)
    assert not {"NodeFSSpaceAlerts", "WeeklyKRRScan", "RobustaMaintenance"} & names


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
        "sinksConfig[0].robusta_sink.name=robusta_ui_sink",
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


def render_full_chart(extra_args: Optional[List[str]] = None) -> List[dict]:
    cmd = [
        "helm",
        "template",
        "robusta",
        str(CHART_PATH),
        "--set",
        "clusterName=test",
        "--set",
        "sinksConfig[0].robusta_sink.name=robusta_ui_sink",
        "--set",
        "enablePrometheusStack=false",
    ] + (extra_args or [])
    return [doc for doc in yaml.safe_load_all(subprocess.check_output(cmd, text=True)) if doc]


def krr_container(docs: List[dict]) -> dict:
    cron_job = get_doc(docs, "CronJob", "robusta-krr")
    return cron_job["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]


def krr_arguments(tmp_path, extra_args: Optional[List[str]] = None, env: Optional[dict] = None) -> List[str]:
    """Runs the CronJob command with a stand-in python and returns the arguments krr.py would get."""
    container = krr_container(render_full_chart(extra_args))
    python_stub = tmp_path / "python"
    python_stub.write_text('#!/bin/sh\nif [ "$1" = -c ]; then echo generated; exit; fi\nprintf "%s\\n" "$@"\n')
    python_stub.chmod(0o755)
    process_env = {"PATH": f"{tmp_path}:{os.environ['PATH']}", **(env or {})}
    return subprocess.check_output(container["command"], text=True, env=process_env).splitlines()


def flag_values(arguments: List[str], flag: str) -> List[str]:
    return [arguments[index + 1] for index, argument in enumerate(arguments) if argument == flag]


def test_krr_cronjob_default_resources():
    docs = render_full_chart()
    cron_job = get_doc(docs, "CronJob", "robusta-krr")
    assert cron_job["spec"]["schedule"] == "0 12 * * 1"
    assert cron_job["spec"]["concurrencyPolicy"] == "Forbid"
    pod_spec = cron_job["spec"]["jobTemplate"]["spec"]["template"]["spec"]
    assert pod_spec["serviceAccountName"] == "robusta-runner-service-account"

    runner_env = get_doc(docs, "Deployment", "robusta-runner")["spec"]["template"]["spec"]["containers"][0]["env"]
    assert {"name": "KRR_CRONJOB_ENABLED", "value": "true"} in runner_env

    created = set()
    for doc in docs:
        if doc["kind"] in ("Role", "ClusterRole") and "runner" in doc["metadata"]["name"]:
            created.update(*(rule["resources"] for rule in doc["rules"] if "create" in rule["verbs"]))
    assert "secrets" not in created


def test_krr_cronjob_disabled():
    docs = render_full_chart(KRR_CRONJOB_DISABLED)
    assert get_doc(docs, "CronJob", "robusta-krr") is None
    env_names = {e["name"] for e in get_doc(docs, "Deployment", "robusta-runner")["spec"]["template"]["spec"]["containers"][0]["env"]}
    assert "KRR_CRONJOB_ENABLED" not in env_names


def test_krr_cronjob_kept_without_runner_role():
    docs = render_full_chart()
    assert get_doc(docs, "CronJob", "robusta-krr") is not None
    assert get_doc(docs, "Role", "runner-local-role") is None


def test_krr_cronjob_off_without_runner_role():
    no_create = ["--set", "runner.rbac.disableCreateFromServiceAccount=true"]
    assert get_doc(render_full_chart(no_create), "CronJob", "robusta-krr") is None
    docs = render_full_chart(no_create + ["--set", "runner.krrCronJob.enabled=true"])
    assert get_doc(docs, "CronJob", "robusta-krr") is not None
    assert get_doc(docs, "Role", "runner-local-role") is None


def test_krr_cronjob_default_arguments(tmp_path):
    arguments = krr_arguments(tmp_path)
    assert arguments[:5] == [
        "krr.py",
        "simple",
        "--publish_scan_url=http://robusta-runner.default.svc.cluster.local/api/trigger",
        "--scan_id=generated",
        "--start_time=generated",
    ]
    assert arguments[5:] == ["--named_sinks=robusta_ui_sink", "--max-workers", "3", "-f", "json", "--width", "2048"]


SCHEDULED_KRR_PLAYBOOK = [
    "--set",
    "customPlaybooks[0].triggers[0].on_schedule.fixed_delay_repeat.seconds_delay=3600",
    "--set-json",
    "customPlaybooks[0].actions[0].krr_scan={}",
]


def test_scheduled_krr_playbook_renders_with_cronjob():
    docs = render_full_chart(SCHEDULED_KRR_PLAYBOOK)
    assert get_doc(docs, "CronJob", "robusta-krr") is not None


def test_scheduled_krr_playbook_kept_without_cronjob():
    docs = render_full_chart(KRR_CRONJOB_DISABLED + SCHEDULED_KRR_PLAYBOOK)
    assert get_doc(docs, "CronJob", "robusta-krr") is None


def krr_job_template(extra_args: List[str]) -> dict:
    docs = render_full_chart(extra_args)
    return get_doc(docs, "CronJob", "robusta-krr")["spec"]["jobTemplate"]


def test_krr_cronjob_keeps_job_labels_and_defaults():
    job = krr_job_template([])
    pod = job["spec"]["template"]
    assert job["metadata"]["labels"] == pod["metadata"]["labels"] == {"app": "krr.robusta.dev"}
    assert job["spec"]["backoffLimit"] == 0
    assert job["spec"]["ttlSecondsAfterFinished"] == 43200
    assert job["spec"]["activeDeadlineSeconds"] == 3600
    container = pod["spec"]["containers"][0]
    assert container["image"] == "robustadev/krr:v1.30.0"
    assert container["imagePullPolicy"] == "Always"
    assert container["resources"] == {"requests": {"memory": "2Gi"}, "limits": {"memory": "2Gi"}}
    assert "securityContext" not in container
    assert pod["spec"]["restartPolicy"] == "Never"


def test_krr_cronjob_needs_robusta_sink():
    docs = render_full_chart(["--set", "sinksConfig[0].robusta_sink=null", "--set", "sinksConfig[0].file_sink.name=test"])
    assert get_doc(docs, "CronJob", "robusta-krr") is None


def test_krr_cronjob_follows_disabled_weekly_playbook():
    docs = render_full_chart(["--set", "disabledPlaybooks[0]=WeeklyKRRScan"])
    assert get_doc(docs, "CronJob", "robusta-krr") is None


def test_krr_cronjob_image_pull_secrets():
    runner_secrets = ["--set", "runner.imagePullSecrets[0].name=runner-registry"]
    pod_spec = krr_job_template(runner_secrets)["spec"]["template"]["spec"]
    assert pod_spec["imagePullSecrets"] == [{"name": "runner-registry"}]

    job_spec_secrets = ["--set", "runner.krrCronJob.jobSpec.imagePullSecrets[0].name=krr-registry"]
    pod_spec = krr_job_template(runner_secrets + job_spec_secrets)["spec"]["template"]["spec"]
    assert pod_spec["imagePullSecrets"] == [{"name": "krr-registry"}]

    assert "imagePullSecrets" not in krr_job_template([])["spec"]["template"]["spec"]


def test_scan_actions_not_in_light_actions():
    light_actions = yaml.safe_load((CHART_PATH / "values.yaml").read_text())["lightActions"]
    assert not {"krr_scan", "popeye_scan"} & set(light_actions)


def test_krr_cronjob_own_settings(tmp_path):
    extra_args = [
        "--set", "globalConfig.prometheus_url=http://prometheus:9090",
        "--set", "runner.krrCronJob.strategy=simple_limit",
        "--set", "runner.krrCronJob.timeout=600",
        "--set", "runner.krrCronJob.image=registry.example/krr:v1",
        "--set", "runner.krrCronJob.memoryLimit=3Gi",
        "--set", "runner.krrCronJob.jobSpec.nodeSelector.pool=scans",
        "--set", "runner.krrCronJob.annotations.team=test",
        "--set", "runner.krrCronJob.serviceAccountName=krr-scan",
        "--set", "runner.krrCronJob.additional_env_vars[0].name=PROMETHEUS_TOKEN",
        "--set", "runner.krrCronJob.additional_env_vars[0].valueFrom.secretKeyRef.name=prometheus",
        "--set", "runner.krrCronJob.additional_env_vars[0].valueFrom.secretKeyRef.key=token",
        "--set", "runner.krrCronJob.additional_env_froms[0].secretRef.name=krr-env",
        "--set-string", 'runner.krrCronJob.krrArgs=--allow-hpa --prometheus-auth-header "Bearer $PROMETHEUS_TOKEN"',
    ]
    arguments = krr_arguments(tmp_path, extra_args, env={"PROMETHEUS_TOKEN": "example-token"})
    assert arguments[1] == "simple_limit"
    assert flag_values(arguments, "-p") == ["http://prometheus:9090"]
    assert flag_values(arguments, "--prometheus-auth-header") == ["Bearer example-token"]
    assert "--allow-hpa" in arguments

    job = krr_job_template(extra_args)
    pod_spec = job["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]
    assert job["spec"]["activeDeadlineSeconds"] == 600
    assert pod_spec["nodeSelector"] == {"pool": "scans"}
    assert pod_spec["serviceAccountName"] == "krr-scan"
    assert job["metadata"]["annotations"] == job["spec"]["template"]["metadata"]["annotations"] == {"team": "test"}
    assert container["image"] == "registry.example/krr:v1"
    assert container["resources"] == {"requests": {"memory": "2Gi"}, "limits": {"memory": "3Gi"}}
    assert [var["name"] for var in container["env"]] == ["PROMETHEUS_TOKEN"]
    assert container["envFrom"] == [{"secretRef": {"name": "krr-env"}}]


def test_krr_cronjob_uses_only_prometheus_url_from_other_settings(tmp_path):
    other_settings = [
        "--set", "globalConfig.prometheus_url=http://prometheus:9090",
        "--set", "globalConfig.prometheus_auth=Bearer example-token",
        "--set", "globalConfig.prometheus_additional_headers.X-Scope-OrgID=1",
        "--set", "globalConfig.prometheus_additional_labels.cluster=test",
        "--set", "globalConfig.krr_args=--allow-hpa",
        "--set", "globalConfig.krr_job_spec.nodeSelector.pool=scans",
        "--set", "globalConfig.custom_annotations.team=test",
        "--set", "globalConfig.strategy=simple_limit",
        "--set", "globalConfig.max_workers=1",
        "--set", "globalConfig.timeout=60",
        "--set", "openshift.enabled=true",
        "--set", "runner.additional_env_vars[0].name=KRR_MEMORY_LIMIT",
        "--set", "runner.additional_env_vars[0].value=5Gi",
        "--set", "runner.additional_env_froms[0].secretRef.name=runner-env",
    ]
    default_job = krr_job_template(["--set", "globalConfig.prometheus_url=http://prometheus:9090"])
    assert krr_job_template(other_settings) == default_job
    assert flag_values(krr_arguments(tmp_path, other_settings), "-p") == ["http://prometheus:9090"]
    assert not [doc for doc in render_full_chart(other_settings) if "krr-prometheus" in doc["metadata"]["name"]]


def test_command_actions_value_reaches_the_runner_config():
    assert runner_config()["command_actions"] == []
    platform = ["--set", "enablePlatformPlaybooks=true"]
    assert runner_config(platform)["command_actions"] == []
    assert runner_config(platform + ["--set", "commandActions={kubectl_command}"])["command_actions"] == ["kubectl_command"]
    enabled = runner_config(["--set", "commandActions={pod_bash_enricher,kubectl_command}"])
    assert enabled["command_actions"] == ["pod_bash_enricher", "kubectl_command"]
