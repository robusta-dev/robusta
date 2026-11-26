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

# drain needs eviction; it cannot create workloads
ALLOWED_CLUSTER_WIDE_CREATE = {"pods/eviction"}
KRR_CRONJOB_DISABLED = ["--set", "runner.krrCronJob.enabled=false"]


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
        "jobs",
        "deployments",
    } <= granted
    assert "secrets" not in granted

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
    assert "WeeklyKRRScan" not in names
    assert "WeeklyKRRScan" in playbook_names(KRR_CRONJOB_DISABLED)


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


def render_full_chart(extra_args: Optional[List[str]] = None) -> List[dict]:
    cmd = [
        "helm",
        "template",
        "robusta",
        str(CHART_PATH),
        "--set",
        "clusterName=test",
        "--set",
        "sinksConfig[0].file_sink.name=test",
        "--set",
        "enablePrometheusStack=false",
    ] + (extra_args or [])
    return [doc for doc in yaml.safe_load_all(subprocess.check_output(cmd, text=True)) if doc]


def krr_container(docs: List[dict]) -> dict:
    cron_job = get_doc(docs, "CronJob", "robusta-krr")
    return cron_job["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]


def krr_arguments(tmp_path, extra_args: Optional[List[str]] = None, env: Optional[dict] = None) -> List[str]:
    """Runs the CronJob command with a stand-in python and returns the arguments krr.py would get."""
    docs = render_full_chart((extra_args or []))
    container = krr_container(docs)
    secret_env = {
        var["name"]: get_doc(docs, "Secret", var["valueFrom"]["secretKeyRef"]["name"])["stringData"][
            var["valueFrom"]["secretKeyRef"]["key"]
        ]
        for var in container["env"] or []
        if "valueFrom" in var
    }
    python_stub = tmp_path / "python"
    python_stub.write_text('#!/bin/sh\nif [ "$1" = -c ]; then echo generated; exit; fi\nprintf "%s\\n" "$@"\n')
    python_stub.chmod(0o755)
    process_env = {"PATH": f"{tmp_path}:{os.environ['PATH']}", **secret_env, **(env or {})}
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


def test_krr_cronjob_disabled_keeps_runner_scan():
    docs = render_full_chart(KRR_CRONJOB_DISABLED)
    assert get_doc(docs, "CronJob", "robusta-krr") is None
    env_names = {e["name"] for e in get_doc(docs, "Deployment", "robusta-runner")["spec"]["template"]["spec"]["containers"][0]["env"]}
    assert "KRR_CRONJOB_ENABLED" not in env_names
    rules = get_doc(docs, "Role", "runner-local-role")["rules"]
    assert any("secrets" in rule["resources"] and "create" in rule["verbs"] for rule in rules)


def test_krr_cronjob_kept_without_runner_role():
    docs = render_full_chart(["--set", "runner.rbac.disableCreateFromServiceAccount=true"])
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


def test_krr_cronjob_prometheus_url_and_krr_settings(tmp_path):
    arguments = krr_arguments(
        tmp_path,
        [
            "--set",
            "globalConfig.prometheus_url=http://prometheus:9090",
            "--set",
            "globalConfig.krr_args=--allow-hpa",
            "--set",
            "runner.krrCronJob.maxWorkers=2",
            "--set",
            "runner.krrCronJob.verbose=true",
        ],
        env={"KRR_STRATEGY": "simple_limit"},
    )
    assert arguments[1] == "simple_limit"
    assert flag_values(arguments, "-p") == ["http://prometheus:9090"]
    assert flag_values(arguments, "--max-workers") == ["2"]
    assert "--allow-hpa" in arguments and "-v" in arguments


def test_krr_cronjob_literal_prometheus_auth(tmp_path):
    extra_args = ["--set-string", "globalConfig.prometheus_auth=Bearer abc"]
    assert flag_values(krr_arguments(tmp_path, extra_args), "--prometheus-auth-header") == ["Bearer abc"]

    docs = render_full_chart(extra_args)
    assert get_doc(docs, "Secret", "robusta-krr-prometheus")["stringData"] == {"PROMETHEUS_AUTH_HEADER": "Bearer abc"}
    assert "Bearer abc" not in krr_container(docs)["command"][2]


def test_krr_cronjob_prometheus_auth_from_env(tmp_path):
    arguments = krr_arguments(
        tmp_path,
        ["--set-string", "globalConfig.prometheus_auth=Basic \\{\\{ env.PROM_AUTH \\}\\}"],
        env={"PROM_AUTH": "xyz"},
    )
    assert flag_values(arguments, "--prometheus-auth-header") == ["Basic xyz"]


def test_krr_cronjob_prometheus_auth_from_existing_secret():
    docs = render_full_chart(
        ["--set", "runner.krrCronJob.prometheusAuthSecret.name=prom", "--set", "runner.krrCronJob.prometheusAuthSecret.key=auth"]
    )
    auth_reference = {"secretKeyRef": {"name": "prom", "key": "auth"}}
    assert {"name": "PROMETHEUS_AUTH_HEADER", "valueFrom": auth_reference} in krr_container(docs)["env"]


def test_krr_cronjob_additional_headers_and_label(tmp_path):
    extra_args = [
        "--set-string",
        "globalConfig.prometheus_additional_headers.X-Scope-OrgID=tenant",
        "--set-string",
        "globalConfig.prometheus_additional_headers.X-Other=value",
        "--set-string",
        "globalConfig.prometheus_additional_labels.cluster=prod",
    ]
    arguments = krr_arguments(tmp_path, extra_args)
    assert flag_values(arguments, "--prometheus-headers") == ["X-Other:value", "X-Scope-OrgID:tenant"]
    assert flag_values(arguments, "--prometheus-label") == ["cluster"]
    assert flag_values(arguments, "-l") == ["prod"]

    with_label_in_args = krr_arguments(tmp_path, extra_args + ["--set", "runner.krrCronJob.krrArgs=-l other"])
    assert "--prometheus-label" not in with_label_in_args


def test_krr_cronjob_header_name_format():
    with pytest.raises(subprocess.CalledProcessError):
        render_full_chart(
            ["--set-string", "globalConfig.prometheus_additional_headers.bad name=x"]
        )


def test_krr_cronjob_aws_arguments(tmp_path):
    env = {
        "AWS_REGION": "us-east-1",
        "AWS_ASSUME_ROLE": "arn:aws:iam::1:role/r",
        "AWS_ACCESS_KEY": "key",
        "AWS_SECRET_ACCESS_KEY": "secret",
        "CORALOGIX_PROMETHEUS_TOKEN": "ignored",
    }
    arguments = krr_arguments(tmp_path, env=env)
    assert "--eks-managed-prom" in arguments
    assert flag_values(arguments, "--eks-managed-prom-region") == ["us-east-1"]
    assert flag_values(arguments, "--eks-service-name") == ["aps"]
    assert flag_values(arguments, "--eks-assume-role") == ["arn:aws:iam::1:role/r"]
    assert flag_values(arguments, "--eks-access-key") == ["key"]
    assert flag_values(arguments, "--eks-secret-key") == ["secret"]
    assert "--coralogix-token" not in arguments


def test_krr_cronjob_coralogix_arguments(tmp_path):
    arguments = krr_arguments(
        tmp_path, ["--set-string", "globalConfig.prometheus_auth=Bearer abc"], env={"CORALOGIX_PROMETHEUS_TOKEN": "cx"}
    )
    assert flag_values(arguments, "--coralogix-token") == ["cx"]
    assert flag_values(arguments, "--prometheus-auth-header") == ["Bearer cx"]


@pytest.mark.parametrize(
    "extra_args,env",
    [(["--set", "openshift.enabled=true"], {}), ([], {"PROMETHEUS_CLUSTER_TOKEN_AUTH": "true"})],
)
def test_krr_cronjob_service_account_token_auth(tmp_path, extra_args, env):
    docs = render_full_chart(extra_args)
    script = krr_container(docs)["command"][2]
    assert 'PROMETHEUS_AUTH_HEADER="Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"' in script

    openshift_env = {var["name"]: var["value"] for var in krr_container(docs)["env"] or [] if "value" in var}
    arguments = krr_arguments(tmp_path, extra_args, env={**openshift_env, **env})
    assert flag_values(arguments, "--prometheus-auth-header")[0].startswith("Bearer")


SCHEDULED_KRR_PLAYBOOK = [
    "--set",
    "customPlaybooks[0].triggers[0].on_schedule.fixed_delay_repeat.seconds_delay=3600",
    "--set-json",
    "customPlaybooks[0].actions[0].krr_scan={}",
]


def test_scheduled_krr_playbook_points_to_cronjob_values():
    result = subprocess.run(
        ["helm", "template", str(CHART_PATH), "--set", "clusterName=test", "--set", "sinksConfig[0].file_sink.name=test"]
        + SCHEDULED_KRR_PLAYBOOK,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "runner.krrCronJob.schedule" in result.stderr


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
    assert "krr:v1.30.0" in (CHART_PATH.parents[1] / "playbooks/robusta_playbooks/krr.py").read_text()
    assert container["imagePullPolicy"] == "Always"
    assert container["resources"] == {"requests": {"memory": "2Gi"}, "limits": {"memory": "2Gi"}}
    assert "securityContext" not in container
    assert pod["spec"]["restartPolicy"] == "Never"


def test_krr_cronjob_keeps_global_config_settings(tmp_path):
    extra_args = [
        "--set",
        "globalConfig.krr_args=--allow-hpa --cpu-min 15",
        "--set",
        "globalConfig.max_workers=2",
        "--set",
        "globalConfig.krr_verbose=true",
        "--set",
        "globalConfig.strategy=simple_limit",
        "--set",
        "globalConfig.timeout=7200",
        "--set",
        "globalConfig.custom_annotations.team=platform",
        "--set",
        "globalConfig.krr_job_spec.nodeSelector.pool=scans",
        "--set",
        "globalConfig.krr_job_spec.tolerations[0].key=dedicated",
        "--set",
        "globalConfig.krr_job_spec.tolerations[0].operator=Exists",
    ]
    job = krr_job_template(extra_args)
    pod = job["spec"]["template"]
    assert job["spec"]["activeDeadlineSeconds"] == 7200
    assert job["metadata"]["annotations"] == pod["metadata"]["annotations"] == {"team": "platform"}
    assert pod["spec"]["nodeSelector"] == {"pool": "scans"}
    assert pod["spec"]["tolerations"] == [{"key": "dedicated", "operator": "Exists"}]

    arguments = krr_arguments(tmp_path, extra_args)
    assert arguments[1] == "simple_limit"
    assert flag_values(arguments, "--max-workers") == ["2"]
    assert flag_values(arguments, "--cpu-min") == ["15"]
    assert "--allow-hpa" in arguments and "-v" in arguments


def test_krr_cronjob_values_take_precedence_over_global_config(tmp_path):
    extra_args = [
        "--set",
        "globalConfig.krr_args=--allow-hpa",
        "--set",
        "globalConfig.custom_annotations.team=platform",
        "--set",
        "runner.krrCronJob.krrArgs=--cpu-min 15",
        "--set",
        "runner.krrCronJob.annotations.owner=finops",
        "--set",
        "runner.krrCronJob.schedule=0 6 * * *",
        "--set",
        "runner.krrCronJob.jobSpec.priorityClassName=low",
    ]
    docs = render_full_chart(extra_args)
    cron_job = get_doc(docs, "CronJob", "robusta-krr")
    pod = cron_job["spec"]["jobTemplate"]["spec"]["template"]
    assert cron_job["spec"]["schedule"] == "0 6 * * *"
    assert pod["metadata"]["annotations"] == {"team": "platform", "owner": "finops"}
    assert pod["spec"]["priorityClassName"] == "low"

    arguments = krr_arguments(tmp_path, extra_args)
    assert flag_values(arguments, "--cpu-min") == ["15"]
    assert "--allow-hpa" not in arguments


def test_krr_cronjob_job_spec_supported_fields():
    with pytest.raises(subprocess.CalledProcessError):
        krr_job_template(["--set", "globalConfig.krr_job_spec.hostNetwork=true"])


def test_krr_cronjob_keeps_runner_env_settings(tmp_path):
    extra_args = [
        "--set",
        "runner.additional_env_vars[0].name=KRR_IMAGE_OVERRIDE",
        "--set",
        "runner.additional_env_vars[0].value=registry.local/krr:v1",
        "--set",
        "runner.additional_env_vars[1].name=KRR_MEMORY_REQUEST",
        "--set",
        "runner.additional_env_vars[1].value=1Gi",
        "--set",
        "runner.additional_env_vars[2].name=KRR_MEMORY_LIMIT",
        "--set",
        "runner.additional_env_vars[2].value=3Gi",
        "--set",
        "runner.additional_env_vars[3].name=HTTPS_PROXY",
        "--set",
        "runner.additional_env_vars[3].value=http://proxy:3128",
        "--set",
        "runner.additional_env_vars[4].name=SECRET_VALUE",
        "--set",
        "runner.additional_env_vars[4].valueFrom.secretKeyRef.name=my-secret",
        "--set",
        "runner.additional_env_vars[4].valueFrom.secretKeyRef.key=value",
        "--set",
        "runner.additional_env_froms[0].secretRef.name=runner-env",
        "--set",
        "runner.setKRRSecurityContext=true",
        "--set",
        "runner.customServiceAccount=custom-sa",
        "--set",
        "global.enableJsonLogsFormat=true",
        "--set",
        "image.registry=registry.local",
    ]
    pod_spec = krr_job_template(extra_args)["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]
    assert pod_spec["serviceAccountName"] == "custom-sa"
    assert container["image"] == "registry.local/krr:v1"
    assert container["resources"] == {"requests": {"memory": "1Gi"}, "limits": {"memory": "3Gi"}}
    assert container["securityContext"] == {
        "runAsNonRoot": True,
        "allowPrivilegeEscalation": False,
        "capabilities": {"drop": ["ALL"]},
        "seccompProfile": {"type": "RuntimeDefault"},
    }
    assert container["envFrom"] == [{"secretRef": {"name": "runner-env"}}]
    assert {"name": "HTTPS_PROXY", "value": "http://proxy:3128"} in container["env"]
    assert {"name": "ENABLE_JSON_LOGS_FORMAT", "value": "true"} in container["env"]
    secret_reference = {"secretKeyRef": {"name": "my-secret", "key": "value"}}
    assert {"name": "SECRET_VALUE", "valueFrom": secret_reference} in container["env"]

    registry_only = krr_job_template(["--set", "image.registry=registry.local"])
    assert registry_only["spec"]["template"]["spec"]["containers"][0]["image"] == "registry.local/krr:v1.30.0"


def test_krr_cronjob_follows_disabled_weekly_playbook():
    docs = render_full_chart(["--set", "disabledPlaybooks[0]=WeeklyKRRScan"])
    assert get_doc(docs, "CronJob", "robusta-krr") is None


def test_krr_cronjob_prometheus_auth_secret_needs_key():
    with pytest.raises(subprocess.CalledProcessError):
        render_full_chart(["--set", "runner.krrCronJob.prometheusAuthSecret.name=prom"])


def test_krr_cronjob_runtime_env_settings(tmp_path):
    arguments = krr_arguments(
        tmp_path,
        ["--set-string", "globalConfig.prometheus_url=\\{\\{ env.PROMETHEUS_URL \\}\\}"],
        env={"KRR_PUBLISH_URL": "http://other/api/trigger", "PROMETHEUS_URL": "http://prometheus:9090"},
    )
    assert arguments[2] == "--publish_scan_url=http://other/api/trigger"
    assert flag_values(arguments, "-p") == ["http://prometheus:9090"]


def test_scheduled_playbook_mentioning_krr_scan_in_params_is_kept():
    docs = render_full_chart(
        [
            "--set",
            "customPlaybooks[0].triggers[0].on_schedule.fixed_delay_repeat.seconds_delay=3600",
            "--set",
            "customPlaybooks[0].actions[0].kubectl_command.command=get pods -l app=krr_scan",
        ]
    )
    assert get_doc(docs, "CronJob", "robusta-krr") is not None


def test_krr_cronjob_env_setting_from_value_from_points_to_values():
    result = subprocess.run(
        [
            "helm",
            "template",
            str(CHART_PATH),
            "--set",
            "clusterName=test",
            "--set",
            "sinksConfig[0].file_sink.name=test",
            "--set",
            "runner.additional_env_vars[0].name=KRR_MEMORY_LIMIT",
            "--set",
            "runner.additional_env_vars[0].valueFrom.configMapKeyRef.name=krr",
            "--set",
            "runner.additional_env_vars[0].valueFrom.configMapKeyRef.key=limit",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "KRR_MEMORY_LIMIT" in result.stderr and "runner.krrCronJob" in result.stderr


def test_krr_cronjob_image_pull_secrets():
    runner_secrets = ["--set", "runner.imagePullSecrets[0].name=runner-registry"]
    pod_spec = krr_job_template(runner_secrets)["spec"]["template"]["spec"]
    assert pod_spec["imagePullSecrets"] == [{"name": "runner-registry"}]

    job_spec_secrets = ["--set", "runner.krrCronJob.jobSpec.imagePullSecrets[0].name=krr-registry"]
    pod_spec = krr_job_template(runner_secrets + job_spec_secrets)["spec"]["template"]["spec"]
    assert pod_spec["imagePullSecrets"] == [{"name": "krr-registry"}]

    assert "imagePullSecrets" not in krr_job_template([])["spec"]["template"]["spec"]


def test_krr_cronjob_strategy_value_takes_precedence_over_env(tmp_path):
    arguments = krr_arguments(tmp_path, ["--set", "runner.krrCronJob.strategy=simple_limit"], env={"KRR_STRATEGY": "simple"})
    assert arguments[1] == "simple_limit"
