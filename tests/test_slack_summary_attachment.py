"""Tests for the file attachment on the Slack "Alerts Summary" digest (ROB-3946 / FRO-211).

The digest can only show part of a large table, so the complete one is attached as a file.
Slack files are immutable while the message is rewritten on every notification, so these tests
pin down the upload/refresh/delete lifecycle.
"""
import time
from unittest.mock import MagicMock, patch

import pytest

from robusta.core.sinks.sink_base import NotificationSummary
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams

SUMMARY_HEADER = ["label:site", "label:component"]
GROUP_HEADER = ["cluster: prod-nj1"]


@pytest.fixture
def slack():
    """A SlackSender wired to a mock Slack client, plus the recorded uploads/deletes."""
    with patch("robusta.integrations.slack.sender.WebClient") as web_client:
        from robusta.integrations.slack.sender import SlackSender

        client = MagicMock()
        uploads, deletes = [], []

        def upload(**kwargs):
            uploads.append(kwargs)
            return {"file": {"permalink": f"https://files.slack.com/f{len(uploads)}", "id": f"F{len(uploads)}"}}

        client.files_upload_v2.side_effect = upload
        client.files_delete.side_effect = lambda **kwargs: deletes.append(kwargs["file"])
        client.chat_postMessage.return_value = {"ts": "111.1", "channel": "C1"}
        client.chat_update.return_value = {"ts": "111.1", "channel": "C1"}
        web_client.return_value = client

        sender = SlackSender("xoxb-test", "account", "prod-nj1", "key", "chan", registry=None)
        yield sender, client, uploads, deletes


def _table(n_groups):
    return {
        (f"ats.betting.betcatcher.validation.impl.Validator{i:03d}Foo", "nj"): [i % 7, i % 3]
        for i in range(n_groups)
    }


def _send(sender, summary_table, state, **kwargs):
    return sender.send_or_update_summary_message(
        GROUP_HEADER,
        SUMMARY_HEADER,
        summary_table,
        SlackSinkParams(name="test", slack_channel="chan", api_key=""),
        False,
        time.time(),
        False,
        grouping_interval=86400,
        channel="chan",
        summary_state=state,
        **kwargs,
    )


def test_no_attachment_when_the_table_fits(slack):
    sender, client, uploads, _ = slack

    _send(sender, _table(1), NotificationSummary())

    assert uploads == []  # nothing was dropped, so there is nothing to attach
    assert "files.slack.com" not in str(client.chat_postMessage.call_args.kwargs["blocks"])


def test_attaches_the_full_table_when_rows_are_dropped(slack):
    sender, client, uploads, _ = slack
    state = NotificationSummary()

    _send(sender, _table(200), state)

    assert len(uploads) == 1
    assert state.attachment_permalink and state.attachment_file_id
    # Every group is in the file, even though the message only shows a fraction of them.
    assert uploads[0]["content"].decode().count("Validator") == 200

    kwargs = client.chat_postMessage.call_args.kwargs
    assert any("files.slack.com" in str(block) for block in kwargs["blocks"])
    # Slack only shares an uploaded file if it is referenced from the message text too.
    assert "files.slack.com" in kwargs["text"]


def test_attachment_is_throttled_across_updates(slack):
    sender, _, uploads, _ = slack
    state = NotificationSummary()

    _send(sender, _table(200), state)
    sender.channel_name_to_id["chan"] = "C1"
    _send(sender, _table(200), state, msg_ts="111.1")

    assert len(uploads) == 1  # the message is rewritten per notification, the file is not


def test_refreshing_the_attachment_deletes_the_previous_file(slack):
    sender, _, uploads, deletes = slack
    state = NotificationSummary()

    _send(sender, _table(200), state)
    state.attachment_ts = 0  # pretend the throttle window elapsed
    sender.channel_name_to_id["chan"] = "C1"
    _send(sender, _table(200), state, msg_ts="111.1")

    assert len(uploads) == 2
    assert deletes == ["F1"]


def test_previous_interval_file_is_cleaned_up_after_reset(slack):
    sender, _, uploads, deletes = slack
    state = NotificationSummary()
    _send(sender, _table(200), state)

    state.start_ts = time.time() - 999999  # force the interval to expire
    state.register_notification(("x", "y"), False, 86400)
    # The link is dropped so the new summary can't point at the old file, but the id is kept
    # so the next upload can still delete it.
    assert state.attachment_permalink is None
    assert state.attachment_file_id == "F1"

    _send(sender, _table(200), state)
    assert deletes == ["F1"]


def test_upload_failure_does_not_break_the_summary(slack):
    sender, client, _, _ = slack
    client.files_upload_v2.side_effect = Exception("no files:write scope")

    ts = _send(sender, _table(200), NotificationSummary())

    assert ts == "111.1"  # the digest is still posted, just without the attachment
    assert "files.slack.com" not in str(client.chat_postMessage.call_args.kwargs["blocks"])
