import logging
import signal
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from http import HTTPStatus
from typing import Any, Generator, NoReturn
from unittest.mock import patch

import kubernetes
import pytest
from kubernetes.client import V1ObjectMeta, V1Pod, V1PodCondition, V1PodStatus
from kubernetes.client.exceptions import ApiException

from robusta.core.discovery.discovery import (
    Discovery,
    extract_ready_pods,
    is_pod_ready,
    resource_ref,
)


# pytest-timeout requires pytest>=7, https://github.com/pytest-dev/pytest-timeout/blob/main/setup.cfg
@contextmanager
def time_limit(seconds: int) -> Generator[None, Any, None]:
    def signal_handler(_signum: Any, _frame: Any) -> NoReturn:
        pytest.fail("Test took to much time...")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def _patch_worker() -> None:
    def _patched(self: Any, **_: Any) -> NoReturn:
        raise ApiException(HTTPStatus.INTERNAL_SERVER_ERROR, reason="Internal Server Error")

    kubernetes.client.CoreV1Api.list_node = _patched


def test_discovery_recovery_on_failure():
    with time_limit(20):
        patched_pool = ProcessPoolExecutor(1, initializer=_patch_worker)
        with patch.object(Discovery, "executor", new=patched_pool):
            with pytest.raises(ApiException):
                Discovery.discover_resources()

            assert patched_pool._shutdown_thread
            assert not Discovery.executor._shutdown_thread 


# ---- is_pod_ready / extract_ready_pods with an unpopulated status ----


def _v1_pod(conditions: Any, name: str = "balloon-pod-pcrkw") -> V1Pod:
    return V1Pod(
        metadata=V1ObjectMeta(name=name, namespace="kube-system"),
        status=V1PodStatus(conditions=conditions),
    )


def test_is_pod_ready_handles_unset_conditions():
    """A pod the API server accepted but kubelet has not reported on yet has
    `status.conditions is None`. This used to raise TypeError, which
    extract_ready_pods swallowed into an ERROR log per discovery cycle."""
    assert is_pod_ready(_v1_pod(None)) is False


def test_is_pod_ready_handles_empty_conditions():
    assert is_pod_ready(_v1_pod([])) is False


@pytest.mark.parametrize(
    "status,expected", [("True", True), ("False", False), ("Unknown", False)]
)
def test_is_pod_ready_reads_ready_condition(status: str, expected: bool):
    pod = _v1_pod([V1PodCondition(type="Ready", status=status)])
    assert is_pod_ready(pod) is expected


def test_is_pod_ready_ignores_other_conditions():
    pod = _v1_pod(
        [
            V1PodCondition(type="PodScheduled", status="True"),
            V1PodCondition(type="Initialized", status="True"),
        ]
    )
    assert is_pod_ready(pod) is False


def test_extract_ready_pods_does_not_log_for_unset_conditions(caplog):
    """The regression this guards: 12 ERROR blocks in 48h of runner logs, each
    dumping the whole pod object."""
    with caplog.at_level(logging.ERROR):
        assert extract_ready_pods(_v1_pod(None)) == 0
    assert not [r for r in caplog.records if "Failed to extract ready pods" in r.getMessage()]


def test_extract_ready_pods_counts_ready_pod():
    pod = _v1_pod([V1PodCondition(type="Ready", status="True")])
    assert extract_ready_pods(pod) == 1


def test_resource_ref_identifies_resource_without_dumping_it():
    """On a genuine failure the ERROR must name the resource, not paste its
    entire spec/status into the log line."""
    ref = resource_ref(_v1_pod(None))
    assert "kube-system/balloon-pod-pcrkw" in ref
    assert "managed_fields" not in ref


def test_resource_ref_survives_a_resource_without_metadata():
    assert resource_ref(object()) == "object"
