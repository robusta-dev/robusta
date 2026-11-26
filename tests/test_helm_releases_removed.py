import logging
import shutil
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from kubernetes.client.exceptions import ApiException

import robusta.api
from robusta.core.discovery import discovery as discovery_module
from robusta.core.discovery.discovery import Discovery, DiscoveryResults
from robusta.core.model import env_vars
from robusta.core.model.runner_config import RunnerConfig
from robusta.core.playbooks.trigger import Trigger
from robusta.runner.web import app
from tests.test_helm_chart import get_doc, render_chart

HELM_TRIGGERS = ["on_helm_release_unhealthy", "on_helm_release_fail", "on_helm_release_deploy"]


def runner_config(active_playbooks):
    return RunnerConfig(playbook_repos={}, sinks_config=[], light_actions=[], active_playbooks=active_playbooks)


def pod_playbook():
    return {"triggers": [{"on_pod_create": {}}], "actions": [{"logs_enricher": {}}]}


@pytest.mark.parametrize("trigger", HELM_TRIGGERS)
def test_helm_trigger_keys_are_not_triggers(trigger):
    with pytest.raises(Exception, match="Exactly one trigger type must be defined"):
        Trigger(**{trigger: {"names": ["app"], "rate_limit": 3600}})


@pytest.mark.parametrize("trigger", HELM_TRIGGERS)
def test_config_skips_helm_release_playbook(trigger, caplog):
    helm_playbook = {
        "name": "HelmReleaseAlerts",
        "triggers": [{trigger: {"namespace": "default"}}],
        "actions": [{"helm_status_enricher": {}}],
    }

    with caplog.at_level(logging.ERROR):
        config = runner_config([helm_playbook, pod_playbook()])

    assert len(config.active_playbooks) == 1
    assert config.active_playbooks[0].get_actions()[0].action_name == "logs_enricher"
    assert trigger in caplog.text
    assert "HelmReleaseAlerts" in caplog.text
    assert "helm_status_enricher" in caplog.text


def test_config_keeps_other_triggers_of_a_mixed_playbook(caplog):
    playbook = {
        "triggers": [{"on_helm_release_fail": {}}, {"on_pod_create": {}}],
        "actions": [{"helm_status_enricher": {}}, {"logs_enricher": {}}],
    }

    with caplog.at_level(logging.ERROR):
        config = runner_config([playbook])

    assert len(config.active_playbooks) == 1
    kept = config.active_playbooks[0]
    assert [t.get().__class__.__name__ for t in kept.triggers] == ["PodCreateTrigger"]
    assert [a.action_name for a in kept.get_actions()] == ["logs_enricher"]
    assert "on_helm_release_fail" in caplog.text


def test_config_skips_playbook_left_without_actions():
    playbook = {"triggers": [{"on_pod_create": {}}], "actions": [{"helm_status_enricher": {}}]}
    assert runner_config([playbook, pod_playbook()]).active_playbooks[0].get_actions()[0].action_name == "logs_enricher"
    assert len(runner_config([playbook]).active_playbooks) == 0


def test_config_without_helm_playbooks_is_unchanged(caplog):
    with caplog.at_level(logging.ERROR):
        config = runner_config([pod_playbook(), pod_playbook()])
    assert len(config.active_playbooks) == 2
    assert caplog.text == ""


@pytest.mark.parametrize("active_playbooks", [None, []])
def test_config_with_no_playbooks(active_playbooks):
    assert not runner_config(active_playbooks).active_playbooks


def test_config_still_rejects_malformed_playbooks():
    with pytest.raises(Exception):
        runner_config([{"triggers": [{"on_unknown_trigger": {}}], "actions": [{"logs_enricher": {}}]}])
    with pytest.raises(Exception):
        runner_config(["not-a-playbook"])


def test_api_does_not_export_helm_release_events():
    assert not hasattr(robusta.api, "HelmReleasesEvent")
    assert not hasattr(robusta.api, "HelmReleasesTriggerEvent")
    assert not hasattr(env_vars, "DISABLE_HELM_MONITORING")


def test_runner_has_no_helm_releases_endpoint():
    response = app.test_client().post("/api/helm-releases", json={"data": []})
    assert response.status_code == 404


def test_discovery_results_have_no_helm_releases():
    assert "helm_releases" not in DiscoveryResults.__fields__


class _FakeApi:
    secret_calls = []

    def __getattr__(self, name):
        def call(*args, **kwargs):
            if "secret" in name:
                _FakeApi.secret_calls.append(name)
                raise ApiException(status=403, reason="Forbidden")
            if name in ("list_cluster_custom_object", "list_namespaced_custom_object"):
                return {"items": [], "metadata": {}}
            return SimpleNamespace(items=[], metadata=SimpleNamespace(_continue=None))

        return call


def test_discovery_does_not_read_secrets():
    _FakeApi.secret_calls = []
    fake_client = SimpleNamespace(
        CoreV1Api=_FakeApi,
        AppsV1Api=_FakeApi,
        BatchV1Api=_FakeApi,
        CustomObjectsApi=_FakeApi,
        RbacAuthorizationV1Api=_FakeApi,
    )
    with patch.object(discovery_module, "client", fake_client):
        results = Discovery.discovery_process()

    assert _FakeApi.secret_calls == []
    assert results.services == []


needs_helm = pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary not available")


def secret_read_rules(docs):
    rules = []
    for kind in ("ClusterRole", "Role"):
        for doc in docs:
            if doc["kind"] != kind or "runner" not in doc["metadata"]["name"]:
                continue
            for rule in doc.get("rules") or []:
                if "" in rule.get("apiGroups", []) and "secrets" in rule.get("resources", []):
                    if {"get", "list", "watch"} & set(rule.get("verbs", [])):
                        rules.append((doc["metadata"]["name"], rule))
    return rules


@needs_helm
@pytest.mark.parametrize(
    "extra_args",
    [
        [],
        ["--set", "monitorHelmReleases=true"],
        ["--set", "monitorHelmReleases=true", "--set", "runner.rbac.namespaceScoped=true"],
        ["--set", "monitorHelmReleases=true", "--set", "runner.rbac.disableCreateFromServiceAccount=true"],
    ],
)
def test_runner_rbac_has_no_secret_read(extra_args):
    docs = render_chart(extra_args)
    assert get_doc(docs, "Deployment", "runner") is not None
    assert secret_read_rules(docs) == []


@needs_helm
@pytest.mark.parametrize("extra_args", [[], ["--set", "monitorHelmReleases=true"]])
def test_runner_env_disables_helm_monitoring_in_older_images(extra_args):
    runner = get_doc(render_chart(extra_args), "Deployment", "runner")
    env = [e for e in runner["spec"]["template"]["spec"]["containers"][0]["env"] if e["name"] == "DISABLE_HELM_MONITORING"]
    assert env == [{"name": "DISABLE_HELM_MONITORING", "value": "True"}]


@needs_helm
def test_custom_cluster_role_rules_still_apply():
    docs = render_chart(
        [
            "--set",
            "runner.customClusterRoleRules[0].apiGroups[0]=",
            "--set",
            "runner.customClusterRoleRules[0].resources[0]=secrets",
            "--set",
            "runner.customClusterRoleRules[0].verbs[0]=get",
        ]
    )
    assert len(secret_read_rules(docs)) == 1
