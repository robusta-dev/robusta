import logging
import shutil

import pytest

from robusta.core.model.runner_config import RunnerConfig
from tests.test_helm_chart import get_doc, render_chart

HELM_TRIGGERS = ["on_helm_release_unhealthy", "on_helm_release_fail", "on_helm_release_deploy"]


def runner_config(active_playbooks):
    return RunnerConfig(playbook_repos={}, sinks_config=[], light_actions=[], active_playbooks=active_playbooks)


def pod_playbook():
    return {"triggers": [{"on_pod_create": {}}], "actions": [{"logs_enricher": {}}]}


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


needs_helm = pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary not available")


@needs_helm
@pytest.mark.parametrize("extra_args", [[], ["--set", "monitorHelmReleases=true"]])
def test_runner_env_disables_helm_monitoring_in_older_images(extra_args):
    runner = get_doc(render_chart(extra_args), "Deployment", "runner")
    env = [
        e for e in runner["spec"]["template"]["spec"]["containers"][0]["env"] if e["name"] == "DISABLE_HELM_MONITORING"
    ]
    assert env == [{"name": "DISABLE_HELM_MONITORING", "value": "True"}]
