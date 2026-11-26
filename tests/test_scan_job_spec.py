import logging
from unittest.mock import MagicMock

import pytest

from playbooks.robusta_playbooks import krr
from playbooks.robusta_playbooks.krr import KRRParams
from playbooks.robusta_playbooks.popeye import PopeyeParams

SCHEDULING_SPEC = {
    "tolerations": [{"key": "appname", "operator": "Equal", "value": "robusta", "effect": "NoSchedule"}],
    "nodeSelector": {"kubernetes.io/os": "linux"},
}

UNSUPPORTED_SPECS = [
    {"initContainers": [{"name": "extra", "image": "busybox"}]},
    {"volumes": [{"name": "host", "hostPath": {"path": "/"}}]},
    {"hostPID": True},
    {"hostNetwork": True},
    {"nodeName": "node-1"},
    {"securityContext": {"runAsUser": 0}},
    {"tolerations": [], "ephemeralContainers": []},
]


def test_scheduling_fields_are_accepted():
    assert KRRParams(krr_job_spec=SCHEDULING_SPEC).krr_job_spec == SCHEDULING_SPEC
    assert PopeyeParams(popeye_job_spec=SCHEDULING_SPEC).popeye_job_spec == SCHEDULING_SPEC


def test_job_spec_defaults_to_empty():
    assert KRRParams().krr_job_spec == {}
    assert PopeyeParams().popeye_job_spec == {}


@pytest.mark.parametrize("job_spec", UNSUPPORTED_SPECS)
def test_other_pod_spec_fields_are_rejected(job_spec):
    with pytest.raises(ValueError):
        KRRParams(krr_job_spec=job_spec)
    with pytest.raises(ValueError):
        PopeyeParams(popeye_job_spec=job_spec)


def test_krr_scan_with_cronjob_logs_where_to_configure_it(monkeypatch, caplog):
    monkeypatch.setattr(krr, "KRR_CRONJOB_ENABLED", True)
    run_job = MagicMock()
    monkeypatch.setattr(krr.RobustaJob, "run_simple_job_spec", run_job)

    with caplog.at_level(logging.ERROR):
        krr.krr_scan(MagicMock(), KRRParams())

    assert "runner.krrCronJob.schedule" in caplog.text
    run_job.assert_not_called()
