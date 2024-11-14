import signal
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from http import HTTPStatus
from typing import Any, Generator, NoReturn
from unittest.mock import patch

import kubernetes
import pytest
from kubernetes.client.exceptions import ApiException

from robusta.core.discovery.discovery import Discovery


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
