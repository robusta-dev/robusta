from unittest.mock import MagicMock, patch

from robusta.integrations.kubernetes.api_client_utils import get_pod_logs


def _get_logs_for(raw_logs: bytes) -> str:
    with patch("robusta.integrations.kubernetes.api_client_utils.core_v1_api") as mock_core_v1_api:
        read_log = mock_core_v1_api.CoreV1Api.return_value.read_namespaced_pod_log
        read_log.return_value = MagicMock(data=raw_logs)
        return get_pod_logs("pod", "default")


def test_get_pod_logs_decodes_valid_utf8():
    assert _get_logs_for("héllo\nwörld".encode("utf-8")) == "héllo\nwörld"


def test_get_pod_logs_survives_bytes_that_are_not_valid_utf8():
    # jsoniter writes raw 0xff bytes into its error messages
    logs = _get_logs_for(b"readUint64: unexpected character: \xff, error found\nnext line")

    assert logs == "readUint64: unexpected character: �, error found\nnext line"
