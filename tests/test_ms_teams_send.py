from unittest.mock import MagicMock, patch

import pytest

from robusta.integrations.msteams.msteams_msg import MsTeamsMsg


def _mock_response(status_code: int, reason: str, text: str = ""):
    response = MagicMock()
    response.status_code = status_code
    response.reason = reason
    response.text = text
    return response


@pytest.mark.parametrize(
    "status_code, reason, should_log_error",
    [
        (200, "OK", False),
        (201, "Created", False),
        # Power Automate workflow webhooks accept the payload asynchronously and
        # return 202 on success. It must not be logged as an error.
        (202, "Accepted", False),
        (400, "Bad Request", True),
        (500, "Internal Server Error", True),
    ],
)
def test_ms_teams_send_status_code_logging(status_code, reason, should_log_error):
    msg = MsTeamsMsg(webhook_url="http://example.com/webhook", prefer_redirect_to_platform=False)
    response = _mock_response(status_code, reason, text="")

    with patch("robusta.integrations.msteams.msteams_msg.requests.post", return_value=response), patch(
        "robusta.integrations.msteams.msteams_msg.logging"
    ) as mock_logging:
        msg.send()

    if should_log_error:
        assert mock_logging.error.called, f"expected an error log for status {status_code}"
    else:
        mock_logging.error.assert_not_called()
