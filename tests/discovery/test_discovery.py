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

from robusta.core.discovery.discovery import Discovery, extract_ready_pods, is_pod_ready


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


# ---- is_pod_ready with an unpopulated status ----


def _pod(status: Any) -> V1Pod:
    return V1Pod(metadata=V1ObjectMeta(name="p", namespace="kube-system"), status=status)


@pytest.mark.parametrize("status", [None, V1PodStatus(conditions=None), V1PodStatus(conditions=[])])
def test_is_pod_ready_handles_unpopulated_status(status: Any):
    """Regression: a pod kubelet has not reported on yet raised TypeError, which
    extract_ready_pods logged as an ERROR with the whole pod dumped into it."""
    assert is_pod_ready(_pod(status)) is False


@pytest.mark.parametrize("condition_status,expected", [("True", True), ("False", False)])
def test_is_pod_ready_reads_ready_condition(condition_status: str, expected: bool):
    pod = _pod(V1PodStatus(conditions=[V1PodCondition(type="Ready", status=condition_status)]))
    assert is_pod_ready(pod) is expected


def test_is_pod_ready_ignores_other_conditions():
    pod = _pod(V1PodStatus(conditions=[V1PodCondition(type="PodScheduled", status="True")]))
    assert is_pod_ready(pod) is False


def test_extract_ready_pods_does_not_log_for_unpopulated_status(caplog):
    with caplog.at_level(logging.ERROR):
        assert extract_ready_pods(_pod(None)) == 0
    assert not caplog.records
